"""Grammar topic, category, and example models.

Supports:
- Grammar categories/topics for organization
- Source material tracking (e.g., "Soumatome", "IELTS Grammar")
- Mastery status (New, Learning, Mastered, Hard)
- JLPT/CEFR level tracking
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, DateTime
from sqlalchemy import func


class GrammarMasteryStatus(str, Enum):
    """Mastery status for grammar items."""
    NEW = "new"
    LEARNING = "learning"
    MASTERED = "mastered"
    HARD = "hard"


class GrammarCategory(SQLModel, table=True):
    """Grammar category/topic group for organizing patterns.
    
    Examples: "N3 Grammar", "て-form patterns", "Passive Voice"
    """
    __tablename__ = "grammar_categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    name: str = Field(max_length=100, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    lang: str = Field(max_length=10, default="jp")  # jp or en
    icon: Optional[str] = Field(default=None, max_length=50)  # Emoji
    color: Optional[str] = Field(default=None, max_length=20)
    is_system: bool = Field(default=False)  # System-provided category
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class GrammarTopic(SQLModel, table=True):
    """Grammar topic/pattern (e.g., "Present Perfect", "て-form").
    
    Represents a single grammar pattern with explanation and examples.
    """
    __tablename__ = "grammar_topics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    
    # Core data
    lang: str = Field(max_length=10, index=True)  # "en" or "jp"
    title: str = Field(max_length=200, index=True)
    pattern: Optional[str] = Field(default=None, max_length=300)  # e.g., "Vて + ください"
    description: Optional[str] = Field(default=None)  # Full explanation
    usage_notes: Optional[str] = Field(default=None)  # When to use
    common_mistakes: Optional[str] = Field(default=None)  # Common errors
    
    # NEW: Organization and Metadata
    category_id: Optional[int] = Field(default=None, foreign_key="grammar_categories.id", index=True)
    level: Optional[str] = Field(default=None, max_length=20)  # N5-N1 or A1-C2
    source_material: Optional[str] = Field(default=None, max_length=200)
    mastery_status: str = Field(
        default=GrammarMasteryStatus.NEW.value,
        max_length=20
    )
    tags: Optional[str] = Field(default=None, max_length=500)  # Comma-separated
    is_ai_enriched: bool = Field(default=False)
    
    # Source and timestamps
    source_url: Optional[str] = Field(default=None, max_length=1000)
    is_bookmarked: bool = Field(default=False)
    # SRS (Spaced Repetition) fields - SM-2
    srs_level: int = Field(default=0)  
    srs_streak: int = Field(default=0)
    srs_ease_factor: float = Field(default=2.5)
    srs_interval: int = Field(default=0)
    review_count: int = Field(default=0)
    
    # Timestamps
    next_review_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    last_reviewed_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    last_updated: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))


class GrammarExample(SQLModel, table=True):
    """Example sentences for grammar topics."""
    __tablename__ = "grammar_examples"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key="grammar_topics.id", index=True)
    
    # Example content
    example_text: str = Field(max_length=1000)
    reading: Optional[str] = Field(default=None, max_length=1000)  # Furigana/IPA
    translation_vi: Optional[str] = Field(default=None, max_length=1000)
    translation_en: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)
    audio_path: Optional[str] = Field(default=None, max_length=500)
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


# ============ Preset Data ============

# Japanese Grammar Levels (JLPT)
JAPANESE_GRAMMAR_LEVELS = ["N5", "N4", "N3", "N2", "N1"]

# English Grammar Levels (CEFR)
ENGLISH_GRAMMAR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Common Grammar Sources - Japanese
JAPANESE_GRAMMAR_SOURCES = [
    "Minna no Nihongo",
    "Genki",
    "Soumatome N5",
    "Soumatome N4",
    "Soumatome N3",
    "Soumatome N2",
    "Soumatome N1",
    "Shin Kanzen Master",
    "Tobira",
    "A Dictionary of Japanese Grammar",
    "Tae Kim's Guide",
    "Bunpro",
    "Other"
]

# Common Grammar Sources - English
ENGLISH_GRAMMAR_SOURCES = [
    "English Grammar in Use (Murphy)",
    "Cambridge Grammar",
    "Oxford Grammar",
    "IELTS Grammar",
    "TOEIC Grammar",
    "Grammarly",
    "Other"
]

# Default Grammar Categories for Japanese
DEFAULT_JP_CATEGORIES = [
    {"name": "N5 基礎文法", "icon": "🟢", "description": "JLPT N5 basic grammar"},
    {"name": "N4 初級文法", "icon": "🟡", "description": "JLPT N4 elementary grammar"},
    {"name": "N3 中級文法", "icon": "🟠", "description": "JLPT N3 intermediate grammar"},
    {"name": "N2 上級文法", "icon": "🔴", "description": "JLPT N2 advanced grammar"},
    {"name": "N1 最上級文法", "icon": "⚫", "description": "JLPT N1 expert grammar"},
    {"name": "動詞活用 (Verb Conjugation)", "icon": "🔄", "description": "Verb forms and conjugations"},
    {"name": "敬語 (Keigo)", "icon": "🎩", "description": "Polite and honorific language"},
    {"name": "接続詞 (Conjunctions)", "icon": "🔗", "description": "Connecting words and phrases"},
]

# Default Grammar Categories for English
DEFAULT_EN_CATEGORIES = [
    {"name": "Tenses", "icon": "⏰", "description": "Past, Present, Future tenses"},
    {"name": "Conditionals", "icon": "❓", "description": "If clauses and conditions"},
    {"name": "Passive Voice", "icon": "🔄", "description": "Passive constructions"},
    {"name": "Modal Verbs", "icon": "💪", "description": "Can, could, should, must, etc."},
    {"name": "Reported Speech", "icon": "💬", "description": "Indirect speech"},
    {"name": "Articles & Determiners", "icon": "📌", "description": "A, an, the, this, that"},
    {"name": "Prepositions", "icon": "📍", "description": "In, on, at, by, etc."},
    {"name": "Relative Clauses", "icon": "🔗", "description": "Who, which, that clauses"},
]
