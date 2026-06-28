import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""List available Gemini models."""
import google.generativeai as genai
import os

api_key = "AIzaSyB5C8dZxVmDrDdhLRXTTThNJKjWIc00MPg"
genai.configure(api_key=api_key)

print("--- Available Models ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}, Display: {m.display_name}")
except Exception as e:
    print(f"Error: {e}")

