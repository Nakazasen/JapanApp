"""Stats Service - Local database operations for Dashboard statistics.

This service provides statistics directly from SQLite without HTTP backend.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sqlmodel import Session, select

from frontend.services.base_service import BaseService
from frontend.core.database import get_session
from frontend.models.vocab import JpVocabItem, EnVocabItem, MasteryStatus
from frontend.models.study import StudyHistory


class StatsService(BaseService):
    """Service for dashboard and statistics from local database."""
    
    def get_dashboard_stats(self, lang: str = None) -> Dict[str, Any]:
        """
        Get dashboard statistics for gamification.
        
        Args:
            lang: Optional language code ('en' or 'jp') to filter stats.
            
        Returns:
            Dict with total_vocab, mastered_vocab, current_streak, due_today, activity_map, and extra stats.
        """
        try:
            user_id = self.get_current_user_id()
            now = datetime.now()
            
            with get_session() as session:
                # Fetch relevant vocab based on language
                all_vocab = []
                if lang == 'jp' or lang is None:
                    jp_vocab = session.exec(
                        select(JpVocabItem).where(JpVocabItem.user_id == user_id)
                    ).all()
                    all_vocab.extend(list(jp_vocab))
                
                if lang == 'en' or lang is None:
                    en_vocab = session.exec(
                        select(EnVocabItem).where(EnVocabItem.user_id == user_id)
                    ).all()
                    all_vocab.extend(list(en_vocab))
                
                total_vocab = len(all_vocab)
                mastered_vocab = sum(
                    1 for v in all_vocab 
                    if v.mastery_status == MasteryStatus.MASTERED.value
                )
                
                # Count due today
                due_today = sum(
                    1 for v in all_vocab
                    if (v.next_review and v.next_review <= now) or not v.next_review
                )
                
                # Calculate streak from study history (Streak is global)
                current_streak = self._calculate_streak(session, user_id)
                
                # Build activity map (last 90 days) - Activity is global
                activity_map = self._build_activity_map(session, user_id)
                
                stats = {
                    "success": True,
                    "total_vocab": total_vocab,
                    "mastered_vocab": mastered_vocab,
                    "current_streak": current_streak,
                    "due_today": due_today,
                    "activity_map": activity_map
                }

                # --- Add Extra Language-Specific Stats ---
                if lang == 'en':
                    stats.update({
                        "toeic_score": 750, # Placeholder/Estimated
                        "accuracy": 85,      # Estimated from study history later
                    })
                elif lang == 'jp':
                    stats.update({
                        "kanji_count": sum(1 for v in all_vocab if getattr(v, 'kanji', None)),
                        "jlpt_level": "N3",  # Placeholder/Estimated
                    })

                return stats
                
        except Exception as e:
            print(f"[ERROR StatsService] Failed to get dashboard stats: {e}")
            return {
                "success": False,
                "total_vocab": 0,
                "mastered_vocab": 0,
                "current_streak": 0,
                "due_today": 0,
                "activity_map": {}
            }
    
    def _calculate_streak(self, session: Session, user_id: int) -> int:
        """Calculate current study streak in days."""
        try:
            # Get study history ordered by date descending
            history = session.exec(
                select(StudyHistory)
                .where(StudyHistory.user_id == user_id)
                .order_by(StudyHistory.study_date.desc())
            ).all()
            
            if not history:
                return 0
            
            streak = 0
            today = datetime.now().date()
            expected_date = today
            
            for record in history:
                record_date = record.study_date.date() if isinstance(record.study_date, datetime) else record.study_date
                
                if record_date == expected_date:
                    streak += 1
                    expected_date -= timedelta(days=1)
                elif record_date < expected_date:
                    # Check if we skipped a day
                    if record_date == expected_date - timedelta(days=1):
                        expected_date = record_date
                        streak += 1
                        expected_date -= timedelta(days=1)
                    else:
                        break
                        
            return streak
            
        except Exception as e:
            print(f"[StatsService] Error calculating streak: {e}")
            return 0
    
    def _build_activity_map(self, session: Session, user_id: int) -> Dict[str, int]:
        """Build activity map for last 90 days."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365) # Show full year
            
            history = session.exec(
                select(StudyHistory)
                .where(
                    StudyHistory.user_id == user_id,
                    StudyHistory.study_date >= start_date
                )
            ).all()
            
            activity_map = defaultdict(int)
            for record in history:
                date_str = record.study_date.strftime("%Y-%m-%d") if isinstance(record.study_date, datetime) else str(record.study_date)
                activity_map[date_str] += record.words_reviewed or 1
            
            return dict(activity_map)
            
        except Exception as e:
            print(f"[StatsService] Error building activity map: {e}")
            return {}
    
    def get_weekly_stats(self) -> Dict[str, Any]:
        """Get statistics for the current week."""
        try:
            user_id = self.get_current_user_id()
            
            with get_session() as session:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=7)
                
                history = session.exec(
                    select(StudyHistory)
                    .where(
                        StudyHistory.user_id == user_id,
                        StudyHistory.study_date >= start_date
                    )
                ).all()
                
                total_reviews = sum(h.words_reviewed or 0 for h in history)
                
                daily_breakdown = defaultdict(int)
                for record in history:
                    date_str = record.study_date.strftime("%Y-%m-%d") if isinstance(record.study_date, datetime) else str(record.study_date)
                    daily_breakdown[date_str] += record.words_reviewed or 0
                
                return {
                    "success": True,
                    "reviews_this_week": total_reviews,
                    "daily_breakdown": dict(daily_breakdown)
                }
                
        except Exception as e:
            print(f"[ERROR StatsService] Failed to get weekly stats: {e}")
            return {
                "success": False,
                "reviews_this_week": 0,
                "daily_breakdown": {}
            }


# Global singleton
_stats_service: Optional[StatsService] = None


def get_stats_service() -> StatsService:
    """Get global StatsService instance."""
    global _stats_service
    if _stats_service is None:
        _stats_service = StatsService()
    return _stats_service
