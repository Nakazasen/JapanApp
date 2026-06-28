from sqlmodel import Session, create_engine, select
import sys
import os

sys.path.append(os.getcwd())
from frontend.core.config import settings
from frontend.models.listening_practice import ListeningItem, ListeningQuestion

def check_db():
    engine = create_engine(f"sqlite:///{settings.db_path}")
    with Session(engine) as session:
        # Check if there are questions with audio
        items = session.exec(select(ListeningItem).limit(10)).all()
        for i in items:
            questions = session.exec(select(ListeningQuestion).where(ListeningQuestion.item_id == i.id)).all()
            q_with_audio = [q for q in questions if q.audio_path]
            print(f"Item ID: {i.id}, Title: {i.title}, Item Audio: {i.audio_path}, Qs with audio: {len(q_with_audio)}")
            if q_with_audio:
                print(f"  Sample Q Audio: {q_with_audio[0].audio_path}")

if __name__ == "__main__":
    check_db()
