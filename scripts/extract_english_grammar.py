import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Extract English Grammar from Grammar in Use PDF books.

Usage:
    python scripts/extract_english_grammar.py --book essential
    python scripts/extract_english_grammar.py --book intermediate
    python scripts/extract_english_grammar.py --book advanced
    python scripts/extract_english_grammar.py --all
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import pdfplumber

# Book configurations
BOOKS = {
    "essential": {
        "file": "Essential Grammar in Use 4th Edition by R. Murphy.pdf",
        "level": "A1-A2",
        "source": "Essential Grammar in Use (Murphy)",
        "toc_pages": (4, 5),  # Table of contents pages
        "content_start": 8,   # First unit page
    },
    "intermediate": {
        "file": "english-grammar-in-use-intermediate.pdf",
        "level": "B1-B2",
        "source": "English Grammar in Use (Murphy)",
        "toc_pages": (4, 6),
        "content_start": 8,
    },
    "advanced": {
        "file": "Advanced grammar in use 3rd_Edition.pdf",
        "level": "C1-C2",
        "source": "Advanced Grammar in Use (Murphy)",
        "toc_pages": (4, 6),
        "content_start": 8,
    }
}

# Category mapping based on content keywords
CATEGORY_KEYWORDS = {
    "Tenses": ["present", "past", "future", "perfect", "continuous", "progressive", "simple"],
    "Modal Verbs": ["can", "could", "may", "might", "must", "should", "would", "shall", "will", "modal"],
    "Conditionals": ["if ", "conditional", "unless", "would have", "wish"],
    "Passive Voice": ["passive", "by (someone)", "get done", "have something done"],
    "Reported Speech": ["reported", "said that", "told", "indirect speech"],
    "Articles & Determiners": ["a/an", "the", "a, an", "some", "any", "no", "none", "article", "determiner"],
    "Prepositions": ["preposition", "in, at, on", "by, until", "for, during", "in/at/on"],
    "Relative Clauses": ["relative", "who", "which", "that", "whose", "whom", "where", "clause"],
    "Nouns & Pronouns": ["noun", "pronoun", "countable", "uncountable", "plural", "singular"],
    "Adjectives & Adverbs": ["adjective", "adverb", "-ly", "comparative", "superlative", "-er", "-est"],
    "Conjunctions": ["and", "but", "or", "so", "because", "although", "conjunction", "linking"],
    "Gerunds & Infinitives": ["gerund", "infinitive", "-ing", "to + verb", "verb + -ing"],
    "Questions": ["question", "wh-", "do/does", "did", "interrogative"],
    "Negation": ["not", "n't", "negative", "never", "no one", "nothing"],
}


def detect_category(title: str, content: str) -> str:
    """Detect grammar category based on title and content keywords."""
    text = (title + " " + content).lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return category
    
    return "Other Grammar"


def clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ""
    # Remove page numbers
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    # Remove header/footer artifacts
    text = re.sub(r'ENGLISH GRAMMAR IN USE.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Unit \d+\s*\n', '', text)
    # Clean whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_examples(text: str) -> list:
    """Extract example sentences from text."""
    examples = []
    
    # Look for patterns like "• example" or "- example" or numbered examples
    patterns = [
        r'[•●○]\s*(.+?)(?=\n|$)',
        r'^\s*[-–—]\s*(.+?)(?=\n|$)',
        r'^\s*\d+[.)]\s*(.+?)(?=\n|$)',
        r"'([^']+)'",  # Quoted examples
        r'"([^"]+)"',  # Double-quoted examples
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for match in matches:
            if len(match) > 10 and len(match) < 200:  # Reasonable sentence length
                examples.append(match.strip())
    
    # Deduplicate and limit
    seen = set()
    unique_examples = []
    for ex in examples:
        if ex not in seen and len(unique_examples) < 5:
            seen.add(ex)
            unique_examples.append(ex)
    
    return unique_examples


def parse_unit(page_text: str, unit_num: int, book_config: dict) -> dict | None:
    """Parse a single unit page and extract grammar content."""
    if not page_text or len(page_text) < 100:
        return None
    
    # Try to extract unit title (usually at the top)
    title_match = re.search(r'^(.+?)(?:\n|$)', page_text)
    if not title_match:
        return None
    
    title = title_match.group(1).strip()
    
    # Skip if this looks like an exercises page or appendix
    if re.search(r'^Exercises?\s*$|^Appendix|^Additional|^Key\s*$', title, re.IGNORECASE):
        return None
    
    # Clean and truncate title
    title = re.sub(r'^\d+\s*', '', title)  # Remove leading numbers
    if len(title) > 100:
        title = title[:100]
    
    # Get main content (first ~60% of page is usually explanation)
    lines = page_text.split('\n')
    explanation_lines = lines[1:int(len(lines) * 0.6)]
    explanation = '\n'.join(explanation_lines)
    explanation = clean_text(explanation)
    
    # Extract examples
    examples = extract_examples(page_text)
    
    # Detect category
    category = detect_category(title, explanation)
    
    return {
        "unit": unit_num,
        "title": title,
        "pattern": "",  # Will be filled from title/first line
        "description": explanation[:2000] if len(explanation) > 2000 else explanation,
        "usage_notes": "",
        "common_mistakes": "",
        "level": book_config["level"],
        "source_material": book_config["source"],
        "category": category,
        "examples": examples,
        "lang": "en"
    }


def extract_from_toc(pdf, toc_pages: tuple) -> list:
    """Try to extract unit info from Table of Contents."""
    units = []
    
    for page_num in range(toc_pages[0], toc_pages[1] + 1):
        if page_num >= len(pdf.pages):
            continue
        
        text = pdf.pages[page_num].extract_text()
        if not text:
            continue
        
        # Look for "Unit X Title" patterns
        matches = re.findall(r'(\d+)\s+([A-Z][^0-9\n]{5,50})', text)
        for unit_num, title in matches:
            units.append({
                "unit": int(unit_num),
                "title": title.strip()
            })
    
    return units


def extract_book(book_key: str, data_dir: Path, dry_run: bool = False) -> list:
    """Extract grammar content from a single book."""
    if book_key not in BOOKS:
        print(f"Unknown book: {book_key}")
        return []
    
    config = BOOKS[book_key]
    pdf_path = data_dir / config["file"]
    
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        return []
    
    print(f"\n{'='*60}")
    print(f"Extracting: {config['source']}")
    print(f"Level: {config['level']}")
    print(f"PDF: {pdf_path.name}")
    print(f"{'='*60}")
    
    grammar_units = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        
        if dry_run:
            # Just test first few pages
            test_pages = min(10, total_pages)
            print(f"[DRY RUN] Testing first {test_pages} pages...")
        else:
            test_pages = total_pages
        
        # Try TOC first
        toc_units = extract_from_toc(pdf, config["toc_pages"])
        if toc_units:
            print(f"Found {len(toc_units)} units in TOC")
        
        # Process content pages
        unit_num = 1
        for page_idx in range(config["content_start"], test_pages):
            if page_idx >= total_pages:
                break
            
            try:
                page_text = pdf.pages[page_idx].extract_text()
                unit_data = parse_unit(page_text, unit_num, config)
                
                if unit_data and unit_data["title"]:
                    grammar_units.append(unit_data)
                    unit_num += 1
                    
                    if unit_num % 20 == 0:
                        print(f"  Extracted {unit_num} units...")
                        
            except Exception as e:
                print(f"  Error on page {page_idx}: {e}")
                continue
    
    print(f"\nExtracted {len(grammar_units)} grammar units from {config['source']}")
    return grammar_units


def main():
    parser = argparse.ArgumentParser(description='Extract English Grammar from PDF books')
    parser.add_argument('--book', choices=['essential', 'intermediate', 'advanced', 'all'],
                        default='all', help='Which book to extract')
    parser.add_argument('--dry-run', action='store_true',
                        help='Only test parsing on first few pages')
    parser.add_argument('--data-dir', type=str, default='data',
                        help='Path to data directory')
    
    args = parser.parse_args()
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / args.data_dir
    output_dir = data_dir / "english_grammar"
    output_dir.mkdir(exist_ok=True)
    
    books_to_process = ['essential', 'intermediate', 'advanced'] if args.book == 'all' else [args.book]
    
    all_results = {}
    
    for book_key in books_to_process:
        units = extract_book(book_key, data_dir, args.dry_run)
        
        if units:
            output_file = output_dir / f"english_grammar_{book_key}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(units, f, ensure_ascii=False, indent=2)
            print(f"Saved to: {output_file}")
            all_results[book_key] = len(units)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for book, count in all_results.items():
        print(f"  {book}: {count} units")
    print(f"  Total: {sum(all_results.values())} units")


if __name__ == "__main__":
    main()

