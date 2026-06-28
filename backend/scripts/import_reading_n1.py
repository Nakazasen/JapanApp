
import pandas as pd
import os
import json
import shutil
import sys

# Ensure project root is in path so we can import frontend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlmodel import Session, create_engine, select
from frontend.core.config import settings
from frontend.models.reading_practice import ReadingCategory, ReadingItem, ReadingQuestion

# --- Configurations ---
excel_path = r"C:\ProgramData\Sandbox\Projects\EnglishApp\reading_n1_data.xlsx"
DB_PATH = settings.db_path
USER_ID = 1 # Default admin

def backup_db():
    if os.path.exists(DB_PATH):
        backup_path = f"{DB_PATH}.bak"
        try:
            shutil.copy2(DB_PATH, backup_path)
            print(f"✅ Database backed up to: {backup_path}")
        except Exception as e:
            print(f"⚠️ Could not backup database: {e}")

def import_data():
    if not os.path.exists(excel_path):
        print(f"❌ Error: Excel file not found at {excel_path}")
        return

    print(f"📖 Reading Excel: {excel_path}")
    try:
        # 1. Load data
        df = pd.read_excel(excel_path)
        
        # 2. Setup engine
        database_url = f"sqlite:///{DB_PATH}"
        engine = create_engine(database_url)
        
        with Session(engine) as session:
            # 3. Ensure Category exists
            cat_name = "JLPT N1 Reading Practice"
            statement = select(ReadingCategory).where(ReadingCategory.name == cat_name)
            category = session.exec(statement).first()
            if not category:
                print(f"📂 Creating category: {cat_name}")
                category = ReadingCategory(
                    name=cat_name,
                    level="N1"
                )
                session.add(category)
                session.commit()
                session.refresh(category)
            else:
                # --- NEW: Clear existing data for this category ---
                print(f"🧹 Clearing old data for category: {cat_name}")
                from sqlalchemy import delete
                
                # Get all item IDs in this category
                item_ids_stmt = select(ReadingItem.id).where(ReadingItem.category_id == category.id)
                item_ids = session.exec(item_ids_stmt).all()
                
                if item_ids:
                    # Delete questions associated with these items
                    del_q_stmt = delete(ReadingQuestion).where(ReadingQuestion.item_id.in_(item_ids))
                    session.exec(del_q_stmt)
                    
                    # Delete the items themselves
                    del_i_stmt = delete(ReadingItem).where(ReadingItem.category_id == category.id)
                    session.exec(del_i_stmt)
                    
                    session.commit()
                    print(f"✅ Old data cleared ({len(item_ids)} items).")
            
            # 4. Group by Passage_ID to separate Items from Questions
            grouped = df.groupby('Passage_ID', sort=False)
            
            item_count = 0
            question_count = 0
            
            print(f"🚀 Processing {len(grouped)} reading passages...")
            
            for passage_id, group in grouped:
                first_row = group.iloc[0]
                
                # Create ReadingItem (The Passage)
                item = ReadingItem(
                    category_id=category.id,
                    title=str(first_row['Title']),
                    content=str(first_row['Content']),
                    source=str(first_row['Source'])
                )
                session.add(item)
                session.commit()
                session.refresh(item)
                item_count += 1
                
                # Create Questions for this Item
                for _, row in group.iterrows():
                    options_dict = {
                        "1": str(row['Option_1']),
                        "2": str(row['Option_2']),
                        "3": str(row['Option_3']),
                        "4": str(row['Option_4'])
                    }
                    
                    question = ReadingQuestion(
                        item_id=item.id,
                        question_text=str(row['Question']),
                        options=options_dict, 
                        correct_option=str(row['Answer']),
                        explanation=str(row['Explanation']) if pd.notna(row['Explanation']) else None
                    )
                    session.add(question)
                    question_count += 1
            
            session.commit()
            print(f"\n✨ Import finished successfully!")
            print(f"--------------------------------")
            print(f"✅ Items created: {item_count}")
            print(f"✅ Questions created: {question_count}")
            print(f"--------------------------------")

    except Exception as e:
        print(f"❌ Error during import: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    backup_db()
    import_data()
