from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime
from sqlalchemy import func

class ToeicFlashcard(SQLModel, table=True):
    """
    Flashcard for vocabulary learning with Spaced Repetition (SuperMemo-2 style).
    """
    __tablename__ = "toeic_flashcards"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    
    # Content
    word: str = Field(index=True, max_length=100)
    definition: str
    example_sentence: Optional[str] = Field(default=None)
    phonetic: Optional[str] = Field(default=None)
    
    # Source context
    source_question_id: Optional[int] = Field(default=None, index=True)
    
    # SRS Metadata (SuperMemo-2)
    repetition: int = Field(default=0)  # n-th review
    interval: int = Field(default=0)    # days until next review
    ease_factor: float = Field(default=2.5)
    
    # Dates
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    last_reviewed_at: Optional[datetime] = Field(default=None)
    next_review_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True
    )
    
    def update_srs(self, quality: int):
        """
        Update SRS state based on recall quality (0-5).
        0-2: Fail, 3-5: Pass.
        """
        if quality >= 3:
            if self.repetition == 0:
                self.interval = 1
            elif self.repetition == 1:
                self.interval = 6
            else:
                self.interval = int(self.interval * self.ease_factor)
            
            self.repetition += 1
            self.ease_factor = self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        else:
            self.repetition = 0
            self.interval = 1
            # ease_factor unchanged
            
        if self.ease_factor < 1.3:
            self.ease_factor = 1.3
            
        from datetime import timedelta
        self.last_reviewed_at = datetime.utcnow()
        self.next_review_at = self.last_reviewed_at + timedelta(days=self.interval)
