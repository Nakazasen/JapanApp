import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Extract vocabulary from image-based PDF using PyMuPDF + OCR."""
import re
import io
import sys
from pathlib import Path
from typing import List, Dict

# Add project root to path
project_root = Path(r"C:\ProgramData\Sandbox\Projects\EnglishApp")
sys.path.insert(0, str(project_root))

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic


def extract_vocab_with_ocr(pdf_path: str, max_pages: int = None) -> List[Dict]:
    """Extract vocabulary from image-based PDF using OCR."""
    vocab_list = []
    
    print(f"Opening PDF: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    if max_pages:
        total_pages = min(max_pages, total_pages)
    
    print(f"Total pages to process: {total_pages}")
    
    for page_num in range(total_pages):
        print(f"Processing page {page_num + 1}/{total_pages}...", end="\r")
        
        page = doc[page_num]
        
        # Render page to image
        mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Use OCR to extract text
        text = pytesseract.image_to_string(img, lang='eng+vie')
        
        # Parse vocabulary entries
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Skip lines that are clearly not vocabulary
            if line.startswith(('DAY', 'LESSON', 'UNIT', 'Hackers', 'TOEIC', 'www.', 'http')):
                continue
            
            # Try to match vocabulary patterns
            # Pattern 1: WORD (IPA) [POS] meaning - most common in HACKERS
            match = re.match(
                r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*\(/([^/]+)/\)?\s*(\w+\.?)\s*(.+)',
                line
            )
            
            if match:
                word = match.group(1).strip()
                ipa = match.group(2).strip()
                pos = match.group(3).strip().rstrip('.')
                meaning = match.group(4).strip()
                
                # Validate word
                if len(word) < 2 or len(word) > 40:
                    continue
                if any(c in word for c in '0123456789'):
                    continue
                
                # Clean up
                vocab_list.append({
                    'word': word,
                    'ipa': f"/{ipa}/" if ipa else "",
                    'pos': pos,
                    'meaning_vi': meaning,
                    'meaning_en': '',
                    'example_en': '',
                    'example_vi': ''
                })
    
    doc.close()
    
    print(f"\nExtracted {len(vocab_list)} vocabulary entries")
    return vocab_list


def import_vocab_to_db(vocab_list: List[Dict], topic_name: str = "HACKERS TOEIC"):
    """Import vocabulary list to database."""
    
    with Session(engine) as session:
        # Get or create topic
        topic = session.exec(
            select(VocabTopic).where(
                VocabTopic.name == topic_name,
                VocabTopic.lang == "en"
            )
        ).first()
        
        if not topic:
            topic = VocabTopic(
                user_id=1,
                name=topic_name,
                lang="en",
                description="Vocabulary from HACKERS TOEIC book (OCR)",
                color="#FF6B6B",
                icon=""
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
            print(f"Created topic: {topic_name}")
        
        topic_id = topic.id
        
        # Import vocabulary
        imported_count = 0
        skipped_count = 0
        
        for vocab in vocab_list:
            if not vocab['word'] or len(vocab['word']) < 2:
                continue
                
            # Check if word already exists
            existing = session.exec(
                select(EnVocabItem).where(
                    EnVocabItem.word == vocab['word'],
                    EnVocabItem.user_id == 1
                )
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            vocab_item = EnVocabItem(
                user_id=1,
                word=vocab['word'],
                ipa=vocab.get('ipa', '')[:100],
                pos=vocab.get('pos', '')[:50],
                meaning_vi=vocab.get('meaning_vi', '')[:500],
                meaning_en='',
                example_en='',
                example_vi='',
                topic_id=topic_id,
                source_material="HACKERS TOEIC",
                level="TOEIC 800",
                mastery_status="new"
            )
            
            session.add(vocab_item)
            imported_count += 1
            
            if imported_count % 50 == 0:
                session.commit()
                print(f"  Imported {imported_count} words...", end="\r")
        
        session.commit()
        
        print(f"\nImport completed!")
        print(f"   - Imported: {imported_count} words")
        print(f"   - Skipped (duplicates): {skipped_count} words")
        print(f"   - Topic: {topic_name}")


def main():
    """Main function."""
    pdf_path = r"C:\Users\Admin\Downloads\HACKERS TOEIC.pdf"
    
    print("=" * 60)
    print("HACKERS TOEIC Vocabulary Extractor (OCR)")
    print("=" * 60)
    
    # Test with first 20 pages first
    vocab_list = extract_vocab_with_ocr(pdf_path, max_pages=20)
    
    if not vocab_list:
        print("\nNo vocabulary found in first 20 pages.")
        print("Checking what content is in the PDF...")
        
        # Check first few pages
        doc = fitz.open(pdf_path)
        for i in range(min(5, len(doc))):
            page = doc[i]
            text = page.get_text()
            print(f"\n--- Page {i+1} ---")
            print(text[:500])
        doc.close()
        return
    
    # Show sample
    print("\nSample entries:")
    for vocab in vocab_list[:10]:
        print(f"  - {vocab['word']} {vocab.get('ipa', '')} [{vocab.get('pos', '')}]")
        print(f"    {vocab.get('meaning_vi', '')[:80]}")
    
    # Import to database
    import_vocab_to_db(vocab_list)
    
    print("\n" + "=" * 60)
    print("Done! Check the vocabulary tab.")
    print("=" * 60)


if __name__ == "__main__":
    main()

