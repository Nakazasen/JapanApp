"""Verification script for Phase 11 (Content Generation)."""
import sys
import os
import asyncio
import time
from pathlib import Path

sys.path.append(os.getcwd())

from frontend.services.content_generator_service import get_content_service
from frontend.services.tts_service import get_tts_service

# Helper to run async in main
def async_test(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

def verify():
    print("Initializing Services...")
    content_service = get_content_service()
    tts_service = get_tts_service()
    
    # 1. Test Reading Generator (Part 5)
    print("\n1. Generating Reading Part 5 Question...")
    start = time.time()
    q_data = async_test(content_service.generate_reading_part5("Office Management"))
    duration = time.time() - start
    print(f"   Time: {duration:.2f}s")
    
    if q_data and "question_text" in q_data:
        print("✅ Part 5 Generation Success:")
        print(f"   Question: {q_data['question_text']}")
        print(f"   Options: {q_data['options']}")
        print(f"   Correct: {q_data['correct_answer']}")
    else:
        print("❌ Part 5 Generation Failed.")

    # 2. Test Listening Generator (Part 1 Script + TTS)
    print("\n2. Generating Listening Part 1 Script...")
    start = time.time()
    l_data = async_test(content_service.generate_listening_part1_script("Coffee Shop"))
    duration = time.time() - start
    print(f"   Script Gen Time: {duration:.2f}s")
    
    if l_data and "script" in l_data:
        print("✅ Part 1 Script Success.")
        print(f"   Script Preview: {l_data['script'][:50]}...")
        
        # 3. Test TTS Generation
        print("\n3. Converting Script to Audio...")
        script_text = l_data["script"]
        filename = f"test_part1_{int(time.time())}.mp3"
        
        start = time.time()
        audio_path = async_test(tts_service.generate_audio(script_text, filename))
        duration = time.time() - start
        print(f"   TTS Time: {duration:.2f}s")
        
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            print(f"✅ Audio File Created: {audio_path} ({os.path.getsize(audio_path)} bytes)")
        else:
            print("❌ Audio File Creation Failed.")
            
    else:
        print("❌ Part 1 Script Generation Failed.")

    print("\n✅ Phase 11 Logic Verification Complete!")

if __name__ == "__main__":
    verify()
