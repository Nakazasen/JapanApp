import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import sqlite3
import os

def migrate():
    """Add transcript column to toeic_questions table."""
    # Assume script is run from project root
    project_root = os.getcwd()
    db_path = os.path.join(project_root, "db", "app.db")
    
    if not os.path.exists(db_path):
        # Fallback for different CWD
        db_path = os.path.join(project_root, "EnglishApp", "db", "app.db")
        if not os.path.exists(db_path):
             print(f"Database not found at {db_path} or relative to {project_root}")
             return

    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Adding transcript column to toeic_questions...")
        cursor.execute("ALTER TABLE toeic_questions ADD COLUMN transcript TEXT")
        print("Success!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'transcript' already exists.")
        else:
            print(f"Error: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()

