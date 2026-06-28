import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import os

def fix_data():
    db_path = 'db/app.db'
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("--- Starting Final Vocabulary Data Fix ---")

    # 1. Create English Topic for TOEIC 800 if not exists
    c.execute("SELECT id FROM vocab_topics WHERE name = 'TOEIC 800 Vocabulary' AND lang = 'en'")
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO vocab_topics (user_id, name, lang, description) VALUES (1, 'TOEIC 800 Vocabulary', 'en', '700+ TOEIC words imported from JSON')")
        en_topic_id = c.lastrowid
        print(f"・ Created English Topic: 'TOEIC 800 Vocabulary' (ID: {en_topic_id})")
    else:
        en_topic_id = row[0]
        print(f"笨・English Topic exists (ID: {en_topic_id})")

    # 2. Link English items
    c.execute("UPDATE unified_vocab_items SET topic_id = ? WHERE lang = 'en' AND level = 'TOEIC 800'", (en_topic_id,))
    print(f"迫 Linked English items - Rows: {c.rowcount}")

    # 3. Link remaining Japanese N1 items to Topic 4 (Pattern Goi)
    # Check if Topic 4 is indeed Pattern Goi
    c.execute("SELECT name FROM vocab_topics WHERE id = 4")
    t_name = c.fetchone()
    if t_name and 'Pattern Goi' in t_name[0]:
        c.execute("UPDATE unified_vocab_items SET topic_id = 4 WHERE lang = 'jp' AND level = 'N1' AND topic_id IS NULL")
        print(f"迫 Linked remaining Japanese N1 items to Topic 4 - Rows: {c.rowcount}")
    else:
        print(f"笞・・Topic 4 is not Pattern Goi (found: {t_name}). Skipping link.")

    # 4. Verification
    c.execute("SELECT lang, topic_id, COUNT(*) FROM unified_vocab_items GROUP BY lang, topic_id")
    print("\n投 Final Status (lang, topic_id, count):")
    [print(f"  {r}") for r in c.fetchall()]

    conn.commit()
    conn.close()
    print("--- Final Data Fix Completed ---")

if __name__ == "__main__":
    fix_data()

