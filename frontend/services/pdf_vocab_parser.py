import pdfplumber
import re
from typing import List, Dict, Any, Optional

class PDFVocabParser:
    """Service to parse vocabulary from PDF files."""
    
    def extract_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract vocabulary items from PDF.
        
        Tries to identify:
        1. Tables with headers like "Word", "Meaning", etc.
        2. Text lines with consistent spacing/structure if no tables found.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of dicts with keys: word, meaning, example, type, etc.
        """
        items = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # Strategy 1: Table Extraction (Best for structured lists)
                    tables = page.extract_tables()
                    for table in tables:
                        headers = None
                        for row in table:
                            # Skip empty rows
                            if not any(row):
                                continue
                                
                            # Clean row data
                            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                            
                            # Detect header
                            if not headers:
                                if self._is_header_row(cleaned_row):
                                    headers = self._map_headers(cleaned_row)
                                    continue
                                # If no header found yet, treat first row as data if it looks like vocab
                                elif self._is_vocab_row(cleaned_row):
                                    # Guess headers based on position
                                    headers = self._guess_headers_by_position(len(cleaned_row))
                            
                            if headers:
                                item = self._parse_row_with_headers(cleaned_row, headers)
                                if item and item.get("word"):
                                    items.append(item)
                    
                    # Strategy 2: Text Line Extraction (Fallback)
                    if not items:
                        text = page.extract_text()
                        if text:
                            lines = text.split('\n')
                            for line in lines:
                                item = self._parse_text_line(line)
                                if item:
                                    items.append(item)
                                    
        except Exception as e:
            print(f"[PDFVocabParser] Error extracting from PDF: {e}")
            return []
            
        return items

    def _is_header_row(self, row: List[str]) -> bool:
        """Check if row looks like a header."""
        keywords = ["word", "term", "meaning", "definition", "nghĩa", "từ vựng", "ví dụ", "example"]
        text = " ".join(row).lower()
        return any(k in text for k in keywords)

    def _map_headers(self, row: List[str]) -> Dict[int, str]:
        """Map column index to field name."""
        mapping = {}
        for idx, col in enumerate(row):
            text = col.lower()
            if "word" in text or "term" in text or "từ" in text or "vocabulary" in text:
                mapping[idx] = "word"
            elif "mean" in text or "def" in text or "nghĩa" in text or "giải thích" in text:
                mapping[idx] = "meaning"
            elif "exam" in text or "ví dụ" in text or "câu" in text:
                mapping[idx] = "example"
            elif "type" in text or "pos" in text or "loại" in text:
                mapping[idx] = "pos"
            elif "pron" in text or "phiên" in text or "ipa" in text:
                mapping[idx] = "reading"
        return mapping

    def _guess_headers_by_position(self, col_count: int) -> Dict[int, str]:
        """Guess headers if none found, based on common layouts."""
        if col_count == 2:
            return {0: "word", 1: "meaning"}
        elif col_count == 3:
            return {0: "word", 1: "pos", 2: "meaning"} # Or Word, Meaning, Example
        elif col_count >= 4:
            return {0: "word", 1: "reading", 2: "pos", 3: "meaning"}
        return {0: "word", 1: "meaning"} # Default

    def _parse_row_with_headers(self, row: List[str], headers: Dict[int, str]) -> Optional[Dict[str, Any]]:
        """Parse a row using header mapping."""
        item = {}
        has_word = False
        
        for idx, val in enumerate(row):
            if idx in headers:
                field = headers[idx]
                item[field] = val
                if field == "word" and val:
                    has_word = True
        
        # If no explicit mapping caught it, maybe try filling specific fields
        if not has_word and len(row) > 0 and row[0]:
             item["word"] = row[0]
             has_word = True
             
        if has_word:
            return item
        return None

    def _parse_text_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a plain text line (e.g., 'apple - quả táo')."""
        line = line.strip()
        if not line:
            return None
            
        # Common separators: " - ", ": ", tab
        separators = [" - ", " : ", "\t", "   "] # 3 spaces
        
        for sep in separators:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    return {
                        "word": parts[0].strip(),
                        "meaning": parts[1].strip()
                    }
        return None
