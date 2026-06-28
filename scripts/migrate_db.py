import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import sqlite3
import os

db_path = r"C:\ProgramData\Sandbox\Projects\EnglishApp\db\app.db"

print(f"Connecting to {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Adding audio_path to listening_questions...")
    cursor.execute("ALTER TABLE listening_questions ADD COLUMN audio_path TEXT")
except sqlite3.OperationalError as e:
    print(f"Notice: {e}")

try:
    print("Adding transcript to listening_questions...")
    cursor.execute("ALTER TABLE listening_questions ADD COLUMN transcript TEXT")
except sqlite3.OperationalError as e:
    print(f"Notice: {e}")

conn.commit()
conn.close()
print("Migration completed.")

