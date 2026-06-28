import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Database initialization script."""
import sys
import os
from pathlib import Path
import hashlib

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session
from frontend.core.database import engine, init_db
from frontend.models import (
    User, NewsSource, ExamSource, GrammarTopic
)


def hash_password(password: str) -> str:
    """Hash password using SHA256 (simple hashing for demo)."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_default_data():
    """Seed default data: news sources, exam sources, grammar topics, admin user."""
    with Session(engine) as session:
        # Create admin user
        admin = session.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),  # Default password
                email="admin@example.com"
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print("[OK] Created admin user (username: admin, password: admin123)")
        else:
            print("[OK] Admin user already exists")
        
        # Seed News Sources
        news_sources = [
            NewsSource(name="BBC News", url="https://www.bbc.com/news", lang="en"),
            NewsSource(name="CNN", url="https://www.cnn.com", lang="en"),
            NewsSource(name="NHK News", url="https://www3.nhk.or.jp/news/", lang="jp"),
            NewsSource(name="Asahi Shimbun", url="https://www.asahi.com/", lang="jp"),
        ]
        
        for source in news_sources:
            existing = session.query(NewsSource).filter(NewsSource.name == source.name).first()
            if not existing:
                session.add(source)
                print(f"[OK] Added news source: {source.name}")
        session.commit()
        
        # Seed Exam Sources
        exam_sources = [
            ExamSource(name="ĐềEthi tiếng Nhật", url="https://dethitiengnhat.com", lang="jp"),
            ExamSource(name="JLPT Practice", url="https://jlpt-practice.com", lang="jp"),
            ExamSource(name="TOEIC Practice", url="https://toeic-practice.com", lang="en"),
            ExamSource(name="IELTS Practice", url="https://ielts-practice.com", lang="en"),
        ]
        
        for source in exam_sources:
            existing = session.query(ExamSource).filter(ExamSource.name == source.name).first()
            if not existing:
                session.add(source)
                print(f"[OK] Added exam source: {source.name}")
        session.commit()
        
        # Seed Grammar Topics (basic examples)
        grammar_topics = [
            GrammarTopic(
                lang="en",
                title="Present Perfect",
                description="Used to describe actions that happened at an unspecified time before now or actions that started in the past and continue to the present.",
                source_url="https://en.wikipedia.org/wiki/Present_perfect"
            ),
            GrammarTopic(
                lang="en",
                title="Past Simple",
                description="Used to describe completed actions in the past.",
                source_url="https://en.wikipedia.org/wiki/Simple_past"
            ),
            GrammarTopic(
                lang="jp",
                title="て-form",
                description="The te-form (て形) is used to connect verbs, express requests, and in various grammatical patterns.",
                source_url="https://en.wikipedia.org/wiki/Japanese_verb_conjugation"
            ),
            GrammarTopic(
                lang="jp",
                title="でぁEだ (desu/da)",
                description="The copula verbs used to indicate that something is or equals something else.",
                source_url="https://en.wikipedia.org/wiki/Japanese_copula"
            ),
        ]
        
        for topic in grammar_topics:
            existing = session.query(GrammarTopic).filter(
                GrammarTopic.title == topic.title,
                GrammarTopic.lang == topic.lang
            ).first()
            if not existing:
                session.add(topic)
                print(f"[OK] Added grammar topic: {topic.title} ({topic.lang})")
        session.commit()
        
        print("\n[OK] Database initialization completed!")


if __name__ == "__main__":
    print("Initializing database...")
    print(f"Database path: {Path(__file__).parent.parent / 'db' / 'app.db'}")
    
    # Create database and tables
    init_db()
    print("[OK] Database tables created")
    
    # Seed default data
    seed_default_data()
    
    print("\nDatabase is ready to use!")


