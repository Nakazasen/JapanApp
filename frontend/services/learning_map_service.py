"""Learning Map Service - Business logic for map progress tracking.

Provides:
- CRUD operations for LearningProgress records
- Region statistics (completion %, total/mastered counts)
- Node unlock logic based on prerequisites
- Initial progress seeding
"""
from datetime import datetime
from typing import Optional
from sqlmodel import Session, select, func

from frontend.models.learning_progress import (
    LearningProgress,
    MapStatus,
    MapRegion,
    get_region_from_level,
    REGION_CONFIG,
)
from frontend.models.grammar import GrammarTopic
from frontend.core.database import engine


class LearningMapService:
    """Service for managing Learning Map progress."""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize service with optional session.
        
        Args:
            session: SQLModel session (creates new if not provided)
        """
        self._session = session
        self._owns_session = session is None
    
    def _get_session(self) -> Session:
        """Get or create database session."""
        if self._session is None:
            self._session = Session(engine)
        return self._session
    
    def close(self):
        """Close session if we own it."""
        if self._owns_session and self._session:
            self._session.close()
            self._session = None
    
    # ============ Progress CRUD ============
    
    def get_progress(self, grammar_id: int) -> Optional[LearningProgress]:
        """Get progress record for a grammar item.
        
        Args:
            grammar_id: ID of the grammar topic
            
        Returns:
            LearningProgress record or None if not found
        """
        session = self._get_session()
        return session.exec(
            select(LearningProgress).where(LearningProgress.grammar_id == grammar_id)
        ).first()
    
    def get_all_progress(self) -> list[LearningProgress]:
        """Get all progress records."""
        session = self._get_session()
        return list(session.exec(select(LearningProgress)).all())
    
    def get_progress_by_region(self, region: MapRegion) -> list[LearningProgress]:
        """Get all progress records for a specific region.
        
        Args:
            region: MapRegion to filter by
            
        Returns:
            List of LearningProgress records in that region
        """
        session = self._get_session()
        
        # Define level mapping for each region
        region_levels = {
            MapRegion.A1: ["A1", "N5"],
            MapRegion.A2: ["A2", "N4"],
            MapRegion.B1: ["B1", "N3"],
            MapRegion.B2: ["B2", "N2"],
            MapRegion.C1: ["C1", "C2", "N1"]
        }
        
        target_levels = region_levels.get(region, [])
        
        # Join LearningProgress with GrammarTopic and filter by level directly in DB
        return list(session.exec(
            select(LearningProgress)
            .join(GrammarTopic, LearningProgress.grammar_id == GrammarTopic.id)
            .where(GrammarTopic.level.in_(target_levels))
            .order_by(LearningProgress.order_in_region)
        ).all())
    
    def update_progress(
        self, 
        grammar_id: int, 
        new_status: MapStatus,
        increment_attempts: bool = True
    ) -> Optional[LearningProgress]:
        """Update progress status for a grammar item.
        
        Args:
            grammar_id: ID of the grammar topic
            new_status: New MapStatus to set
            increment_attempts: Whether to increment attempt count
            
        Returns:
            Updated LearningProgress record
        """
        session = self._get_session()
        progress = self.get_progress(grammar_id)
        
        if not progress:
            return None
        
        old_status = progress.map_status
        progress.map_status = new_status.value
        progress.last_studied = datetime.utcnow()
        
        if increment_attempts:
            progress.attempts += 1
        
        # Set timestamps based on status change
        if new_status == MapStatus.AVAILABLE and old_status == MapStatus.LOCKED.value:
            progress.unlocked_at = datetime.utcnow()
        elif new_status == MapStatus.MASTERED and old_status != MapStatus.MASTERED.value:
            progress.mastered_at = datetime.utcnow()
        
        session.add(progress)
        session.commit()
        session.refresh(progress)
        
        return progress
    
    # ============ Region Statistics ============
    
    def get_region_stats(self, region: MapRegion) -> dict:
        """Get completion statistics for a region.
        
        Args:
            region: MapRegion to get stats for
            
        Returns:
            Dict with total, mastered, learning counts and percentage
        """
        progress_list = self.get_progress_by_region(region)
        
        if not progress_list:
            return {
                "region": region.value,
                "region_name": REGION_CONFIG[region]["name"],
                "icon": REGION_CONFIG[region]["icon"],
                "total": 0,
                "mastered": 0,
                "learning": 0,
                "available": 0,
                "locked": 0,
                "percent_complete": 0.0,
            }
        
        mastered = sum(1 for p in progress_list if p.map_status == MapStatus.MASTERED.value)
        learning = sum(1 for p in progress_list if p.map_status == MapStatus.LEARNING.value)
        available = sum(1 for p in progress_list if p.map_status == MapStatus.AVAILABLE.value)
        locked = sum(1 for p in progress_list if p.map_status == MapStatus.LOCKED.value)
        total = len(progress_list)
        
        return {
            "region": region.value,
            "region_name": REGION_CONFIG[region]["name"],
            "icon": REGION_CONFIG[region]["icon"],
            "total": total,
            "mastered": mastered,
            "learning": learning,
            "available": available,
            "locked": locked,
            "percent_complete": (mastered / total * 100) if total > 0 else 0.0,
        }
    
    def get_all_region_stats(self) -> list[dict]:
        """Get stats for all regions."""
        return [self.get_region_stats(region) for region in MapRegion]
    
    def get_overall_stats(self) -> dict:
        """Get overall progress statistics."""
        all_progress = self.get_all_progress()
        
        if not all_progress:
            return {
                "total": 0,
                "mastered": 0,
                "learning": 0,
                "available": 0,
                "locked": 0,
                "percent_complete": 0.0,
            }
        
        mastered = sum(1 for p in all_progress if p.map_status == MapStatus.MASTERED.value)
        learning = sum(1 for p in all_progress if p.map_status == MapStatus.LEARNING.value)
        available = sum(1 for p in all_progress if p.map_status == MapStatus.AVAILABLE.value)
        locked = sum(1 for p in all_progress if p.map_status == MapStatus.LOCKED.value)
        total = len(all_progress)
        
        return {
            "total": total,
            "mastered": mastered,
            "learning": learning,
            "available": available,
            "locked": locked,
            "percent_complete": (mastered / total * 100) if total > 0 else 0.0,
        }
    
    # ============ Unlock Logic ============
    
    def unlock_next_nodes(self, completed_grammar_id: int) -> list[LearningProgress]:
        """Unlock nodes that depend on the completed grammar item.
        
        Args:
            completed_grammar_id: ID of the just-completed grammar item
            
        Returns:
            List of newly unlocked LearningProgress records
        """
        session = self._get_session()
        all_progress = self.get_all_progress()
        
        # Get all mastered IDs
        mastered_ids = {
            p.grammar_id for p in all_progress 
            if p.map_status == MapStatus.MASTERED.value
        }
        mastered_ids.add(completed_grammar_id)  # Include the just-completed one
        
        unlocked = []
        
        for progress in all_progress:
            if progress.map_status == MapStatus.LOCKED.value:
                if progress.can_unlock(mastered_ids):
                    progress.map_status = MapStatus.AVAILABLE.value
                    progress.unlocked_at = datetime.utcnow()
                    session.add(progress)
                    unlocked.append(progress)
        
        if unlocked:
            session.commit()
            for p in unlocked:
                session.refresh(p)
        
        return unlocked
    
    def check_region_boss_completion(self, region: MapRegion) -> bool:
        """Check if the boss node for a region is completed.
        
        Args:
            region: MapRegion to check
            
        Returns:
            True if boss node is mastered
        """
        progress_list = self.get_progress_by_region(region)
        
        for p in progress_list:
            if p.is_boss_node and p.map_status == MapStatus.MASTERED.value:
                return True
        
        return False
    
    # ============ Seeding ============
    
    def seed_progress(self, force: bool = False) -> int:
        """Seed initial progress records for all grammar items.
        
        Creates LearningProgress records for all GrammarTopic items.
        - A1 items: AVAILABLE (ready to learn)
        - A2-C1 items: LOCKED (need to unlock)
        - Boss nodes: Last item in each region
        
        Args:
            force: If True, recreate all records even if they exist
            
        Returns:
            Number of records created
        """
        session = self._get_session()
        
        # Check if already seeded
        existing_count = session.exec(
            select(func.count(LearningProgress.id))
        ).one()
        
        if existing_count > 0 and not force:
            return 0  # Already seeded
        
        # Clear existing if forcing
        if force and existing_count > 0:
            for p in session.exec(select(LearningProgress)).all():
                session.delete(p)
            session.commit()
        
        # Get all grammar topics
        grammar_items = list(session.exec(
            select(GrammarTopic).order_by(GrammarTopic.level, GrammarTopic.id)
        ).all())
        
        if not grammar_items:
            return 0
        
        # Group by region
        region_items: dict[MapRegion, list[GrammarTopic]] = {}
        for item in grammar_items:
            region = get_region_from_level(item.level)
            if region not in region_items:
                region_items[region] = []
            region_items[region].append(item)
        
        created_count = 0
        
        for region, items in region_items.items():
            for i, item in enumerate(items):
                is_boss = (i == len(items) - 1)  # Last item is boss
                is_first_region = (region == MapRegion.A1)
                
                # Calculate position (spiral layout)
                import math
                angle = i * 0.5
                radius = 50 + (i // 5) * 30
                pos_x = 400 + radius * math.cos(angle)
                pos_y = 300 + radius * math.sin(angle)
                
                # Determine initial status
                if is_first_region:
                    # First few A1 nodes are available
                    initial_status = MapStatus.AVAILABLE if i < 5 else MapStatus.LOCKED
                else:
                    initial_status = MapStatus.LOCKED
                
                # Set prerequisites (previous node in region)
                prereq_ids = None
                if i > 0:
                    prereq_ids = str(items[i - 1].id)
                
                progress = LearningProgress(
                    grammar_id=item.id,
                    map_status=initial_status.value,
                    position_x=pos_x,
                    position_y=pos_y,
                    is_boss_node=is_boss,
                    order_in_region=i,
                    prerequisite_ids=prereq_ids,
                    unlocked_at=datetime.utcnow() if initial_status == MapStatus.AVAILABLE else None,
                )
                session.add(progress)
                created_count += 1
        
        session.commit()
        return created_count
    
    def ensure_progress_exists(self) -> bool:
        """Ensure progress records exist, seed if not.
        
        Returns:
            True if records were seeded, False if already existed
        """
        count = self.seed_progress(force=False)
        return count > 0
