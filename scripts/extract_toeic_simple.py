import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Extract TOEIC vocab with resume capability - Simple but effective."""
import re
import os
import sys
import json
import fitz
from pathlib import Path
from typing import List, Dict, Set

sys.path.insert(0, r"C:\ProgramData\Sandbox\Projects\EnglishApp")

import pytesseract
from PIL import Image
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PDF_PATH = r"C:\Users\Admin\Downloads\HACKERS TOEIC.pdf"
CACHE_FILE = "toeic_progress.json"

def load_progress():
    """Load progress from cache."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'completed_pages': [], 'vocab': []}

def save_progress(data):
    """Save progress to cache."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def parse_vocab_line(line: str) -> Dict:
    """Parse a vocabulary entry from a line."""
    line = line.strip()
    if not line or len(line) < 5:
        return None
    
    # Skip headers and non-vocab lines
    skip_patterns = [
        r'^\d+$', r'^DAY\s*\d+', r'^LESSON', r'^UNIT',
        r'^HACKERS', r'^TOEIC', r'^www\.', r'^http'
    ]
    for pattern in skip_patterns:
        if re.match(pattern, line, re.I):
            return None
    
    # Pattern 1: WORD (IPA) POS meaning
    match = re.match(
        r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\s*\(\s*/?([^/)]+)/?\s*\)\s*(n\.|v\.|adj\.|adv\.|prep\.)\s*(.+)$',
        line
    )
    if match:
        word = match.group(1).strip()
        ipa = match.group(2).strip()
        pos = match.group(3).strip().rstrip('.')
        meaning = match.group(4).strip()
        
        if 2 <= len(word) <= 35 and not any(c.isdigit() for c in word):
            return {'word': word, 'ipa': f'/{ipa}/', 'pos': pos, 'meaning_vi': meaning}
    
    # Pattern 2: WORD /IPA/ POS meaning
    match = re.match(
        r'^([A-Z][a-zA-Z]+)\s+/([^/]+)/\s*(n\.|v\.|adj\.|adv\.)\s*(.+)$',
        line
    )
    if match:
        word = match.group(1).strip()
        ipa = match.group(2).strip()
        pos = match.group(3).strip().rstrip('.')
        meaning = match.group(4).strip()
        
        if 2 <= len(word) <= 35:
            return {'word': word, 'ipa': f'/{ipa}/', 'pos': pos, 'meaning_vi': meaning}
    
    return None

def extract_page(doc, page_num: int) -> List[Dict]:
    """Extract vocabulary from a single page."""
    vocab_list = []
    
    try:
        page = doc[page_num]
        
        # Render at 150 DPI (balance quality/speed)
        mat = fitz.Matrix(150/72, 150/72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # OCR
        text = pytesseract.image_to_string(img, lang='eng')
        
        # Parse lines
        for line in text.split('\n'):
            vocab = parse_vocab_line(line)
            if vocab:
                vocab_list.append(vocab)
    except Exception as e:
        print(f"  Error on page {page_num+1}: {e}")
    
    return vocab_list

def extract_all():
    """Main extraction loop with resume capability."""
    print("=" * 60)
    print("HACKERS TOEIC Vocabulary Extractor")
    print("=" * 60)
    print(f"PDF: {PDF_PATH}")
    print("Press Ctrl+C to pause and resume later\n")
    
    # Load progress
    progress = load_progress()
    completed_pages = set(progress['completed_pages'])
    all_vocab = progress['vocab']
    existing_words = {v['word'].lower() for v in all_vocab}
    
    # Open PDF
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    
    print(f"Total pages: {total_pages}")
    print(f"Already processed: {len(completed_pages)} pages")
    print(f"Vocabulary found so far: {len(all_vocab)}\n")
    
    try:
        for page_num in range(total_pages):
            if page_num in completed_pages:
                continue
            
            print(f"Processing page {page_num + 1}/{total_pages}...", end="\r")
            
            # Extract from page
            page_vocab = extract_page(doc, page_num)
            
            # Add unique words only
            new_words = 0
            for vocab in page_vocab:
                word_key = vocab['word'].lower()
                if word_key not in existing_words:
                    existing_words.add(word_key)
                    all_vocab.append(vocab)
                    new_words += 1
            
            # Mark as completed
            completed_pages.add(page_num)
            
            # Save progress every 10 pages
            if len(completed_pages) % 10 == 0:
                progress['completed_pages'] = list(completed_pages)
                progress['vocab'] = all_vocab
                save_progress(progress)
                print(f"Progress saved: {len(completed_pages)}/{total_pages} pages, {len(all_vocab)} words")
        
        doc.close()
        
        print(f"\n\nExtraction completed!")
        print(f"Total unique words: {len(all_vocab)}")
        
        return all_vocab
        
    except KeyboardInterrupt:
        doc.close()
        progress['completed_pages'] = list(completed_pages)
        progress['vocab'] = all_vocab
        save_progress(progress)
        print(f"\n\nPaused! Progress saved.")
        print(f"Processed: {len(completed_pages)}/{total_pages} pages")
        print(f"Vocabulary: {len(all_vocab)} words")
        print(f"\nRun this script again to continue.")
        sys.exit(0)

def import_to_db(vocab_list: List[Dict]):
    """Import vocabulary to database."""
    print("\nImporting to database...")
    
    with Session(engine) as session:
        # Get or create topic
        topic = session.exec(
            select(VocabTopic).where(VocabTopic.name == "HACKERS TOEIC", VocabTopic.lang == "en")
        ).first()
        
        if not topic:
            topic = VocabTopic(
                user_id=1,
                name="HACKERS TOEIC",
                lang="en",
                description="Vocabulary from HACKERS TOEIC",
                color="#FF6B6B",
                icon=""
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
            print(f"Created topic: HACKERS TOEIC")
        
        imported = 0
        skipped = 0
        
        for vocab in vocab_list:
            # Check if exists
            existing = session.exec(
                select(EnVocabItem).where(
                    EnVocabItem.word == vocab['word'],
                    EnVocabItem.user_id == 1
                )
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Create new item
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
                print(f"  Imported {imported} words...", end="\r")
        
        session.commit()
        
        print(f"\nImport completed!")
        print(f"  New words imported: {imported}")
        print(f"  Skipped (duplicates): {skipped}")

def main():
    # Extract vocabulary
    vocab_list = extract_all()
    
    if not vocab_list:
        print("No vocabulary found!")
        return
    
    # Show sample
    print("\nSample entries:")
    for vocab in vocab_list[:10]:
        print(f"  {vocab['word']:<20} {vocab.get('ipa', ''):<20} [{vocab.get('pos', ''):<5}] {vocab.get('meaning_vi', '')[:50]}")
    
    # Import to database
    import_to_db(vocab_list)
    
    # Clean up cache
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print("\nProgress cache cleaned up.")
    
    print("\n" + "=" * 60)
    print("Done! Check the Vocabulary tab in the application.")
    print("=" * 60)

if __name__ == "__main__":
    main()

