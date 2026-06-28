import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Migration script to update news_articles table with new columns."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "app.db")

NEW_COLUMNS = [
    ("source_name", "VARCHAR(100) DEFAULT 'Unknown'"),
    ("author", "VARCHAR(200)"),
    ("summary", "TEXT"),
    ("content_html", "TEXT"),
    ("language", "VARCHAR(10) DEFAULT 'en'"),
    ("tags", "TEXT"),
    ("thumbnail_url", "VARCHAR(1000)"),
    ("upvotes", "INTEGER DEFAULT 0"),
    ("comments_count", "INTEGER DEFAULT 0"),
    ("stocks", "INTEGER DEFAULT 0"),
    ("is_read", "BOOLEAN DEFAULT 0"),
    ("is_saved", "BOOLEAN DEFAULT 0"),
    ("furigana_title", "TEXT"),
    ("furigana_content", "TEXT"),
]

def get_existing_columns(cursor, table_name):
    """Get list of existing column names in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def migrate():
    print(f"[Migration] Connecting to database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("[Migration] Database file not found!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_articles'")
        if not cursor.fetchone():
            print("[Migration] Table 'news_articles' does not exist. Will be created on app start.")
            return
        
        existing_columns = get_existing_columns(cursor, "news_articles")
        print(f"[Migration] Existing columns: {existing_columns}")
        
        added = 0
        for col_name, col_type in NEW_COLUMNS:
            if col_name not in existing_columns:
                sql = f"ALTER TABLE news_articles ADD COLUMN {col_name} {col_type}"
                print(f"[Migration] Adding column: {col_name}")
                cursor.execute(sql)
                added += 1
        
        conn.commit()
        print(f"[Migration] Done! Added {added} new columns.")
        
    except Exception as e:
        print(f"[Migration] Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

