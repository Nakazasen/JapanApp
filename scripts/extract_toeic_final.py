import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Extract TOEIC vocab with corrected patterns for HACKERS TOEIC format."""
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
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'completed_pages': [], 'vocab': []}

def save_progress(data):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def clean_word(word: str) -> str:
    """Clean extracted word."""
    # Remove ** markers
    word = re.sub(r'\*+', '', word)
    # Remove numbers at start
    word = re.sub(r'^\d+\s*', '', word)
    # Clean up
    word = word.strip()
    return word

def parse_vocab_line(line: str) -> Dict:
    """Parse a vocabulary entry from OCR text."""
    line = line.strip()
    if not line or len(line) < 5:
        return None
    
    # Skip headers
    skip_patterns = [
        r'^\d+$', r'^DAY\s*\d+', r'^LESSON', r'^UNIT',
        r'^HACKERS', r'^TOEIC', r'^www\.', r'^http',
        r'^(der|syn|ant|e)', r'^\[', r'^\(', r'^phr',
        r'xuat hien', r'tu vung', r'Part \d'
    ]
    for pattern in skip_patterns:
        if re.match(pattern, line, re.I):
            return None
    
    # Pattern 1: number word @ pos meaning (most common in HACKERS)
    # Example: "33 obligation** @ = nghia vu, trach nhiem"
    match = re.match(
        r'^(?:\d+\s+)?([A-Za-z\-]+(?:\s+[A-Za-z\-]+){0,2}\*?)\s*[@=]\s*(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|det\.)?\s*(.+)',
        line
    )
    if match:
        word = clean_word(match.group(1))
        pos = match.group(2).strip().rstrip('.') if match.group(2) else ""
        meaning = match.group(3).strip()
        
        if 2 <= len(word) <= 35 and not any(c.isdigit() for c in word):
            # Skip if meaning looks like example sentence
            if len(meaning) > 100 and '.' in meaning[:50]:
                return None
            return {'word': word, 'ipa': '', 'pos': pos, 'meaning_vi': meaning}
    
    # Pattern 2: word (pos) meaning
    match = re.match(
        r'^([A-Z][a-zA-Z]+)\s*\(([^)]+)\)\s*(.+)',
        line
    )
    if match:
        word = clean_word(match.group(1))
        pos_or_ipa = match.group(2).strip()
        meaning = match.group(3).strip()
        
        if 2 <= len(word) <= 35:
            pos = ''
            if pos_or_ipa in ['n', 'v', 'adj', 'adv', 'prep']:
                pos = pos_or_ipa
            return {'word': word, 'ipa': '', 'pos': pos, 'meaning_vi': meaning}
    
    # Pattern 3: Simple word followed by meaning with Vietnamese
    # Look for Vietnamese characters in meaning
    vn_chars = 'ﾃﾃ｡蘯｡蘯｣ﾃ｣ﾃ｢蘯ｧ蘯･蘯ｭ蘯ｩ蘯ｫﾄ・ｺｱ蘯ｯ蘯ｷ蘯ｩ蘯ｵﾃｨﾃｩ蘯ｹ蘯ｻ蘯ｽﾃｪ盻≪ｺｿ盻・ｻ・ｻ・ｬﾃｭ盻吟ｻ夏ｩﾃｲﾃｳ盻冴ｻ湘ｵﾃｴ盻乍ｻ黛ｻ吼ｻ甫ｻ糧｡盻昵ｻ帋ｻ｣盻溂ｻ｡ﾃｹﾃｺ盻･盻ｧﾅｩﾆｰ盻ｫ盻ｩ盻ｱ盻ｭ盻ｯ盻ｳﾃｽ盻ｵ盻ｷ盻ｹﾄ・
    
    match = re.match(
        r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s+([^.]{5,100})$',
        line
    )
    if match:
        word = clean_word(match.group(1))
        meaning = match.group(2).strip()
        
        # Only if meaning contains Vietnamese
        if any(c in meaning.lower() for c in vn_chars):
            if 2 <= len(word) <= 35 and not any(c.isdigit() for c in word):
                return {'word': word, 'ipa': '', 'pos': '', 'meaning_vi': meaning}
    
    return None

def extract_page(doc, page_num: int) -> List[Dict]:
    """Extract vocabulary from a single page."""
    vocab_list = []
    
    try:
        page = doc[page_num]
        mat = fitz.Matrix(150/72, 150/72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img, lang='eng')
        
        for line in text.split('\n'):
            vocab = parse_vocab_line(line)
            if vocab:
                vocab_list.append(vocab)
    except Exception as e:
        pass
    
    return vocab_list

def extract_all():
    """Main extraction loop."""
    print("=" * 60)
    print("HACKERS TOEIC Vocabulary Extractor")
    print("=" * 60)
    
    progress = load_progress()
    completed_pages = set(progress['completed_pages'])
    all_vocab = progress['vocab']
    existing_words = {v['word'].lower() for v in all_vocab}
    
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    
    print(f"Total pages: {total_pages}")
    print(f"Already processed: {len(completed_pages)} pages")
    print(f"Vocabulary found so far: {len(all_vocab)}")
    print("Press Ctrl+C to pause and resume later\n")
    
    try:
        for page_num in range(total_pages):
            if page_num in completed_pages:
                continue
            
            if page_num % 10 == 0:
                print(f"Processing page {page_num + 1}/{total_pages}... (found {len(all_vocab)} words)")
            
            page_vocab = extract_page(doc, page_num)
            
            new_words = 0
            for vocab in page_vocab:
                word_key = vocab['word'].lower()
                if word_key not in existing_words:
                    existing_words.add(word_key)
                    all_vocab.append(vocab)
                    new_words += 1
            
            completed_pages.add(page_num)
            
            # Save every 20 pages
            if len(completed_pages) % 20 == 0:
                progress['completed_pages'] = list(completed_pages)
                progress['vocab'] = all_vocab
                save_progress(progress)
        
        doc.close()
        
        print(f"\nExtraction completed!")
        print(f"Total unique words: {len(all_vocab)}")
        return all_vocab
        
    except KeyboardInterrupt:
        doc.close()
        progress['completed_pages'] = list(completed_pages)
        progress['vocab'] = all_vocab
        save_progress(progress)
        print(f"\nPaused! Processed: {len(completed_pages)}/{total_pages} pages, {len(all_vocab)} words")
        print("Run again to continue.")
        sys.exit(0)

def import_to_db(vocab_list: List[Dict]):
    """Import vocabulary to database."""
    print("\nImporting to database...")
    
    with Session(engine) as session:
        topic = session.exec(
            select(VocabTopic).where(VocabTopic.name == "HACKERS TOEIC", VocabTopic.lang == "en")
        ).first()
        
        if not topic:
            topic = VocabTopic(
                user_id=1, name="HACKERS TOEIC", lang="en",
                description="Vocabulary from HACKERS TOEIC",
                color="#FF6B6B", icon=""
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
            print("Created topic: HACKERS TOEIC")
        
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
        print(f"\nDone! Imported: {imported}, Skipped: {skipped}")

def main():
    vocab_list = extract_all()
    
    if not vocab_list:
        print("No vocabulary found!")
        return
    
    print("\nSample entries:")
    for vocab in vocab_list[:15]:
        print(f"  {vocab['word']:<20} [{vocab.get('pos', ''):<5}] {vocab.get('meaning_vi', '')[:60]}")
    
    import_to_db(vocab_list)
    
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    
    print("\n" + "=" * 60)
    print("Done! Check the Vocabulary tab.")
    print("=" * 60)

if __name__ == "__main__":
    main()

