import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
HACKERS TOEIC Vocabulary Import Script
=======================================

Vì PDF là dạng hình ảnh và cần OCR (Tesseract) đềEtrích xuất, 
bạn có thềEdùng một trong các cách sau:

CÁCH 1: Dùng file CSV/Excel (Khuyến nghềE
-----------------------------------------
Nếu bạn có file Excel hoặc CSV chứa danh sách từ vựng HACKERS TOEIC,
hãy đặt file đó vào thư mục này và đổi tên thành 'hackers_toeic_vocab.csv'

Format CSV mong muốn:
word,ipa,pos,meaning_vi,example_en
abandon,/əˁEændən/,v.,từ bềEThey had to abandon the project.
ability,/əˁEɪləti/,n.,khả năng,She has the ability to learn quickly.
...

Sau đó chạy: python import_csv_vocab.py

CÁCH 2: Dùng Online OCR
------------------------
1. Truy cập: https://www.onlineocr.net/ hoặc https://www.newocr.com/
2. Upload file HACKERS TOEIC.pdf
3. Chọn output là TXT hoặc Word
4. Copy nội dung và lưu vào file 'hackers_toeic_text.txt'
5. Chạy script parse_text.py đềEtrích xuất từ vựng

CÁCH 3: Cài đặt Tesseract OCR
------------------------------
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Cài đặt vào C:\Program Files\Tesseract-OCR
3. Thêm vào PATH environment variable
4. Chạy lại script extract_toeic_ocr.py

CÁCH 4: Dùng Google Drive OCR
------------------------------
1. Upload PDF lên Google Drive
2. MềEbằng Google Docs (sẽ tự động OCR)
3. File > Download > Plain Text (.txt)
4. Chạy script parse_text.py đềEtrích xuất từ vựng

SCRIPT HềETRỢ
=============
"""

import_csv_script = '''
"""Import vocabulary from CSV file."""
import csv
import sys
from pathlib import Path
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic

def import_from_csv(csv_path: str):
    """Import vocabulary from CSV file."""
    vocab_list = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vocab_list.append({
                'word': row.get('word', ''),
                'ipa': row.get('ipa', ''),
                'pos': row.get('pos', ''),
                'meaning_vi': row.get('meaning_vi', ''),
                'example_en': row.get('example_en', '')
            })
    
    print(f"Loaded {len(vocab_list)} words from CSV")
    
    with Session(engine) as session:
        # Create topic
        topic = session.exec(
            select(VocabTopic).where(
                VocabTopic.name == "HACKERS TOEIC",
                VocabTopic.lang == "en"
            )
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
        
        # Import words
        imported = 0
        for vocab in vocab_list:
            if not vocab['word']:
                continue
                
            existing = session.exec(
                select(EnVocabItem).where(
                    EnVocabItem.word == vocab['word'],
                    EnVocabItem.user_id == 1
                )
            ).first()
            
            if existing:
                continue
            
            item = EnVocabItem(
                user_id=1,
                word=vocab['word'],
                ipa=vocab.get('ipa', '')[:100],
                pos=vocab.get('pos', '')[:50],
                meaning_vi=vocab.get('meaning_vi', '')[:500],
                example_en=vocab.get('example_en', '')[:1000],
                topic_id=topic.id,
                source_material="HACKERS TOEIC",
                level="TOEIC 800",
                mastery_status="new"
            )
            session.add(item)
            imported += 1
            
            if imported % 100 == 0:
                session.commit()
                print(f"Imported {imported} words...")
        
        session.commit()
        print(f"Total imported: {imported} words")

if __name__ == "__main__":
    import_from_csv("hackers_toeic_vocab.csv")
'''

parse_text_script = '''
"""Parse vocabulary from text file extracted via OCR."""
import re
import sys
from pathlib import Path
from sqlmodel import Session, select
from frontend.core.database import engine
from frontend.models.vocab import EnVocabItem, VocabTopic

def parse_vocab_from_text(text_path: str):
    """Parse vocabulary from OCR text file."""
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    vocab_list = []
    lines = text.split('\\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Pattern for HACKERS TOEIC: WORD (IPA) POS meaning
        match = re.match(
            r'^([A-Z][a-zA-Z]+(?:\\s+[A-Z][a-zA-Z]+)?)\\s*\\(/([^/]+)/\\)?\\s*(\\w+\\.?)\\s*(.+)',
            line
        )
        
        if match:
            word = match.group(1).strip()
            ipa = match.group(2).strip()
            pos = match.group(3).strip().rstrip('.')
            meaning = match.group(4).strip()
            
            if len(word) >= 2 and len(word) <= 40:
                vocab_list.append({
                    'word': word,
                    'ipa': f"/{ipa}/",
                    'pos': pos,
                    'meaning_vi': meaning
                })
    
    print(f"Found {len(vocab_list)} vocabulary entries")
    return vocab_list

def import_to_db(vocab_list):
    """Import to database."""
    with Session(engine) as session:
        topic = session.exec(
            select(VocabTopic).where(
                VocabTopic.name == "HACKERS TOEIC",
                VocabTopic.lang == "en"
            )
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
        
        imported = 0
        for vocab in vocab_list:
            existing = session.exec(
                select(EnVocabItem).where(
                    EnVocabItem.word == vocab['word'],
                    EnVocabItem.user_id == 1
                )
            ).first()
            
            if not existing:
                item = EnVocabItem(
                    user_id=1,
                    word=vocab['word'],
                    ipa=vocab['ipa'][:100],
                    pos=vocab['pos'][:50],
                    meaning_vi=vocab['meaning_vi'][:500],
                    topic_id=topic.id,
                    source_material="HACKERS TOEIC",
                    level="TOEIC 800",
                    mastery_status="new"
                )
                session.add(item)
                imported += 1
        
        session.commit()
        print(f"Imported {imported} words to database")

if __name__ == "__main__":
    vocab_list = parse_vocab_from_text("hackers_toeic_text.txt")
    import_to_db(vocab_list)
'''

print(__doc__)
print("\n" + "="*60)
print("ĐÁETẠO SẴN CÁC SCRIPT:")
print("="*60)
print("\n1. import_csv_vocab.py - Import từ file CSV")
print("2. parse_text.py - Parse từ file text (sau OCR)")

# Save helper scripts
with open("import_csv_vocab.py", "w", encoding="utf-8") as f:
    f.write(import_csv_script)

with open("parse_text.py", "w", encoding="utf-8") as f:
    f.write(parse_text_script)

print("\n✁EĐã tạo file: import_csv_vocab.py")
print("✁EĐã tạo file: parse_text.py")

