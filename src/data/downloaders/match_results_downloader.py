import bs4
import time
import logging
import requests

from bs4 import BeautifulSoup
from typing import Optional, List, Dict

from src.data.mappings import SEASON_TO_PAGE_MATCHES
from src.data.downloaders.config import BaseDownloaderConfig
from src.data.downloaders.match_stats_downloader import MatchStatsDownloader


# Create logger for MatchStatsDownloader
stats_logger = logging.getLogger('MatchResultsDownloaderLogger')
stats_logger.setLevel(logging.INFO)


class MatchResultsDownloader:
    season_to_url = SEASON_TO_PAGE_MATCHES

    def __init__(self, config: BaseDownloaderConfig):
        self.config = config
        self.match_stats_downloader = MatchStatsDownloader()

    def _get_url_based_on_season(self, season: str) -> Optional[str]:
        return self.season_to_url.get(season, None)

    def _get_home_team(self, stats_table: bs4.element.ResultSet) -> List[str]:
        home_teams = []
        for elem in stats_table.find_all(class_='right'):
            if 'data-stat' in elem.attrs.keys() and 'squad_a' == elem.attrs['data-stat']:
                if any(l.isalpha() for l in elem.text):
                    home_teams.append(elem.text.lower())
        return home_teams

    def _get_score(self, stats_table: bs4.element.ResultSet) -> List[str]:
        scores = []
        for elem in stats_table.find_all(class_='center'):
            if 'data-stat' in elem.attrs.keys() and 'score' == elem.attrs['data-stat']:
                if any(l.isnumeric() for l in elem.text):
                    scores.append(elem.text.lower())
        return scores

    def _get_away_team(self, stats_table: bs4.element.ResultSet) -> List[str]:
        away_team = []
        for elem in stats_table.find_all(class_='left'):
            if 'data-stat' in elem.attrs.keys() and 'squad_b' == elem.attrs['data-stat']:
                if any(l.isalpha() for l in elem.text):
                    away_team.append(elem.text.lower())
        return away_team

    def _consolidate_data(self, home_team: List, away_team: List, scores: List) -> Optional[Dict[str, List]]:
        if not len(home_team) == len(away_team) == len(scores):
            stats_logger.error('Home team, away team and scores list differ in length!')
            return None
        return {'home_team': home_team,
                'scores': scores,
                'away_team': away_team}

    def _get_stats_table(self, page: BeautifulSoup):
        stats_table = page.find_all(class_='stats_table')
        return stats_table[0]

    def _get_match_report_link(self, stats_table: bs4.element.ResultSet) -> List[str]:
        links = []
        for elem in stats_table.find_all(class_='left'):
            if 'data-stat' in elem.attrs.keys() and 'match_report' == elem.attrs['data-stat']:
                link = elem.next.get('href')
                if link:
                    links.append(link)
        return links

    def _get_matches_stats(self, links: List[str]):
        base = 'https://fbref.com'
        for link in links:
            self._get_match_stats(link=base + link)

    def _download_and_parse(self, url: str):
        time.sleep(5)
        response = requests.get(url)
        if response.status_code != 200:
            stats_logger.error(f'Unable to download data from page {url}. Got response code: {response.status_code}')

        page_soup = BeautifulSoup(response.text, 'html.parser')
        stats = self._get_stats_table(page_soup)
        home_team = self._get_home_team(stats_table=stats)
        away_team = self._get_away_team(stats_table=stats)
        score = self._get_score(stats_table=stats)

        match_stats_links = self._get_match_report_link(stats_table=stats)
        matches_stats = []
        for link in match_stats_links:
            full_link = f'http://fbref.com{link}'
            matches_stats.append(self.match_stats_downloader.download(url=full_link))

        matches_dict = self._consolidate_data(home_team, away_team, score)
        return matches_dict

    def download(self) -> Dict:
        all_data = {}
        if 'all' in self.config.seasons:
            seasons_to_download = self.season_to_url.keys()
        else:
            seasons_to_download = self.config.seasons

        for season in seasons_to_download:
            season_url = self._get_url_based_on_season(season)
            if not season_url:
                stats_logger.warning(f'No season {season} available! Skipping ...')
                continue
            else:
                season_data = self._download_and_parse(season_url)
                all_data[season] = season_data
        return all_data
