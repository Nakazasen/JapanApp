"""Writing draft models."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class WritingDraft(SQLModel, table=True):
    """Model for storing writing drafts."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="Untitled")
    content: str = Field(default="")
    language: str = Field(default="en")  # 'en' or 'jp'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
