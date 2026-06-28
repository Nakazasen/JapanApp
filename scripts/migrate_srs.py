import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import sqlite3
from frontend.core.config import settings

def migrate():
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    
    for table in ["jp_vocab_items", "en_vocab_items"]:
        print(f"Migrating {table}...")
        
        # Add srs_level if missing
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [c[1] for c in cursor.fetchall()]
        
        if "srs_level" not in cols:
            print(f"Adding srs_level to {table}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN srs_level INTEGER DEFAULT 0")
            
        if "review_count" not in cols:
            print(f"Adding review_count to {table}")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN review_count INTEGER DEFAULT 0")
            
        if "next_review" not in cols and "next_review_at" in cols:
            print(f"Renaming next_review_at to next_review in {table}")
            # SQLite 3.25.0+ supports RENAME COLUMN
            try:
                cursor.execute(f"ALTER TABLE {table} RENAME COLUMN next_review_at TO next_review")
            except Exception as e:
                print(f"Failed RENAME COLUMN (likely old sqlite version): {e}")
                # Fallback: manually handle if needed, but usually RENAME is safe in modern envs
        
        if "last_reviewed" not in cols and "last_reviewed_at" in cols:
            print(f"Renaming last_reviewed_at to last_reviewed in {table}")
            try:
                cursor.execute(f"ALTER TABLE {table} RENAME COLUMN last_reviewed_at TO last_reviewed")
            except Exception as e:
                print(f"Failed RENAME COLUMN: {e}")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()

