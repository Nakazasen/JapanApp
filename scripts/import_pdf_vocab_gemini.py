"""Import Vocabulary/Idioms from PDFs using Gemini Vision.

This script uploads PDFs to Gemini and extracts structured vocabulary data.
"""
import sys
import os
import json
import asyncio
import google.generativeai as genai
from sqlmodel import Session, select

# Add project root to python path
sys.path.append(os.getcwd())

from frontend.core.config import settings
from frontend.core.database import engine
from frontend.models.user import User
from frontend.models.vocab import VocabTopic
from frontend.models.unified_vocab import VocabItem, MasteryStatus
from frontend.services.ai_service import get_config_manager

# --- Configuration ---
ai_config = get_config_manager()
if not ai_config.api_key:
    # Fallback to settings
    if settings.gemini_api_key:
         genai.configure(api_key=settings.gemini_api_key)
    else:
        print("❌ Error: GEMINI_API_KEY not found in AI Settings or Environment.")
        sys.exit(1)
else:
    genai.configure(api_key=ai_config.api_key)

# --- Constants ---
FILES_TO_PROCESS = [
    {
        "path": r"C:\Users\Admin\Downloads\DANH SÁCH TỪ.pdf",
        "type": "vocab",
        "prompt": """
        Extract all English vocabulary words from this document.
        Return a JSON list of objects with the following structure:
        [
            {
                "word": "english word",
                "meaning_vi": "vietnamese meaning",
                "example_en": "example sentence in english",
                "ipa": "ipa pronunciation (optional)"
            }
        ]
        Ignore headers, footers, and page numbers. Return ONLY valid JSON.
        """
    },
    {
        "path": r"C:\Users\Admin\Downloads\120 THÀNH NGỮ + CỤM TỪ.pdf",
        "type": "idiom",
        "prompt": """
        Extract all English idioms and phrasal verbs from this document.
        Return a JSON list of objects with the following structure:
        [
            {
                "word": "idiom/phrase",
                "meaning_vi": "vietnamese meaning",
                "example_en": "example sentence in english",
                "note": "usage note (optional)"
            }
        ]
        Ignore headers, footers, and page numbers. Return ONLY valid JSON.
        """
    }
]

# --- Helpers ---
def get_default_user_id(session):
    user = session.exec(select(User)).first()
    if user:
        return user.id
    print("❌ Error: No users found in database.")
    return None

def save_to_db(items, item_type, source_name):
    print(f"   💾 Saving to database...")
    count = 0
    with Session(engine) as session:
        user_id = get_default_user_id(session)
        if not user_id:
            return

        for item in items:
            word = item.get("word")
            if not word: continue
            
            # Check existing
            existing = session.exec(select(VocabItem).where(VocabItem.term == word, VocabItem.user_id == user_id)).first()
            if existing:
                # print(f"      Skipping existing: {word}")
                continue
            
            # Prepare metadata
            meta_data = {
                "ipa": item_data.get("ipa", ""),
                "pos": item_data.get("pos", ""),
                "meaning_en": item_data.get("meaning_en", ""),
                "note": item_data.get("note", "") # Include note for idioms
            }
            
            # Prepare examples
            examples = []
            if item_data.get("example_en"):
                examples.append({
                    "sentence": item_data["example_en"],
                    "translation": item_data.get("example_vi", "")
                })

            item = VocabItem(
                user_id=user_id,
                term=item_data["word"],
                reading=item_data.get("ipa", ""), # IPA can be used as reading
                meaning=item_data["meaning_vi"],
                lang="en",
                level="Imported",
                source_material=f"Imported from {source_name}",
                meta_data=meta_data,
                examples=examples,
                mastery_status=MasteryStatus.NEW.value
            )
            session.add(item)
            count += 1
        
        try:
            session.commit()
            print(f"   ✅ Successfully saved {count} new items.")
        except Exception as e:
            print(f"   ❌ Database error: {e}")

async def process_file(file_info):
    file_path = file_info["path"]
    if not os.path.exists(file_path):
        print(f"⚠️ File not found: {file_path}")
        return

    print(f"\n📄 Processing: {os.path.basename(file_path)}...")
    
    try:
        # 1. Upload File
        print("   ☁️ Uploading to Gemini...")
        sample_file = genai.upload_file(path=file_path, display_name=os.path.basename(file_path))
        print(f"   ✅ Uploaded: {sample_file.display_name} (URI: {sample_file.uri})")
        
        # 2. Generate Content
        print("   🧠 Analyzing content (this may take a minute)...")
        
        # Use a model known to work
        model_name = "gemini-3-flash-preview" 
        try:
             # Try getting from config if available
             if ai_config.active_models:
                 model_name = ai_config.active_models[0]
        except:
            pass
            
        print(f"      Using model: {model_name}")
        model = genai.GenerativeModel(model_name=model_name)
        
        response = model.generate_content([file_info["prompt"], sample_file])
        
        # 3. Parse Response
        text = response.text
        # Clean markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        data = json.loads(text.strip())
        print(f"   ✅ Extracted {len(data)} items.")
        
        # 4. Save to Database
        save_to_db(data, file_info["type"], os.path.basename(file_path))
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")

async def main():
    print("🚀 Starting PDF Import...")
    for file_info in FILES_TO_PROCESS:
        await process_file(file_info)
    print("\n✨ All imports finished.")

if __name__ == "__main__":
    asyncio.run(main())
