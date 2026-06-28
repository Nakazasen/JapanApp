"""Import TOEIC Reading Parts 6 & 7 data.

Supports grouping by `question_set_id` and importing `passage` content.
"""
import json
import os
import sys

# Add project root to python path
sys.path.append(os.getcwd())
print("Script started, path added.")

try:
    from frontend.core.database import get_session, init_db
    from frontend.models.toeic import ToeicQuestion, QuestionType
    from sqlmodel import select, func
    print("Imports successful.")
except Exception as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def import_reading(part: int, json_path: str):
    """Import Reading data from JSON."""
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        with get_session() as session:
            # Get max question_set_id
            max_set = session.exec(select(func.max(ToeicQuestion.question_set_id))).first() or 0
            current_set_id_base = max_set + 1
            
            count = 0
            for set_data in data:
                # Assign a unique set ID (or use provided if managing manually, but auto-inc is safer for script)
                # We'll rely on the existing set_id in JSON just for relative grouping within file, 
                # but in DB we should probably ensure uniqueness if appending.
                # For this simple script, we'll increment based on DB max.
                actual_set_id = current_set_id_base + count
                
                passage = set_data.get("passage")
                topic = set_data.get("topic")
                
                # Determine question type
                q_type = QuestionType.TEXT_COMPLETION.value if part == 6 else QuestionType.READING.value
                
                for q_data in set_data.get("questions", []):
                    # Check if exists
                    existing = session.exec(
                        select(ToeicQuestion).where(
                            ToeicQuestion.question_number == q_data["question_number"],
                            ToeicQuestion.part == part
                        )
                    ).first()
                    
                    if existing:
                        print(f"Skipping existing Q{q_data['question_number']}")
                        continue
                        
                    q = ToeicQuestion(
                        part=part,
                        question_type=q_type,
                        difficulty=3,
                        topic=topic,
                        question_text=q_data["question_text"],
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        explanation=q_data["explanation"],
                        passage=passage, # Shared passage
                        question_number=q_data["question_number"],
                        question_set_id=actual_set_id 
                    )
                    session.add(q)
                
                count += 1
            
            session.commit()
            print(f"Successfully imported {count} sets for Part {part}.")

    except Exception as e:
        print(f"Error importing Part {part}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_db()
    print("Importing Part 6...")
    import_reading(6, "data/toeic/reading_part6.json")
    print("Importing Part 7...")
    import_reading(7, "data/toeic/reading_part7.json")
