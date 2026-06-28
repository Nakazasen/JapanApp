import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Parse vocabulary from text file extracted via OCR."""
import re
import sys
from pathlib import Path
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic

def parse_vocab_from_text(text_path: str):
    """Parse vocabulary from OCR text file."""
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    vocab_list = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Pattern for HACKERS TOEIC: WORD (IPA) POS meaning
        match = re.match(
            r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*\(/([^/]+)/\)?\s*(\w+\.?)\s*(.+)',
            line
        )
        
        if match:
            word = match.group(1).strip()
            ipa = match.group(2).strip()
            pos = match.group(3).strip().rstrip('.')
            meaning = match.group(4).strip()
            
            if len(word) >= 2 and len(word) <= 40:
                vocab_list.append({
                    'word': word,
                    'ipa': f"/{ipa}/",
                    'pos': pos,
                    'meaning_vi': meaning
                })
    
    print(f"Found {len(vocab_list)} vocabulary entries")
    return vocab_list

def import_to_db(vocab_list):
    """Import to database."""
    with Session(engine) as session:
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
        
        imported = 0
        for vocab in vocab_list:
            existing = session.exec(
                select(EnVocabItem).where(
                    EnVocabItem.word == vocab['word'],
                    EnVocabItem.user_id == 1
                )
            ).first()
            
            if not existing:
                item = EnVocabItem(
                    user_id=1,
                    word=vocab['word'],
                    ipa=vocab['ipa'][:100],
                    pos=vocab['pos'][:50],
                    meaning_vi=vocab['meaning_vi'][:500],
                    topic_id=topic.id,
                    source_material="HACKERS TOEIC",
                    level="TOEIC 800",
                    mastery_status="new"
                )
                session.add(item)
                imported += 1
        
        session.commit()
        print(f"Imported {imported} words to database")

if __name__ == "__main__":
    vocab_list = parse_vocab_from_text("hackers_toeic_text.txt")
    import_to_db(vocab_list)

