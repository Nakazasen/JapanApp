"""Practice Service - Database operations for Reading and Listening exercises."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlmodel import Session, select, or_

from frontend.services.base_service import BaseService
from frontend.core.database import get_session
from frontend.models.practice import PracticeCategory, PracticeItem, PracticeQuestion, PracticeProgress, PracticeType

class PracticeService(BaseService):
    """Service for Reading and Listening practice database operations."""
    
    # =============== Category Management ===============
    
    def create_category(self, name: str, practice_type: str, level: str, icon: str = None) -> Dict[str, Any]:
        """Create a new practice category."""
        try:
            with get_session() as session:
                cat = PracticeCategory(
                    user_id=self.get_current_user_id(),
                    name=name,
                    type=practice_type,
                    level=level,
                    icon=icon
                )
                session.add(cat)
                session.commit()
                session.refresh(cat)
                return {"success": True, "id": cat.id, "name": cat.name}
        except Exception as e:
            return {"error": str(e)}

    def list_categories(self, practice_type: str) -> List[Dict[str, Any]]:
        """List categories by type."""
        try:
            with get_session() as session:
                statement = select(PracticeCategory).where(
                    PracticeCategory.type == practice_type
                )
                cats = session.exec(statement).all()
                
                # Enrich with counts and sort
                result = []
                for c in cats:
                    count = len(c.items)
                    result.append({
                        "id": c.id, 
                        "name": c.name, 
                        "level": c.level, 
                        "icon": c.icon,
                        "count": count
                    })
                
                # Sort by count desc, then name
                result.sort(key=lambda x: (-x['count'], x['name']))
                return result
        except Exception as e:
            print(f"[PracticeService] list_categories error: {e}")
            return []

    # =============== Item Management ===============

    def list_items(self, category_id: int) -> List[Dict[str, Any]]:
        """List all items in a category."""
        try:
            with get_session() as session:
                statement = select(PracticeItem).where(
                    PracticeItem.category_id == category_id
                )
                items = session.exec(statement).all()
                return [
                    {
                        "id": i.id, 
                        "title": i.title, 
                        "source": i.source,
                        "question_count": len(i.questions)
                    } 
                    for i in items
                ]
        except Exception as e:
            print(f"[PracticeService] list_items error: {e}")
            return []

    def get_item_detail(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get full item detail including questions."""
        try:
            with get_session() as session:
                item = session.get(PracticeItem, item_id)
                if not item:
                    return None
                
                return {
                    "id": item.id,
                    "title": item.title,
                    "content": item.content,
                    "audio_path": item.audio_path,
                    "image_path": item.image_path,
                    "source": item.source,
                    "questions": [
                        {
                            "id": q.id,
                            "question_text": q.question_text,
                            "options": q.options,
                            "correct_option": q.correct_option,
                            "explanation": q.explanation
                        }
                        for q in item.questions
                    ],
                    "vocabulary": item.vocabulary,
                    "translation": item.translation,
                    "analysis": item.analysis,
                    "audio_path": item.audio_path
                }
        except Exception as e:
            print(f"[PracticeService] get_item_detail error: {e}")
            return None

    # =============== Progress & Stats ===============

    def get_stats(self, practice_type: str) -> Dict[str, Any]:
        """Get summary stats for a practice type."""
        try:
            with get_session() as session:
                # Count total items for this type
                cat_statement = select(PracticeCategory.id).where(PracticeCategory.type == practice_type)
                cat_ids = session.exec(cat_statement).all()
                
                if not cat_ids:
                    return {"total": 0, "completed": 0, "avg_score": 0.0}
                
                # Total items
                items_statement = select(PracticeItem).where(PracticeItem.category_id.in_(cat_ids))
                total_items = len(session.exec(items_statement).all())
                
                # Completed items
                progress_statement = select(PracticeProgress).where(
                    PracticeProgress.user_id == self.get_current_user_id()
                )
                completed_items = session.exec(progress_statement).all()
                # Filter by those that belong to the right cats
                # (Simple approach for now)
                
                return {
                    "total": total_items,
                    "completed": len(completed_items),
                    "avg_score": 0.0 # Placeholder
                }
        except Exception as e:
            print(f"[PracticeService] get_stats error: {e}")
            return {"total": 0, "completed": 0, "avg_score": 0.0}

    def update_item_analysis(
        self, item_id: int, 
        vocabulary: List[Dict], 
        translation: str, 
        analysis: List[Dict]
    ) -> bool:
        """Update item with AI analysis data."""
        try:
            with get_session() as session:
                item = session.get(PracticeItem, item_id)
                if item:
                    item.vocabulary = vocabulary
                    item.translation = translation
                    item.analysis = analysis
                    session.add(item)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"[PracticeService] update_item_analysis error: {e}")
            return False

    def update_item_audio(self, item_id: int, audio_path: str) -> bool:
        """Update item audio path."""
        try:
            with get_session() as session:
                item = session.get(PracticeItem, item_id)
                if item:
                    item.audio_path = audio_path
                    session.add(item)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"[PracticeService] update_item_audio error: {e}")
            return False

_practice_service = None

def get_practice_service():
    global _practice_service
    if _practice_service is None:
        _practice_service = PracticeService()
    return _practice_service
