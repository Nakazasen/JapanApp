
import os
import sys
import time
import json
import re
import io
from typing import Optional, List, Dict, Any, Type
from sqlmodel import Session, create_engine, select, SQLModel
import google.generativeai as genai

# Setup UTF-8 for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.core.config import settings
from frontend.models.practice import PracticeItem, PracticeCategory
from frontend.models.listening_practice import ListeningItem, ListeningCategory
from frontend.services.ai_service import get_ai_service

DB_PATH = settings.db_path
PROJECT_ROOT = settings.project_root
AI_SETTINGS_PATH = os.path.join(PROJECT_ROOT, "data", "config", "ai_settings.json")

def is_junk(content: Optional[str]) -> bool:
    if not content: return True
    content_str = str(content).strip()
    if len(content_str) < 150: return True
    
    # Strong garbage markers
    junk_markers = [
        "Home", "Ebooks", "Flashcards", "F.A.Q", "Donate", "Copyright",
        "Answer Key", "Question 1", "Question 2", "Download", 
        "New words", "View transcript", "Japanesetest4you"
    ]
    # Check if content is just a list of 'Question X'
    if re.search(r'^\d+\.\s+Question\s+\d+$', content_str, re.MULTILINE):
        return True
        
    found_markers = [m for m in junk_markers if m.lower() in content_str.lower()]
    return len(found_markers) > 0

def get_models_from_config() -> List[str]:
    try:
        if not os.path.exists(AI_SETTINGS_PATH): return ["models/gemini-2.0-flash"]
        with open(AI_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        models = [m["model_id"] for m in config.get("waterfall_strategy", []) if m.get("is_active", True)]
        return [m if m.startswith("models/") else f"models/{m}" for m in models] or ["models/gemini-2.0-flash"]
    except: return ["models/gemini-2.0-flash"]

# Global state for rate-limited models to avoid repeated waits in the same session
RATE_LIMITED_MODELS = set()

def transcribe_chunk(items: List[Any], models_to_try: List[str]) -> Dict[int, str]:
    """Transcribe a list of items using provided models with smart model skipping."""
    import concurrent.futures
    results = {}
    uploads = []
    
    # Filter out models that are known to be rate-limited in this session
    active_models = [m for m in models_to_try if m not in RATE_LIMITED_MODELS]
    
    if not active_models:
        print("  ! WARNING: All configured models are currently marked as rate-limited.", flush=True)
        # Fallback: try them all again if we have no other choice
        active_models = models_to_try

    # 1. Prepare items for upload (same as before)
    items_to_upload = []
    for item in items:
        path = getattr(item, 'audio_path', "")
        if not path or path == "per_question": continue
        path = path.lstrip('/')
        abs_path = os.path.join(PROJECT_ROOT, path)
        if os.path.exists(abs_path): items_to_upload.append((item, abs_path))
        else: print(f"File not found: {abs_path}", flush=True)

    # 2. Parallel Uploads (Speed up!)
    if items_to_upload:
        print(f"  > Uploading {len(items_to_upload)} files in parallel...", flush=True)
        def upload_single_item(data):
            it, ap = data
            try:
                # print(f"    - Uploading: {getattr(it, 'title', 'Item '+str(it.id))}", flush=True)
                f = genai.upload_file(path=ap, mime_type="audio/mpeg")
                return (it.id, f)
            except Exception as e:
                print(f"    ! Upload error for {it.id}: {e}", flush=True)
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {executor.submit(upload_single_item, i): i for i in items_to_upload}
            for future in concurrent.futures.as_completed(future_to_item):
                res = future.result()
                if res: uploads.append(res)
        
        if not uploads: 
            print("  ! No files were successfully uploaded.", flush=True)
            break

        # Wait for processing
        msg_printed = False
        for _, f in uploads:
            while genai.get_file(f.name).state.name == "PROCESSING":
                if not msg_printed:
                    print("  > Waiting for Google to process audio files...", flush=True)
                    msg_printed = True
                time.sleep(1)
        
        # 3. Batch Transcription
        print(f"  > Requesting transcription from Gemini...", flush=True)
        prompt = "Transcribe Japanese audio exactly. Speaker labels: '女：', '男：'. Output ONLY JSON: {'ID': 'text'}"
        content = [prompt]
        for iid, f in uploads:
            content.extend([f"ID {iid}:", f])
        
        success_this_chunk = False
        for mname in active_models:
            try:
                print(f"  > Trying model: {mname}", flush=True)
                model = genai.GenerativeModel(mname)
                resp = model.generate_content(content)
                
                # Safe text retrieval
                resp_text = ""
                try:
                    resp_text = resp.text
                except:
                    if hasattr(resp, 'candidates') and resp.candidates:
                        parts = resp.candidates[0].content.parts
                        resp_text = "".join([p.text for p in parts if hasattr(p, 'text')])
                
                # JSON extraction logic
                data = {}
                json_matches = re.finditer(r'(\{.*?\})', resp_text, re.DOTALL)
                parsed_successfully = False
                for match in json_matches:
                    try:
                        candidate = match.group(1)
                        if '"ID' in candidate or "'ID" in candidate:
                            data = json.loads(candidate.replace("'", '"'))
                            parsed_successfully = True
                            break
                    except: continue
                
                if not parsed_successfully:
                    json_text_match = re.search(r'\{.*\}', resp_text, re.DOTALL)
                    if json_text_match:
                        try:
                            data = json.loads(json_text_match.group(0))
                            parsed_successfully = True
                        except: pass

                if parsed_successfully:
                    for k, v in data.items():
                        match = re.search(r'(\d+)', str(k))
                        if match:
                            if isinstance(v, list):
                                text_lines = []
                                for segment in v:
                                    if isinstance(segment, dict):
                                        line = f"{segment.get('start', '')} {segment.get('label', '')} {segment.get('text', '')}".strip()
                                        text_lines.append(line)
                                    else: text_lines.append(str(segment))
                                v = "\n".join(text_lines)
                            results[int(match.group(1))] = str(v)
                    
                    print(f"  > ✅ Successfully transcribed {len(results)} items.", flush=True)
                    success_this_chunk = True
                    break # Success! Break model loop
            except Exception as e:
                err_msg = str(e)
                print(f"  ! Model {mname} failed: {err_msg}", flush=True)
                if "429" in err_msg or "quota" in err_msg.lower():
                    from frontend.services.ai_service import get_config_manager
                    config_mgr = get_config_manager()
                    if config_mgr.rotate_api_key():
                        print(f"  ! Quota exceeded for {mname}. Rotating API Key and MUST re-upload files...", flush=True)
                        genai.configure(api_key=config_mgr.api_key)
                        rotated = True
                        break # Break model loop to trigger re-upload
                    else:
                        print(f"  ! Quota exceeded for {mname}. No more keys to rotate.", flush=True)
                        RATE_LIMITED_MODELS.add(mname)
                        continue

        # Cleanup files for THIS key
        # print("  > Cleaning up remote files for current key...", flush=True)
        for _, f in uploads:
            try: genai.delete_file(f.name)
            except: pass
            
        if success_this_chunk: return results
        if not rotated: break # No more models or rotation didn't happen, give up on chunk
        
    return results

def process_questions(session: Session, models: List[str]):
    """Transcribe audio for individual questions."""
    from frontend.models.listening_practice import ListeningQuestion
    
    # Only questions with audio and no transcript
    to_proc = session.exec(select(ListeningQuestion).where(
        ListeningQuestion.audio_path != None,
        (ListeningQuestion.transcript == None) | (ListeningQuestion.transcript == "")
    )).all()
    
    if not to_proc:
        print("No questions to transcribe.")
        return

    print(f"Transcribing {len(to_proc)} questions...")
    for i in range(0, len(to_proc), 5):
        chunk = to_proc[i:i+5]
        trans_results = transcribe_chunk(chunk, models)
        for q in chunk:
            if q.id in trans_results:
                q.transcript = trans_results[q.id]
                session.add(q)
        session.commit()
        print(f"  Question batch {i//5 + 1} saved.")

def process_table(session: Session, cat_model: Type[Any], item_model: Type[Any], field: str, models: List[str]):
    print(f"--- Table: {item_model.__tablename__} ---")
    # Identify categories
    cats = session.exec(select(cat_model).where(cat_model.name.like("%Listening%"))).all()
    
    for cat in cats:
        print(f"Checking category: {cat.name}")
        items = session.exec(select(item_model).where(item_model.category_id == cat.id)).all()
        
        # 1. First, handle per-question transcript if applicable
        if item_model.__name__ == "ListeningItem":
             from frontend.models.listening_practice import ListeningQuestion
             for item in items:
                 if item.audio_path == "per_question":
                     # Check if we can build a combined transcript from questions
                     questions = session.exec(select(ListeningQuestion).where(ListeningQuestion.item_id == item.id)).all()
                     q_transcripts = [q.transcript for q in questions if q.transcript]
                     
                     if len(q_transcripts) > 0 and is_junk(item.transcript):
                        print(f"  Generating combined transcript for: {item.title}")
                        combined = "\n\n".join([f"--- Câu {idx+1} ---\n{t}" for idx, t in enumerate(q_transcripts)])
                        item.transcript = combined
                        session.add(item)
             session.commit()

        # 2. Then proceed with normal file-based transcription for direct items
        to_proc = [i for i in items if is_junk(getattr(i, field)) and i.audio_path and i.audio_path != "per_question"]
        
        if to_proc:
            print(f"  Transcribing {len(to_proc)} direct audio items...")
            for i in range(0, len(to_proc), 5):
                chunk = to_proc[i:i+5]
                trans = transcribe_chunk(chunk, models)
                for item in chunk:
                    if item.id in trans:
                        setattr(item, field, trans[item.id])
                        session.add(item)
                session.commit()
                print(f"  Batch {i//5 + 1} saved.")
                time.sleep(1)

def run():
    """Main execution of the transcription script."""
    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        
        # Use config as the absolute source of truth
        if not os.path.exists(AI_SETTINGS_PATH):
            print(f"CRITICAL ERROR: AI Settings file not found at {AI_SETTINGS_PATH}", flush=True)
            sys.exit(1)
            
        with open(AI_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Use the rotating Config Manager from the AI service
        from frontend.services.ai_service import get_config_manager
        config_mgr = get_config_manager()
        api_key = config_mgr.api_key
        
        if not api_key:
            print("ERROR: No api_key or api_keys found in ai_settings.json", flush=True)
            sys.exit(1)
            
        # Configure the AI library globally with the initial key
        genai.configure(api_key=api_key)
        
        # Get active models strictly from config
        models = [m["model_id"] for m in config.get("waterfall_strategy", []) if m.get("is_active", True)]
        models = [m if m.startswith("models/") else f"models/{m}" for m in models]
        
        if not models:
            print("ERROR: No active models found in waterfall_strategy.", flush=True)
            sys.exit(1)
            
        print(f"Verified Config: Using {len(models)} active models from local AI settings.", flush=True)
        
        with Session(engine) as session:
            # Step 0: Initial Merge (Handle items whose questions were already transcribed)
            print("  > Initial step: Merging existing question transcripts into parent items...", flush=True)
            process_table(session, PracticeCategory, PracticeItem, 'content', models)
            process_table(session, ListeningCategory, ListeningItem, 'transcript', models)
            
            # Step 1: Transcribe remaining individual questions
            process_questions(session, models)
            
            # Step 2: Final Merge (Process remaining direct tables and newly transcribed questions)
            print("  > Final step: Updating parent items with newly transcribed content...", flush=True)
            process_table(session, PracticeCategory, PracticeItem, 'content', models)
            process_table(session, ListeningCategory, ListeningItem, 'transcript', models)
            
        print("FINISHED ALL TASKS SUCCESSFULLY", flush=True)
        
    except Exception as e:
        import traceback
        print(f"\nFATAL ERROR DURING EXECUTION: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run()
