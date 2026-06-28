"""Grammar practice models."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, DateTime, JSON, Relationship
from sqlalchemy import func, Text

class GrammarPracticeItem(SQLModel, table=True):
    """A grammar exercise with multiple questions."""
    __tablename__ = "grammar_practice_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(default=1, foreign_key="users.id", index=True)
    title: str = Field(max_length=500)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    source: Optional[str] = Field(default=None, max_length=200)
    transcript: Optional[str] = Field(default=None, sa_column=Column(Text))
    # AI Analysis fields
    vocabulary: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    translation: Optional[str] = Field(default=None, sa_column=Column(Text))
    analysis: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    questions: List["GrammarPracticeQuestion"] = Relationship(back_populates="item")

class GrammarPracticeQuestion(SQLModel, table=True):
    """Question for grammar practice."""
    __tablename__ = "grammar_practice_questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="grammar_practice_items.id", index=True)
    question_text: str = Field(sa_column=Column(Text))
    options: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    correct_option: str = Field(max_length=10)
    explanation: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    item: GrammarPracticeItem = Relationship(back_populates="questions")
