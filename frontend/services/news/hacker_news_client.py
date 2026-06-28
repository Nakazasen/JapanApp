"""Hacker News API client for global tech articles.

API Documentation: https://github.com/HackerNews/API
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

from frontend.services.news.base_client import (
    BaseNewsClient, Article, SourceLanguage, SourceType
)


class HackerNewsClient(BaseNewsClient):
    """Hacker News API client."""
    
    API_BASE = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def source_name(self) -> str:
        return "Hacker News"
    
    @property
    def source_url(self) -> str:
        return "https://news.ycombinator.com"
    
    @property
    def source_language(self) -> SourceLanguage:
        return SourceLanguage.ENGLISH
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.API
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.DEFAULT_HEADERS)
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            
    def _parse_item(self, data: Dict[str, Any]) -> Article:
        """Convert HN item to Article."""
        # Note: HN doesn't have thumbnails or summary in API easy to fetch
        return Article(
            id=str(data.get('id')),
            title=data.get('title', 'Untitled'),
            url=data.get('url') or f"https://news.ycombinator.com/item?id={data.get('id')}",
            source_name=self.source_name,
            language=self.source_language,
            author=data.get('by'),
            published_at=datetime.fromtimestamp(data.get('time', 0)) if data.get('time') else None,
            upvotes=data.get('score', 0),
            comments_count=data.get('descendants', 0),
            summary=data.get('text'), # For story text items
            content=data.get('text'),
        )

    async def fetch_articles(
        self,
        tags: Optional[List[str]] = None,
        max_articles: int = 20,
        page: int = 1
    ) -> List[Article]:
        """Fetch top stories from Hacker News."""
        session = await self._get_session()
        
        try:
            # 1. Get Top Story IDs
            url_top = f"{self.API_BASE}/topstories.json"
            async with session.get(url_top) as response:
                if response.status != 200:
                    print(f"[WARN HNClient] Failed to fetch top stories: {response.status}")
                    return []
                story_ids = await response.json()
            
            # 2. Paginate IDs
            start_idx = (page - 1) * max_articles
            end_idx = start_idx + max_articles
            paged_ids = story_ids[start_idx:end_idx]
            
            # 3. Fetch details for each story in parallel
            articles = []
            tasks = []
            for item_id in paged_ids:
                tasks.append(self._fetch_item(session, item_id))
            
            items = await asyncio.gather(*tasks)
            for item in items:
                if item:
                    articles.append(self._parse_item(item))
            
            return articles
            
        except Exception as e:
            print(f"[ERROR HNClient] Failed to fetch articles: {e}")
            return []

    async def _fetch_item(self, session: aiohttp.ClientSession, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single item by ID."""
        url = f"{self.API_BASE}/item/{item_id}.json"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception:
            return None

    async def fetch_article_content(self, article: Article) -> Article:
        """HN stories usually point to external URLs. 
        Full content scraping is handled by other services if needed.
        """
        return article
