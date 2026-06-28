import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Import extracted English Grammar into database.

Usage:
    python scripts/import_english_grammar.py
    python scripts/import_english_grammar.py --book intermediate
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.core.database import get_session
from frontend.services.grammar_fetcher_service import GrammarFetcherService
from frontend.models.grammar import GrammarCategory


# Category definitions with icons
CATEGORIES = {
    "Tenses": {"icon": "竢ｰ", "description": "Past, Present, Future tenses and aspects"},
    "Modal Verbs": {"icon": "潮", "description": "Can, could, should, must, might, etc."},
    "Conditionals": {"icon": "笶・, "description": "If clauses and conditional sentences"},
    "Passive Voice": {"icon": "売", "description": "Passive constructions"},
    "Reported Speech": {"icon": "町", "description": "Indirect speech patterns"},
    "Articles & Determiners": {"icon": "東", "description": "A, an, the, some, any, etc."},
    "Prepositions": {"icon": "桃", "description": "In, on, at, by, for, etc."},
    "Relative Clauses": {"icon": "迫", "description": "Who, which, that, where clauses"},
    "Gerunds & Infinitives": {"icon": "統", "description": "Verb + -ing and to + verb patterns"},
    "Adjectives & Adverbs": {"icon": "耳", "description": "Adjectives, adverbs, comparatives"},
    "Nouns & Pronouns": {"icon": "側", "description": "Nouns, pronouns, countable/uncountable"},
    "Questions": {"icon": "笶・, "description": "Question forms and wh- words"},
    "Other Grammar": {"icon": "答", "description": "Other grammar topics"},
}


def ensure_categories(session) -> dict:
    """Create categories if they don't exist. Returns category name -> id mapping."""
    category_ids = {}
    
    for name, data in CATEGORIES.items():
        # Check existing
        existing = session.exec(
            GrammarCategory.__table__.select().where(
                GrammarCategory.name == name,
                GrammarCategory.lang == "en"
            )
        ).first()
        
        if existing:
            category_ids[name] = existing.id
        else:
            new_cat = GrammarCategory(
                name=name,
                lang="en",
                icon=data["icon"],
                description=data["description"],
                is_system=True
            )
            session.add(new_cat)
            session.flush()
            category_ids[name] = new_cat.id
    
    session.commit()
    return category_ids


def import_grammar_file(file_path: Path, service: GrammarFetcherService, session, category_ids: dict) -> dict:
    """Import a single JSON grammar file."""
    if not file_path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        units = json.load(f)
    
    # Map category names to IDs
    for unit in units:
        cat_name = unit.get("category", "Other Grammar")
        unit["category_id"] = category_ids.get(cat_name)
        unit["source"] = unit.get("source_material", "")
    
    result = service.bulk_import(
        items=units,
        lang="en",
        session=session,
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Import English Grammar into database')
    parser.add_argument('--book', choices=['essential', 'intermediate', 'advanced', 'all'],
                        default='all', help='Which book to import')
    
    args = parser.parse_args()
    
    data_dir = project_root / "data" / "english_grammar"
    
    files = {
        "essential": data_dir / "english_grammar_essential.json",
        "intermediate": data_dir / "english_grammar_intermediate.json",
        "advanced": data_dir / "english_grammar_advanced.json",
    }
    
    books_to_import = list(files.keys()) if args.book == 'all' else [args.book]
    
    service = GrammarFetcherService()
    
    with get_session() as session:
        # Ensure categories exist
        print("Creating/checking categories...")
        category_ids = ensure_categories(session)
        print(f"  {len(category_ids)} categories ready")
        
        # Import each book
        total_imported = 0
        for book_key in books_to_import:
            file_path = files[book_key]
            print(f"\nImporting: {file_path.name}")
            
            result = import_grammar_file(file_path, service, session, category_ids)
            
            if result.get("success"):
                imported = result.get("imported", 0)
                skipped = result.get("skipped", 0)
                total_imported += imported
                print(f"  笨・Imported: {imported}, Skipped (duplicates): {skipped}")
                if result.get("errors"):
                    print(f"  笞・・Errors: {len(result['errors'])}")
            else:
                print(f"  笶・Failed: {result.get('error')}")
    
    print(f"\n{'='*40}")
    print(f"TOTAL IMPORTED: {total_imported} grammar units")
    print("Done! Check the Grammar tab (English) in the app.")


if __name__ == "__main__":
    main()

