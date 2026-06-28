"""TOEIC Module Database Models.

Contains all SQLModel classes for TOEIC learning features:
- Questions (Part 1-7)
- Tests
- User Progress
- Study Sessions
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, DateTime, JSON
from sqlalchemy import func


class QuestionType(str, Enum):
    """Question types for TOEIC."""
    PHOTO = "photo"                 # Part 1: Photographs
    QR = "qr"                       # Part 2: Question-Response
    CONVERSATION = "conversation"   # Part 3: Conversations
    TALK = "talk"                   # Part 4: Talks
    GRAMMAR = "grammar"             # Part 5: Incomplete Sentences
    TEXT_COMPLETION = "text"        # Part 6: Text Completion
    READING = "reading"             # Part 7: Reading Comprehension


class TestType(str, Enum):
    """Types of TOEIC tests."""
    FULL = "full"       # Full test (200 questions, 120 min)
    MINI = "mini"       # Mini test (subset)
    PART = "part"       # Single part practice


class SessionType(str, Enum):
    """Types of study sessions."""
    VOCABULARY = "vocabulary"
    LISTENING = "listening"
    READING = "reading"
    TEST = "test"


class ToeicQuestion(SQLModel, table=True):
    """TOEIC question for any part (1-7)."""
    __tablename__ = "toeic_questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Classification
    part: int = Field(index=True)  # 1-7
    question_type: str = Field(max_length=20)  # QuestionType values
    difficulty: int = Field(default=3)  # 1-5
    topic: Optional[str] = Field(default=None, max_length=50)  # Office, Travel...
    
    # Content
    question_text: Optional[str] = Field(default=None)  # Question text (if any)
    passage: Optional[str] = Field(default=None)  # Reading passage (Part 6-7)
    options: List[str] = Field(default=[], sa_column=Column(JSON))  # ["A text", "B text", "C text", "D text"]
    correct_answer: str = Field(max_length=1)  # A/B/C/D
    explanation: Optional[str] = Field(default=None)  # Answer explanation
    transcript: Optional[str] = Field(default=None)  # Listening script (Part 1-4)
    
    # Media paths
    audio_path: Optional[str] = Field(default=None, max_length=500)  # Part 1-4
    image_path: Optional[str] = Field(default=None, max_length=500)  # Part 1
    
    # Grouping
    test_id: Optional[int] = Field(default=None, index=True)  # FK to toeic_tests
    question_set_id: Optional[int] = Field(default=None)  # Group questions (Part 3-4, 6-7)
    question_number: Optional[int] = Field(default=None)  # Order in test/set
    
    # Metadata
    source: Optional[str] = Field(default=None, max_length=100)  # "ETS 2024", "Hackers"
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class ToeicTest(SQLModel, table=True):
    """TOEIC test definition."""
    __tablename__ = "toeic_tests"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)  # "ETS 2024 Test 1"
    test_type: str = Field(max_length=20, default=TestType.FULL.value)
    
    # Configuration
    total_questions: int = Field(default=200)
    time_limit: int = Field(default=120)  # minutes
    
    # Metadata
    source: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class ToeicUserProgress(SQLModel, table=True):
    """Tracks user's answer to each question."""
    __tablename__ = "toeic_user_progress"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    question_id: int = Field(index=True)  # FK to toeic_questions
    session_id: Optional[int] = Field(default=None, index=True)  # FK to toeic_study_sessions
    
    # Answer data
    user_answer: str = Field(max_length=1)  # A/B/C/D
    is_correct: bool
    time_spent: int = Field(default=0)  # seconds
    
    # Metadata
    answered_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class ToeicStudySession(SQLModel, table=True):
    """Tracks a study session (practice or test)."""
    __tablename__ = "toeic_study_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    
    # Session type
    session_type: str = Field(max_length=20)  # SessionType values
    part: Optional[int] = Field(default=None)  # Specific part (1-7) or None for mixed
    test_id: Optional[int] = Field(default=None)  # FK to toeic_tests (for full test mode)
    
    # Timing
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    ended_at: Optional[datetime] = Field(default=None)
    
    # Results
    correct_count: int = Field(default=0)
    total_count: int = Field(default=0)
    
    # Scoring
    listening_score: Optional[int] = Field(default=None)  # 5-495
    reading_score: Optional[int] = Field(default=None)  # 5-495
    estimated_score: Optional[int] = Field(default=None)  # Total: 10-990
    
    # Status
    is_completed: bool = Field(default=False)


# Export all models for easy import
__all__ = [
    "QuestionType",
    "TestType", 
    "SessionType",
    "ToeicQuestion",
    "ToeicTest",
    "ToeicUserProgress",
    "ToeicStudySession",
]
