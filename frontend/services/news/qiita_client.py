"""Qiita API client for fetching Japanese tech articles.

Qiita (https://qiita.com) is THE platform for Japanese developers.
Think of it as Dev.to + Medium for Japan.

API Documentation: https://qiita.com/api/v2/docs

Rate Limits:
- Without auth: 60 requests/hour
- With auth: 1000 requests/hour

Popular tags:
- Python, MachineLearning, DeepLearning, AI
- Docker, Kubernetes, GitHub, AWS
- React, Vue.js, TypeScript
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode

from frontend.services.news.base_client import (
    BaseNewsClient, Article, SourceLanguage, SourceType
)


class QiitaClient(BaseNewsClient):
    """Qiita API client for Japanese tech articles.
    
    Usage:
        client = QiitaClient()
        
        # Fetch Python articles
        articles = await client.fetch_articles(tags=["python"], max_articles=20)
        
        # Fetch article content
        article = await client.fetch_article_content(articles[0])
        print(article.content)
    """
    
    API_BASE = "https://qiita.com/api/v2"
    
    # Default tags to fetch if none specified
    DEFAULT_TAGS = [
        "Python",
        "MachineLearning", 
        "DeepLearning",
        "AI",
        "LLM",
        "OpenAI",
        "ChatGPT",
        "Docker",
        "GitHub",
    ]
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize Qiita client.
        
        Args:
            access_token: Optional Qiita API token for higher rate limits.
                          Get one at: https://qiita.com/settings/applications
        """
        self.access_token = access_token
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def source_name(self) -> str:
        return "Qiita"
    
    @property
    def source_url(self) -> str:
        return "https://qiita.com"
    
    @property
    def source_language(self) -> SourceLanguage:
        return SourceLanguage.JAPANESE
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.API
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional auth."""
        headers = self.DEFAULT_HEADERS.copy()
        headers["Accept"] = "application/json"
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self._get_headers())
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string."""
        if not dt_str:
            return None
        try:
            # Qiita uses ISO 8601 format: 2024-01-15T12:30:00+09:00
            # Python's fromisoformat handles this in 3.11+
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _article_from_api(self, data: Dict[str, Any]) -> Article:
        """Convert Qiita API response to Article."""
        # Extract tags
        tags = []
        if data.get('tags'):
            tags = [tag.get('name', '') for tag in data['tags'] if tag.get('name')]
        
        # Get author info
        user = data.get('user', {})
        author = user.get('id') or user.get('name')
        
        return Article(
            id=data.get('id'),
            title=data.get('title', 'Untitled'),
            url=data.get('url', ''),
            source_name=self.source_name,
            language=self.source_language,
            author=author,
            published_at=self._parse_datetime(data.get('created_at')),
            updated_at=self._parse_datetime(data.get('updated_at')),
            summary=data.get('rendered_body', '')[:500] if data.get('rendered_body') else None,
            content=data.get('body'),  # Markdown content
            content_html=data.get('rendered_body'),  # HTML content
            tags=tags,
            upvotes=data.get('likes_count', 0),
            comments_count=data.get('comments_count', 0),
            stocks=data.get('stocks_count', 0),  # Qiita bookmark count
            thumbnail_url=user.get('profile_image_url'),
        )
    
    async def fetch_articles(
        self,
        tags: Optional[List[str]] = None,
        max_articles: int = 20,
        page: int = 1
    ) -> List[Article]:
        """Fetch articles from Qiita using a single optimized query.
        
        Args:
            tags: Filter by these tags (uses OR logic)
            max_articles: Maximum articles per request (max 100)
            page: Page number (1-indexed)
            
        Returns:
            List of Article objects
        """
        session = await self._get_session()
        articles = []
        
        # Build query using OR logic for tags
        # Format: tag:Python OR tag:AI OR tag:MachineLearning
        use_tags = tags or self.DEFAULT_TAGS
        query_parts = [f"tag:{tag}" for tag in use_tags[:10]] # Support up to 10 tags
        query = " OR ".join(query_parts)
        
        params = {
            "query": query,
            "page": page,
            "per_page": min(max_articles, 100),
        }
        
        try:
            url = f"{self.API_BASE}/items?{urlencode(params)}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data:
                        articles.append(self._article_from_api(item))
                elif response.status == 403:
                    limit = response.headers.get("X-RateLimit-Limit")
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    print(f"[WARN QiitaClient] Rate limited. Limit: {limit}, Remaining: {remaining}")
                    # Return a special error or empty list
                else:
                    print(f"[WARN QiitaClient] Failed to fetch: {response.status}")
            
            # Sort by published date (newest first)
            articles.sort(
                key=lambda a: a.published_at or datetime.min,
                reverse=True
            )
            
            return articles
            
        except aiohttp.ClientError as e:
            print(f"[ERROR QiitaClient] Network error: {e}")
            return []
        except Exception as e:
            print(f"[ERROR QiitaClient] Unexpected error: {e}")
            return []
    
    async def fetch_article_content(self, article: Article) -> Article:
        """Fetch full content for an article.
        
        Note: Qiita API already returns full content in fetch_articles,
        so this is mainly for refreshing or getting updated content.
        """
        if not article.id:
            return article
        
        session = await self._get_session()
        
        try:
            url = f"{self.API_BASE}/items/{article.id}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Update article with fresh data
                    article.content = data.get('body')
                    article.content_html = data.get('rendered_body')
                    article.upvotes = data.get('likes_count', article.upvotes)
                    article.stocks = data.get('stocks_count', article.stocks)
                    article.comments_count = data.get('comments_count', article.comments_count)
                else:
                    print(f"[WARN QiitaClient] Failed to fetch article {article.id}: {response.status}")
            
            return article
            
        except Exception as e:
            print(f"[ERROR QiitaClient] Failed to fetch article content: {e}")
            return article
    
    async def search(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Article]:
        """Search Qiita articles by keyword.
        
        Args:
            query: Search query (supports Qiita search syntax)
            max_results: Maximum results to return
            
        Returns:
            List of matching articles
        """
        session = await self._get_session()
        
        try:
            params = {
                "query": query,
                "page": 1,
                "per_page": min(max_results, 100),
            }
            
            url = f"{self.API_BASE}/items?{urlencode(params)}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [self._article_from_api(item) for item in data]
                else:
                    print(f"[WARN QiitaClient] Search failed: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"[ERROR QiitaClient] Search error: {e}")
            return []
    
    async def fetch_trending(self, max_articles: int = 20) -> List[Article]:
        """Fetch trending/popular articles.
        
        Qiita doesn't have a direct trending endpoint, so we fetch
        recent articles sorted by stocks (bookmarks).
        """
        session = await self._get_session()
        
        try:
            params = {
                "page": 1,
                "per_page": min(max_articles, 100),
            }
            
            url = f"{self.API_BASE}/items?{urlencode(params)}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = [self._article_from_api(item) for item in data]
                    # Sort by stocks (popularity indicator)
                    articles.sort(key=lambda a: a.stocks, reverse=True)
                    return articles[:max_articles]
                else:
                    return []
                    
        except Exception as e:
            print(f"[ERROR QiitaClient] Trending error: {e}")
            return []


# =============================================================================
# Synchronous wrapper for non-async contexts
# =============================================================================

def fetch_qiita_articles_sync(
    tags: Optional[List[str]] = None,
    max_articles: int = 20
) -> List[Article]:
    """Synchronous wrapper for fetch_articles.
    
    Use this in non-async contexts (like PyQt slots).
    """
    async def _fetch():
        client = QiitaClient()
        try:
            return await client.fetch_articles(tags=tags, max_articles=max_articles)
        finally:
            await client.close()
    
    return asyncio.run(_fetch())
