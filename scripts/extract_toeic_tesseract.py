import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Extract vocabulary from HACKERS TOEIC PDF using Tesseract OCR.

Optimized for batch processing to handle 541 pages efficiently.
"""
import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

# Add project root to path
project_root = Path(r"C:\ProgramData\Sandbox\Projects\EnglishApp")
sys.path.insert(0, str(project_root))

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class VocabularyExtractor:
    """Extract vocabulary from PDF with batch processing."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.total_pages = len(self.doc)
        self.extracted_words: Set[str] = set()
        
    def __del__(self):
        if hasattr(self, 'doc'):
            self.doc.close()
    
    def ocr_page(self, page_num: int, zoom: int = 2) -> str:
        """OCR a single page."""
        page = self.doc[page_num]
        
        # Render page to image with zoom for better OCR
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # OCR with both English and Vietnamese
        text = pytesseract.image_to_string(img, lang='eng+vie')
        
        return text
    
    def parse_vocab_entry(self, line: str) -> Dict:
        """Parse a single vocabulary entry from text line."""
        line = line.strip()
        if not line or len(line) < 5:
            return None
        
        # Skip non-vocabulary lines
        skip_patterns = [
            r'^\d+$',  # Just numbers
            r'^DAY\s*\d+',  # Day headers
            r'^LESSON',  # Lesson headers
            r'^UNIT',  # Unit headers
            r'^HACKERS',  # Book title
            r'^TOEIC',  # TOEIC mentions
            r'^www\.',  # URLs
            r'^[\d\.]+$',  # Page numbers
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return None
        
        # Pattern 1: WORD (IPA) POS meaning (most common in HACKERS)
        # Example: "abandon (/əˁEændən/) v. từ bềE bềErơi"
        match = re.match(
            r'^([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]+){0,2})\s*\(\s*/?([^/)]+)/?\s*\)\s*(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|det\.)\s*(.+)$',
            line
        )
        
        if match:
            word = match.group(1).strip()
            ipa = match.group(2).strip()
            pos = match.group(3).strip().rstrip('.')
            meaning = match.group(4).strip()
            
            # Validate word
            if not self._is_valid_word(word):
                return None
            
            return {
                'word': word,
                'ipa': f"/{ipa}/" if ipa else "",
                'pos': pos,
                'meaning_vi': meaning,
                'meaning_en': '',
                'example_en': '',
                'example_vi': ''
            }
        
        # Pattern 2: WORD IPA POS meaning (without parentheses around IPA)
        # Example: "abandon /əˁEændən/ v. từ bềE
        match = re.match(
            r'^([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]+){0,2})\s+/([^/]+)/\s*(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|det\.)\s*(.+)$',
            line
        )
        
        if match:
            word = match.group(1).strip()
            ipa = match.group(2).strip()
            pos = match.group(3).strip().rstrip('.')
            meaning = match.group(4).strip()
            
            if not self._is_valid_word(word):
                return None
            
            return {
                'word': word,
                'ipa': f"/{ipa}/",
                'pos': pos,
                'meaning_vi': meaning
            }
        
        # Pattern 3: Simple WORD POS meaning
        match = re.match(
            r'^([A-Z][a-zA-Z]{2,20})\s+(n\.|v\.|adj\.|adv\.)\s+(.{10,200})$',
            line
        )
        
        if match:
            word = match.group(1).strip()
            pos = match.group(2).strip().rstrip('.')
            meaning = match.group(3).strip()
            
            if not self._is_valid_word(word):
                return None
            
            return {
                'word': word,
                'ipa': '',
                'pos': pos,
                'meaning_vi': meaning
            }
        
        return None
    
    def _is_valid_word(self, word: str) -> bool:
        """Check if extracted text is a valid English word."""
        if len(word) < 2 or len(word) > 35:
            return False
        
        # Skip if contains Vietnamese characters
        vietnamese_chars = 'àáạảãâầấậẩẫāE��ắặẩẵèéẹẻẽêềếềE��E��E�íịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẨẴÈÉẸẺẼÊỀẾềE��ềE�ÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸāE
        if any(c in word for c in vietnamese_chars):
            return False
        
        # Skip if contains numbers
        if any(c.isdigit() for c in word):
            return False
        
        # Skip if all uppercase (likely headers)
        if word.isupper() and len(word) > 3:
            return False
        
        return True
    
    def extract_from_page(self, page_num: int) -> List[Dict]:
        """Extract vocabulary from a single page."""
        vocab_list = []
        
        try:
            text = self.ocr_page(page_num)
            lines = text.split('\n')
            
            for line in lines:
                vocab = self.parse_vocab_entry(line)
                if vocab:
                    # Avoid duplicates
                    word_key = vocab['word'].lower()
                    if word_key not in self.extracted_words:
                        self.extracted_words.add(word_key)
                        vocab_list.append(vocab)
        except Exception as e:
            print(f"Error processing page {page_num + 1}: {e}")
        
        return vocab_list
    
    def extract_batch(self, start_page: int, end_page: int) -> List[Dict]:
        """Extract vocabulary from a range of pages."""
        vocab_list = []
        
        for page_num in range(start_page, min(end_page, self.total_pages)):
            if (page_num - start_page) % 10 == 0:
                print(f"  Processing page {page_num + 1}/{end_page}...", end="\r")
            
            page_vocab = self.extract_from_page(page_num)
            vocab_list.extend(page_vocab)
        
        return vocab_list
    
    def extract_all(self, batch_size: int = 50) -> List[Dict]:
        """Extract vocabulary from all pages in batches."""
        all_vocab = []
        
        print(f"Starting OCR extraction from {self.total_pages} pages...")
        print(f"Processing in batches of {batch_size} pages\n")
        
        for start in range(0, self.total_pages, batch_size):
            end = min(start + batch_size, self.total_pages)
            print(f"Batch: pages {start + 1} to {end}")
            
            batch_vocab = self.extract_batch(start, end)
            all_vocab.extend(batch_vocab)
            
            print(f"  Found {len(batch_vocab)} words in this batch")
            print(f"  Total so far: {len(all_vocab)} unique words\n")
        
        return all_vocab


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
                description="Vocabulary from HACKERS TOEIC book",
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
                meaning_en=vocab.get('meaning_en', '')[:500],
                example_en=vocab.get('example_en', '')[:1000],
                example_vi=vocab.get('example_vi', '')[:1000],
                topic_id=topic_id,
                source_material="HACKERS TOEIC",
                level="TOEIC 800",
                mastery_status="new"
            )
            
            session.add(vocab_item)
            imported_count += 1
            
            if imported_count % 100 == 0:
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
    
    print("=" * 70)
    print("HACKERS TOEIC Vocabulary Extractor (Tesseract OCR)")
    print("=" * 70)
    print(f"PDF: {pdf_path}")
    print(f"Tesseract: {pytesseract.pytesseract.tesseract_cmd}")
    print("=" * 70 + "\n")
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
    
    # Create extractor and process
    extractor = VocabularyExtractor(pdf_path)
    
    print(f"Total pages in PDF: {extractor.total_pages}")
    print("Note: OCR may take 30-60 minutes for 541 pages")
    print("You can stop anytime with Ctrl+C and resume later\n")
    
    try:
        vocab_list = extractor.extract_all(batch_size=50)
        
        if not vocab_list:
            print("\nNo vocabulary found!")
            print("The PDF might have a different format than expected.")
            return
        
        print("\n" + "=" * 70)
        print(f"Extraction completed: {len(vocab_list)} unique words found")
        print("=" * 70)
        
        # Show sample
        print("\nSample entries:")
        for vocab in vocab_list[:10]:
            print(f"  - {vocab['word']:<20} {vocab.get('ipa', ''):<20} [{vocab.get('pos', ''):<5}] {vocab.get('meaning_vi', '')[:50]}...")
        
        # Import to database
        print("\nImporting to database...")
        import_vocab_to_db(vocab_list)
        
        print("\n" + "=" * 70)
        print("Done! Open the application and check the Vocabulary tab.")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        print("You can run the script again to continue.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

