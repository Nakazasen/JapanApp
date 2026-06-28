import os
import sys
import time
from sqlmodel import Session, SQLModel, create_engine, select

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from frontend.core.config import settings
from frontend.services.jt4y_scraper import JT4YScraper
from frontend.models.reading_practice import ReadingCategory, ReadingItem, ReadingQuestion

# --- Configurations ---
DB_PATH = settings.db_path
LIMIT_PER_CAT = 100 
N1_READING_URL = "https://japanesetest4you.com/category/jlpt-n1/jlpt-n1-reading-test/"

def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    return Session(engine)

def cleanup_n1_reading():
    print("🧹 Cleaning up N1 Reading data ONLY...")
    with get_session() as session:
        # 1. Find the N1 Reading Category
        cat = session.exec(select(ReadingCategory).where(ReadingCategory.name == "JT4Y N1 Reading")).first()
        if not cat:
            print("  Category 'JT4Y N1 Reading' not found. Nothing to clean.")
            return

        # 2. Find items in this category AND items with N1 in title as safety
        items = session.exec(
            select(ReadingItem).where(
                (ReadingItem.category_id == cat.id) | 
                (ReadingItem.source == "JT4Y") & (ReadingItem.title.contains("N1"))
            )
        ).all()
        
        count = len(items)
        if count == 0:
            print("  No items found in N1 Reading.")
            return

        print(f"  Deleting {count} existing N1 reading exercises...")
        for i in items:
            for q in i.questions: session.delete(q)
            session.delete(i)
        
        session.commit()
        print("  Cleanup complete.")

def ensure_n1_category():
    with get_session() as session:
        if not session.exec(select(ReadingCategory).where(ReadingCategory.name == "JT4Y N1 Reading")).first():
            print("📁 Creating 'JT4Y N1 Reading' category...")
            session.add(ReadingCategory(name="JT4Y N1 Reading", level="N1"))
            session.commit()

def import_n1_reading():
    cleanup_n1_reading()
    ensure_n1_category()
    
    print("🚀 Importing N1 Reading...")
    links = JT4YScraper.get_exercise_links(N1_READING_URL)[:LIMIT_PER_CAT]
    print(f"  Found {len(links)} exercises.")

    with get_session() as session:
        cat = session.exec(select(ReadingCategory).where(ReadingCategory.name == "JT4Y N1 Reading")).first()
        
        for link in links:
            print(f"  Scraping {link['title']}...")
            try:
                sections = JT4YScraper.scrape_reading(link['url'])
                if not sections: continue
                
                for section in sections:
                    if not section.get('questions'): continue
                    
                    # Create Item (Passage)
                    item = ReadingItem(
                        category_id=cat.id,
                        title=section['title'],
                        content=section.get('passage', ""),
                        source="JT4Y"
                    )
                    session.add(item)
                    session.commit()
                    session.refresh(item)
                    
                    # Create Questions
                    for q in section['questions']:
                        question = ReadingQuestion(
                            item_id=item.id,
                            question_text=q['text'],
                            options=q['options'],
                            correct_option=str(q.get('answer'))
                        )
                        session.add(question)
                    session.commit()
            except Exception as e:
                print(f"  ❌ Error scraping {link['url']}: {e}")
                # Don't stop, continue to next
                continue
    
    print("\n✨ N1 Reading Import Finished!")

if __name__ == "__main__":
    try:
        import_n1_reading()
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
