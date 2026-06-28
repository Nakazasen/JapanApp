import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""Check what OCR returns from sample pages."""
import fitz
import pytesseract
import sys
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PDF_PATH = r"C:\Users\Admin\Downloads\HACKERS TOEIC.pdf"

doc = fitz.open(PDF_PATH)

# Check pages 50-70 (vocabulary section likely starts here)
for page_num in [50, 60, 70, 80, 90, 100]:
    page = doc[page_num]
    mat = fitz.Matrix(150/72, 150/72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img, lang='eng')
    
    print(f"\n{'='*60}")
    print(f"PAGE {page_num + 1}")
    print('='*60)
    # Safe print
    safe_text = text.encode('ascii', 'ignore').decode('ascii')
    print(safe_text[:1000])
    print("...")

doc.close()

