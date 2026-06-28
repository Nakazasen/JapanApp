"""Dev.to API client for English tech articles.

Dev.to is a popular English developer community with quality articles.
Uses their public API.
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import List, Optional

from frontend.services.news.base_client import (
    BaseNewsClient, Article, SourceType, SourceLanguage
)


class DevToClient(BaseNewsClient):
    """Client for fetching articles from Dev.to.
    
    Dev.to has a free public API with trending articles.
    """
    
    BASE_URL = "https://dev.to/api"
    ARTICLES_ENDPOINT = "/articles"
    
    def __init__(self):
        super().__init__()
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def source_name(self) -> str:
        return "Dev.to"

    @property
    def source_url(self) -> str:
        return "https://dev.to"
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.API
    
    @property
    def source_language(self) -> SourceLanguage:
        return SourceLanguage.ENGLISH
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "EnglishApp/1.0 TechHub",
                    "Accept": "application/json"
                }
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def fetch_articles(
        self,
        tags: Optional[List[str]] = None,
        max_articles: int = 20,
        page: int = 1
    ) -> List[Article]:
        """Fetch trending articles from Dev.to.
        
        Args:
            tags: Optional tag filters (e.g., ["python", "ai"])
            max_articles: Maximum articles to return
            page: Page number for pagination
            
        Returns:
            List of Article objects
        """
        try:
            session = await self._get_session()
            articles = []
            
            # Build query params
            params = {
                "per_page": min(max_articles, 30),
                "page": page,
            }
            
            # Add tag filter
            if tags:
                params["tag"] = tags[0].lower()  # Dev.to API takes single tag
            
            async with session.get(
                f"{self.BASE_URL}{self.ARTICLES_ENDPOINT}",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = self._parse_articles(data)
                elif response.status == 429:
                    print("[DevToClient] Rate limited")
                else:
                    print(f"[DevToClient] HTTP {response.status}")
            
            return articles[:max_articles]
            
        except Exception as e:
            print(f"[DevToClient] Error: {e}")
            return []
    
    def _parse_articles(self, data: List[dict]) -> List[Article]:
        """Parse Dev.to API response into Article objects."""
        articles = []
        
        for item in data:
            try:
                # Parse publication date
                published_at = None
                if item.get("published_at"):
                    try:
                        # ISO format: 2024-12-28T10:30:00Z
                        published_at = datetime.fromisoformat(
                            item["published_at"].replace("Z", "+00:00")
                        )
                    except Exception:
                        pass
                
                # Extract tags
                tags = item.get("tag_list", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",")]
                
                article = Article(
                    id=str(item.get("id", "")),
                    title=item.get("title", "Untitled"),
                    url=item.get("url", ""),
                    source_name=self.source_name,
                    language=self.source_language,
                    author=item.get("user", {}).get("username", ""),
                    summary=item.get("description", ""),
                    content=item.get("body_markdown", ""),  # May be empty
                    published_at=published_at,
                    tags=tags,
                    upvotes=item.get("public_reactions_count", 0),
                    comments_count=item.get("comments_count", 0),
                    thumbnail_url=item.get("cover_image", None)
                )
                articles.append(article)
                
            except Exception as e:
                print(f"[DevToClient] Error parsing article: {e}")
                continue
        
        return articles
    
    async def fetch_article_content(self, article_id: str) -> Optional[str]:
        """Fetch full content of an article by ID."""
        try:
            session = await self._get_session()
            
            async with session.get(
                f"{self.BASE_URL}{self.ARTICLES_ENDPOINT}/{article_id}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("body_markdown", "") or data.get("body_html", "")
            
            return None
            
        except Exception as e:
            print(f"[DevToClient] Error fetching content: {e}")
            return None
