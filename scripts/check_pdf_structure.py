import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Check PDF structure."""
import pdfplumber

pdf_path = r"C:\Users\Admin\Downloads\HACKERS TOEIC.pdf"

with pdfplumber.open(pdf_path) as pdf:
    # Check first few pages
    for page_num in [10, 11, 12, 13, 14]:
        print(f"\n{'='*60}")
        print(f"PAGE {page_num}")
        print('='*60)
        page = pdf.pages[page_num]
        text = page.extract_text()
        print(text[:2000])  # Print first 2000 chars

