from typing import List, Optional
from sqlmodel import select, Session
from frontend.core.database import get_session
from frontend.models.flashcard import ToeicFlashcard
from datetime import datetime

class FlashcardService:
    """
    Service to manage Flashcards.
    """
    
    def create_flashcard(self, user_id: int, word: str, definition: str, 
                         example: str = None, source_question_id: int = None) -> Optional[ToeicFlashcard]:
        """Create a new flashcard."""
        try:
            with get_session() as session:
                # Check duplicate
                existing = session.exec(
                    select(ToeicFlashcard)
                    .where(ToeicFlashcard.user_id == user_id)
                    .where(ToeicFlashcard.word == word)
                ).first()
                
                if existing:
                    return existing

                card = ToeicFlashcard(
                    user_id=user_id,
                    word=word,
                    definition=definition,
                    example_sentence=example,
                    source_question_id=source_question_id,
                    created_at=datetime.utcnow(),
                    next_review_at=datetime.utcnow() # Ready for review immediately
                )
                session.add(card)
                session.commit()
                session.refresh(card)
                return card
        except Exception as e:
            print(f"Error creating flashcard: {e}")
            return None

    def get_due_flashcards(self, user_id: int) -> List[ToeicFlashcard]:
        """Get cards due for review."""
        with get_session() as session:
            return session.exec(
                select(ToeicFlashcard)
                .where(ToeicFlashcard.user_id == user_id)
                .where(ToeicFlashcard.next_review_at <= datetime.utcnow())
                .order_by(ToeicFlashcard.next_review_at)
            ).all()

    def update_card_progress(self, card_id: int, quality: int):
        """Update SRS progress."""
        with get_session() as session:
            card = session.get(ToeicFlashcard, card_id)
            if card:
                card.update_srs(quality)
                session.add(card)
                session.commit()

# Singleton
_flashcard_service = None

def get_flashcard_service():
    global _flashcard_service
    if _flashcard_service is None:
        _flashcard_service = FlashcardService()
    return _flashcard_service
