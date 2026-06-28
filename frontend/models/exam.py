"""Exam source, exam, question, and result models."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, DateTime, ForeignKey, JSON
from sqlalchemy import func


class ExamSource(SQLModel, table=True):
    """Exam source (e.g., dethitiengnhat.com)."""
    __tablename__ = "exam_sources"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=100)
    url: str = Field(max_length=500)
    lang: str = Field(max_length=10)  # "en" hoặc "jp"
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class Exam(SQLModel, table=True):
    """Exam/Test."""
    __tablename__ = "exams"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    source_id: int = Field(foreign_key="exam_sources.id", index=True)
    title: str = Field(max_length=500)
    description: Optional[str] = Field(default=None)
    total_questions: int = Field(default=0)
    last_updated: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class ExamQuestion(SQLModel, table=True):
    """Exam question with options."""
    __tablename__ = "exam_questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exams.id", index=True)
    question_text: str = Field(max_length=2000)
    options: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # {"A": "...", "B": "...", ...}
    correct_option: Optional[str] = Field(default=None, max_length=10)  # "A", "B", "C", etc. (None if not available)
    explanation: Optional[str] = Field(default=None, max_length=2000)
    question_order: int = Field(default=0)  # Thứ tự câu hỏi
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class ExamResult(SQLModel, table=True):
    """Exam result with detailed feedback."""
    __tablename__ = "exam_results"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    exam_id: int = Field(foreign_key="exams.id", index=True)
    user_score: float = Field(default=0.0)  # Score percentage (0.0 - 100.0)
    user_time: int = Field(default=0)  # Time taken in seconds
    date_taken: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    detailed_feedback: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # {"question_id": {"answer": "A", "correct": true, ...}, ...}

