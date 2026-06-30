
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from frontend.services.toeic_listening_service import get_toeic_listening_service
from frontend.core.database import get_session
from frontend.models.toeic import ToeicQuestion

def main():
    print("Testing TOEIC Listening Enhancements...")
    
    # 1. Check Model Field
    print("\n1. Checking ToeicQuestion model...")
    try:
        q = ToeicQuestion(
            part=1, 
            question_type="photo", 
            correct_answer="A",
            transcript="This is a test transcript."
        )
        print(f"✅ ToeicQuestion has transcript field: '{q.transcript}'")
    except Exception as e:
        print(f"❌ ToeicQuestion missing transcript field: {e}")
        return

    # 2. Check Service
    print("\n2. Checking AI Analysis Service...")
    service = get_toeic_listening_service()
    
    # Create a real dummy question in DB to test service
    with get_session() as session:
        dummy = ToeicQuestion(
            part=999,
            question_type="test",
            correct_answer="A",
            topic="Testing",
            explanation="Because logic.",
            question_text="Why?",
            transcript="Transcript content."
        )
        session.add(dummy)
        session.commit()
        session.refresh(dummy)
        dummy_id = dummy.id
    
    try:
        analysis = service.get_ai_analysis(dummy_id)
        print(f"✅ AI Analysis Result:\n{analysis}")
        
        # Cleanup
        with get_session() as session:
            q = session.get(ToeicQuestion, dummy_id)
            if q:
                session.delete(q)
                session.commit()
            
    except Exception as e:
        print(f"❌ Service check failed: {e}")

if __name__ == "__main__":
    main()
