"""Learning Map progress tracking models.

Tracks user progress through the Learning Map feature:
- MapStatus: Current state of each grammar node (locked/available/learning/mastered)
- MapRegion: Geographic regions representing CEFR levels (A1-C1)
- LearningProgress: Progress data for each grammar item on the map
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime
from sqlalchemy import func


class MapStatus(str, Enum):
    """Status of a grammar node on the Learning Map."""
    LOCKED = "locked"         # 🔒 Cannot access yet
    AVAILABLE = "available"   # ⬜ Ready to learn
    LEARNING = "learning"     # 🔵 In progress
    MASTERED = "mastered"     # ✅ Completed


class MapRegion(str, Enum):
    """Geographic regions on the Learning Map, mapped to CEFR levels."""
    A1 = "a1"  # 🏝️ Đảo Khởi Đầu (Starter Island)
    A2 = "a2"  # 🌲 Rừng Sơ Cấp (Elementary Forest)
    B1 = "b1"  # 🏔️ Núi Trung Cấp (Intermediate Mountain)
    B2 = "b2"  # 🌋 Núi Lửa Nâng Cao (Upper Volcano)
    C1 = "c1"  # 🏰 Lâu Đài Master (Master Castle)


# Region configuration with display names, colors, and unlock conditions
REGION_CONFIG = {
    MapRegion.A1: {
        "name": "Đảo Khởi Đầu",
        "name_en": "Starter Island",
        "icon": "🏝️",
        "color_primary": "#4ecdc4",    # Cyan
        "color_secondary": "#a8e6cf",  # Light green
        "color_accent": "#ffd93d",     # Yellow
        "unlock_condition": None,       # Always available
    },
    MapRegion.A2: {
        "name": "Rừng Sơ Cấp",
        "name_en": "Elementary Forest",
        "icon": "🌲",
        "color_primary": "#2d5016",    # Dark green
        "color_secondary": "#6b8e23",  # Olive
        "color_accent": "#98d8c8",     # Mint
        "unlock_condition": "complete_a1_boss",
    },
    MapRegion.B1: {
        "name": "Núi Trung Cấp",
        "name_en": "Intermediate Mountain",
        "icon": "🏔️",
        "color_primary": "#6c757d",    # Grey
        "color_secondary": "#adb5bd",  # Light grey
        "color_accent": "#74b9ff",     # Sky blue
        "unlock_condition": "complete_a2_boss",
    },
    MapRegion.B2: {
        "name": "Núi Lửa Nâng Cao",
        "name_en": "Upper Volcano",
        "icon": "🌋",
        "color_primary": "#d63031",    # Red
        "color_secondary": "#ff7675",  # Light red
        "color_accent": "#fdcb6e",     # Orange
        "unlock_condition": "complete_b1_boss",
    },
    MapRegion.C1: {
        "name": "Lâu Đài Master",
        "name_en": "Master Castle",
        "icon": "🏰",
        "color_primary": "#6c5ce7",    # Purple
        "color_secondary": "#a29bfe",  # Light purple
        "color_accent": "#ffeaa7",     # Gold
        "unlock_condition": "complete_b2_boss",
    },
}


def get_region_from_level(level: str | None) -> MapRegion:
    """Map grammar CEFR level to map region.
    
    Args:
        level: CEFR level string (A1, A2, B1, B2, C1, C2) or None
        
    Returns:
        MapRegion enum value
    """
    if not level:
        return MapRegion.A1  # Default to starter region
    
    level_upper = level.upper().strip()
    mapping = {
        "A1": MapRegion.A1,
        "A2": MapRegion.A2,
        "B1": MapRegion.B1,
        "B2": MapRegion.B2,
        "C1": MapRegion.C1,
        "C2": MapRegion.C1,  # Merge C2 into C1
        # Also support JLPT levels
        "N5": MapRegion.A1,
        "N4": MapRegion.A2,
        "N3": MapRegion.B1,
        "N2": MapRegion.B2,
        "N1": MapRegion.C1,
    }
    return mapping.get(level_upper, MapRegion.A1)


def get_region_display_name(region: MapRegion) -> str:
    """Get Vietnamese display name for a region."""
    return REGION_CONFIG[region]["name"]


def get_region_icon(region: MapRegion) -> str:
    """Get emoji icon for a region."""
    return REGION_CONFIG[region]["icon"]


class LearningProgress(SQLModel, table=True):
    """Tracks progress for each grammar item on the Learning Map.
    
    One record per grammar item, storing:
    - Current status (locked/available/learning/mastered)
    - Node position on the map
    - Progress timestamps
    - Prerequisites for unlocking
    """
    __tablename__ = "learning_progress"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    grammar_id: int = Field(foreign_key="grammar_topics.id", unique=True, index=True)
    
    # Map-specific fields
    map_status: str = Field(default=MapStatus.LOCKED.value, max_length=20)
    position_x: float = Field(default=0.0)  # Node X position in region
    position_y: float = Field(default=0.0)  # Node Y position in region
    is_boss_node: bool = Field(default=False)  # Final node of region
    order_in_region: int = Field(default=0)  # Order within region for path drawing
    
    # Progress tracking
    attempts: int = Field(default=0)  # Number of study attempts
    correct_count: int = Field(default=0)  # Number of correct answers
    
    # Timestamps
    unlocked_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    mastered_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    last_studied: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    
    # Dependencies - comma-separated grammar_ids that must be completed first
    prerequisite_ids: Optional[str] = Field(default=None, max_length=500)
    
    @property
    def status(self) -> MapStatus:
        """Get status as enum."""
        return MapStatus(self.map_status)
    
    @status.setter
    def status(self, value: MapStatus):
        """Set status from enum."""
        self.map_status = value.value
    
    @property
    def prerequisite_list(self) -> list[int]:
        """Get prerequisites as list of IDs."""
        if not self.prerequisite_ids:
            return []
        return [int(x.strip()) for x in self.prerequisite_ids.split(",") if x.strip()]
    
    @prerequisite_list.setter
    def prerequisite_list(self, ids: list[int]):
        """Set prerequisites from list of IDs."""
        self.prerequisite_ids = ",".join(str(x) for x in ids) if ids else None
    
    def can_unlock(self, completed_ids: set[int]) -> bool:
        """Check if this node can be unlocked based on completed prerequisites."""
        if self.map_status != MapStatus.LOCKED.value:
            return False  # Already unlocked
        
        prereqs = self.prerequisite_list
        if not prereqs:
            return True  # No prerequisites
        
        return all(pid in completed_ids for pid in prereqs)
