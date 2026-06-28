"""Listening Practice Service."""
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select
from frontend.services.base_service import BaseService
from frontend.core.database import get_session
from frontend.models.listening_practice import ListeningCategory, ListeningItem, ListeningQuestion, ListeningProgress

class ListeningPracticeService(BaseService):
    def list_categories(self) -> List[Dict[str, Any]]:
        try:
            with get_session() as session:
                cats = session.exec(select(ListeningCategory)).all()
                result = []
                for c in cats:
                    result.append({
                        "id": c.id, "name": c.name, "level": c.level, "icon": c.icon,
                        "count": len(c.items)
                    })
                result.sort(key=lambda x: (-x['count'], x['name']))
                return result
        except Exception as e:
            return []

    def list_items(self, category_id: int) -> List[Dict[str, Any]]:
        try:
            with get_session() as session:
                items = session.exec(select(ListeningItem).where(ListeningItem.category_id == category_id)).all()
                return [{"id": i.id, "title": i.title, "source": i.source, "question_count": len(i.questions)} for i in items]
        except Exception:
            return []

    def get_item_detail(self, item_id: int) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as session:
                item = session.get(ListeningItem, item_id)
                if not item: return None
                return {
                    "id": item.id, "title": item.title, "audio_path": item.audio_path, "transcript": item.transcript, "source": item.source,
                    "vocabulary": item.vocabulary, "translation": item.translation, "analysis": item.analysis,
                    "questions": [{"id": q.id, "question_text": q.question_text, "options": q.options, "correct_option": q.correct_option, "explanation": q.explanation, "audio_path": q.audio_path, "transcript": q.transcript} for q in item.questions]
                }
        except Exception:
            return None

    def update_item_analysis(self, item_id: int, vocabulary: List[Dict], translation: str, analysis: List[Dict]):
        try:
            with get_session() as session:
                item = session.get(ListeningItem, item_id)
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

    def get_stats(self) -> Dict[str, Any]:
        try:
            with get_session() as session:
                total = len(session.exec(select(ListeningItem)).all())
                completed = len(session.exec(select(ListeningProgress).where(ListeningProgress.user_id == self.get_current_user_id())).all())
                return {"total": total, "completed": completed}
        except Exception:
            return {"total": 0, "completed": 0}

_service = None
def get_listening_practice_service():
    global _service
    if _service is None: _service = ListeningPracticeService()
    return _service
