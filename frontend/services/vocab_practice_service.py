"""Vocab Practice Service."""
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select
from frontend.services.base_service import BaseService
from frontend.core.database import get_session
from frontend.models.vocab_practice import VocabPracticeItem, VocabPracticeQuestion

class VocabPracticeService(BaseService):
    def list_items(self) -> List[Dict[str, Any]]:
        try:
            with get_session() as session:
                items = session.exec(select(VocabPracticeItem)).all()
                return [{"id": i.id, "title": i.title, "source": i.source, "question_count": 0} for i in items]
        except Exception as e:
            print(f"[ERROR VocabPracticeService] list_items: {e}")
            return []

    def get_item_detail(self, item_id: int) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as session:
                item = session.get(VocabPracticeItem, item_id)
                if not item: return None
                return {
                    "id": item.id, "title": item.title, "transcript": item.transcript,
                    "vocabulary": item.vocabulary, "translation": item.translation, "analysis": item.analysis,
                    "questions": [{"id": q.id, "question_text": q.question_text, "options": q.options, "correct_option": q.correct_option, "explanation": q.explanation} for q in item.questions]
                }
        except Exception as e:
            print(f"[ERROR VocabPracticeService] get_item_detail: {e}")
            return None

    def update_item_analysis(self, item_id: int, vocabulary: List[Dict], translation: str, analysis: List[Dict]):
        try:
            with get_session() as session:
                item = session.get(VocabPracticeItem, item_id)
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

_service = None
def get_vocab_practice_service():
    global _service
    if _service is None: _service = VocabPracticeService()
    return _service
