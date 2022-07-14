import time
import logging
import requests
import bs4.element

from bs4 import BeautifulSoup
from typing import List, Dict

from src.data.mappings import CLUB_TO_PAGE_STATS
from src.data.downloaders.config import StatsDownloaderConfig


# Create logger for stats
stats_logger = logging.getLogger('StatsLogger')
stats_logger.setLevel(logging.INFO)


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
        time.sleep(5)
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
