import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import sqlite3
import os

db_path = "db/app.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(listening_items)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "vocabulary" not in columns:
        print("Adding 'vocabulary' column to listening_items")
        cursor.execute("ALTER TABLE listening_items ADD COLUMN vocabulary JSON")
    
    if "translation" not in columns:
        print("Adding 'translation' column to listening_items")
        cursor.execute("ALTER TABLE listening_items ADD COLUMN translation TEXT")
        
    if "analysis" not in columns:
        print("Adding 'analysis' column to listening_items")
        cursor.execute("ALTER TABLE listening_items ADD COLUMN analysis JSON")
        
    conn.commit()
    conn.close()
    print("Migration completed.")
else:
    print(f"Database not found at {db_path}")

