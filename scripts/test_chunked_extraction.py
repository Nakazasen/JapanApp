import google.generativeai as genai
import json
import os
import sys

# Setup Gemini
sys.path.append(os.getcwd())
from frontend.core.config import settings
from frontend.services.ai_service import get_config_manager

ai_config = get_config_manager()
genai.configure(api_key=ai_config.api_key or settings.gemini_api_key)

pdf_path = r"C:\Users\Admin\Downloads\DANH SÁCH TỪ.pdf"
model_name = "gemini-3-flash-preview" # Fast and supports PDF

print(f"Uploading {pdf_path}...")
sample_file = genai.upload_file(path=pdf_path)

model = genai.GenerativeModel(model_name=model_name)

# Test Page 1 and 2
prompt = """
Extract all English vocabulary words from pages 1 and 2 of this document.
Return a JSON list:
[{"word": "...", "meaning_vi": "...", "example_en": "..."}]
Return ONLY valid JSON.
"""

print("Analyzing pages 1-2...")
response = model.generate_content([prompt, sample_file])
print("Response received.")
print(response.text)
