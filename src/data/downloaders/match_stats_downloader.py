import re
import logging
import requests
import bs4.element

from bs4 import BeautifulSoup
from typing import List, Dict, Tuple

from src.data.enums import TeamType


# Create logger for MatchStatsDownloader
stats_logger = logging.getLogger('MatchStatsDownloaderLogger')
stats_logger.setLevel(logging.INFO)


class MatchStatsDownloader:

    def _download_and_parse(self, url: str):
        response = requests.get(url)
        if response.status_code != 200:
            stats_logger.error(f'Unable to download data from page {url}. Got response code: {response.status_code}')

        page_soup = BeautifulSoup(response.text, 'html.parser')
        stats = self._get_match_stats(page=page_soup)
        return stats

    def _get_attendance(self, tag) -> int:
        attendance = -1
        tag_text = tag.text.lower().replace(u'\xa0', u'')
        if 'attendance' in tag_text:
            attendance_pattern = "([attendance: ]*)([0-9,]*)"
            match_att = re.match(attendance_pattern, tag_text)
            if match_att:
                attendance = float(match_att.group(2).replace(',', '.')) * 1000
        return attendance

    def _get_referee(self, tag) -> str:
        referee = ''
        tag_text = tag.text.lower().replace(u'\xa0', u' ').replace('(', '').replace(')', '')
        if 'referee' in tag_text:
            referee_pattern = "([a-z]*:)([ a-z]*)(referee)"
            match_ref = re.match(referee_pattern, tag_text)
            if match_ref and match_ref.group(3) == 'referee':
                referee = match_ref.group(2).strip()
        return referee

    def _get_players(self, page: BeautifulSoup, team: TeamType) -> List[str]:
        players = []
        id = 'a' if team == team.home else 'b'
        lineup = page.find('div', {'class': 'lineup', 'id': id})
        if len(lineup) % 2 != 0:
            logging.warning('Number of records in lineup not even! Some data may be missing!')

        for player in lineup:
            if not player.text.lower().isdigit():
                player.append(player.text.lower())

        return players

    def _get_extra_team_stats(self, page: BeautifulSoup) -> Dict[str, int]:
        tag = page.find('div', {'id': 'team_stats_extra'})
        extra_team_stats = {}
        keys = ['fouls', 'crosses', 'corners', 'touches', 'tackles', 'interceptions', 'aerials won',
                'clearances', 'offsides', 'goal kicks', 'throw ins', 'long balls']

        for k in keys:
            stats = re.search(f' ([0-9]+)([{k}]+)([0-9]+) ',
                              tag.text.lower().replace(u'\xa0', u' ').replace(u'\n', u' '))
            if stats:
                stats = stats.groups()
            else:
                continue

            if len(stats) != 3:  # 3 because format is 'x stat y'
                stats_logger.warning(f'Dropping stat {k}, non-regular length! Result: {stats}')
            else:
                extra_team_stats[f'ht_{k}'] = int(stats[0])
                extra_team_stats[f'at_{k}'] = int(stats[-1])

        return extra_team_stats

    def _get_possesion(self) -> Tuple:
        pass

    def _get_passing_accuracy(self):
        pass

    def _get_cards(self):
        pass

    def _get_match_stats(self, page: BeautifulSoup) -> Dict:
        # Get managers and captains from scorebox
        match_stats = {}
        scorebox = page.find(class_='scorebox')
        datapoints = scorebox.find_all('div', {'class': 'datapoint'})
        scorebox_data_keys = ['ht_manager', 'ht_captain', 'at_manager', 'at_captain']

        if len(datapoints) != 4:
            stats_logger.warning(f'Not enough data in scorebox - found only {str(datapoints)}')

        for key, datapoint in zip(scorebox_data_keys, datapoints):
            match_stats[key] = datapoint.text.split(':')[-1].lower().strip().replace(u'\xa0', u' ')

        scorebox_meta = page.find(class_='scorebox_meta').find_all('div')
        attendance = -1
        referee = ''
        for meta_tag in scorebox_meta:
            if attendance == -1:
                attendance = self._get_attendance(tag=meta_tag)
            if referee == '':
                referee = self._get_referee(tag=meta_tag)

        match_stats['attendance'] = attendance
        match_stats['referee'] = referee

        match_stats['extra_team_stats'] = self._get_extra_team_stats(page=page)

        return match_stats

    def download(self, url: str):
        self._download_and_parse(url=url)
