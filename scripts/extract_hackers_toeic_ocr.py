import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Extract vocabulary from image-based PDF using OCR."""
import re
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add project root to path
project_root = Path(r"C:\ProgramData\Sandbox\Projects\EnglishApp")
sys.path.insert(0, str(project_root))

from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic


def extract_vocab_with_ocr(pdf_path: str, max_pages: int = None) -> List[Dict]:
    """Extract vocabulary from image-based PDF using OCR."""
    vocab_list = []
    
    print(f"Converting PDF to images...")
    
    # Convert PDF to images (first few pages for testing)
    if max_pages:
        images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
    else:
        images = convert_from_path(pdf_path)
    
    print(f"Total pages to process: {len(images)}")
    
    for i, image in enumerate(images):
        page_num = i + 1
        print(f"Processing page {page_num}/{len(images)}...", end="\r")
        
        # Use OCR to extract text
        text = pytesseract.image_to_string(image, lang='eng+vie')
        
        # Parse vocabulary entries
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to match vocabulary patterns
            # HACKERS TOEIC format: WORD (IPA) POS meaning
            patterns = [
                # Pattern 1: WORD (IPA) [POS] meaning
                r'^([A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+)*)\s*\(/([^/]+)/\)?\s*(\w+\.)?\s*(.+)',
                # Pattern 2: WORD IPA POS meaning (simpler)
                r'^([A-Za-z\-]+)\s*\(?([^)]+)\)?\s*(n\.|v\.|adj\.|adv\.)\s*(.+)',
                # Pattern 3: Just word and meaning
                r'^([A-Za-z\-]+(?:\s+[A-Za-z\-]+){0,2})\s+(là|đồng nghĩa|có nghĩa)\s*(.+)',
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    word = match.group(1).strip()
                    # Skip if word contains Vietnamese characters or is too long
                    if any(c in word for c in 'àáạảãâầấậẩẫāE��ắặẩẵèéẹẻẽêềếềE��E��E�íịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹāE):
                        continue
                    if len(word) > 50:
                        continue
                    
                    ipa = match.group(2).strip() if len(match.groups()) > 1 else ""
                    pos = match.group(3).strip() if len(match.groups()) > 2 else ""
                    meaning = match.group(4).strip() if len(match.groups()) > 3 else ""
                    
                    # Clean up IPA
                    if ipa and not any(c in ipa for c in 'æɑɔəɜɪʊʌθðʃʒŁE):
                        # Probably not IPA, might be something else
                        meaning = pos + " " + meaning if pos else meaning
                        pos = ipa
                        ipa = ""
                    
                    vocab_list.append({
                        'word': word,
                        'ipa': ipa,
                        'pos': pos.rstrip('.') if pos else "",
                        'meaning_vi': meaning,
                        'meaning_en': '',
                        'example_en': '',
                        'example_vi': ''
                    })
                    break
    
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
                icon="📚"
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
            # Skip if word is empty or too short
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
            
            # Create new vocab item
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
    
    # Process all pages or just first 10 for testing
    vocab_list = extract_vocab_with_ocr(pdf_path, max_pages=10)  # Test with first 10 pages
    # vocab_list = extract_vocab_with_ocr(pdf_path)  # Process all pages
    
    if not vocab_list:
        print("No vocabulary found!")
        return
    
    # Show sample
    print("\nSample entries:")
    for vocab in vocab_list[:5]:
        print(f"  - {vocab['word']} {vocab.get('ipa', '')} [{vocab.get('pos', '')}]")
        print(f"    {vocab.get('meaning_vi', '')[:60]}...")
    
    # Import to database
    import_vocab_to_db(vocab_list)
    
    print("\n" + "=" * 60)
    print("Done! Check the vocabulary tab.")
    print("=" * 60)


if __name__ == "__main__":
    main()

