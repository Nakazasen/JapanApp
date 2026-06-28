"""Unified aggregator for all news sources.

Combines results from multiple sources:
- Japanese: Qiita, Zenn
- English: Hacker News, Dev.to
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from frontend.services.news.base_client import Article, SourceLanguage
from frontend.services.news.qiita_client import QiitaClient
from frontend.services.news.hacker_news_client import HackerNewsClient
from frontend.services.news.zenn_client import ZennClient
from frontend.services.news.devto_client import DevToClient
from frontend.services.news.smart_filter import SmartFilter


def _normalize_datetime(dt):
    """Convert any datetime to naive UTC for comparison."""
    if dt is None:
        return datetime.min
    # If timezone-aware, convert to UTC and remove tzinfo
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class TechHubAggregator:
    """Combines multiple news sources into a single feed.
    
    Sources:
    - Japanese: Qiita, Zenn (RSS)
    - English: Hacker News, Dev.to (API)
    """
    
    def __init__(self):
        # All available clients
        self.clients = [
            QiitaClient(),      # Japanese tech Q&A
            ZennClient(),       # Japanese tech blog
            HackerNewsClient(), # English/Global tech news
            DevToClient()       # English dev community
        ]
        self.smart_filter = SmartFilter()
        
    async def fetch_all(
        self, 
        mode: str = "mixed", 
        tags: Optional[List[str]] = None,
        max_articles: int = 30,
        timeout_seconds: int = 15
    ) -> List[Article]:
        """Fetch and combine articles from enabled sources.
        
        Args:
            mode: "global" (EN), "japan" (JP), or "mixed" (Both)
            tags: Optional filters
            max_articles: Total target number of articles
            timeout_seconds: Timeout per client in seconds
        """
        tasks = []
        
        # Determine which clients to use
        active_clients = []
        if mode == "global":
            active_clients = [c for c in self.clients if c.source_language == SourceLanguage.ENGLISH]
        elif mode == "japan":
            active_clients = [c for c in self.clients if c.source_language == SourceLanguage.JAPANESE]
        else: # mixed
            active_clients = self.clients
            
        if not active_clients:
            print("[Aggregator] No active clients for mode:", mode)
            return []
            
        # Distribute max_articles among active clients
        per_client = max(max_articles // len(active_clients), 10)
        
        # Wrap each client fetch with timeout
        async def fetch_with_timeout(client, timeout: int):
            try:
                return await asyncio.wait_for(
                    client.fetch_articles(tags=tags, max_articles=per_client),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                print(f"[Aggregator] Timeout fetching from {client.source_name}")
                return []
            except Exception as e:
                print(f"[Aggregator] Error from {client.source_name}: {e}")
                return []
        
        for client in active_clients:
            tasks.append(fetch_with_timeout(client, timeout_seconds))
            
        # Fetch in parallel with overall timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_seconds + 5  # Give extra 5s for overall
            )
        except asyncio.TimeoutError:
            print("[Aggregator] Overall timeout reached")
            results = []
        
        combined_articles = []
        for res in results:
            if isinstance(res, list):
                combined_articles.extend(res)
            elif isinstance(res, Exception):
                print(f"[Aggregator] Client error: {res}")
                
        # Close all clients
        await self.close()
        
        # Sort by date (newest first) - normalize datetimes first
        combined_articles.sort(
            key=lambda a: _normalize_datetime(a.published_at),
            reverse=True
        )
        
        print(f"[Aggregator] Fetched {len(combined_articles)} articles total")
        return combined_articles[:max_articles]
        
    async def close(self):
        """Clean up HTTP sessions."""
        for client in self.clients:
            if hasattr(client, 'close'):
                await client.close()

# Synchronous wrapper for convenience
def fetch_tech_hub_sync(mode="mixed", tags=None, max_articles=30):
    async def _run():
        agg = TechHubAggregator()
        return await agg.fetch_all(mode=mode, tags=tags, max_articles=max_articles)
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        # This is tricky in PyQt, usually we use run_async helper
        return []
    
    return loop.run_until_complete(_run())
