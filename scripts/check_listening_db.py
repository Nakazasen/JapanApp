from sqlmodel import Session, create_engine, select
import sys
import os

sys.path.append(os.getcwd())
from frontend.core.config import settings
from frontend.models.listening_practice import ListeningItem, ListeningCategory

def check_db():
    engine = create_engine(f"sqlite:///{settings.db_path}")
    with Session(engine) as session:
        # List first 5 listening items and their paths
        items = session.exec(select(ListeningItem).limit(5)).all()
        for i in items:
            print(f"ID: {i.id}, Title: {i.title}, Path: {i.audio_path}, Transcript length: {len(i.transcript or '')}")
            
        # Check a specific one if possible
        n1_items = session.exec(select(ListeningItem).where(ListeningItem.title.like("%Exercise 01%"))).all()
        for i in n1_items:
            print(f"N1 Entry: {i.title}, Path: {i.audio_path}, Transcript: {i.transcript[:50] if i.transcript else 'EMPTY'}")

if __name__ == "__main__":
    check_db()
