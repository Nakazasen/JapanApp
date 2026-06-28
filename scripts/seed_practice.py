import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.core.database import engine, get_session, create_db_and_tables
from frontend.models.practice import PracticeCategory, PracticeType
from sqlmodel import Session, select

def seed_practice_categories():
    # Ensure tables are created
    create_db_and_tables()
    
    with get_session() as session:
        # Check if categories already exist
        existing = session.exec(select(PracticeCategory)).first()
        if existing:
            print("Practice categories already exist. Skipping seed.")
            return
            
        categories = [
            # Reading
            {"name": "JLPT N5 Reading", "type": "reading", "level": "N5", "icon": "🟢"},
            {"name": "JLPT N4 Reading", "type": "reading", "level": "N4", "icon": "🟡"},
            {"name": "JLPT N3 Reading", "type": "reading", "level": "N3", "icon": "🟠"},
            {"name": "JLPT N2 Reading", "type": "reading", "level": "N2", "icon": "🔴"},
            {"name": "JLPT N1 Reading", "type": "reading", "level": "N1", "icon": "⚫"},
            
            # Listening
            {"name": "JLPT N5 Listening", "type": "listening", "level": "N5", "icon": "🟢"},
            {"name": "JLPT N4 Listening", "type": "listening", "level": "N4", "icon": "🟡"},
            {"name": "JLPT N3 Listening", "type": "listening", "level": "N3", "icon": "🟠"},
            {"name": "JLPT N2 Listening", "type": "listening", "level": "N2", "icon": "🔴"},
            {"name": "JLPT N1 Listening", "type": "listening", "level": "N1", "icon": "⚫"},
        ]
        
        for cat_data in categories:
            cat = PracticeCategory(**cat_data)
            session.add(cat)
            
        session.commit()
        print(f"Seeded {len(categories)} practice categories.")

if __name__ == "__main__":
    seed_practice_categories()

