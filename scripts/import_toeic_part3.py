"""Import TOEIC Listening Part 3 (Conversations) data.

Supports grouping questions into sets using `question_set_id`.
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

def import_part3():
    """Import Part 3 data from JSON."""
    json_path = "data/toeic/listening_part3.json"
    
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        with get_session() as session:
            # Get max question_set_id to avoid collissions if appending
            # For simplicity, we assume fresh sets or handle distinct sets logic later.
            # Here we just use an auto-incrementing logic helper if needed, 
            # but for now we'll trust the script to create fresh sets.
            
            # Find next set ID start 
            # (In a real app, strict management of set IDs is needed)
            max_set = session.exec(select(func.max(ToeicQuestion.question_set_id))).first() or 0
            current_set_id_base = max_set + 1
            
            count = 0
            for set_data in data:
                # Assign a unique set ID
                actual_set_id = current_set_id_base + count
                
                audio_path = set_data.get("audio_path")
                transcript = set_data.get("transcript")
                topic = set_data.get("topic")
                
                for q_data in set_data.get("questions", []):
                    # Check if exists
                    existing = session.exec(
                        select(ToeicQuestion).where(
                            ToeicQuestion.question_number == q_data["question_number"],
                            ToeicQuestion.part == 3
                        )
                    ).first()
                    
                    if existing:
                        print(f"Skipping existing Q{q_data['question_number']}")
                        continue
                        
                    q = ToeicQuestion(
                        part=3,
                        question_type=QuestionType.CONVERSATION.value,
                        difficulty=3,
                        topic=topic,
                        question_text=q_data["question_text"],
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        explanation=q_data["explanation"],
                        transcript=transcript, # Shared transcript
                        audio_path=audio_path, # Shared audio
                        question_number=q_data["question_number"],
                        question_set_id=actual_set_id # !Important: Link them
                    )
                    session.add(q)
                
                count += 1
            
            session.commit()
            print(f"Successfully imported {count} sets.")

    except Exception as e:
        print(f"Error importing Part 3: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from sqlalchemy import func
    init_db()
    import_part3()
