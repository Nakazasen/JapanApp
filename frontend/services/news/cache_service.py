"""News Cache Service for offline reading.

Provides SQLite-based caching for news articles.
Features:
- Auto-save fetched articles to database
- Load cached articles when offline/rate-limited
- Track read/saved status per user
- Auto-cleanup old articles (keep last 500)
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import select

from frontend.core.database import get_session
from frontend.models.news import NewsArticle
from frontend.services.news.base_client import Article, SourceLanguage


class NewsCacheService:
    """Service for caching news articles in SQLite."""
    
    MAX_CACHED_ARTICLES = 500  # Per user
    CACHE_EXPIRY_DAYS = 7      # Auto-delete articles older than this
    
    def __init__(self, user_id: int = 1):
        self.user_id = user_id
    
    def cache_articles(self, articles: List[Article]) -> int:
        """Save articles to cache. Returns number of new articles cached."""
        if not articles:
            return 0
            
        cached_count = 0
        
        with get_session() as session:
            for article in articles:
                # Check if already cached by URL
                existing = session.exec(
                    select(NewsArticle).where(NewsArticle.url == article.url)
                ).first()
                
                if existing:
                    # Update metrics only
                    existing.upvotes = article.upvotes
                    existing.comments_count = article.comments_count
                    existing.stocks = article.stocks
                    session.add(existing)
                else:
                    # Create new cached article
                    db_article = NewsArticle(
                        user_id=self.user_id,
                        title=article.title,
                        url=article.url,
                        source_name=article.source_name,
                        author=article.author,
                        summary=article.summary,
                        content=article.content,
                        content_html=article.content_html,
                        language=article.language.value if hasattr(article.language, 'value') else str(article.language),
                        tags=json.dumps(article.tags) if article.tags else None,
                        thumbnail_url=article.thumbnail_url,
                        upvotes=article.upvotes,
                        comments_count=article.comments_count,
                        stocks=article.stocks,
                        furigana_title=article.furigana_title,
                        furigana_content=article.furigana_content,
                        published_at=article.published_at,
                        cached_at=datetime.utcnow(),
                    )
                    session.add(db_article)
                    cached_count += 1
            
            session.commit()
            
        # Cleanup old articles after caching
        self._cleanup_old_articles()
        
        return cached_count
    
    def get_cached_articles(
        self, 
        language: Optional[str] = None,
        limit: int = 50,
        only_saved: bool = False
    ) -> List[Article]:
        """Load cached articles from database."""
        with get_session() as session:
            query = select(NewsArticle).where(
                NewsArticle.user_id == self.user_id
            )
            
            if language and language != "mixed":
                lang_code = "jp" if language == "japan" else "en"
                query = query.where(NewsArticle.language == lang_code)
            
            if only_saved:
                query = query.where(NewsArticle.is_saved == True)
            
            query = query.order_by(NewsArticle.published_at.desc()).limit(limit)
            
            db_articles = session.exec(query).all()
            
            # Convert to Article dataclass
            articles = []
            for db_art in db_articles:
                articles.append(self._db_to_article(db_art))
            
            return articles
    
    def mark_as_read(self, url: str) -> bool:
        """Mark an article as read."""
        with get_session() as session:
            article = session.exec(
                select(NewsArticle).where(
                    NewsArticle.url == url,
                    NewsArticle.user_id == self.user_id
                )
            ).first()
            
            if article:
                article.is_read = True
                session.add(article)
                session.commit()
                return True
            return False
    
    def toggle_saved(self, url: str) -> Optional[bool]:
        """Toggle saved status. Returns new status or None if not found."""
        with get_session() as session:
            article = session.exec(
                select(NewsArticle).where(
                    NewsArticle.url == url,
                    NewsArticle.user_id == self.user_id
                )
            ).first()
            
            if article:
                article.is_saved = not article.is_saved
                session.add(article)
                session.commit()
                return article.is_saved
            return None
    
    def get_saved_count(self) -> int:
        """Get count of saved articles."""
        with get_session() as session:
            result = session.exec(
                select(NewsArticle).where(
                    NewsArticle.user_id == self.user_id,
                    NewsArticle.is_saved == True
                )
            ).all()
            return len(result)
    
    def _cleanup_old_articles(self):
        """Remove old unsaved articles to keep cache size manageable."""
        with get_session() as session:
            # Get total count
            all_articles = session.exec(
                select(NewsArticle).where(
                    NewsArticle.user_id == self.user_id,
                    NewsArticle.is_saved == False  # Don't delete saved articles
                ).order_by(NewsArticle.cached_at.desc())
            ).all()
            
            # Remove oldest if over limit
            if len(all_articles) > self.MAX_CACHED_ARTICLES:
                to_delete = all_articles[self.MAX_CACHED_ARTICLES:]
                for art in to_delete:
                    session.delete(art)
                session.commit()
                print(f"[NewsCache] Cleaned up {len(to_delete)} old articles")
            
            # Also delete articles older than CACHE_EXPIRY_DAYS
            cutoff = datetime.utcnow() - timedelta(days=self.CACHE_EXPIRY_DAYS)
            expired = session.exec(
                select(NewsArticle).where(
                    NewsArticle.user_id == self.user_id,
                    NewsArticle.is_saved == False,
                    NewsArticle.cached_at < cutoff
                )
            ).all()
            
            for art in expired:
                session.delete(art)
            
            if expired:
                session.commit()
                print(f"[NewsCache] Deleted {len(expired)} expired articles")
    
    def _db_to_article(self, db_art: NewsArticle) -> Article:
        """Convert database model to Article dataclass."""
        lang = SourceLanguage.JAPANESE if db_art.language == "jp" else SourceLanguage.ENGLISH
        
        return Article(
            id=str(db_art.id),
            title=db_art.title,
            url=db_art.url,
            source_name=db_art.source_name,
            language=lang,
            author=db_art.author,
            published_at=db_art.published_at,
            summary=db_art.summary,
            content=db_art.content,
            content_html=db_art.content_html,
            tags=json.loads(db_art.tags) if db_art.tags else [],
            upvotes=db_art.upvotes,
            comments_count=db_art.comments_count,
            stocks=db_art.stocks,
            thumbnail_url=db_art.thumbnail_url,
            furigana_title=db_art.furigana_title,
            furigana_content=db_art.furigana_content,
            is_read=db_art.is_read,
            is_saved=db_art.is_saved,
            cached_at=db_art.cached_at,
        )
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for current user."""
        with get_session() as session:
            # Total cached
            all_articles = session.exec(
                select(NewsArticle).where(NewsArticle.user_id == self.user_id)
            ).all()
            
            total = len(all_articles)
            saved = sum(1 for a in all_articles if a.is_saved)
            read = sum(1 for a in all_articles if a.is_read)
            japanese = sum(1 for a in all_articles if a.language == "jp")
            english = sum(1 for a in all_articles if a.language == "en")
            
            # Sources breakdown
            sources = {}
            for a in all_articles:
                sources[a.source_name] = sources.get(a.source_name, 0) + 1
            
            return {
                "total": total,
                "saved": saved,
                "read": read,
                "unread": total - read,
                "japanese": japanese,
                "english": english,
                "sources": sources,
                "max_limit": self.MAX_CACHED_ARTICLES,
                "expiry_days": self.CACHE_EXPIRY_DAYS,
            }
    
    def clear_cache(self, keep_saved: bool = True) -> int:
        """Clear cached articles. Returns number of articles deleted.
        
        Args:
            keep_saved: If True, don't delete saved/bookmarked articles
        """
        with get_session() as session:
            query = select(NewsArticle).where(NewsArticle.user_id == self.user_id)
            
            if keep_saved:
                query = query.where(NewsArticle.is_saved == False)
            
            articles = session.exec(query).all()
            count = len(articles)
            
            for art in articles:
                session.delete(art)
            
            session.commit()
            print(f"[NewsCache] Cleared {count} cached articles")
            return count
    
    def export_saved_articles(self, format: str = "json") -> str:
        """Export saved articles to JSON or Markdown format."""
        saved = self.get_cached_articles(only_saved=True, limit=1000)
        
        if format == "markdown":
            lines = ["# Saved Articles\n"]
            for art in saved:
                lines.append(f"## {art.title}")
                lines.append(f"- **Source**: {art.source_name}")
                lines.append(f"- **Author**: {art.author or 'Unknown'}")
                lines.append(f"- **URL**: {art.url}")
                if art.published_at:
                    lines.append(f"- **Date**: {art.published_at.strftime('%Y-%m-%d')}")
                lines.append(f"\n{art.summary or ''}\n")
                lines.append("---\n")
            return "\n".join(lines)
        else:
            # JSON format
            data = []
            for art in saved:
                data.append({
                    "title": art.title,
                    "url": art.url,
                    "source": art.source_name,
                    "author": art.author,
                    "summary": art.summary,
                    "tags": art.tags,
                    "published_at": art.published_at.isoformat() if art.published_at else None,
                })
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def search_cached(self, query: str, limit: int = 20) -> List[Article]:
        """Search cached articles by title or content."""
        with get_session() as session:
            # SQLite LIKE search
            search_term = f"%{query}%"
            results = session.exec(
                select(NewsArticle).where(
                    NewsArticle.user_id == self.user_id,
                    (NewsArticle.title.like(search_term)) | 
                    (NewsArticle.content.like(search_term))
                ).order_by(NewsArticle.published_at.desc()).limit(limit)
            ).all()
            
            return [self._db_to_article(db_art) for db_art in results]
