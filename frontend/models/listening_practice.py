"""Listening practice models."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, DateTime, JSON, Relationship
from sqlalchemy import func, Text

class ListeningCategory(SQLModel, table=True):
    """Category for listening exercises."""
    __tablename__ = "listening_categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    level: str = Field(max_length=10) # N1, N2, N3, N4, N5
    icon: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    items: List["ListeningItem"] = Relationship(back_populates="category")

class ListeningItem(SQLModel, table=True):
    """A listening exercise with audio."""
    __tablename__ = "listening_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="listening_categories.id", index=True)
    title: str = Field(max_length=500)
    audio_path: str = Field(max_length=1000)
    image_path: Optional[str] = Field(default=None, max_length=1000)
    transcript: Optional[str] = Field(default=None, sa_column=Column(Text))
    source: Optional[str] = Field(default=None, max_length=200)
    
    # AI Analysis fields
    vocabulary: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    translation: Optional[str] = Field(default=None, sa_column=Column(Text))
    analysis: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    category: ListeningCategory = Relationship(back_populates="items")
    questions: List["ListeningQuestion"] = Relationship(back_populates="item")

class ListeningQuestion(SQLModel, table=True):
    """Question for listening exercise."""
    __tablename__ = "listening_questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="listening_items.id", index=True)
    question_text: str = Field(sa_column=Column(Text))
    options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    correct_option: str = Field(max_length=10)
    explanation: Optional[str] = Field(default=None, sa_column=Column(Text))
    audio_path: Optional[str] = Field(default=None, max_length=1000)
    transcript: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    item: ListeningItem = Relationship(back_populates="questions")

class ListeningProgress(SQLModel, table=True):
    """User progress for listening."""
    __tablename__ = "listening_progress"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    item_id: int = Field(foreign_key="listening_items.id", index=True)
    is_completed: bool = Field(default=False)
    score: float = Field(default=0.0)
    last_practiced: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
