import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Extract vocabulary from HACKERS TOEIC PDF and import to database."""
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add project root to path
project_root = Path(r"C:\ProgramData\Sandbox\Projects\EnglishApp")
sys.path.insert(0, str(project_root))

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber

from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic


def extract_vocab_from_pdf(pdf_path: str) -> List[Dict]:
    """Extract vocabulary entries from HACKERS TOEIC PDF.
    
    HACKERS TOEIC format typically has:
    - Word in bold/larger font
    - IPA pronunciation
    - Part of speech
    - Vietnamese meaning
    - Example sentences
    """
    vocab_list = []
    
    print(f"Reading PDF: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"  Processing page {page_num}/{total_pages}...", end="\r")
            
            # Extract text with layout information
            text = page.extract_text()
            if not text:
                continue
            
            # Try to identify vocabulary entries
            # HACKERS TOEIC typically has patterns like:
            # WORD (ipa) [pos] meaning
            # or multi-line entries
            
            lines = text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines and headers
                if not line or any(header in line.lower() for header in ['hackers toeic', 'lesson', 'day', 'vocabulary']):
                    i += 1
                    continue
                
                # Try to match vocabulary entry patterns
                # Pattern 1: WORD (ipa) part_of_speech meaning
                vocab_match = re.match(
                    r'^([A-Za-z\-]+(?:\s+[A-Za-z\-]+)*)\s*\(([^)]+)\)\s*(\w+)\s*(.+)$',
                    line
                )
                
                if vocab_match:
                    word = vocab_match.group(1).strip()
                    ipa = vocab_match.group(2).strip()
                    pos = vocab_match.group(3).strip()
                    meaning = vocab_match.group(4).strip()
                    
                    # Look for example in next lines
                    example_en = ""
                    example_vi = ""
                    j = i + 1
                    while j < len(lines) and j < i + 5:
                        next_line = lines[j].strip()
                        if next_line and not re.match(r'^[A-Za-z\-]+\s*\(', next_line):
                            if not example_en:
                                example_en = next_line
                            elif not example_vi and any(c in next_line for c in 'ﾃﾃ｡蘯｡蘯｣ﾃ｣ﾃ｢蘯ｧ蘯･蘯ｭ蘯ｩ蘯ｫﾄ・ｺｱ蘯ｯ蘯ｷ蘯ｩ蘯ｵﾃｨﾃｩ蘯ｹ蘯ｻ蘯ｽﾃｪ盻≪ｺｿ盻・ｻ・ｻ・ｬﾃｭ盻吟ｻ夏ｩﾃｲﾃｳ盻冴ｻ湘ｵﾃｴ盻乍ｻ黛ｻ吼ｻ甫ｻ糧｡盻昵ｻ帋ｻ｣盻溂ｻ｡ﾃｹﾃｺ盻･盻ｧﾅｩﾆｰ盻ｫ盻ｩ盻ｱ盻ｭ盻ｯ盻ｳﾃｽ盻ｵ盻ｷ盻ｹﾄ・):
                                example_vi = next_line
                                break
                        j += 1
                    
                    vocab_list.append({
                        'word': word,
                        'ipa': ipa,
                        'pos': pos,
                        'meaning_vi': meaning,
                        'meaning_en': '',
                        'example_en': example_en,
                        'example_vi': example_vi
                    })
                
                i += 1
    
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
                description="Vocabulary from HACKERS TOEIC book",
                color="#FF6B6B",
                icon="答"
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
                ipa=vocab.get('ipa', ''),
                pos=vocab.get('pos', ''),
                meaning_vi=vocab.get('meaning_vi', ''),
                meaning_en=vocab.get('meaning_en', ''),
                example_en=vocab.get('example_en', ''),
                example_vi=vocab.get('example_vi', ''),
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
    """Main function to extract and import vocabulary."""
    pdf_path = r"C:\Users\Admin\Downloads\HACKERS TOEIC.pdf"
    
    print("=" * 60)
    print("HACKERS TOEIC Vocabulary Extractor")
    print("=" * 60)
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
    
    # Extract vocabulary
    vocab_list = extract_vocab_from_pdf(pdf_path)
    
    if not vocab_list:
        print("No vocabulary found in PDF")
        sys.exit(1)
    
    # Show sample
    print("\nSample entries:")
    for vocab in vocab_list[:3]:
        print(f"  窶｢ {vocab['word']} ({vocab.get('ipa', '')}) [{vocab.get('pos', '')}]")
        print(f"    Meaning: {vocab.get('meaning_vi', '')[:50]}...")
        if vocab.get('example_en'):
            print(f"    Example: {vocab['example_en'][:60]}...")
        print()
    
    # Import to database
    import_vocab_to_db(vocab_list)
    
    print("\n" + "=" * 60)
    print("Done! Check the vocabulary tab in the application.")
    print("=" * 60)


if __name__ == "__main__":
    main()

