"""Study history and app settings models."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime
from sqlalchemy import func


class StudyHistory(SQLModel, table=True):
    """Study history for vocabulary review."""
    __tablename__ = "study_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    vocab_id: int = Field(index=True)  # ID của từ trong JpVocabItem hoặc EnVocabItem
    lang: str = Field(max_length=10)  # "jp" hoặc "en"
    next_review: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    last_review: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    success_rate: float = Field(default=0.0)  # Tỷ lệ thành công (0.0 - 1.0)
    status: str = Field(default="new", max_length=20)  # new, learning, mastered, forgotten
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    # Stats fields
    study_date: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    words_reviewed: int = Field(default=0)


class AppSettings(SQLModel, table=True):
    """Application settings per user."""
    __tablename__ = "app_settings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    key: str = Field(max_length=100, index=True)
    value: str = Field(max_length=2000)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )


class PomodoroSession(SQLModel, table=True):
    """Statistics for Pomodoro cycles."""
    __tablename__ = "pomodoro_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    duration_minutes: int = Field(default=25)
    mode: str = Field(default="work", max_length=20) # work, short_break, long_break

