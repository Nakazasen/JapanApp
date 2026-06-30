import os
import sys


def main() -> int:
    """Manual Gemini PDF extraction probe.

    This script performs a live upload and must never run during pytest
    collection. Enable explicitly with RUN_GEMINI_CHUNK_TEST=1.
    """
    if os.getenv("RUN_GEMINI_CHUNK_TEST") != "1":
        print("Skipped: set RUN_GEMINI_CHUNK_TEST=1 to run this live Gemini probe.")
        return 0

    import google.generativeai as genai

    # Setup Gemini
    sys.path.append(os.getcwd())
    from frontend.core.config import settings
    from frontend.services.ai_service import get_config_manager

    ai_config = get_config_manager()
    api_key = ai_config.api_key or settings.gemini_api_key
    if not api_key:
        raise RuntimeError("Missing Gemini API key for manual chunk extraction probe.")
    genai.configure(api_key=api_key)

    pdf_path = os.getenv("GEMINI_CHUNK_TEST_PDF", r"C:\Users\Admin\Downloads\DANH SÁCH TỪ.pdf")
    model_name = os.getenv("GEMINI_CHUNK_TEST_MODEL", "gemini-3-flash-preview")

    print(f"Uploading {pdf_path}...")
    sample_file = genai.upload_file(path=pdf_path)

    model = genai.GenerativeModel(model_name=model_name)

    prompt = """
Extract all English vocabulary words from pages 1 and 2 of this document.
Return a JSON list:
[{"word": "...", "meaning_vi": "...", "example_en": "..."}]
Return ONLY valid JSON.
"""

    print("Analyzing pages 1-2...")
    response = model.generate_content([prompt, sample_file])
    print("Response received.")
    print(response.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
