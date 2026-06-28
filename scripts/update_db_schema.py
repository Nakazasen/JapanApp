
"""Update database schema to add all missing columns."""
import sys
import os
sys.path.append(os.getcwd())

from sqlmodel import Session, text
from frontend.core.database import engine

def upgrade_db():
    print("Checking database schema...")
    with Session(engine) as session:
        # ==========================================
        # 1. jp_vocab_items
        # ==========================================
        _add_column_if_missing(session, "jp_vocab_items", "source_material", "VARCHAR")
        _add_column_if_missing(session, "jp_vocab_items", "mastery_status", "VARCHAR DEFAULT 'new'")
        _add_column_if_missing(session, "jp_vocab_items", "topic_id", "INTEGER")
        _add_column_if_missing(session, "jp_vocab_items", "tags", "VARCHAR")
        
        # ==========================================
        # 2. en_vocab_items
        # ==========================================
        _add_column_if_missing(session, "en_vocab_items", "source_material", "VARCHAR")
        _add_column_if_missing(session, "en_vocab_items", "mastery_status", "VARCHAR DEFAULT 'new'")
        _add_column_if_missing(session, "en_vocab_items", "topic_id", "INTEGER")
        _add_column_if_missing(session, "en_vocab_items", "tags", "VARCHAR")

        # ==========================================
        # 3. grammar_topics
        # ==========================================
        _add_column_if_missing(session, "grammar_topics", "user_id", "INTEGER", index=True)
        _add_column_if_missing(session, "grammar_topics", "lang", "VARCHAR DEFAULT 'jp'")
        _add_column_if_missing(session, "grammar_topics", "pattern", "VARCHAR")
        _add_column_if_missing(session, "grammar_topics", "usage_notes", "VARCHAR")
        _add_column_if_missing(session, "grammar_topics", "common_mistakes", "VARCHAR")
        _add_column_if_missing(session, "grammar_topics", "category_id", "INTEGER", index=True)
        _add_column_if_missing(session, "grammar_topics", "level", "VARCHAR")
        _add_column_if_missing(session, "grammar_topics", "source_material", "VARCHAR")
        _add_column_if_missing(session, "grammar_topics", "mastery_status", "VARCHAR DEFAULT 'new'")
        _add_column_if_missing(session, "grammar_topics", "tags", "VARCHAR")
        _add_column_if_missing(session, "grammar_topics", "source_url", "VARCHAR")
        _add_column_if_missing(session, "grammar_topics", "is_bookmarked", "BOOLEAN DEFAULT 0")
        _add_column_if_missing(session, "grammar_topics", "last_reviewed_at", "DATETIME")
        _add_column_if_missing(session, "grammar_topics", "created_at", "DATETIME")
        _add_column_if_missing(session, "grammar_topics", "last_updated", "DATETIME")

        # ==========================================
        # 4. study_history
        # ==========================================
        _add_column_if_missing(session, "study_history", "study_date", "DATETIME")
        _add_column_if_missing(session, "study_history", "words_reviewed", "INTEGER DEFAULT 0")

        session.commit()
    print("Database schema update complete.")

def _add_column_if_missing(session, table, column, col_type, index=False):
    try:
        session.exec(text(f"SELECT {column} FROM {table} LIMIT 1"))
        print(f"✅ {table}.{column} already exists.")
    except Exception:
        print(f"🛠 Adding {column} to {table}...")
        try:
            session.exec(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            if index:
                 session.exec(text(f"CREATE INDEX ix_{table}_{column} ON {table} ({column})"))
            print(f"   -> Added.")
        except Exception as e:
            print(f"   -> Error adding column: {e}")

if __name__ == "__main__":
    upgrade_db()
