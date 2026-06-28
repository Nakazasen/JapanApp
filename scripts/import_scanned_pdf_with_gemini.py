
import sys
import os
import json
import time
import google.generativeai as genai

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.core.gemini_client import get_gemini_client
from frontend.services.vocab_service import get_vocab_service

def setup_gemini():
    """Configure Gemini with API key from the app."""
    client = get_gemini_client()
    client._ensure_configured()
    return client.config_manager.api_key

def get_config_models():
    """Get active models from config."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'config', 'ai_settings.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return [m['model_id'] for m in config.get('waterfall_strategy', []) if m.get('is_active')]
    except Exception as e:
        print(f"⚠️ Could not read config: {e}")
        return []

def get_best_model():
    """Discover available models and select the best one."""
    valid_models = []
    try:
        print("🔎 Discovering available models via API...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                valid_models.append(m.name)
        print(f"📋 Found {len(valid_models)} supported models.")
    except Exception as e:
        print(f"⚠️ Error listing models: {e}")
        # If list fails, we can't do much but guess
        return 'gemini-1.5-flash-latest'

    # valid_models constains full names like 'models/gemini-1.5-flash'
    
    # 1. Try config models if they exist in valid list
    config_models = get_config_models()
    for cm in config_models:
        for vm in valid_models:
            # Match "gemini-1.5-flash" with "models/gemini-1.5-flash"
            if cm == vm or vm.endswith(f"/{cm}"):
                print(f"👉 Selected config model: {vm}")
                return vm

    # 2. Heuristic Preference
    preferences = [
        'gemini-1.5-flash', 
        'gemini-1.5-flash-latest', 
        'gemini-1.5-flash-001',
        'gemini-1.5-pro',
        'gemini-1.5-pro-latest',
        'gemini-pro-vision'
    ]
    
    for pref in preferences:
        for vm in valid_models:
            if vm.endswith(f"/{pref}"):
                print(f"👉 Selected preferred model: {vm}")
                return vm
                
    # 3. Fallback to any VALID model
    if valid_models:
        print(f"👉 Fallback to first available: {valid_models[0]}")
        return valid_models[0]
        
    print("❌ No valid models found.")
    return 'gemini-1.5-flash'

def import_scanned_pdf(file_path, topic_name, prompt_instruction):
    print(f"\n🚀 STARTING AI IMPORT: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    try:
        # 1. Upload File to Gemini
        print("📤 Uploading PDF to Gemini...")
        sample_file = genai.upload_file(path=file_path, display_name=os.path.basename(file_path))
        print(f"✅ Uploaded: {sample_file.display_name} (URI: {sample_file.uri})")
        
        # 2. Extract Data
        print("🧠 Analyzing document (this may take 30-60s)...")
        
        model_name = get_best_model()
        
        model = genai.GenerativeModel(model_name)
        
        full_prompt = f"""
        {prompt_instruction}
        
        Output valid JSON format only. Use this schema:
        [
          {{
            "word": "original text",
            "meaning": "vietnamese meaning",
            "example": "example sentence if any",
            "type": "noun/verb/idiom etc"
          }}
        ]
        """
        
        # Wait a bit for file processing state?
        # Usually instantaneous for small files, but good practice
        
        response = model.generate_content(
            [sample_file, full_prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # 3. Parse JSON
        print("✅ Analysis complete. Parsing data...")
        try:
            items = json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback cleanup
            clean_text = response.text.replace('```json', '').replace('```', '')
            if clean_text.strip().startswith('['):
                 items = json.loads(clean_text)
            else:
                 print("Cannot parse JSON.")
                 print(clean_text[:500])
                 return

        print(f"📊 Found {len(items)} items.")
        
        if not items:
            print("⚠️ No items extraction. Exiting.")
            return

        # 4. Import to DB
        service = get_vocab_service()
        
        # Find/Create Topic
        existing_topics = service.list_topics("en")
        target_topic = next((t for t in existing_topics if t['name'] == topic_name), None)
        
        if not target_topic:
            print(f"Creating topic: {topic_name}")
            res = service.create_topic(topic_name, "en", "Imported via AI Scan")
            topic_id = res["id"]
        else:
            topic_id = target_topic['id']
            print(f"Using topic: {topic_name} (ID: {topic_id})")
            
        # Bulk Import
        print("💾 Saving to database...")
        result = service.bulk_import(
            items=items,
            lang="en",
            default_topic_id=topic_id,
            default_source="AI Scan Import",
            default_level="Unknown"
        )
        
        if result.get("success"):
            print(f"🎉 SUCCESS! Imported: {result['imported']}, Skipped: {result['skipped']}")
        else:
            print(f"❌ Database error: {result.get('error')}")

    except Exception as e:
        import traceback
        print(f"❌ Critical error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    setup_gemini()
    
    # File 1: Danh sách từ
    import_scanned_pdf(
        r"C:\Users\Admin\Downloads\DANH SÁCH TỪ.pdf", 
        "AI Import: Danh Sách Từ",
        "Extract all English vocabulary words from this document. The document contains a list of words with Vietnamese meanings. Extract 'word', 'meaning' (Vietnamese), and 'type' (n, v, adj...) if visible."
    )
    
    # File 2: Thành ngữ
    import_scanned_pdf(
        r"C:\Users\Admin\Downloads\120 THÀNH NGỮ + CỤM TỪ.pdf", 
        "AI Import: 120 Thành Ngữ",
        "Extract all English idioms and phrasal verbs. The document lists idioms with Vietnamese meanings. Extract 'word' (the idiom), 'meaning' (Vietnamese definition), and 'example' if provided."
    )
