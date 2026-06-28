import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Inspect PDF Structure.

This script reads the first page of the specified PDF files and prints the text/tables
to help determine the parsing strategy.
"""
import pdfplumber
import sys

FILES = [
    r"C:\Users\Admin\Downloads\DANH SÁCH TỪ.pdf",
    r"C:\Users\Admin\Downloads\120 THÀNH NGỮ + CỤM TỪ.pdf"
]

def inspect_file(path):
    print(f"\n{'='*50}")
    print(f"Inspecting: {path}")
    print(f"{'='*50}")
    
    try:
        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                print("No pages found.")
                return

            page = pdf.pages[0]
            
            print("\n--- Raw Text (First Page) ---")
            text = page.extract_text()
            print(text if text else "[No text extracted]")
            
            print("\n--- Tables (First Page) ---")
            tables = page.extract_tables()
            if tables:
                for idx, table in enumerate(tables):
                    print(f"Table {idx+1}:")
                    for row in table[:3]: # Print first 3 rows
                        print(row)
                    if len(table) > 3:
                        print("...")
            else:
                print("[No tables found]")
                
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    for f in FILES:
        inspect_file(f)

