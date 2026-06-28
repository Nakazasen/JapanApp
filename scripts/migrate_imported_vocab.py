import sys
import os
sys.path.append(os.getcwd())

from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem
from frontend.models.unified_vocab import VocabItem

def migrate():
    with Session(engine) as session:
        # 1. Get items from legacy table
        legacy_items = session.exec(select(EnVocabItem).where(EnVocabItem.level == "Imported")).all()
        print(f"Found {len(legacy_items)} items in en_vocab_items to migrate.")
        
        migrated_count = 0
        for legacy in legacy_items:
            # Check if already exists in unified table (by term and lang)
            existing = session.exec(
                select(VocabItem).where(
                    VocabItem.term == legacy.word,
                    VocabItem.lang == "en"
                )
            ).first()
            
            if not existing:
                # Prepare examples
                examples = []
                if legacy.example_en:
                    examples.append({
                        "sentence": legacy.example_en,
                        "translation": legacy.example_vi or ""
                    })
                
                # Prepare meta_data
                meta_data = {}
                if legacy.ipa: meta_data["ipa"] = legacy.ipa
                if legacy.pos: meta_data["pos"] = legacy.pos
                if legacy.meaning_en: meta_data["meaning_en"] = legacy.meaning_en
                
                # Create unified item
                unified = VocabItem(
                    user_id=legacy.user_id,
                    term=legacy.word,
                    reading=legacy.ipa,
                    meaning=legacy.meaning_vi,
                    lang="en",
                    level=legacy.level,
                    topic_id=legacy.topic_id,
                    source_material=legacy.source_material,
                    meta_data=meta_data,
                    examples=examples,
                    user_note=legacy.user_note,
                    tags=legacy.tags,
                    created_at=legacy.created_at
                )
                session.add(unified)
                migrated_count += 1
            
            # Delete from legacy table
            session.delete(legacy)
            
        session.commit()
        print(f"Successfully migrated {migrated_count} items to unified_vocab_items.")
        print(f"Deleted {len(legacy_items)} items from en_vocab_items.")

if __name__ == "__main__":
    migrate()
