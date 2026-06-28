
import sys
import os
import pdfplumber

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.services.pdf_vocab_parser import PDFVocabParser
from frontend.services.vocab_service import get_vocab_service, VocabService

def import_pdf(file_path, topic_name):
    print(f"\n--- Importing: {os.path.basename(file_path)} ---")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    try:
        # 1. Parse PDF
        parser = PDFVocabParser()
        print("Parsing PDF... (this might take a moment)")
        items = parser.extract_from_pdf(file_path)
        
        if not items:
            print(f"⚠️ No vocabulary items found in {file_path}. Checking raw text...")
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) > 0:
                    text = pdf.pages[0].extract_text()
                    if text and text.strip():
                        print(f"--- RAW TEXT SAMPLE (Page 1) ---\n{text[:1000]}\n-------------------------------")
                    else:
                        print("❌ No text text extracted. Checking for images...")
                        if pdf.pages[0].images:
                             print(f"⚠️ Page 1 has {len(pdf.pages[0].images)} images. This is likely a SCANNED PDF.")
                        else:
                             print("⚠️ No text and no images found. File might be blank or encrypted.")
                else:
                    print("❌ PDF has no pages.")
            return

        print(f"✅ Extracted {len(items)} items.")
        
        # 2. Get Service
        service = get_vocab_service()
        
        # 3. Create or Find Topic
        # We need a topic ID. Let's list topics first.
        # For simplicity, let's just pick the first topic or create a new one "Imported PDF"
        # Or better, pass topic_name
        
        # Check if topic exists
        existing_topics = service.list_topics("en") # Assuming English
        target_topic = None
        for t in existing_topics:
            if t['name'] == topic_name:
                target_topic = t
                break
        
        if not target_topic:
            print(f"Creating new topic: {topic_name}")
            result = service.create_topic(topic_name, "en", "Imported from PDF")
            if result.get("success"):
                topic_id = result["id"]
            else:
                print(f"❌ Failed to create topic: {result.get('error')}")
                return
        else:
            topic_id = target_topic['id']
            print(f"Using existing topic: {topic_name} (ID: {topic_id})")

        # 4. Bulk Import
        print(f"Importing to database...")
        result = service.bulk_import(
            items=items,
            lang="en",
            default_topic_id=topic_id,
            default_source="PDF Import",
            default_level="Unknown"
        )
        
        if result.get("success"):
            print(f"✅ Success! Imported: {result['imported']}, Skipped: {result['skipped']}, Errors: {len(result['errors'])}")
            if result['errors']:
                print("First 5 errors:")
                for err in result['errors'][:5]:
                    print(f"  - {err}")
        else:
            print(f"❌ Import failed: {result.get('error')}")

    except Exception as e:
        import traceback
        print(f"❌ Critical error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    files = [
        (r"C:\Users\Admin\Downloads\DANH SÁCH TỪ.pdf", "PDF: Danh Sách Từ"),
        (r"C:\Users\Admin\Downloads\120 THÀNH NGỮ + CỤM TỪ.pdf", "PDF: 120 Thành Ngữ")
    ]
    
    for path, topic in files:
        import_pdf(path, topic)
