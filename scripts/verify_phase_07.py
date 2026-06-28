"""Verification script for Phase 07 (Reading Part 6-7)."""
import sys
import os
sys.path.append(os.getcwd())

from frontend.services.toeic_listening_service import get_toeic_listening_service
from frontend.core.database import init_db

def verify():
    print("Initializing Service...")
    service = get_toeic_listening_service()
    
    # 1. Test Part 6 (Text Completion)
    print("\nTesting list_question_sets(6)...")
    sets_p6 = service.list_question_sets(6)
    
    if not sets_p6:
        print("❌ No Part 6 sets returned!")
    else:
        p6_set = sets_p6[0]
        print(f"✅ Found Part 6 set.")
        print(f"   Passage Length: {len(p6_set.get('passage', ''))}")
        print(f"   Questions: {len(p6_set.get('questions', []))}")
        if p6_set.get('passage'):
            print("   ✅ Passage content present.")
        else:
            print("   ❌ Passage content MISSING.")

    # 2. Test Part 7 (Reading Comp)
    print("\nTesting list_question_sets(7)...")
    sets_p7 = service.list_question_sets(7)
    
    if not sets_p7:
        print("❌ No Part 7 sets returned!")
    else:
        p7_set = sets_p7[0]
        print(f"✅ Found Part 7 set.")
        print(f"   Passage Length: {len(p7_set.get('passage', ''))}")
        print(f"   Questions: {len(p7_set.get('questions', []))}")
        if p7_set.get('passage'):
            print("   ✅ Passage content present.")
        else:
            print("   ❌ Passage content MISSING.")

    print("\n✅ Phase 07 Verification Complete!")

if __name__ == "__main__":
    verify()
