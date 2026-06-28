"""News source and article models."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, ForeignKey
from sqlalchemy import func


class NewsSource(SQLModel, table=True):
    """News source (BBC, CNN, NHK, etc.)."""
    __tablename__ = "news_sources"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=100)
    url: str = Field(max_length=500)
    lang: str = Field(max_length=10)  # "en" hoặc "jp"
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class NewsArticle(SQLModel, table=True):
    """News article with cached content."""
    __tablename__ = "news_articles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: Optional[int] = Field(default=None, foreign_key="news_sources.id", index=True)
    
    # Core fields
    title: str = Field(max_length=500, index=True)
    url: str = Field(unique=True, max_length=1000)
    source_name: str = Field(default="Unknown", max_length=100)
    author: Optional[str] = Field(default=None, max_length=200)
    summary: Optional[str] = Field(default=None)
    content: Optional[str] = Field(default=None)
    content_html: Optional[str] = Field(default=None)
    
    # Metadata
    language: str = Field(default="en", max_length=10)  # "en" | "jp"
    tags: Optional[str] = Field(default=None)  # JSON array
    thumbnail_url: Optional[str] = Field(default=None, max_length=1000)
    
    # Metrics
    upvotes: int = Field(default=0)
    comments_count: int = Field(default=0)
    stocks: int = Field(default=0)  # Qiita bookmarks
    
    # User state
    is_read: bool = Field(default=False)
    is_saved: bool = Field(default=False)
    
    # Japanese support
    furigana_title: Optional[str] = Field(default=None)
    furigana_content: Optional[str] = Field(default=None)
    
    # Timestamps
    published_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    cached_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )

