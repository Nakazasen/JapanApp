import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.services.content_generator_service import get_content_service
from frontend.core.database import init_db

async def main():
    print("🚀 Starting Content Generation Verification...")
    
    # Ensure DB tables exist
    init_db()
    
    service = get_content_service()
    
    # 1. Test Reading Part 5
    print("\n--- Testing Reading Part 5 Generation ---")
    reading_data = await service.generate_reading_part5("Business")
    if reading_data:
        print("✅ Generated Reading Data:")
        print(f"Question: {reading_data.get('question_text')}")
        print(f"Options: {reading_data.get('options')}")
        
        # Test Saving
        print("Saving to DB...")
        if await service.save_question_to_db(reading_data):
            print("✅ Reading Question Saved!")
        else:
            print("❌ Failed to save Reading Question")
    else:
        print("❌ Failed to generate Reading Part 5")

    # 2. Test Listening Part 2
    print("\n--- Testing Listening Part 2 Generation ---")
    listening_data = await service.generate_listening_part2("Office")
    if listening_data:
        print("✅ Generated Listening Data:")
        print(f"Script: {listening_data.get('script')}")
        
        # TTS would be called by UI, but let's check if we can simulate the full flow including TTS if needed.
        # The service generate_listening_part2 DOES NOT call TTS itself (as per my implementation).
        # The UI calls TTS.
        # Let's verify TTS manually here to be sure.
        
        from frontend.services.tts_service import get_tts_service
        tts = get_tts_service()
        print("Generating Audio...")
        try:
            audio_path = await tts.generate_audio(listening_data['script'], "test_part2.mp3")
            print(f"✅ Audio generated at: {audio_path}")
            
            # Add audio path to data for saving
            listening_data["audio_path"] = audio_path
            
            # Test Saving
            print("Saving to DB...")
            if await service.save_question_to_db(listening_data):
                print("✅ Listening Question Saved!")
            else:
                print("❌ Failed to save Listening Question")
                
        except Exception as e:
            print(f"❌ TTS Failed: {e}")

    else:
        print("❌ Failed to generate Listening Part 2")

if __name__ == "__main__":
    asyncio.run(main())
