import sys
import os
sys.path.append(os.getcwd())

from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.unified_vocab import VocabItem

with Session(engine) as session:
    items = session.exec(select(VocabItem).where(VocabItem.lang == "en")).all()
    print(f"Total English items in unified table: {len(items)}")
    
    imported = session.exec(select(VocabItem).where(VocabItem.level == "Imported")).all()
    print(f"Items with level 'Imported': {len(imported)}")
    
    if imported:
        first = imported[0]
        print(f"Sample: {first.term} - {first.meaning} (Topic: {first.topic_id})")
