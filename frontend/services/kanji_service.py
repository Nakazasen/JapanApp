"""Kanji Service - Centralized Kanji database operations."""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlmodel import Session, select, or_, func, col
from frontend.core.database import engine, get_session
from frontend.models.kanji import KanjiItem, KanjiMasteryStatus, KanjiDeck, KanjiVocab
from frontend.services.srs_service import SRSService
from frontend.services.base_service import BaseService

class KanjiService(BaseService):
    """Service to handle Kanji-related database operations."""

    def search_kanji(
        self, 
        deck_id: Optional[int] = None, 
        status: Optional[str] = None, 
        query: Optional[str] = None, 
        offset: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search kanji with filters and pagination."""
        with Session(engine) as session:
            statement = select(KanjiItem)
            
            if deck_id:
                statement = statement.where(KanjiItem.deck_id == deck_id)
            if status:
                statement = statement.where(KanjiItem.mastery_status == status)
            if query:
                statement = statement.where(or_(
                    KanjiItem.kanji.contains(query),
                    KanjiItem.han_viet.contains(query),
                    KanjiItem.meaning_vi.contains(query)
                ))
            
            # Get total count
            count_statement = select(func.count()).select_from(statement.subquery())
            total = session.exec(count_statement).one()
            
            # Get results
            statement = statement.offset(offset).limit(limit)
            results = session.exec(statement).all()
            
            return [item.model_dump() for item in results], total

    def submit_review(self, kanji_id: int, quality: int) -> bool:
        """Submit review for a kanji card using SM-2."""
        with get_session() as session:
            item = session.get(KanjiItem, kanji_id)
            if not item:
                return False
            
            # SM-2 Logic
            new_streak, new_ef, new_interval = SRSService.calculate_next_state(
                current_streak=item.srs_streak or 0,
                current_ease_factor=item.srs_ease_factor or 2.5,
                current_interval=item.srs_interval or 0,
                quality=quality
            )
            
            item.srs_streak = new_streak
            item.srs_ease_factor = new_ef
            item.srs_interval = new_interval
            item.next_review_at = SRSService.get_next_review_date(new_interval)
            item.review_count = (item.review_count or 0) + 1
            item.last_reviewed_at = datetime.utcnow()
            
            # Update Mastery Status
            if quality == 1:
                # If it's a "Leech" (repeatedly forgotten), mark it
                if (item.lapse_count or 0) > 8:
                    item.mastery_status = KanjiMasteryStatus.LEECH.value
                else:
                    item.mastery_status = KanjiMasteryStatus.REVIEWING.value
                item.lapse_count = (item.lapse_count or 0) + 1
            elif new_interval >= 21:
                item.mastery_status = KanjiMasteryStatus.MASTERED.value
            else:
                item.mastery_status = KanjiMasteryStatus.REVIEWING.value
                
            session.add(item)
            return True

    def change_status(self, kanji_id: int, status: str) -> bool:
        """Manually change the mastery status of a kanji."""
        with get_session() as session:
            item = session.get(KanjiItem, kanji_id)
            if item:
                item.mastery_status = status
                session.add(item)
                return True
            return False

_instance = None
def get_kanji_service() -> KanjiService:
    global _instance
    if _instance is None:
        _instance = KanjiService()
    return _instance
