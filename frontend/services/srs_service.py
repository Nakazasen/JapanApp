"""SRSService - Centralized Spaced Repetition System logic (SM-2 Algorithm)."""
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

class SRSService:
    """Service to calculate next review dates using the SM-2 algorithm."""

    @staticmethod
    def calculate_next_state(
        current_streak: int,
        current_ease_factor: float,
        current_interval: int,
        quality: int
    ) -> Tuple[int, float, int]:
        """
        Calculate the next state of an SRS item.
        
        Args:
            current_streak: How many times correctly reviewed in a row.
            current_ease_factor: The SM-2 ease factor (EF), default 2.5.
            current_interval: Previous interval in days.
            quality: User rating (1=Again, 2=Hard, 3=Good, 4=Easy).
            
        Returns:
            Tuple of (new_streak, new_ease_factor, new_interval_days)
        """
        # Map our 1-4 rating to SM-2 0-5 scale
        # 1 (Again) -> 0 (Complete blackout)
        # 2 (Hard)  -> 3 (Recalled with difficulty)
        # 3 (Good)  -> 4 (Recalled after hesitation)
        # 4 (Easy)  -> 5 (Perfect response)
        q_map = {1: 0, 2: 3, 3: 4, 4: 5}
        q = q_map.get(quality, 3)

        if q < 3:
            # Failed to remember
            new_streak = 0
            new_interval = 1 # Review again tomorrow
            # Ease factor doesn't change on failure in classic SM-2, 
            # but some implementations drop it. We'll keep it.
            new_ease_factor = current_ease_factor
        else:
            # Success
            if current_streak == 0:
                new_interval = 1
            elif current_streak == 1:
                new_interval = 6
            else:
                new_interval = round(current_interval * current_ease_factor)
            
            new_streak = current_streak + 1
            
            # Calculate new ease factor
            new_ease_factor = current_ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            
        # Bounds check
        if new_ease_factor < 1.3:
            new_ease_factor = 1.3
            
        return new_streak, new_ease_factor, new_interval

    @staticmethod
    def get_next_review_date(interval_days: int) -> datetime:
        """Get the next review timestamp based on interval."""
        return datetime.utcnow() + timedelta(days=interval_days)
