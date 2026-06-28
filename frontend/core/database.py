"""Database connection and session management."""
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session
from frontend.core.config import settings
from frontend.models import (
    User, JpVocabItem, EnVocabItem, StudyHistory, AppSettings,
    YoutubeChannel, YoutubeVideo, NewsSource, NewsArticle,
    GrammarTopic, GrammarExample,    ExamSource, Exam, ExamQuestion, ExamResult,
    Book, BookChapter, ReadingState, Bookmark,
    PracticeCategory, PracticeItem, PracticeQuestion, PracticeProgress,
    ToeicQuestion, ToeicTest, ToeicUserProgress, ToeicStudySession
)
from frontend.models.writing import WritingDraft
from frontend.models.unified_vocab import VocabItem


# Create SQLite engine
database_url = f"sqlite:///{settings.db_path}"
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL query logging
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_depedency_session():
    """Get database session (dependency for FastAPI - uses yield)."""
    with Session(engine) as session:
        yield session


@contextmanager
def get_session():
    """Get database session as context manager for desktop app use.
    
    Usage:
        with get_session() as session:
            user = session.exec(select(User).where(...)).first()
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize database - create tables."""
    create_db_and_tables()

