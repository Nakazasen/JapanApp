"""Normalize vocabulary levels in unified_vocab_items.

Converts level 'TOEIC' to 'TOEIC 800' to match UI filters.
"""
import sys
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from sqlmodel import Session, create_engine, text

# Database Configuration
DB_PATH = project_root / "db" / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)

def normalize_levels():
    print(f"🚀 Normalizing vocabulary levels...")
    print(f"📁 Database: {DB_PATH}")
    
    with Session(engine) as session:
        # Check current counts
        res = session.exec(text("SELECT count(*) FROM unified_vocab_items WHERE level = 'TOEIC'")).scalar()
        print(f"🔍 Found {res} items with level='TOEIC'")
        
        if res > 0:
            print(f"🆙 Updating {res} items to level='TOEIC 800'...")
            session.exec(text("UPDATE unified_vocab_items SET level = 'TOEIC 800' WHERE level = 'TOEIC'"))
            session.commit()
            print("✅ Update complete!")
        else:
            print("ℹ️ No items with level='TOEIC' found.")
            
        # Verify total for TOEIC 800
        total = session.exec(text("SELECT count(*) FROM unified_vocab_items WHERE level = 'TOEIC 800'")).scalar()
        print(f"📊 Total items with level='TOEIC 800': {total}")

if __name__ == "__main__":
    normalize_levels()
