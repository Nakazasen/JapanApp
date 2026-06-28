import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Script to find specific reading questions in database."""
import sqlite3

conn = sqlite3.connect('db/app.db')
cursor = conn.cursor()

# Find reading items with "Exercise 01" in title
print("=" * 50)
print("Reading Items containing 'Exercise 01':")
print("=" * 50)
cursor.execute("SELECT id, category_id, title FROM reading_items WHERE title LIKE '%Exercise 01%'")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Category: {row[1]}, Title: {row[2]}")

# Find all questions for Exercise01
print("\n" + "=" * 50)
print("Questions for Exercise 01:")
print("=" * 50)
cursor.execute("""
    SELECT rq.id, rq.item_id, rq.question_text, rq.options, rq.correct_option
    FROM reading_questions rq
    JOIN reading_items ri ON rq.item_id = ri.id
    WHERE ri.title LIKE '%Exercise 01%'
""")
for row in cursor.fetchall():
    print(f"\nQuestion ID: {row[0]}, Item ID: {row[1]}")
    print(f"Question: {row[2]}")
    print(f"Options: {row[3]}")
    print(f"Correct: {row[4]}")

# Search for the specific questions
print("\n" + "=" * 50)
print("Searching for '山頁E in questions:")
print("=" * 50)
cursor.execute("SELECT id, item_id, question_text, options FROM reading_questions WHERE question_text LIKE '%山頁E'")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Item: {row[1]}")
    print(f"Question: {row[2]}")
    print(f"Options: {row[3]}")

print("\n" + "=" * 50)
print("Searching for 'プロの楽しみ' in questions:")
print("=" * 50)
cursor.execute("SELECT id, item_id, question_text, options FROM reading_questions WHERE question_text LIKE '%プロの楽しみ%'")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Item: {row[1]}")
    print(f"Question: {row[2]}")
    print(f"Options: {row[3]}")

# Check categories
print("\n" + "=" * 50)
print("Reading Categories (JT4Y N1 Reading):")
print("=" * 50)
cursor.execute("SELECT id, name, level FROM reading_categories WHERE name LIKE '%JT4Y%' OR name LIKE '%N1%'")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Level: {row[2]}")

conn.close()

