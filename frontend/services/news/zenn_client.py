"""Zenn.dev API client for Japanese tech articles.

Zenn is a popular Japanese tech blogging platform similar to Medium.
Uses their public feed endpoint.
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree

from frontend.services.news.base_client import (
    BaseNewsClient, Article, SourceType, SourceLanguage
)


class ZennClient(BaseNewsClient):
    """Client for fetching articles from Zenn.dev.
    
    Zenn provides RSS feeds for different topics and trending articles.
    """
    
    # Zenn RSS endpoints
    BASE_URL = "https://zenn.dev"
    TRENDING_FEED = "https://zenn.dev/feed"
    TOPIC_FEED = "https://zenn.dev/topics/{topic}/feed"
    
    # Tech topics to fetch from
    TECH_TOPICS = [
        "python", "machinelearning", "ai", "deeplearning",
        "docker", "kubernetes", "react", "typescript",
        "rust", "go", "aws", "gcp"
    ]
    
    def __init__(self):
        super().__init__()
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def source_name(self) -> str:
        return "Zenn"

    @property
    def source_url(self) -> str:
        return self.BASE_URL
    
    @property
    def source_type(self) -> SourceType:
        return SourceType.RSS
    
    @property
    def source_language(self) -> SourceLanguage:
        return SourceLanguage.JAPANESE
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "EnglishApp/1.0 TechHub"}
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
        """Fetch trending articles from Zenn.
        
        Args:
            tags: Optional filter (not used directly, we fetch from trending)
            max_articles: Maximum articles to return
            page: Page number (not supported by RSS, ignored)
            
        Returns:
            List of Article objects
        """
        try:
            session = await self._get_session()
            articles = []
            
            # Fetch from trending feed
            try:
                async with session.get(
                    self.TRENDING_FEED,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        articles.extend(self._parse_rss(xml_content))
            except Exception as e:
                print(f"[ZennClient] Error fetching trending: {e}")
            
            # Also fetch from specific topics if we need more
            if len(articles) < max_articles and tags:
                for topic in tags[:3]:  # Limit to 3 topics
                    topic_lower = topic.lower()
                    if topic_lower in self.TECH_TOPICS:
                        try:
                            url = self.TOPIC_FEED.format(topic=topic_lower)
                            async with session.get(
                                url,
                                timeout=aiohttp.ClientTimeout(total=10)
                            ) as response:
                                if response.status == 200:
                                    xml_content = await response.text()
                                    topic_articles = self._parse_rss(xml_content)
                                    articles.extend(topic_articles)
                        except Exception as e:
                            print(f"[ZennClient] Error fetching topic {topic}: {e}")
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article.url not in seen_urls:
                    seen_urls.add(article.url)
                    unique_articles.append(article)
            
            return unique_articles[:max_articles]
            
        except Exception as e:
            print(f"[ZennClient] Error: {e}")
            return []
    
    def _parse_rss(self, xml_content: str) -> List[Article]:
        """Parse Zenn RSS feed into Article objects."""
        articles = []
        
        try:
            root = ElementTree.fromstring(xml_content)
            
            # Find channel and items
            channel = root.find("channel")
            if channel is None:
                return []
            
            items = channel.findall("item")
            
            for item in items:
                try:
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    description = item.find("description")
                    creator = item.find("{http://purl.org/dc/elements/1.1/}creator")
                    
                    if title is None or link is None:
                        continue
                    
                    # Parse publication date
                    published_at = None
                    if pub_date is not None and pub_date.text:
                        try:
                            # RSS date format: "Sat, 28 Dec 2024 10:30:00 +0900"
                            from email.utils import parsedate_to_datetime
                            published_at = parsedate_to_datetime(pub_date.text)
                        except Exception:
                            pass
                    
                    # Extract content/summary
                    content = ""
                    summary = ""
                    if description is not None and description.text:
                        summary = description.text[:500]
                        content = description.text
                    
                    # Author
                    author = creator.text if creator is not None else ""
                    
                    article = Article(
                        id=link.text,
                        title=title.text or "Untitled",
                        url=link.text,
                        source_name=self.source_name,
                        language=self.source_language,
                        author=author,
                        summary=summary,
                        content=content,
                        published_at=published_at
                    )
                    articles.append(article)
                    
                except Exception as e:
                    print(f"[ZennClient] Error parsing item: {e}")
                    continue
            
        except ElementTree.ParseError as e:
            print(f"[ZennClient] XML parse error: {e}")
        
        return articles
    
    async def fetch_article_content(self, article_id: str) -> Optional[str]:
        """Fetch full content of an article.
        
        For Zenn, we'd need to scrape the page since RSS has limited content.
        For now, return None and let the UI handle it via ContentExtractor.
        """
        return None
