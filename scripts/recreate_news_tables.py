import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Recreate news tables with updated schema."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "app.db")

def recreate_tables():
    print(f"[Migration] Connecting to database: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("[Migration] Database file not found!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Drop old tables
        print("[Migration] Dropping old news tables...")
        cursor.execute("DROP TABLE IF EXISTS news_articles")
        cursor.execute("DROP TABLE IF EXISTS news_sources")
        
        # Create new news_sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                url VARCHAR(500) NOT NULL,
                lang VARCHAR(10) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create new news_articles table with all new columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source_id INTEGER,
                title VARCHAR(500) NOT NULL,
                url VARCHAR(1000) UNIQUE NOT NULL,
                source_name VARCHAR(100) DEFAULT 'Unknown',
                author VARCHAR(200),
                summary TEXT,
                content TEXT,
                content_html TEXT,
                language VARCHAR(10) DEFAULT 'en',
                tags TEXT,
                thumbnail_url VARCHAR(1000),
                upvotes INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                stocks INTEGER DEFAULT 0,
                is_read BOOLEAN DEFAULT 0,
                is_saved BOOLEAN DEFAULT 0,
                furigana_title TEXT,
                furigana_content TEXT,
                published_at DATETIME,
                cached_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (source_id) REFERENCES news_sources(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_user ON news_articles(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_source ON news_articles(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_title ON news_articles(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_language ON news_articles(language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_saved ON news_articles(is_saved)")
        
        conn.commit()
        print("[Migration] Successfully recreated news tables with updated schema!")
        
    except Exception as e:
        print(f"[Migration] Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    recreate_tables()

