"""Seed all TOEIC data.

Imports:
- Listening Part 1, 2, 3
- Reading Part 5, 6, 7
- Creates Full Mock Test
"""
import sys
import os
import json
from pathlib import Path

# Add project root to python path
sys.path.append(os.getcwd())

from frontend.core.database import get_session, init_db
from frontend.models.toeic import ToeicQuestion, QuestionType, ToeicTest, TestType
from sqlmodel import select, func

DATA_DIR = Path("data/toeic")

def import_questions(part, filename, is_set_based=False):
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"⚠️  Skipping Part {part}: matched file {filename} not found.")
        return

    print(f"Importing Part {part} from {filename}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with get_session() as session:
        count = 0
        skipped = 0
        
        # Helper to get next set ID
        def get_next_set_id():
            max_id = session.exec(select(func.max(ToeicQuestion.question_set_id))).first() or 0
            return max_id + 1

        if is_set_based:
            # Data is list of sets
            current_set_id = get_next_set_id()
            for set_data in data:
                passage = set_data.get("passage")
                topic = set_data.get("topic")
                transcript = set_data.get("transcript")
                audio_path = set_data.get("audio_path")
                
                # Determine QType
                if part in [3, 4]: q_type = QuestionType.CONVERSATION.value
                elif part == 6: q_type = QuestionType.TEXT_COMPLETION.value
                elif part == 7: q_type = QuestionType.READING.value
                else: q_type = QuestionType.PHOTO.value

                for q_data in set_data.get("questions", []):
                    # Check existing
                    existing = session.exec(select(ToeicQuestion).where(
                        ToeicQuestion.part == part,
                        ToeicQuestion.question_number == q_data.get("question_number")
                    )).first()
                    
                    if existing:
                        skipped += 1
                        continue

                    q = ToeicQuestion(
                        part=part,
                        question_type=q_type,
                        difficulty=3,
                        topic=topic,
                        question_text=q_data["question_text"],
                        options=q_data["options"],
                        correct_answer=q_data["correct_answer"],
                        explanation=q_data.get("explanation"),
                        passage=passage,
                        transcript=transcript,
                        audio_path=audio_path,
                        question_number=q_data.get("question_number", 0),
                        question_set_id=current_set_id
                    )
                    session.add(q)
                    count += 1
                current_set_id += 1
        else:
            # Data is list of questions
            for idx, q_data in enumerate(data):
                # Check existing
                existing = session.exec(select(ToeicQuestion).where(
                    ToeicQuestion.part == part,
                    ToeicQuestion.question_text == q_data.get("question_text")
                )).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # Determine QType
                if part == 1: q_type = QuestionType.PHOTO.value
                elif part == 2: q_type = QuestionType.QR.value
                elif part == 5: q_type = QuestionType.GRAMMAR.value
                else: q_type = QuestionType.READING.value

                q = ToeicQuestion(
                    part=part,
                    question_type=q_type,
                    difficulty=3,
                    topic=q_data.get("topic"),
                    question_text=q_data.get("question_text"),
                    options=q_data.get("options", {}),
                    correct_answer=q_data.get("correct_answer"),
                    explanation=q_data.get("explanation"),
                    audio_path=q_data.get("audio_path"),
                    image_path=q_data.get("image_path"),
                    question_number=q_data.get("question_number", idx+1)
                )
                session.add(q)
                count += 1

        session.commit()
        print(f"✅ Imported {count} items (Skipped {skipped})")

def create_full_test():
    print("\nCreating/Updating Full Test...")
    with get_session() as session:
        # Check if exists
        test = session.exec(select(ToeicTest).where(ToeicTest.name == "TOEIC Full Mock Test 1")).first()
        if not test:
            test = ToeicTest(
                name="TOEIC Full Mock Test 1",
                test_type=TestType.FULL.value,
                total_questions=0,
                time_limit=120,
                description="Simulated full test."
            )
            session.add(test)
            session.commit()
            session.refresh(test)
            print(f"Created Test ID: {test.id}")
        else:
            print(f"Updating Test ID: {test.id}")

        # Link questions
        parts = [1, 2, 3, 4, 5, 6, 7]
        total_linked = 0
        
        for part in parts:
            questions = session.exec(select(ToeicQuestion).where(ToeicQuestion.part == part)).all()
            for q in questions:
                 q.test_id = test.id
                 session.add(q)
                 total_linked += 1
        
        test.total_questions = total_linked
        session.add(test)
        session.commit()
        print(f"✅ Linked {total_linked} questions to test.")

if __name__ == "__main__":
    init_db()
    
    # Listening
    import_questions(1, "listening_part1.json", is_set_based=False)
    import_questions(2, "listening_part2.json", is_set_based=False)
    import_questions(3, "listening_part3.json", is_set_based=True)
    
    # Reading
    import_questions(5, "reading_part5.json", is_set_based=False)
    import_questions(6, "reading_part6.json", is_set_based=True)
    import_questions(7, "reading_part7.json", is_set_based=True)
    
    create_full_test()
    print("\n🎉 Seeding Complete!")
