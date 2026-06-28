"""Reading Practice Service."""
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select
from frontend.services.base_service import BaseService
from frontend.core.database import get_session
from frontend.models.reading_practice import ReadingCategory, ReadingItem, ReadingQuestion, ReadingProgress

class ReadingPracticeService(BaseService):
    def list_categories(self) -> List[Dict[str, Any]]:
        try:
            with get_session() as session:
                cats = session.exec(select(ReadingCategory)).all()
                result = []
                for c in cats:
                    result.append({
                        "id": c.id, "name": c.name, "level": c.level, "icon": c.icon,
                        "count": len(c.items)
                    })
                result.sort(key=lambda x: (-x['count'], x['name']))
                return result
        except Exception as e:
            print(f"Error list_categories: {e}")
            return []

    def list_items(self, category_id: int) -> List[Dict[str, Any]]:
        try:
            with get_session() as session:
                items = session.exec(select(ReadingItem).where(ReadingItem.category_id == category_id)).all()
                return [{"id": i.id, "title": i.title, "source": i.source, "question_count": len(i.questions)} for i in items]
        except Exception as e:
            return []

    def get_item_detail(self, item_id: int) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as session:
                item = session.get(ReadingItem, item_id)
                if not item: return None
                return {
                    "id": item.id, "title": item.title, "content": item.content, "source": item.source,
                    "image_path": item.image_path, "audio_path": item.audio_path,
                    "vocabulary": item.vocabulary, "translation": item.translation, "analysis": item.analysis,
                    "questions": [{"id": q.id, "question_text": q.question_text, "options": q.options, "correct_option": q.correct_option, "explanation": q.explanation} for q in item.questions]
                }
        except Exception as e:
            return None

    def get_stats(self) -> Dict[str, Any]:
        try:
            with get_session() as session:
                total = len(session.exec(select(ReadingItem)).all())
                completed = len(session.exec(select(ReadingProgress).where(ReadingProgress.user_id == self.get_current_user_id())).all())
                return {"total": total, "completed": completed}
        except Exception:
            return {"total": 0, "completed": 0}

    def update_item_analysis(self, item_id: int, vocabulary: List, translation: str, analysis: List) -> bool:
        try:
            with get_session() as session:
                item = session.get(ReadingItem, item_id)
                if item:
                    item.vocabulary = vocabulary
                    item.translation = translation
                    item.analysis = analysis
                    session.add(item)
                    session.commit()
                    return True
                return False
        except Exception:
            return False

    def update_item_audio(self, item_id: int, audio_path: str) -> bool:
        try:
            with get_session() as session:
                item = session.get(ReadingItem, item_id)
                if item:
                    item.audio_path = audio_path
                    session.add(item)
                    session.commit()
                    return True
                return False
        except Exception:
            return False

_service = None
def get_reading_practice_service():
    global _service
    if _service is None: _service = ReadingPracticeService()
    return _service
