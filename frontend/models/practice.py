"""Practice models for Reading and Listening exercises."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, DateTime, JSON, Relationship
from sqlalchemy import func, Text


class PracticeType(str, Enum):
    READING = "reading"
    LISTENING = "listening"


class PracticeCategory(SQLModel, table=True):
    """Category for practice items (e.g. JLPT N1 Reading, JLPT N2 Listening)."""
    __tablename__ = "practice_categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    type: str = Field(max_length=20)  # reading or listening
    level: str = Field(max_length=10) # N1, N2, N3, N4, N5
    icon: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    # Relationships
    items: List["PracticeItem"] = Relationship(back_populates="category")


class PracticeItem(SQLModel, table=True):
    """A reading passage or listening exercise."""
    __tablename__ = "practice_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(foreign_key="practice_categories.id", index=True)
    title: str = Field(max_length=500)
    content: Optional[str] = Field(default=None, sa_column=Column(Text))  # Passage text for reading
    audio_path: Optional[str] = Field(default=None, max_length=1000)      # Audio file for listening
    image_path: Optional[str] = Field(default=None, max_length=1000)      # Optional image
    # audio_path is already defined above
    source: Optional[str] = Field(default=None, max_length=200)
    
    # Enhanced learning data
    vocabulary: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    translation: Optional[str] = Field(default=None, sa_column=Column(Text))
    # Structure: [{ 'original': '...', 'translation': '...', 'grammar': '...' }]
    analysis: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    # Relationships
    category: PracticeCategory = Relationship(back_populates="items")
    questions: List["PracticeQuestion"] = Relationship(back_populates="item")


class PracticeQuestion(SQLModel, table=True):
    """A question associated with a practice item."""
    __tablename__ = "practice_questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="practice_items.id", index=True)
    question_text: str = Field(sa_column=Column(Text))
    # options: {"A": "Choice A", "B": "Choice B", ...}
    options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    correct_option: str = Field(max_length=10)
    explanation: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Relationships
    item: PracticeItem = Relationship(back_populates="questions")


class PracticeProgress(SQLModel, table=True):
    """User progress for a practice item."""
    __tablename__ = "practice_progress"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    item_id: int = Field(foreign_key="practice_items.id", index=True)
    is_completed: bool = Field(default=False)
    score: float = Field(default=0.0) # Score achieved
    last_practiced: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
