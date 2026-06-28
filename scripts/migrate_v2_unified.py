"""Migration script: Convert JpVocabItem/EnVocabItem to Unified VocabItem (Data Preserved)."""
import sys
import os
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from sqlmodel import Session, create_engine, select, text
from sqlalchemy import func
from frontend.models.vocab import JpVocabItem, EnVocabItem
from frontend.models.unified_vocab import VocabItem

# Database Configuration (From config if needed, hardcoded for script simplicity)
DB_PATH = project_root / "db" / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)

def migrate_data():
    print(f"🚀 Starting Migration: Legacy Tables -> Unified VocabItem")
    print(f"📁 Database: {DB_PATH}")
    
    with Session(engine) as session:
        # 1. Create new table if not exists
        print("🛠️ Creating 'unified_vocab_items' table...")
        VocabItem.metadata.create_all(engine)
        
        # 1.5 Clear existing data to avoid duplicates
        print("🧹 Clearing existing data...")
        session.exec(text("DELETE FROM unified_vocab_items"))
        session.commit()
        
        # 2. Migrate Japanese Items
        jp_items = session.exec(select(JpVocabItem)).all()
        print(f"🇯🇵 Found {len(jp_items)} Japanese items.")
        
        new_jp_items = []
        for item in jp_items:
            # Map examples
            examples = []
            if item.example_jp or item.example_vi:
                examples.append({
                    "sentence": item.example_jp,
                    "translation": item.example_vi
                })
            
            # Map metadata
            meta = {
                "romaji": item.romaji,
                "han_viet": item.han_viet
            }
            
            new_item = VocabItem(
                user_id=item.user_id,
                term=item.word_kanji,
                reading=item.word_kana,
                meaning=item.meaning_vi,
                lang="jp",
                level=item.level,
                topic_id=item.topic_id,
                source_material=item.source_material,
                tags=item.tags,
                meta_data=meta,
                examples=examples,
                audio_path=item.audio_path,
                user_note=item.user_note,
                mastery_status=item.mastery_status,
                is_ai_enriched=item.is_ai_enriched,
                created_at=item.created_at,
                srs_level=item.srs_level,
                srs_streak=item.srs_streak,
                srs_ease_factor=item.srs_ease_factor,
                srs_interval=item.srs_interval,
                next_review=item.next_review,
                last_reviewed=item.last_reviewed,
                review_count=item.review_count
            )
            new_jp_items.append(new_item)
            
        # 3. Migrate English Items
        en_items = session.exec(select(EnVocabItem)).all()
        print(f"🇬🇧 Found {len(en_items)} English items.")
        
        new_en_items = []
        for item in en_items:
             # Map examples
            examples = []
            if item.example_en or item.example_vi:
                examples.append({
                    "sentence": item.example_en,
                    "translation": item.example_vi
                })
            
            # Map metadata
            meta = {
                "pos": item.pos,
                "ipa": item.ipa,
                "meaning_en": item.meaning_en
            }
            
            new_item = VocabItem(
                user_id=item.user_id,
                term=item.word,
                reading=item.ipa, # Using IPA as reading for English
                meaning=item.meaning_vi,
                lang="en",
                level=item.level,
                topic_id=item.topic_id,
                source_material=item.source_material,
                tags=item.tags,
                meta_data=meta,
                examples=examples,
                user_note=item.user_note,
                mastery_status=item.mastery_status,
                is_ai_enriched=item.is_ai_enriched,
                created_at=item.created_at,
                srs_level=item.srs_level,
                srs_streak=item.srs_streak,
                srs_ease_factor=item.srs_ease_factor,
                srs_interval=item.srs_interval,
                next_review=item.next_review,
                last_reviewed=item.last_reviewed,
                review_count=item.review_count
            )
            new_en_items.append(new_item)
        
        # 4. Save to DB
        print("💾 Saving to database...")
        session.add_all(new_jp_items)
        session.add_all(new_en_items)
        session.commit()
        
        # 5. Verification
        total_new = session.exec(select(func.count(VocabItem.id))).one()
        print(f"✅ Migration Complete!")
        print(f"📊 Total items in 'unified_vocab_items': {total_new}")
        
        if total_new == len(jp_items) + len(en_items):
            print("✨ SUCCESS: Row count matches!")
        else:
            print(f"⚠️ WARNING: Row count mismatch! (Expected {len(jp_items) + len(en_items)})")

if __name__ == "__main__":
    migrate_data()
