# Download all available data from https://fbref.com
# https://github.com/aleksandradabro1997/PLScorePrediction.git

import logging

import bs4.element
import requests

from enum import Enum
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional, List, Union, Tuple, Dict


from mappings import SEASON_TO_PAGE_MATCHES, CLUB_TO_PAGE_STATS


# Create logger for stats
stats_logger = logging.getLogger('StatsLogger')
stats_logger.setLevel(logging.INFO)


class StatsType(Enum):
    player = 0
    club = 1
    all = 2


@dataclass
class BaseDownloaderConfig:
    seasons: List[str] = field(default_factory=lambda: ['2021/2022'])  # List with '2021/2022, 2020/2021 ...'


@dataclass
class SpecificStatsDownloaderConfig(BaseDownloaderConfig):
    stats: List[str] = field(default_factory=lambda: ['all'])  # List with either 'all' or the name of stat
    names: List[str] = field(default_factory=lambda: ['all'])  # List with either 'all' or the name ex: Watford


@dataclass
class StatsDownloaderConfig:
    match_results_config: BaseDownloaderConfig = BaseDownloaderConfig()
    players_stats_config: SpecificStatsDownloaderConfig = SpecificStatsDownloaderConfig()
    clubs_stats_config: SpecificStatsDownloaderConfig = SpecificStatsDownloaderConfig()


class MatchResultsDownloader:
    season_to_url = SEASON_TO_PAGE_MATCHES

    def __init__(self, config: BaseDownloaderConfig):
        self.config = config

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

    def _download_and_parse(self, url: str):
        response = requests.get(url)
        if response.status_code != 200:
            stats_logger.error(f'Unable to download data from page {url}. Got response code: {response.status_code}')

        page_soup = BeautifulSoup(response.text, 'html.parser')
        stats = self._get_stats_table(page_soup)
        home_team = self._get_home_team(stats_table=stats)
        away_team = self._get_away_team(stats_table=stats)
        score = self._get_score(stats_table=stats)

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


class ClubsStatsDownloader:
    club_to_url = CLUB_TO_PAGE_STATS

    def __init__(self, config: StatsDownloaderConfig):
        self.config = config

    def _get_url_based_on_clubs_name(self, club: str):
        return self.club_to_url.get(club, None)

    def _get_and_parse_rows(self, stats_table: bs4.element.Tag) -> List[Dict]:
        rows = stats_table.find_all('tr')
        parsed_rows = []
        for row in rows:
            cols = row.find_all('td')
            club_stats_row = {}
            for col in cols:
                club_stats_row[col.attrs['data-stat']] = col.getText()
            parsed_rows.append(club_stats_row)
        return parsed_rows

    def _get_stats_table(self, page: BeautifulSoup):
        table = page.find('table', attrs={'id': 'comps_fa_club_league'})
        table_body = table.find('tbody')
        return table_body

    def _download_and_parse(self, url: str):
        response = requests.get(url)
        if response.status_code != 200:
            stats_logger.error(f'Unable to download data from page {url}. Got response code: {response.status_code}')

        page_soup = BeautifulSoup(response.text, 'html.parser')
        stats = self._get_stats_table(page_soup)
        club_stats = self._get_and_parse_rows(stats_table=stats)

        return club_stats

    def download(self) -> Dict:
        all_stats = {}

        if 'all' in self.config.clubs_stats_config.names:
            clubs_to_download = self.club_to_url.keys()
        else:
            clubs_to_download = self.config.clubs_stats_config.names

        for club_name in clubs_to_download:
            club_stats_url = self._get_url_based_on_clubs_name(club=club_name)

            if not club_stats_url:
                stats_logger.warning(f'No {club_name} stats available! Skipping ...')
                continue
            else:
                club_stats = self._download_and_parse(url=club_stats_url)
                all_stats[club_name] = club_stats

        return all_stats
