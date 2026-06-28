"""Verification script for Phase 08 (Full Test Mode)."""
import sys
import os
sys.path.append(os.getcwd())

from frontend.services.toeic_listening_service import get_toeic_listening_service
from frontend.core.database import init_db

def verify():
    print("Initializing Service...")
    service = get_toeic_listening_service()
    
    # 1. Test get_test_details(1)
    print("\nTesting get_test_details(1)...")
    details = service.get_test_details(1)
    
    if not details:
        print("❌ No test details returned! Did you run create_full_test.py?")
        return

    print(f"✅ Found Test: {details['name']}")
    parts = details['parts']
    total_items = 0
    for part_num, items in parts.items():
        print(f"   Part {part_num}: {len(items)} items")
        total_items += len(items)
        
    if total_items > 0:
        print(f"✅ Total Items Loaded: {total_items}")
    else:
        print("❌ Test has no items.")

    # 2. Test submit_test(1)
    print("\nTesting submit_test(1)...")
    # Fake some answers
    fake_answers = {1: "A", 2: "B"} 
    result = service.submit_test(1, fake_answers)
    
    print(f"✅ Submission Result: Score={result['score']}, Correct={result['correct_count']}")
    
    print("\n✅ Phase 08 Service Verification Complete!")

if __name__ == "__main__":
    verify()
