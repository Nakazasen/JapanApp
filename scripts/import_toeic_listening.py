import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Import script for TOEIC Listening questions.

Usage:
    python scripts/import_toeic_listening.py
"""
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from frontend.core.database import init_db, get_session
from frontend.models.toeic import ToeicQuestion


def import_listening_questions():
    """Import TOEIC listening questions from JSON files."""
    print("=" * 60)
    print("而 TOEIC Listening Questions Import")
    print("=" * 60)
    
    init_db()
    
    data_dir = PROJECT_ROOT / "data" / "toeic"
    files = [
        ("listening_part1.json", 1),
        ("listening_part2.json", 2),
    ]
    
    total_imported = 0
    total_skipped = 0
    
    for filename, part in files:
        filepath = data_dir / filename
        if not filepath.exists():
            print(f"笞・・ File not found: {filename}")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        print(f"\n唐 Processing: {filename} ({len(questions)} questions)")
        
        imported = 0
        skipped = 0
        
        with get_session() as session:
            for idx, q in enumerate(questions, 1):
                # Check if already exists (by part + question_text)
                existing = session.query(ToeicQuestion).filter(
                    ToeicQuestion.part == q["part"],
                    ToeicQuestion.question_text == q.get("question_text")
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # Create new question
                question = ToeicQuestion(
                    part=q["part"],
                    question_type=q["question_type"],
                    difficulty=q.get("difficulty", 3),
                    topic=q.get("topic"),
                    question_text=q.get("question_text"),
                    options=q["options"],
                    correct_answer=q["correct_answer"],
                    explanation=q.get("explanation"),
                    audio_path=q.get("audio_path"),
                    image_path=q.get("image_path"),
                    source=q.get("source", "Sample"),
                    question_number=idx,
                )
                session.add(question)
                imported += 1
            
            session.commit()
        
        print(f"   笨・Imported: {imported} | 竢ｭ・・Skipped: {skipped}")
        total_imported += imported
        total_skipped += skipped
    
    print("\n" + "=" * 60)
    print("投 SUMMARY")
    print("=" * 60)
    print(f"   Total Imported: {total_imported}")
    print(f"   Total Skipped:  {total_skipped}")
    print("\n笨・Import complete!")


if __name__ == "__main__":
    import_listening_questions()

