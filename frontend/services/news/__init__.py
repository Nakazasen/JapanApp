"""News aggregation module for Real-time Tech Hub.

This module provides:
- Multi-source news aggregation (Japan + Global)
- Smart filtering based on tech tags
- Extensible client architecture

Structure:
- base_client.py: Abstract base class for all API clients
- qiita_client.py: Qiita API client (Japan)
- zenn_client.py: Zenn.dev crawler (Japan - future)
- hacker_news_client.py: Hacker News API (Global - future)
- smart_filter.py: Tag-based filtering engine
- aggregator.py: Main aggregator combining all sources
"""

from frontend.services.news.base_client import BaseNewsClient, Article
from frontend.services.news.smart_filter import SmartFilter, HARDCORE_TAGS
from frontend.services.news.qiita_client import QiitaClient

__all__ = [
    'BaseNewsClient',
    'Article', 
    'SmartFilter',
    'HARDCORE_TAGS',
    'QiitaClient',
]
