"""Test script for AI connection after config fix."""
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent))

from frontend.services.ai_service import get_ai_service

def test_connection():
    print("--- Testing AI Connection ---")
    ai_service = get_ai_service()
    
    # Reload config just in case
    ai_service.reload_config()
    
    print(f"Active models: {ai_service.models_priority}")
    print(f"API Key: {ai_service.api_key[:8]}...")
    
    prompt = "Xin chào, hãy phản hồi ngắn gọn 'OK' nếu bạn hoạt động."
    print(f"Sending prompt: {prompt}")
    
    result = ai_service.generate_response(prompt)
    
    print("\n--- Result ---")
    print(f"Status: {result.get('status')}")
    print(f"Model used: {result.get('model_used')}")
    print(f"Text: {result.get('text')}")

if __name__ == "__main__":
    test_connection()
