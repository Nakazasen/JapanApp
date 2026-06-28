import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from sqlmodel import Session, create_engine, select
from frontend.core.config import settings
from frontend.models.vocab import JpVocabItem, EnVocabItem, VocabTopic
from frontend.models.user import User
from datetime import datetime

def seed_vocab():
    # Create SQLite engine directly
    database_url = f"sqlite:///{settings.db_path}"
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        # 0. Check for default user
        user = session.exec(select(User).where(User.id == 1)).first()
        if not user:
            user = User(
                id=1,
                username="testuser",
                password_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", # empty string hash
                created_at=datetime.utcnow()
            )
            session.add(user)
            session.commit()
            print("Created default user ID: 1")

        # 1. Create a Topic
        topic = session.exec(select(VocabTopic).where(VocabTopic.name == "Dữ liệu mẫu")).first()
        if not topic:
            topic = VocabTopic(
                name="Dữ liệu mẫu", 
                icon="📚", 
                description="Dữ liệu mẫu đềEtest",
                user_id=1,
                lang="jp"
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
        topic_id = topic.id

        # 2. Sample Japanese Words
        jp_words = [
            {"word_kanji": "食べめE, "word_kana": "たべめE, "meaning_vi": "ăn", "level": "N5", "source_material": "Minna no Nihongo"},
            {"word_kanji": "勉強", "word_kana": "べんきめE��", "meaning_vi": "học tập", "level": "N5", "source_material": "Minna no Nihongo"},
            {"word_kanji": "経渁E, "word_kana": "けいざい", "meaning_vi": "kinh tế", "level": "N3", "source_material": "Soumatome N3"},
            {"word_kanji": "環墁E, "word_kana": "かんきょぁE, "meaning_vi": "môi trường", "level": "N3", "source_material": "Soumatome N3"},
            {"word_kanji": "難しい", "word_kana": "むずかしい", "meaning_vi": "khó", "level": "N4", "source_material": "Genki"},
        ]
        
        print("Seeding Japanese vocab...")
        for w in jp_words:
            existing = session.exec(select(JpVocabItem).where(JpVocabItem.word_kanji == w['word_kanji'])).first()
            if not existing:
                item = JpVocabItem(
                    **w, 
                    topic_id=topic_id, 
                    user_id=1, 
                    mastery_status="new",
                    created_at=datetime.utcnow(),
                    next_review_at=datetime.utcnow()
                )
                session.add(item)
                print(f"  Added JP: {w['word_kanji']}")
            else:
                print(f"  Skipped JP: {w['word_kanji']} (exists)")

        # 3. Sample English Words
        en_words = [
            {"word": "sustainable", "meaning_vi": "bền vững", "level": "B2", "source_material": "IELTS Cambridge"},
            {"word": "ubiquitous", "meaning_vi": "phềEbiến khắp nơi", "level": "C1", "source_material": "IELTS Cambridge"},
            {"word": "apple", "meaning_vi": "quả táo", "level": "A1", "source_material": "Basic English"},
            {"word": "negotiate", "meaning_vi": "đàm phán", "level": "B2", "source_material": "Business English"},
        ]
        
        print("\nSeeding English vocab...")
        for w in en_words:
            existing = session.exec(select(EnVocabItem).where(EnVocabItem.word == w['word'])).first()
            if not existing:
                item = EnVocabItem(
                    **w, 
                    topic_id=topic_id, 
                    user_id=1, 
                    mastery_status="new",
                    created_at=datetime.utcnow(),
                    next_review_at=datetime.utcnow()
                )
                session.add(item)
                print(f"  Added EN: {w['word']}")
            else:
                print(f"  Skipped EN: {w['word']} (exists)")

        session.commit()
    print("\nDone seeding!")

if __name__ == "__main__":
    seed_vocab()

