import os
import sys
import sqlite3

# Ensure project root is in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

from frontend.core.config import settings

def migrate():
    db_path = settings.db_path
    print(f"🛠️ Migrating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ["vocab_practice_items", "grammar_practice_items", "kanji_practice_items"]
    new_columns = [
        ("transcript", "TEXT"),
        ("vocabulary", "JSON"),
        ("translation", "TEXT"),
        ("analysis", "JSON")
    ]
    
    for table in tables:
        # Check existing columns
        cursor.execute(f"PRAGMA table_info({table})")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                print(f"  Adding column {col_name} to {table}...")
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    print(f"    Error: {e}")
            else:
                print(f"  Column {col_name} already exists in {table}")
                
    conn.commit()
    conn.close()
    print("✅ Migration completed.")

if __name__ == "__main__":
    migrate()
