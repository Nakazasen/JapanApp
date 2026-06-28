import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Import TOEIC vocabulary into the unified VocabItem database.

Usage:
    python scripts/import_toeic_vocab.py

This script reads from data/toeic/toeic_vocabulary.json and inserts
words into the unified_vocab_items table with source_material='TOEIC'.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from frontend.core.database import get_session, init_db
from frontend.models.unified_vocab import VocabItem, MasteryStatus


def load_toeic_vocab(json_path: Path) -> list:
    """Load vocabulary from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_vocab(vocab_list: list, user_id: int = 1, dry_run: bool = False) -> dict:
    """
    Import vocabulary into database.
    
    Args:
        vocab_list: List of vocabulary dictionaries
        user_id: User ID to associate with vocab
        dry_run: If True, don't actually insert, just validate
        
    Returns:
        Dictionary with import stats
    """
    stats = {
        "total": len(vocab_list),
        "imported": 0,
        "skipped": 0,
        "errors": []
    }
    
    if dry_run:
        print("剥 DRY RUN MODE - No data will be inserted")
    
    with get_session() as session:
        for i, word in enumerate(vocab_list):
            try:
                # Check if word already exists
                existing = session.query(VocabItem).filter(
                    VocabItem.term == word["term"],
                    VocabItem.source_material == "TOEIC",
                    VocabItem.user_id == user_id
                ).first()
                
                if existing:
                    stats["skipped"] += 1
                    print(f"竢ｭ・・ [{i+1}/{stats['total']}] Skipped (exists): {word['term']}")
                    continue
                
                # Create new VocabItem
                vocab_item = VocabItem(
                    user_id=user_id,
                    term=word["term"],
                    reading=word.get("reading"),
                    meaning=word["meaning"],
                    lang="en",
                    level="TOEIC",
                    source_material="TOEIC",
                    topic_id=None,  # Could map topics later
                    meta_data=word.get("meta_data", {}),
                    examples=word.get("examples", []),
                    mastery_status=MasteryStatus.NEW.value,
                    srs_level=0,
                    next_review=datetime.utcnow(),
                )
                
                if not dry_run:
                    session.add(vocab_item)
                    session.commit()
                
                stats["imported"] += 1
                topic = word.get("meta_data", {}).get("topic", "General")
                print(f"笨・[{i+1}/{stats['total']}] Imported: {word['term']} ({topic})")
                
            except Exception as e:
                stats["errors"].append({"term": word.get("term", "?"), "error": str(e)})
                print(f"笶・[{i+1}/{stats['total']}] Error: {word.get('term', '?')} - {e}")
    
    return stats


def main():
    """Main function."""
    print("=" * 60)
    print("答 TOEIC Vocabulary Import Script")
    print("=" * 60)
    
    # Initialize database
    print("\n肌 Initializing database...")
    init_db()
    
    # Load vocabulary
    vocab_path = PROJECT_ROOT / "data" / "toeic" / "toeic_vocabulary.json"
    if not vocab_path.exists():
        print(f"笶・File not found: {vocab_path}")
        return
    
    print(f"当 Loading vocabulary from: {vocab_path}")
    vocab_list = load_toeic_vocab(vocab_path)
    print(f"投 Found {len(vocab_list)} words\n")
    
    # Import
    print("-" * 60)
    stats = import_vocab(vocab_list, user_id=1, dry_run=False)
    
    # Summary
    print("\n" + "=" * 60)
    print("投 IMPORT SUMMARY")
    print("=" * 60)
    print(f"   Total words:  {stats['total']}")
    print(f"   笨・Imported:   {stats['imported']}")
    print(f"   竢ｭ・・ Skipped:    {stats['skipped']}")
    print(f"   笶・Errors:     {len(stats['errors'])}")
    
    if stats['errors']:
        print("\n笞・・Errors:")
        for err in stats['errors']:
            print(f"   - {err['term']}: {err['error']}")
    
    print("\n笨・Import complete!")


if __name__ == "__main__":
    main()

