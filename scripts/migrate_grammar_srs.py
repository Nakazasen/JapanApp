import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import os

db_path = r"C:\ProgramData\Sandbox\Projects\EnglishApp\db\app.db"
print(f"Connecting to database at {db_path}...")

if not os.path.exists(db_path):
    print("Database file NOT found! Check paths.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Update grammar_topics
print("\nChecking grammar_topics table...")
columns_to_add = [
    ("srs_level", "INTEGER DEFAULT 0"),
    ("srs_streak", "INTEGER DEFAULT 0"),
    ("srs_ease_factor", "REAL DEFAULT 2.5"),
    ("srs_interval", "INTEGER DEFAULT 0"),
    ("review_count", "INTEGER DEFAULT 0"),
    ("next_review_at", "DATETIME")
]

for col_name, col_def in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE grammar_topics ADD COLUMN {col_name} {col_def}")
        print(f"  + Added column {col_name} to grammar_topics")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"  - Column {col_name} already exists in grammar_topics")
        else:
            print(f"  ! Error adding {col_name}: {e}")

# Set default values for next_review_at if they were just added
cursor.execute("UPDATE grammar_topics SET next_review_at = CURRENT_TIMESTAMP WHERE next_review_at IS NULL")
print("  + Set default CURRENT_TIMESTAMP for next_review_at")

conn.commit()
conn.close()
print("\nMigration completed successfully.")

