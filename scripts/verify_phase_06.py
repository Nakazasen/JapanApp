"""Verification script for Phase 06 (Listening Part 3)."""
import sys
import os
sys.path.append(os.getcwd())

from frontend.services.toeic_listening_service import get_toeic_listening_service
from frontend.core.database import init_db

def verify():
    print("Initializing Service...")
    service = get_toeic_listening_service()
    
    # 1. Test List Sets
    print("\nTesting list_question_sets(3)...")
    sets = service.list_question_sets(3)
    
    if not sets:
        print("❌ No sets returned! Did import fail?")
        return
        
    print(f"✅ Found {len(sets)} sets.")
    first_set = sets[0]
    print(f"Set ID: {first_set.get('set_id')}")
    print(f"Audio: {first_set.get('audio_path')}")
    print(f"Questions: {len(first_set.get('questions', []))}")
    
    if len(first_set.get('questions', [])) != 3:
        print("❌ Expected 3 questions in set 1.")
        return
        
    # 2. Test Check Answer
    q1 = first_set['questions'][0]
    print(f"\nTesting check_answer for Q{q1['question_number']}...")
    
    # Correct answer is 'A' (from json)
    res = service.check_answer(q1['id'], "A")
    if res['is_correct']:
        print("✅ Answer check PASSED (Correct)")
    else:
        print(f"❌ Answer check FAILED. Expected Correct, got {res}")

    res = service.check_answer(q1['id'], "B")
    if not res['is_correct']:
        print("✅ Answer check PASSED (Incorrect)")
    else:
        print(f"❌ Answer check FAILED. Expected Incorrect, got {res}")

    print("\n✅ Phase 06 Verification Complete!")

if __name__ == "__main__":
    verify()
