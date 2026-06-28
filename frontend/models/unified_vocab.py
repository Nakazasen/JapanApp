"""Unified Vocabulary Model for Multi-language support.

Replaces JpVocabItem and EnVocabItem with a generic VocabItem.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, DateTime, JSON
from sqlalchemy import func


class MasteryStatus(str, Enum):
    """Mastery status for vocabulary items."""
    NEW = "new"
    LEARNING = "learning"
    MASTERED = "mastered"
    HARD = "hard"
    REVIEWING = "reviewing"


class VocabItem(SQLModel, table=True):
    """Generic vocabulary item for any language."""
    __tablename__ = "unified_vocab_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)  # No foreign key constraint for now to avoid dependency issues during migration
    
    # Core Data
    term: str = Field(max_length=200, index=True)  # word (En) or kanji/word (Jp)
    reading: Optional[str] = Field(default=None, max_length=200)  # IPA (En) or Kana (Jp)
    meaning: str = Field(max_length=1000)  # Primary meaning (usually in native lang, e.g., Vienamese)
    
    # Language & Classification
    lang: str = Field(max_length=10, index=True)  # "en", "jp", "kr", "cn", etc.
    level: Optional[str] = Field(default=None, max_length=50)  # N1, B2, TOEIC 800...
    
    # Organization
    topic_id: Optional[int] = Field(default=None, index=True)
    source_material: Optional[str] = Field(default=None, max_length=200)
    tags: Optional[str] = Field(default=None, max_length=500)
    
    # Extended Data (JSON for flexibility)
    # JP: {romaji: "...", han_viet: "..."}
    # EN: {pos: "noun", meaning_en: "..."}
    meta_data: Optional[Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))
    
    # Examples (JSON List)
    # [{"sentence": "...", "translation": "...", "audio": "..."}]
    examples: Optional[List[Dict[str, Any]]] = Field(default=[], sa_column=Column(JSON))
    
    # Media & Notes
    audio_path: Optional[str] = Field(default=None, max_length=500)
    user_note: Optional[str] = Field(default=None, max_length=2000)
    image_path: Optional[str] = Field(default=None, max_length=500)
    
    # Status
    mastery_status: str = Field(
        default=MasteryStatus.NEW.value,
        max_length=20
    )
    is_ai_enriched: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
    
    # SRS (Spaced Repetition System)
    srs_level: int = Field(default=0)
    srs_streak: int = Field(default=0)
    srs_ease_factor: float = Field(default=2.5)
    srs_interval: int = Field(default=0)
    next_review: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    last_reviewed: Optional[datetime] = Field(default=None)
    review_count: int = Field(default=0)
