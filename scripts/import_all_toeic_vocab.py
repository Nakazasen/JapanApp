import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Import all TOEIC vocabulary batches into the database.

Usage:
    python scripts/import_all_toeic_vocab.py
"""
import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from frontend.core.database import get_session, init_db
from frontend.models.unified_vocab import VocabItem, MasteryStatus


def import_batch(json_path: Path, user_id: int = 1):
    """Import a single batch file."""
    if not json_path.exists():
        print(f"笞・・ File not found: {json_path.name}")
        return {"imported": 0, "skipped": 0, "errors": 0}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        vocab_list = json.load(f)
    
    stats = {"imported": 0, "skipped": 0, "errors": 0}
    
    with get_session() as session:
        for word in vocab_list:
            try:
                existing = session.query(VocabItem).filter(
                    VocabItem.term == word["term"],
                    VocabItem.source_material == "TOEIC",
                    VocabItem.user_id == user_id
                ).first()
                
                if existing:
                    stats["skipped"] += 1
                    continue
                
                vocab_item = VocabItem(
                    user_id=user_id,
                    term=word["term"],
                    reading=word.get("reading"),
                    meaning=word["meaning"],
                    lang="en",
                    level="TOEIC",
                    source_material="TOEIC",
                    meta_data=word.get("meta_data", {}),
                    examples=word.get("examples", []),
                    mastery_status=MasteryStatus.NEW.value,
                    srs_level=0,
                    next_review=datetime.utcnow(),
                )
                session.add(vocab_item)
                session.commit()
                stats["imported"] += 1
            except Exception as e:
                stats["errors"] += 1
    
    return stats


def main():
    print("=" * 60)
    print("答 TOEIC Vocabulary Batch Import")
    print("=" * 60)
    
    init_db()
    
    data_dir = PROJECT_ROOT / "data" / "toeic"
    batch_files = sorted(data_dir.glob("toeic_vocab*.json"))
    
    total_stats = {"imported": 0, "skipped": 0, "errors": 0}
    
    for batch_file in batch_files:
        print(f"\n当 Processing: {batch_file.name}")
        stats = import_batch(batch_file)
        total_stats["imported"] += stats["imported"]
        total_stats["skipped"] += stats["skipped"]
        total_stats["errors"] += stats["errors"]
        print(f"   笨・{stats['imported']} imported, 竢ｭ・・{stats['skipped']} skipped, 笶・{stats['errors']} errors")
    
    print("\n" + "=" * 60)
    print("投 TOTAL SUMMARY")
    print("=" * 60)
    print(f"   Files processed: {len(batch_files)}")
    print(f"   笨・Imported:     {total_stats['imported']}")
    print(f"   竢ｭ・・ Skipped:      {total_stats['skipped']}")
    print(f"   笶・Errors:       {total_stats['errors']}")
    print("\n笨・All batches imported!")


if __name__ == "__main__":
    main()

