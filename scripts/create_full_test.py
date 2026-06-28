"""Create a Full TOEIC Test from existing questions.

This script:
1. Creates a new ToeicTest record (e.g., "Mock Test 1").
2. Finds existing questions from Parts 1, 2, 3, 5, 6, 7.
3. Links them to the new Test ID.
"""
import sys
import os
import random

# Add project root to python path
sys.path.append(os.getcwd())

from frontend.core.database import get_session, init_db
from frontend.models.toeic import ToeicTest, ToeicQuestion, TestType

def create_full_test():
    print("Creating Full Test...")
    with get_session() as session:
        # 1. Create Test Record
        test = ToeicTest(
            name="TOEIC Full Mock Test 1",
            test_type=TestType.FULL.value,
            total_questions=0, # Will update later
            time_limit=120, # 2 hours
            description="A simulated full test using available practice questions."
        )
        session.add(test)
        session.commit()
        session.refresh(test)
        print(f"Created Test: {test.name} (ID: {test.id})")
        
        # 2. Link Questions
        # We will fetch questions that are NOT already part of a test (test_id is None)
        # For this script, we'll just grab everything available for MVP simulation.
        
        from sqlmodel import select
        
        total_q = 0
        
        # Parts to include
        parts = [1, 2, 3, 5, 6, 7] # Part 4 might be missing data if we didn't import it, but that's fine.
        
        for part in parts:
            statement = select(ToeicQuestion).where(ToeicQuestion.part == part)
            questions = session.exec(statement).all()
            
            if not questions:
                print(f"⚠️ No questions found for Part {part}")
                continue
                
            print(f"Found {len(questions)} questions for Part {part}")
            
            # Link to test
            for q in questions:
                q.test_id = test.id
                session.add(q)
                total_q += 1
                
        # Update total count
        test.total_questions = total_q
        session.add(test)
        session.commit()
        
        print(f"✅ Successfully linked {total_q} questions to Test ID {test.id}")

if __name__ == "__main__":
    init_db()
    create_full_test()
