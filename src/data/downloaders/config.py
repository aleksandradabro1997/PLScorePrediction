from typing import List
from dataclasses import dataclass, field


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