import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Import vocabulary from CSV file."""
import csv
import sys
from pathlib import Path
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic

def import_from_csv(csv_path: str):
    """Import vocabulary from CSV file."""
    vocab_list = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vocab_list.append({
                'word': row.get('word', ''),
                'ipa': row.get('ipa', ''),
                'pos': row.get('pos', ''),
                'meaning_vi': row.get('meaning_vi', ''),
                'example_en': row.get('example_en', '')
            })
    
    print(f"Loaded {len(vocab_list)} words from CSV")
    
    with Session(engine) as session:
        # Create topic
        topic = session.exec(
            select(VocabTopic).where(
                VocabTopic.name == "HACKERS TOEIC",
                VocabTopic.lang == "en"
            )
        ).first()
        
        if not topic:
            topic = VocabTopic(
                user_id=1,
                name="HACKERS TOEIC",
                lang="en",
                description="Vocabulary from HACKERS TOEIC",
                color="#FF6B6B",
                icon=""
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
        
        # Import words
        imported = 0
        for vocab in vocab_list:
            if not vocab['word']:
                continue
                
            existing = session.exec(
                select(EnVocabItem).where(
                    EnVocabItem.word == vocab['word'],
                    EnVocabItem.user_id == 1
                )
            ).first()
            
            if existing:
                continue
            
            item = EnVocabItem(
                user_id=1,
                word=vocab['word'],
                ipa=vocab.get('ipa', '')[:100],
                pos=vocab.get('pos', '')[:50],
                meaning_vi=vocab.get('meaning_vi', '')[:500],
                example_en=vocab.get('example_en', '')[:1000],
                topic_id=topic.id,
                source_material="HACKERS TOEIC",
                level="TOEIC 800",
                mastery_status="new"
            )
            session.add(item)
            imported += 1
            
            if imported % 100 == 0:
                session.commit()
                print(f"Imported {imported} words...")
        
        session.commit()
        print(f"Total imported: {imported} words")

if __name__ == "__main__":
    import_from_csv("hackers_toeic_vocab.csv")

