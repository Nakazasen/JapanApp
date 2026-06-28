"""YouTube channel and video models."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, ForeignKey
from sqlalchemy import func


class YoutubeChannel(SQLModel, table=True):
    """YouTube channel that user follows."""
    __tablename__ = "youtube_channels"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    channel_id: str = Field(unique=True, index=True, max_length=100)
    channel_name: str = Field(max_length=200)
    url: str = Field(max_length=500)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class YoutubeVideo(SQLModel, table=True):
    """YouTube video with transcript cache."""
    __tablename__ = "youtube_videos"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    video_id: str = Field(unique=True, index=True, max_length=100)
    title: str = Field(max_length=500)
    channel_id: Optional[int] = Field(default=None, foreign_key="youtube_channels.id")
    last_watched: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    user_progress: float = Field(default=0.0)  # Progress percentage (0.0 - 1.0)
    transcript_cached: bool = Field(default=False)
    transcript_text: Optional[str] = Field(default=None)  # Cached transcript
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )

