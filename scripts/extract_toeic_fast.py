import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Fast TOEIC vocab extractor - Optimized for speed with parallel processing."""
import re
import os
import sys
import json
import fitz
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Set, Tuple
from datetime import datetime

sys.path.insert(0, r"C:\ProgramData\Sandbox\Projects\EnglishApp")

import pytesseract
from PIL import Image
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Cache file to resume
CACHE_FILE = "toeic_extraction_cache.json"

def ocr_single_page(args: Tuple[int, bytes]) -> Tuple[int, str]:
    """OCR a single page - runs in separate process."""
    page_num, pdf_bytes = args
    
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[page_num]
        
        # Render at 150 DPI (faster than 200)
        mat = fitz.Matrix(150/72, 150/72)
        pix = page.get_pixmap(matrix=mat)
        
        # Create image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # OCR
        text = pytesseract.image_to_string(img, lang='eng')
        doc.close()
        
        return page_num, text
    except Exception as e:
        return page_num, ""

def parse_vocab_from_text(text: str, existing_words: Set[str]) -> List[Dict]:
    """Parse vocabulary entries from OCR text."""
    vocab_list = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        # Skip headers
        if re.match(r'^(DAY|LESSON|UNIT|\d+|HACKERS|TOEIC|www|http)', line, re.I):
            continue
        
        # Pattern: WORD (IPA) POS meaning
        match = re.match(
            r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*\(\s*/?([^/)]+)/?\s*\)\s*(n\.|v\.|adj\.|adv\.)\s*(.+)$',
            line
        )
        
        if match:
            word = match.group(1).strip()
            ipa = match.group(2).strip()
            pos = match.group(3).strip().rstrip('.')
            meaning = match.group(4).strip()
            
            # Validate
            if len(word) < 2 or len(word) > 35:
                continue
            if any(c in word for c in '0123456789'):
                continue
            if word.lower() in existing_words:
                continue
            
            existing_words.add(word.lower())
            vocab_list.append({
                'word': word,
                'ipa': f"/{ipa}/",
                'pos': pos,
                'meaning_vi': meaning
            })
    
    return vocab_list

def load_cache() -> Dict:
    """Load extraction cache."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'processed_pages': [], 'vocab': []}

def save_cache(cache: Dict):
    """Save extraction cache."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def extract_vocab_parallel(pdf_path: str, max_workers: int = 4) -> List[Dict]:
    """Extract vocabulary using parallel processing."""
    cache = load_cache()
    processed_pages = set(cache['processed_pages'])
    all_vocab = cache['vocab']
    existing_words = {v['word'].lower() for v in all_vocab}
    
    # Open PDF
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    # Get PDF bytes for multiprocessing
    pdf_bytes = doc.tobytes()
    doc.close()
    
    # Find pages to process
    pages_to_process = [p for p in range(total_pages) if p not in processed_pages]
    
    if not pages_to_process:
        print("All pages already processed!")
        return all_vocab
    
    print(f"Processing {len(pages_to_process)} pages using {max_workers} workers...")
    print(f"Already processed: {len(processed_pages)} pages")
    print(f"Total vocabulary so far: {len(all_vocab)}\n")
    
    # Process in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        args = [(p, pdf_bytes) for p in pages_to_process]
        futures = {executor.submit(ocr_single_page, arg): arg[0] for arg in args}
        
        completed = 0
        for future in as_completed(futures):
            page_num = futures[future]
            try:
                _, text = future.result(timeout=60)
                vocab = parse_vocab_from_text(text, existing_words)
                
                all_vocab.extend(vocab)
                processed_pages.add(page_num)
                
                completed += 1
                if completed % 10 == 0:
                    print(f"Progress: {completed}/{len(pages_to_process)} pages, {len(all_vocab)} words", end="\r")
                    
                    # Save cache periodically
                    cache['processed_pages'] = list(processed_pages)
                    cache['vocab'] = all_vocab
                    save_cache(cache)
                    
            except Exception as e:
                print(f"\nError on page {page_num}: {e}")
    
    # Final save
    cache['processed_pages'] = list(processed_pages)
    cache['vocab'] = all_vocab
    save_cache(cache)
    
    print(f"\n\nCompleted! Total unique words: {len(all_vocab)}")
    return all_vocab

def import_to_db(vocab_list: List[Dict]):
    """Import to database."""
    with Session(engine) as session:
        # Get or create topic
        topic = session.exec(
            select(VocabTopic).where(VocabTopic.name == "HACKERS TOEIC", VocabTopic.lang == "en")
        ).first()
        
        if not topic:
            topic = VocabTopic(
                user_id=1, name="HACKERS TOEIC", lang="en",
                description="Vocabulary from HACKERS TOEIC (OCR)",
                color="#FF6B6B", icon=""
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
        
        imported = 0
        skipped = 0
        
        for vocab in vocab_list:
            existing = session.exec(
                select(EnVocabItem).where(EnVocabItem.word == vocab['word'], EnVocabItem.user_id == 1)
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            item = EnVocabItem(
                user_id=1,
                word=vocab['word'],
                ipa=vocab.get('ipa', '')[:100],
                pos=vocab.get('pos', '')[:50],
                meaning_vi=vocab.get('meaning_vi', '')[:500],
                topic_id=topic.id,
                source_material="HACKERS TOEIC",
                level="TOEIC 800",
                mastery_status="new"
            )
            session.add(item)
            imported += 1
            
            if imported % 100 == 0:
                print(f"  Imported {imported}...", end="\r")
        
        session.commit()
        print(f"\nImported: {imported}, Skipped: {skipped}")

def main():
    pdf_path = r"C:\Users\Admin\Downloads\HACKERS TOEIC.pdf"
    
    print("=" * 60)
    print("HACKERS TOEIC Vocabulary Extractor (Fast)")
    print("=" * 60)
    print(f"PDF: {pdf_path}")
    print("Using parallel processing for speed\n")
    
    # Extract
    vocab_list = extract_vocab_parallel(pdf_path, max_workers=4)
    
    if not vocab_list:
        print("No vocabulary found!")
        return
    
    # Show sample
    print("\nSample entries:")
    for v in vocab_list[:10]:
        print(f"  {v['word']:<20} {v.get('ipa', ''):<20} {v.get('pos', ''):<5} {v.get('meaning_vi', '')[:40]}")
    
    # Import
    print("\nImporting to database...")
    import_to_db(vocab_list)
    
    print("\nDone! Check the Vocabulary tab.")
    
    # Clean cache
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print("Cache cleaned up.")

if __name__ == "__main__":
    main()

