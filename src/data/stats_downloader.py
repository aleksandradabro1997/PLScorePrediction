# Download all available data from official Premier League site
# https://github.com/aleksandradabro1997/PLScorePrediction.git

import abc
import wget


from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


from mappings import SEASON_TO_PAGE_NUMBER, STAT_NAME_TO_PAGE_NAME_CLUB, STAT_NAME_TO_PAGE_NAME_PLAYER


class StatsType(Enum):
    player = 0
    club = 1
    all = 2


@dataclass
class PlayerStatsDownloaderConfig:
    name: str


@dataclass
class ClubStatsDownloaderConfig:
    name: str


@dataclass
class StatsDownloaderConfig:
    seasons: List[str]     # List with either 'all' or '2021/20, 2020/2019 ...'
    players: List[PlayerStatsDownloaderConfig]
    clubs: List[ClubStatsDownloaderConfig]


PATTERNS = {'player name': '',
            'club name': '',
            'stat': '(<td class="mainStat text-centre">)([0-9]*)(</td>)'}


class BaseStatsDownloader(abc.ABC):
    url = ''
    patterns = PATTERNS
    season_to_number_map = SEASON_TO_PAGE_NUMBER
    stat_name_to_page_map = None

    @abc.abstractmethod
    def download(self):
        pass

    def stat_to_page(self, stat_name: str) -> str:
        """
        Converts name of the statistics to its web subpage.
        :param stat_name: name of the statistics to download
        :return: subpage name
        """
        return self.stat_name_to_page_map.get(stat_name, None)

    def season_to_number(self, season: str) -> Optional[int]:
        """
        Converts season string to number.
        Example: '2021/22' -> 418
        https://www.premierleague.com/stats/top/clubs/total_pass?se=418 <- the number at the end corresponds to season
        :param season: string representing season
        :return: number corresponding to season
        """
        return self.season_to_number_map.get(season, None)


class PlayerStatsDownloader(BaseStatsDownloader):
    """
    Download all available stats for particular player, that is specified in PlayerStatsConfig.
    """
    url = 'https://www.premierleague.com/stats/top/players'
    available_stats = ['goals', 'assists', 'appearances', 'minutes_played', 'yellow cards', 'red cards',
                       'substituted on', 'substituted off', 'shots', 'shots on target', 'hit woodwork',
                       'goals from header', 'goals from penalty', 'goals from freekick', 'offsides', 'touches',
                       'passes', 'through balls', 'crosses', 'corners taken', 'blocks', 'interceptions', 'tackles',
                       'last man tackles', 'clearances', 'headed clearances', 'aerial battles won', 'own goals',
                       'errors leading to goal', 'penalties conceded', 'fouls', 'aerial battles lost', 'clean sheets',
                       'goals conceded', 'saves', 'penalties saved', 'punches', 'high claims', 'sweeper clearances',
                       'throw outs', 'goal kicks']
    stat_name_to_page_map = STAT_NAME_TO_PAGE_NAME_PLAYER

    def download(self):
        pass

    def _get_named_stat(self, season: str, stat_name: str) -> Optional[int]:
        season_number = self.season_to_number(season=season)
        stat_url = '/'.join([self.url])
        pass


class ClubStatsDownloader(BaseStatsDownloader):
    """
    Download all available stats for particular player, that is specified in ClubStatsDownloaderConfig.
    """
    url = 'https://www.premierleague.com/stats/top/clubs'
    available_stats = ['wins', 'losses', 'goals', 'yellow cards', 'red_cards', 'substitutions on',
                       'clean sheets', 'goals conceded', 'saves', 'blocks', 'interceptions', 'tackles',
                       'last man tackles', 'clearances', 'headed clearances', 'caught opponent offside',
                       'own goals', 'penalties conceded', 'goals conceded from penalty', 'fouls',
                       'shots', 'shots on target', 'hit woodwork', 'goals from header', 'goals from penalty',
                       'goals from freekick', 'goals from inside box', 'goals from outside box',
                       'goals from counter attack', 'offsides', 'passes', 'through balls', 'long passes',
                       'backwards passes', 'crosses', 'corners taken']
    stat_name_to_page_map = STAT_NAME_TO_PAGE_NAME_CLUB

    def download(self):
        pass

    def _get_named_stat(self, season: str, stat_name: str) -> Optional[int]:
        season_number = self.season_to_number(season=season)
        stat_url = '/'.join([self.url])
        pass


class StatsDownloader:
    """
    Main downloader class.
    """
    def __init__(self, config: StatsDownloaderConfig):
        self.config = config
        self.player_downloader = PlayerStatsDownloader()
        self.club_downloader = ClubStatsDownloader()