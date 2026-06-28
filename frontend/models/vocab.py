"""Vocabulary models for Japanese and English words.

Supports:
- Topics/Decks for organizing vocabulary
- Source material tracking (e.g., "Soumatome", "IELTS Cambridge")
- Mastery status (New, Learning, Mastered, Hard)
- SRS (Spaced Repetition System) for review scheduling
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, DateTime, Relationship
from sqlalchemy import func, Enum as SAEnum


class MasteryStatus(str, Enum):
    """Mastery status for vocabulary items."""
    NEW = "new"
    LEARNING = "learning"
    MASTERED = "mastered"
    HARD = "hard"
    REVIEWING = "reviewing"


class VocabTopic(SQLModel, table=True):
    """Vocabulary topic/deck for organizing words into groups.
    
    Examples: "N1 Grammar", "IT Vocabulary", "IELTS Reading"
    """
    __tablename__ = "vocab_topics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    lang: str = Field(max_length=10, default="jp")  # jp or en
    color: Optional[str] = Field(default=None, max_length=20)  # For UI display
    icon: Optional[str] = Field(default=None, max_length=50)  # Emoji or icon name
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
    
    # Relationships - will be populated by ORM
    # jp_vocab_items: List["JpVocabItem"] = Relationship(back_populates="topic")
    # en_vocab_items: List["EnVocabItem"] = Relationship(back_populates="topic")


class JpVocabItem(SQLModel, table=True):
    """Japanese vocabulary item."""
    __tablename__ = "jp_vocab_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Core word data
    word_kanji: str = Field(max_length=100, index=True)
    word_kana: str = Field(max_length=100)
    romaji: Optional[str] = Field(default=None, max_length=100)
    meaning_vi: str = Field(max_length=500)
    han_viet: Optional[str] = Field(default=None, max_length=100)
    example_jp: Optional[str] = Field(default=None, max_length=1000)
    example_vi: Optional[str] = Field(default=None, max_length=1000)
    audio_path: Optional[str] = Field(default=None, max_length=500)
    user_note: Optional[str] = Field(default=None, max_length=2000)
    
    # NEW: Categorization and Metadata
    topic_id: Optional[int] = Field(default=None, foreign_key="vocab_topics.id", index=True)
    source_material: Optional[str] = Field(default=None, max_length=200)  # e.g., "Soumatome N2", "Minna no Nihongo"
    level: Optional[str] = Field(default=None, max_length=20)  # N5, N4, N3, N2, N1
    mastery_status: str = Field(
        default=MasteryStatus.NEW.value,
        max_length=20
    )  # new, learning, mastered, hard
    tags: Optional[str] = Field(default=None, max_length=500)  # Comma-separated tags
    is_ai_enriched: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    # SRS (Spaced Repetition System) fields
    srs_level: int = Field(default=0)  # SM-2 level or equivalent
    srs_streak: int = Field(default=0)  # Current repetition streak
    srs_ease_factor: float = Field(default=2.5)  # SM-2 ease factor (min 1.3)
    srs_interval: int = Field(default=0)  # Days until next review
    next_review: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    last_reviewed: Optional[datetime] = Field(default=None)
    review_count: int = Field(default=0)
    
    # Relationship
    # topic: Optional[VocabTopic] = Relationship(back_populates="jp_vocab_items")


class EnVocabItem(SQLModel, table=True):
    """English vocabulary item."""
    __tablename__ = "en_vocab_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    
    # Core word data
    word: str = Field(max_length=100, index=True)
    ipa: Optional[str] = Field(default=None, max_length=100)  # IPA pronunciation
    pos: Optional[str] = Field(default=None, max_length=50)  # Part of speech
    meaning_vi: str = Field(max_length=500)
    meaning_en: Optional[str] = Field(default=None, max_length=500)
    example_en: Optional[str] = Field(default=None, max_length=1000)
    example_vi: Optional[str] = Field(default=None, max_length=1000)
    user_note: Optional[str] = Field(default=None, max_length=2000)
    
    # NEW: Categorization and Metadata
    topic_id: Optional[int] = Field(default=None, foreign_key="vocab_topics.id", index=True)
    source_material: Optional[str] = Field(default=None, max_length=200)  # e.g., "IELTS Cambridge", "TOEIC 800"
    level: Optional[str] = Field(default=None, max_length=20)  # A1, A2, B1, B2, C1, C2, TOEIC scores
    mastery_status: str = Field(
        default=MasteryStatus.NEW.value,
        max_length=20
    )  # new, learning, mastered, hard
    tags: Optional[str] = Field(default=None, max_length=500)  # Comma-separated tags
    is_ai_enriched: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    # SRS (Spaced Repetition System) fields
    srs_level: int = Field(default=0)
    srs_streak: int = Field(default=0)  # Current repetition streak
    srs_ease_factor: float = Field(default=2.5)  # SM-2 ease factor (min 1.3)
    srs_interval: int = Field(default=0)  # Days until next review
    next_review: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    last_reviewed: Optional[datetime] = Field(default=None)
    review_count: int = Field(default=0)
    
    # Relationship
    # topic: Optional[VocabTopic] = Relationship(back_populates="en_vocab_items")


# ============ Preset Data ============

# Common learning levels by language
JAPANESE_LEVELS = ["N5", "N4", "N3", "N2", "N1"]
ENGLISH_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2", "TOEIC 400", "TOEIC 600", "TOEIC 800", "IELTS 5.0", "IELTS 6.5", "IELTS 7.0"]

# Common source materials
JAPANESE_SOURCES = [
    "Minna no Nihongo",
    "Genki",
    "Soumatome N5",
    "Soumatome N4", 
    "Soumatome N3",
    "Soumatome N2",
    "Soumatome N1",
    "Mimikara Oboeru",
    "Pattern Goi N1",
    "Tobira",
    "Shin Kanzen Master",
    "Anime/Drama",
    "News/NHK",
    "Other"
]

ENGLISH_SOURCES = [
    "IELTS Cambridge",
    "TOEIC Official",
    "Longman",
    "Oxford",
    "Cambridge Dictionary",
    "News/BBC",
    "Movies/TV",
    "Academic Papers",
    "Other"
]

