"""Reading practice models."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, DateTime, JSON, Relationship
from sqlalchemy import func, Text

class ReadingCategory(SQLModel, table=True):
    """Category for reading exercises."""
    __tablename__ = "reading_categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    level: str = Field(max_length=10) # N1, N2, N3, N4, N5
    icon: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    items: List["ReadingItem"] = Relationship(back_populates="category")

class ReadingItem(SQLModel, table=True):
    """A reading passage with questions."""
    __tablename__ = "reading_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="reading_categories.id", index=True)
    title: str = Field(max_length=500)
    content: str = Field(sa_column=Column(Text))
    image_path: Optional[str] = Field(default=None, max_length=1000)
    audio_path: Optional[str] = Field(default=None, max_length=1000)
    translation: Optional[str] = Field(default=None, sa_column=Column(Text))
    vocabulary: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    analysis: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    source: Optional[str] = Field(default=None, max_length=200)
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    category: ReadingCategory = Relationship(back_populates="items")
    questions: List["ReadingQuestion"] = Relationship(back_populates="item")

class ReadingQuestion(SQLModel, table=True):
    """Question for reading passage."""
    __tablename__ = "reading_questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="reading_items.id", index=True)
    question_text: str = Field(sa_column=Column(Text))
    options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    correct_option: str = Field(max_length=10)
    explanation: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    item: ReadingItem = Relationship(back_populates="questions")

class ReadingProgress(SQLModel, table=True):
    """User progress for reading."""
    __tablename__ = "reading_progress"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    item_id: int = Field(foreign_key="reading_items.id", index=True)
    is_completed: bool = Field(default=False)
    score: float = Field(default=0.0)
    last_practiced: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
