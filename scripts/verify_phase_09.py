"""Verification script for Phase 09 (AI Analysis)."""
import sys
import os
import asyncio
sys.path.append(os.getcwd())

from frontend.services.toeic_listening_service import get_toeic_listening_service
from frontend.core.database import init_db

# Helper to run async in main
def async_test(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

def verify():
    print("Initializing Service...")
    service = get_toeic_listening_service()
    
    # 1. Test Statistical Analysis
    print("\nTesting analyze_weaknesses()...")
    stats = service.analyze_weaknesses()
    
    if not stats:
        print("⚠️ No stats found. Ensure you have some test data (run verify_phase_08 or create_full_test).")
    else:
        print("✅ Stats Calculated:")
        weak_parts = stats.get("weak_parts", [])
        print(f"   Weak Parts identified: {len(weak_parts)}")
        for wp in weak_parts:
            print(f"   - Part {wp['part']}: {wp['accuracy']:.1f}% accuracy")
            
    # 2. Test AI Advice (Async)
    print("\nTesting generate_ai_advice()...")
    
    try:
        advice = async_test(service.generate_ai_advice())
        print("✅ AI Advice Generated:")
        print("-" * 40)
        print(advice[:200] + "..." if len(advice) > 200 else advice)
        print("-" * 40)
    except Exception as e:
        print(f"❌ AI Advice Failed: {e}")

    print("\n✅ Phase 09 Verification Complete!")

if __name__ == "__main__":
    verify()
