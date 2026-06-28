"""Base class for news API clients.

This module provides an abstract base class that all news clients must implement.
Designed for extensibility - adding new sources (Hacker News, Zenn, etc.) is easy.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class SourceLanguage(Enum):
    """Supported languages for news sources."""
    ENGLISH = "en"
    JAPANESE = "jp"
    MIXED = "mixed"


class SourceType(Enum):
    """Type of news source."""
    API = "api"           # Official REST API
    RSS = "rss"           # RSS/Atom feed
    CRAWLER = "crawler"   # HTML scraping


@dataclass
class Article:
    """Unified article data structure for all sources.
    
    This is the common format that all clients must return.
    Includes fields for both EN and JP sources.
    """
    # Required fields
    title: str
    url: str
    source_name: str
    language: SourceLanguage
    
    # Optional metadata
    id: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Content (fetched on demand)
    summary: Optional[str] = None
    content: Optional[str] = None
    content_html: Optional[str] = None
    
    # Tags and metrics
    tags: List[str] = field(default_factory=list)
    upvotes: int = 0
    comments_count: int = 0
    stocks: int = 0  # Qiita-specific (bookmarks)
    
    # Images
    thumbnail_url: Optional[str] = None
    images: List[str] = field(default_factory=list)
    
    # Japanese-specific
    furigana_title: Optional[str] = None
    furigana_content: Optional[str] = None
    
    # User state (for caching)
    is_read: bool = False
    is_saved: bool = False
    cached_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source_name": self.source_name,
            "language": self.language.value,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "tags": self.tags,
            "upvotes": self.upvotes,
            "comments_count": self.comments_count,
            "stocks": self.stocks,
            "thumbnail_url": self.thumbnail_url,
        }


class BaseNewsClient(ABC):
    """Abstract base class for all news API clients.
    
    To add a new source:
    1. Create a new file (e.g., hacker_news_client.py)
    2. Inherit from BaseNewsClient
    3. Implement all abstract methods
    4. Register in aggregator.py
    
    Example:
        class HackerNewsClient(BaseNewsClient):
            @property
            def source_name(self) -> str:
                return "Hacker News"
            
            async def fetch_articles(...) -> List[Article]:
                ...
    """
    
    # HTTP headers for requests
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/html",
        "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
    }
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique name for this source (e.g., 'Qiita', 'Hacker News')."""
        pass
    
    @property
    @abstractmethod
    def source_url(self) -> str:
        """Base URL of the source."""
        pass
    
    @property
    @abstractmethod
    def source_language(self) -> SourceLanguage:
        """Primary language of articles from this source."""
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """How this source is accessed (API, RSS, or crawler)."""
        pass
    
    @abstractmethod
    async def fetch_articles(
        self,
        tags: Optional[List[str]] = None,
        max_articles: int = 20,
        page: int = 1
    ) -> List[Article]:
        """Fetch articles from this source.
        
        Args:
            tags: Filter by these tags (implementation-specific)
            max_articles: Maximum number of articles to fetch
            page: Page number for pagination
            
        Returns:
            List of Article objects
        """
        pass
    
    @abstractmethod
    async def fetch_article_content(self, article: Article) -> Article:
        """Fetch full content for a single article.
        
        Args:
            article: Article with URL set
            
        Returns:
            Same article with content, content_html populated
        """
        pass
    
    async def search(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Article]:
        """Search articles by keyword (optional implementation).
        
        Default: Returns empty list. Override in subclass if source supports search.
        """
        return []
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get metadata about this source."""
        return {
            "name": self.source_name,
            "url": self.source_url,
            "language": self.source_language.value,
            "type": self.source_type.value,
        }
