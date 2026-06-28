"""Kanji (Hán tự) models for Japanese character learning.

Inspired by Anki's Kanji learning approach:
- Spaced Repetition System (SRS) for optimal review timing
- Multiple study modes (Recognition, Production, Reading)
- Radical/component breakdown
- Stroke order information
- JLPT/Grade level organization
- Example vocabulary using each kanji
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, DateTime, Relationship
from sqlalchemy import func


class KanjiMasteryStatus(str, Enum):
    """Mastery status for kanji items."""
    NEW = "new"
    LEARNING = "learning"
    REVIEWING = "reviewing"
    MASTERED = "mastered"
    LEECH = "leech"  # Card that keeps being forgotten (Anki concept)


class KanjiStudyMode(str, Enum):
    """Study modes for kanji (Anki-style card types)."""
    RECOGNITION = "recognition"      # Kanji → Reading + Meaning
    PRODUCTION = "production"        # Meaning → Kanji (writing practice)
    READING = "reading"              # Kanji in context → Reading
    COMPONENTS = "components"        # Learn radicals/components


class KanjiDeck(SQLModel, table=True):
    """Kanji deck/group for organization (like Anki decks).
    
    Examples: "JLPT N5 Kanji", "RTK Order", "School Grade 1"
    """
    __tablename__ = "kanji_decks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    name: str = Field(max_length=100, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    icon: Optional[str] = Field(default=None, max_length=50)
    color: Optional[str] = Field(default=None, max_length=20)
    order_index: int = Field(default=0)  # For custom ordering
    is_system: bool = Field(default=False)  # Built-in deck
    items: List["KanjiItem"] = Relationship(back_populates="deck")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )


class Radical(SQLModel, table=True):
    """Kanji radicals (部首) - building blocks of kanji."""
    __tablename__ = "radicals"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    radical: str = Field(max_length=10, index=True)  # The radical character
    name_jp: Optional[str] = Field(default=None, max_length=100)  # Japanese name
    name_en: Optional[str] = Field(default=None, max_length=100)  # English name
    name_vi: Optional[str] = Field(default=None, max_length=100)  # Vietnamese name
    meaning: Optional[str] = Field(default=None, max_length=200)
    stroke_count: int = Field(default=1)
    mnemonic: Optional[str] = Field(default=None, max_length=500)  # Memory hint
    image_path: Optional[str] = Field(default=None, max_length=500)


class KanjiItem(SQLModel, table=True):
    """Individual kanji character with all learning data."""
    __tablename__ = "kanji_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    
    # Core kanji data
    kanji: str = Field(max_length=10, index=True)  # The kanji character
    onyomi: Optional[str] = Field(default=None, max_length=200)  # 音読み (Chinese reading)
    kunyomi: Optional[str] = Field(default=None, max_length=200)  # 訓読み (Japanese reading)
    meaning_en: Optional[str] = Field(default=None, max_length=500)  # English meaning
    meaning_vi: Optional[str] = Field(default=None, max_length=500)  # Vietnamese meaning (Hán Việt)
    han_viet: Optional[str] = Field(default=None, max_length=100)  # Hán Việt reading
    
    # Stroke and visual info
    stroke_count: int = Field(default=1)
    stroke_order: Optional[str] = Field(default=None)  # SVG or animation data path
    stroke_order_image: Optional[str] = Field(default=None, max_length=500)
    
    # Components and radicals
    radicals: Optional[str] = Field(default=None, max_length=200)  # Comma-separated radical IDs
    components: Optional[str] = Field(default=None, max_length=500)  # Component breakdown
    mnemonic: Optional[str] = Field(default=None, max_length=1000)  # Memory story/hint
    
    # Organization
    deck_id: Optional[int] = Field(default=None, foreign_key="kanji_decks.id", index=True)
    jlpt_level: Optional[str] = Field(default=None, max_length=10)  # N5-N1
    grade_level: Optional[int] = Field(default=None)  # School grade (1-6, 7=middle, 8+=high)
    frequency_rank: Optional[int] = Field(default=None)  # Frequency in newspapers
    rtk_order: Optional[int] = Field(default=None)  # Remembering The Kanji order
    
    # Learning metadata
    source_material: Optional[str] = Field(default=None, max_length=200)
    tags: Optional[str] = Field(default=None, max_length=500)
    user_note: Optional[str] = Field(default=None, max_length=2000)
    
    # Mastery status
    mastery_status: str = Field(
        default=KanjiMasteryStatus.NEW.value,
        max_length=20
    )
    
    # AI Enrichment status
    is_ai_enriched: bool = Field(default=False)
    
    deck: Optional[KanjiDeck] = Relationship(back_populates="items")
    vocabs: List["KanjiVocab"] = Relationship(back_populates="kanji")
    
    # SRS (Spaced Repetition) fields - Anki-style
    srs_level: int = Field(default=0)  # Current SRS level (0-8 typically)
    srs_ease_factor: float = Field(default=2.5)  # SM-2 ease factor
    srs_interval: int = Field(default=0)  # Days until next review
    srs_streak: int = Field(default=0)  # Correct answers in a row
    review_count: int = Field(default=0)  # Total reviews
    lapse_count: int = Field(default=0)  # Times forgotten (for leech detection)
    
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


class KanjiVocab(SQLModel, table=True):
    """Example vocabulary words using a kanji."""
    __tablename__ = "kanji_vocab"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    kanji_id: int = Field(foreign_key="kanji_items.id", index=True)
    
    word: str = Field(max_length=100)  # The word (e.g., 食べる)
    reading: str = Field(max_length=100)  # Hiragana reading (e.g., たべる)
    han_viet: Optional[str] = Field(default=None, max_length=100)  # Hán Việt (e.g., THỰC)
    meaning_vi: Optional[str] = Field(default=None, max_length=500)
    meaning_en: Optional[str] = Field(default=None, max_length=500)
    example_sentence: Optional[str] = Field(default=None, max_length=1000)
    is_common: bool = Field(default=True)
    jlpt_level: Optional[str] = Field(default=None, max_length=10)
    
    kanji: Optional["KanjiItem"] = Relationship(back_populates="vocabs")


# ============ Preset Data ============

# JLPT Kanji counts (approximate)
JLPT_KANJI_COUNTS = {
    "N5": 80,
    "N4": 170,
    "N3": 370,
    "N2": 1000,
    "N1": 2000,
}

# School grade levels
GRADE_LEVELS = [
    {"grade": 1, "name": "小学1年", "count": 80},
    {"grade": 2, "name": "小学2年", "count": 160},
    {"grade": 3, "name": "小学3年", "count": 200},
    {"grade": 4, "name": "小学4年", "count": 200},
    {"grade": 5, "name": "小学5年", "count": 185},
    {"grade": 6, "name": "小学6年", "count": 181},
    {"grade": 7, "name": "中学校", "count": 1130},
]

# Default Kanji Decks
DEFAULT_KANJI_DECKS = [
    {"name": "JLPT N5 漢字", "icon": "🟢", "description": "80 kanji for JLPT N5"},
    {"name": "JLPT N4 漢字", "icon": "🟡", "description": "170 kanji for JLPT N4"},
    {"name": "JLPT N3 漢字", "icon": "🟠", "description": "370 kanji for JLPT N3"},
    {"name": "JLPT N2 漢字", "icon": "🔴", "description": "1000 kanji for JLPT N2"},
    {"name": "JLPT N1 漢字", "icon": "⚫", "description": "2000 kanji for JLPT N1"},
    {"name": "RTK Order", "icon": "📘", "description": "Remembering The Kanji order"},
    {"name": "Frequency Order", "icon": "📊", "description": "Ordered by usage frequency"},
    {"name": "Custom Cards", "icon": "✨", "description": "Your custom kanji cards"},
]

# SRS Intervals (Anki-style, in days)
SRS_INTERVALS = {
    0: 0,      # New card - same day
    1: 1,      # Learning - 1 day
    2: 3,      # 3 days
    3: 7,      # 1 week
    4: 14,     # 2 weeks
    5: 30,     # 1 month
    6: 60,     # 2 months
    7: 120,    # 4 months
    8: 240,    # 8 months (mature)
}

# Rating descriptions (Anki-style)
SRS_RATINGS = {
    1: {"name": "Again", "description": "Didn't remember at all", "icon": "❌"},
    2: {"name": "Hard", "description": "Remembered with difficulty", "icon": "🟠"},
    3: {"name": "Good", "description": "Remembered correctly", "icon": "🟢"},
    4: {"name": "Easy", "description": "Very easy to remember", "icon": "⭐"},
}
