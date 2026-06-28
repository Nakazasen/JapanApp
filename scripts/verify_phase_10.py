"""Verification script for Phase 10 (Optimization)."""
import sys
import os
import asyncio
import time
import shutil
from pathlib import Path

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
    
    # Clean cache for testing
    cache_path = Path("data/cache/ai_advice_cache.json")
    if cache_path.exists():
        print("Cleaning old cache...")
        os.remove(cache_path)

    # 1. Test First Call (Cache Miss)
    print("\n1. Generating Advice (Expect API Call)...")
    start = time.time()
    advice1 = async_test(service.generate_ai_advice())
    duration1 = time.time() - start
    print(f"   Time taken: {duration1:.2f}s")
    
    if not advice1 or "Not enough data" in advice1:
        print("⚠️ No stats/data found. Please run verify_phase_08 to generate data first.")
        # Create dummy data if needed, but assuming phase 08 data exists
    
    if cache_path.exists():
        print("✅ Cache file created.")
    else:
        print("❌ Cache file NOT created.")

    # 2. Test Second Call (Cache Hit)
    print("\n2. Fetching Advice Again (Expect Cache Hit)...")
    start = time.time()
    advice2 = async_test(service.generate_ai_advice())
    duration2 = time.time() - start
    print(f"   Time taken: {duration2:.4f}s")
    
    if duration2 < 1.0: # Should be instant
        print("✅ Speed test passed (Instant response).")
    else:
        print("⚠️ Speed test warning (Too slow for cache?).")

    if advice1 == advice2:
        print("✅ Content consistency passed.")
    else:
        print("❌ Content mismatch.")

    print("\n✅ Phase 10 Logic Verification Complete!")

if __name__ == "__main__":
    verify()
