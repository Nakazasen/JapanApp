import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pandas as pd
import os
from sqlmodel import Session, create_engine, select
from frontend.core.config import settings
from frontend.models.vocab import JpVocabItem, VocabTopic

# --- Configurations ---
file_path = r"C:\Users\Admin\Downloads\Từ-vựng-N5-N1.xlsx"
SOURCE = "MimikaraOboeru"
USER_ID = 1 # Admin user

def import_level(engine, level_name):
    print(f"\nProcessing Level: {level_name}")
    try:
        # Read Excel sheet
        df = pd.read_excel(file_path, sheet_name=level_name)
        
        # Determine column mapping based on the sheet structure we peeked at
        # Common columns: 'Từ vựng', 'Phiên âm', 'Hán Việt', 'ÁEnghĩa', 'No'
        # N2 has 'Unnamed: 5' which seems to be a duplicate of meaning in some cases, let's stick to 'ÁEnghĩa'
        
        col_word = 'Từ vựng'
        col_reading = 'Phiên âm'
        col_hanviet = 'Hán Việt'
        col_meaning = 'ÁEnghĩa'
        col_no = 'No'
        
        if col_word not in df.columns:
            print(f"Error: {col_word} column not found in {level_name}")
            return

        vocab_list = []
        current_main_word = None
        
        TOPIC_NAME = f"Mimikara {level_name} 耳から"
        
        # Ensure Topic exists
        with Session(engine) as session:
            statement = select(VocabTopic).where(VocabTopic.name == TOPIC_NAME)
            topic = session.exec(statement).first()
            if not topic:
                topic = VocabTopic(
                    name=TOPIC_NAME,
                    description=f"Từ vựng Mimikara Oboeru {level_name} nhập từ Excel",
                    user_id=USER_ID,
                    lang="jp",
                    icon="📔"
                )
                session.add(topic)
                session.commit()
                session.refresh(topic)
            topic_id = topic.id

        # Process rows
        for index, row in df.iterrows():
            no = str(row[col_no]) if col_no in df.columns and pd.notna(row[col_no]) else ""
            kanji = str(row[col_word]) if pd.notna(row[col_word]) else ""
            kana = str(row[col_reading]) if col_reading in df.columns and pd.notna(row[col_reading]) else ""
            han_viet = str(row[col_hanviet]) if col_hanviet in df.columns and pd.notna(row[col_hanviet]) else ""
            meaning = str(row[col_meaning]) if col_meaning in df.columns and pd.notna(row[col_meaning]) else ""
            
            if not kanji:
                continue
                
            # Check if it's a main number (e.g. "1", "1.0", "2")
            is_main = False
            try:
                if no:
                    # Clean the 'no' string, sometimes it's like '1.' or '1'
                    num_str = no.rstrip('.')
                    num = float(num_str)
                    if num.is_integer():
                        is_main = True
            except ValueError:
                pass
            
            # If 'no' is empty, we treat it as a main word if it's the first one or if we don't care about numbers
            # In this sheet, all words seem to have a main number (1, 2, 3...)
            
            if is_main or not no:
                # Create a new main word entry
                current_main_word = {
                    "user_id": USER_ID,
                    "topic_id": topic_id,
                    "word_kanji": kanji,
                    "word_kana": kana,
                    "han_viet": han_viet,
                    "meaning_vi": meaning,
                    "example_jp": "",
                    "level": level_name,
                    "source_material": SOURCE,
                    "mastery_status": "new"
                }
                vocab_list.append(current_main_word)
            else:
                # It's a sub-item (1.1, 1.2...), add as example to current_main_word
                if current_main_word:
                    example_text = f"{kanji} ({kana})" if kana else kanji
                    if current_main_word["example_jp"]:
                        current_main_word["example_jp"] += f"\n{example_text}"
                    else:
                        current_main_word["example_jp"] = example_text

        print(f"Collected {len(vocab_list)} main words for {level_name}.")
        
        # Save to Database
        with Session(engine) as session:
            count = 0
            for item_data in vocab_list:
                # Avoid direct duplicates by word_kanji AND topic_id
                statement = select(JpVocabItem).where(
                    JpVocabItem.word_kanji == item_data["word_kanji"],
                    JpVocabItem.topic_id == topic_id
                )
                existing = session.exec(statement).first()
                
                if not existing:
                    db_item = JpVocabItem(**item_data)
                    session.add(db_item)
                    count += 1
            
            session.commit()
            print(f"Successfully imported {count} new entries for {level_name} to database.")
            
    except Exception as e:
        print(f"Error processing level {level_name}: {e}")

def main():
    database_url = f"sqlite:///{settings.db_path}"
    engine = create_engine(database_url)
    
    levels = ["N5", "N4", "N3", "N2"] # As requested
    
    if not os.path.exists(file_path):
        print(f"Error: Excel file not found at {file_path}")
        return
        
    for level in levels:
        import_level(engine, level)

if __name__ == "__main__":
    main()

