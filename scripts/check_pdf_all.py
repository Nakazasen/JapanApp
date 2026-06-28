import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Check PDF structure - check all pages for content."""
import pdfplumber

pdf_path = r"C:\Users\Admin\Downloads\HACKERS TOEIC.pdf"

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    # Check all pages for text content
    pages_with_text = 0
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text and text.strip():
            pages_with_text += 1
            if pages_with_text <= 5:  # Show first 5 pages with text
                print(f"\n{'='*60}")
                print(f"PAGE {i+1} (has content)")
                print('='*60)
                print(text[:1500])
    
    print(f"\n\nTotal pages with text: {pages_with_text}")

