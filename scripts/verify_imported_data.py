import sys
import os
sys.path.append(os.getcwd())

from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem
from frontend.models.user import User

with Session(engine) as session:
    # Check total count
    count = session.exec(select(EnVocabItem)).all()
    print(f"Total English items: {len(count)}")
    
    # Check imported items
    imported = session.exec(select(EnVocabItem).where(EnVocabItem.level == "Imported")).all()
    print(f"Items with level 'Imported': {len(imported)}")
    
    if imported:
        first = imported[0]
        print(f"Sample - Word: {first.word}, Meaning: {first.meaning_vi}, UserID: {first.user_id}, TopicID: {first.topic_id}")
    
    # Check users
    users = session.exec(select(User)).all()
    for u in users:
        print(f"DB User: {u.username}, ID: {u.id}")
