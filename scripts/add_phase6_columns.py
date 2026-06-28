"""Migration script to add Phase 06 columns to toeic_questions."""
import sqlite3
import os

DB_PATH = "data/english_app.db" # Standard path based on project conventions
# Or find it dynamically. config.yaml usually has it.
# Taking a guess based on file list: db_temp.db is large (131MB).
# But usually it's in data/ or root.
# Let's check where the app connects.

# From previous logs or model:
# frontend/core/database.py handles this.
# I'll rely on SqlAlchemy to get the engine URL or just try known paths.
# But for safety, I will use SQLAlchemy raw connection from the codebase.

import sys
sys.path.append(os.getcwd())
from frontend.core.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Checking columns...")
        # Check if columns exist to avoid error
        result = conn.execute(text("PRAGMA table_info(toeic_questions)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "transcript" not in columns:
            print("Adding transcript column...")
            try:
                conn.execute(text("ALTER TABLE toeic_questions ADD COLUMN transcript TEXT"))
                print("Added transcript.")
            except Exception as e:
                print(f"Error adding transcript: {e}")
        else:
            print("transcript column already exists.")
            
        if "question_set_id" not in columns:
            print("Adding question_set_id column...")
            try:
                conn.execute(text("ALTER TABLE toeic_questions ADD COLUMN question_set_id INTEGER"))
                conn.execute(text("CREATE INDEX ix_toeic_questions_question_set_id ON toeic_questions (question_set_id)"))
                print("Added question_set_id.")
            except Exception as e:
                print(f"Error adding question_set_id: {e}")
        else:
            print("question_set_id column already exists.")
            
        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
