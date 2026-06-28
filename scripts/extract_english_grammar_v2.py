import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Extract English Grammar from Grammar in Use PDF books - Optimized version.
Uses TOC extraction and batch processing for faster results.

Usage:
    python scripts/extract_english_grammar_v2.py --book intermediate
    python scripts/extract_english_grammar_v2.py --all
"""

import argparse
import json
import re
from pathlib import Path

import pdfplumber

# Book configurations
BOOKS = {
    "essential": {
        "file": "Essential Grammar in Use 4th Edition by R. Murphy.pdf",
        "level": "A1-A2",
        "source": "Essential Grammar in Use (Murphy)",
    },
    "intermediate": {
        "file": "english-grammar-in-use-intermediate.pdf",
        "level": "B1-B2",
        "source": "English Grammar in Use (Murphy)",
    },
    "advanced": {
        "file": "Advanced grammar in use 3rd_Edition.pdf",
        "level": "C1-C2",
        "source": "Advanced Grammar in Use (Murphy)",
    }
}

# Grammar categories based on common GIU topics
CATEGORY_MAP = {
    "present": "Tenses",
    "past": "Tenses", 
    "future": "Tenses",
    "perfect": "Tenses",
    "continuous": "Tenses",
    "will": "Tenses",
    "going to": "Tenses",
    "can": "Modal Verbs",
    "could": "Modal Verbs",
    "may": "Modal Verbs",
    "might": "Modal Verbs",
    "must": "Modal Verbs",
    "should": "Modal Verbs",
    "would": "Modal Verbs",
    "have to": "Modal Verbs",
    "if ": "Conditionals",
    "unless": "Conditionals",
    "wish": "Conditionals",
    "conditional": "Conditionals",
    "passive": "Passive Voice",
    "reported": "Reported Speech",
    "said": "Reported Speech",
    "told": "Reported Speech",
    "a/an": "Articles & Determiners",
    "the": "Articles & Determiners",
    "some": "Articles & Determiners",
    "any": "Articles & Determiners",
    "preposition": "Prepositions",
    "in/at/on": "Prepositions",
    "by/until": "Prepositions",
    "relative": "Relative Clauses",
    "who": "Relative Clauses",
    "which": "Relative Clauses",
    "-ing": "Gerunds & Infinitives",
    "to ...": "Gerunds & Infinitives",
    "infinitive": "Gerunds & Infinitives",
    "adjective": "Adjectives & Adverbs",
    "adverb": "Adjectives & Adverbs",
    "comparative": "Adjectives & Adverbs",
    "superlative": "Adjectives & Adverbs",
    "noun": "Nouns & Pronouns",
    "pronoun": "Nouns & Pronouns",
    "countable": "Nouns & Pronouns",
    "question": "Questions",
    "do/does": "Questions",
}


def detect_category(title: str) -> str:
    """Detect grammar category from unit title."""
    title_lower = title.lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in title_lower:
            return category
    return "Other Grammar"


def extract_toc_units(pdf) -> list:
    """Extract unit list from Table of Contents pages."""
    units = []
    
    # Check pages 2-10 for TOC
    for page_idx in range(2, min(10, len(pdf.pages))):
        text = pdf.pages[page_idx].extract_text()
        if not text:
            continue
        
        # Pattern: "1 Present continuous (I am doing)" or similar
        matches = re.findall(r'(\d+)\s+([A-Z][^0-9\n]{3,60})', text)
        for unit_num, title in matches:
            unit_num = int(unit_num)
            title = title.strip()
            # Skip non-grammar entries
            if any(skip in title.lower() for skip in ['appendix', 'answer', 'index', 'contents']):
                continue
            if unit_num > 0 and len(title) > 5:
                units.append({
                    "unit": unit_num,
                    "title": title,
                })
    
    # Remove duplicates by unit number
    seen = set()
    unique = []
    for u in units:
        if u["unit"] not in seen:
            seen.add(u["unit"])
            unique.append(u)
    
    return sorted(unique, key=lambda x: x["unit"])


def build_grammar_data(units: list, book_config: dict) -> list:
    """Build grammar topic data from TOC units."""
    grammar_data = []
    
    for u in units:
        category = detect_category(u["title"])
        
        grammar_data.append({
            "unit": u["unit"],
            "title": u["title"],
            "pattern": "",
            "description": f"Grammar point from {book_config['source']}, Unit {u['unit']}.",
            "usage_notes": "",
            "common_mistakes": "",
            "level": book_config["level"],
            "source_material": book_config["source"],
            "category": category,
            "examples": [],
            "lang": "en"
        })
    
    return grammar_data


def extract_book(book_key: str, data_dir: Path) -> list:
    """Extract grammar content from a single book."""
    config = BOOKS[book_key]
    pdf_path = data_dir / config["file"]
    
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return []
    
    print(f"\nExtracting: {config['source']}")
    print(f"Level: {config['level']}")
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        # Extract from TOC
        units = extract_toc_units(pdf)
        print(f"Found {len(units)} units from TOC")
        
        # Build grammar data
        grammar_data = build_grammar_data(units, config)
        
    return grammar_data


def main():
    parser = argparse.ArgumentParser(description='Extract English Grammar from PDF books (v2)')
    parser.add_argument('--book', choices=['essential', 'intermediate', 'advanced', 'all'],
                        default='all', help='Which book to extract')
    parser.add_argument('--data-dir', type=str, default='data', help='Path to data directory')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    data_dir = project_root / args.data_dir
    output_dir = data_dir / "english_grammar"
    output_dir.mkdir(exist_ok=True)
    
    books = ['essential', 'intermediate', 'advanced'] if args.book == 'all' else [args.book]
    
    results = {}
    for book_key in books:
        units = extract_book(book_key, data_dir)
        if units:
            output_file = output_dir / f"english_grammar_{book_key}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(units, f, ensure_ascii=False, indent=2)
            print(f"Saved: {output_file.name} ({len(units)} units)")
            results[book_key] = len(units)
    
    print(f"\n{'='*40}")
    print("TOTAL:", sum(results.values()), "grammar units extracted")


if __name__ == "__main__":
    main()

