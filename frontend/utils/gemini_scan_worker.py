"""Gemini AI Scan Worker for extracting vocabulary from images.

This module provides a QThread-based worker that calls Google Gemini API
to extract Japanese vocabulary from images without blocking the UI thread.
"""
import json
import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtCore import QObject, Signal, QThread

from frontend.services.ai_service import get_config_manager


class GeminiScanWorker(QObject):
    """Worker that runs Gemini API calls in a separate thread."""
    
    # Signals
    # Updated: scan_finished now emits a tuple (vocab_list, model_name_used)
    # This allows the UI to know which model succeeded and prioritize it next time.
    scan_finished = Signal(object)      
    scan_error = Signal(str)          
    scan_progress = Signal(str)       
    
    # Prompt for Gemini to extract vocabulary
    EXTRACTION_PROMPT = """Bạn là một trợ lý AI chuyên trích xuất từ vựng tiếng Nhật từ hình ảnh.

Hãy phân tích hình ảnh này và trích xuất TẤT CẢ các từ vựng tiếng Nhật có trong ảnh.

Với mỗi từ, hãy cung cấp:
1. **kanji**: Chữ Kanji (nếu có), nếu không có thì để trống
2. **furigana**: Cách đọc bằng Hiragana hoặc Katakana
3. **meaning_vi**: Nghĩa tiếng Việt
4. **sino_vietnamese**: Âm Hán Việt (nếu có Kanji)

Trả về kết quả dưới dạng JSON array, ví dụ:
```json
[
    {
        "kanji": "日本語",
        "furigana": "にほんご",
        "meaning_vi": "Tiếng Nhật",
        "sino_vietnamese": "Nhật Bản Ngữ"
    },
    {
        "kanji": "勉強",
        "furigana": "べんきょう",
        "meaning_vi": "Học tập",
        "sino_vietnamese": "Miễn Cưỡng"
    }
]
```

Nếu không tìm thấy từ vựng tiếng Nhật nào, trả về mảng rỗng: []

CHỈ TRẢ VỀ JSON, KHÔNG CÓ TEXT KHÁC."""

    def __init__(self, image_path: str, api_key: str = None, preferred_model: str = None):
        """Initialize the worker.
        
        Args:
            image_path: Path to the image file to scan
            api_key: Optional API key override (uses config manager if None)
            preferred_model: Name of the model to try first (optimization)
        """
        super().__init__()
        self.image_path = image_path
        self.config_manager = get_config_manager()
        self.api_key = api_key or self.config_manager.api_key
        self.preferred_model = preferred_model
        self._is_cancelled = False
    
    def cancel(self):
        """Request cancellation of the current operation."""
        self._is_cancelled = True
    
    def run(self):
        """Execute the Gemini API call and emit results."""
        try:
            self.scan_progress.emit("Đang khởi tạo Gemini API...")
            
            # --- IMPORT SAFETY BLOCK ---
            try:
                import google.generativeai as genai
            except ImportError:
                # Try to locate the package manually
                try:
                    project_root = Path(__file__).parent.parent.parent
                    potential_paths = [
                        project_root / ".venv" / "Lib" / "site-packages",
                        project_root / "venv" / "Lib" / "site-packages",
                        Path("C:/ProgramData/Sandbox/.venv/Lib/site-packages")
                    ]
                    
                    added = False
                    for p in potential_paths:
                        if p.exists() and str(p) not in sys.path:
                            sys.path.append(str(p))
                            added = True
                    
                    if added:
                        import google.generativeai as genai
                    else:
                        raise ImportError("Could not find site-packages")
                        
                except ImportError as e:
                    self.scan_error.emit(
                        f"Không tìm thấy thư viện google-generativeai.\nLỗi: {e}\n"
                        "Vui lòng chạy: pip install google-generativeai"
                    )
                    return
            
            if self._is_cancelled: return
            
            genai.configure(api_key=self.api_key)
            self.scan_progress.emit("Đang tải hình ảnh...")
            
            image_path = Path(self.image_path)
            if not image_path.exists():
                self.scan_error.emit(f"Không tìm thấy file: {self.image_path}")
                return
            
            import PIL.Image
            image = PIL.Image.open(image_path)
            
            if self._is_cancelled: return
            
            self.scan_progress.emit("Đang phân tích ảnh với AI...")
            
            # --- MODEL SELECTION (From Global Config) ---
            active_models = self.config_manager.active_models
            if not active_models:
                active_models = [
                    "gemini-2.0-flash-exp",
                    "gemini-1.5-flash",
                ]
            
            # Move preferred model to top of list if valid
            models_to_try = list(active_models)
            if self.preferred_model and self.preferred_model in models_to_try:
                models_to_try.remove(self.preferred_model)
                models_to_try.insert(0, self.preferred_model)
            elif self.preferred_model:
                models_to_try.insert(0, self.preferred_model)
            
            response = None
            last_error = None
            success_model = ""
            
            generation_config = genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=4096,
            )

            for model_name in models_to_try:
                if self._is_cancelled: return
                    
                try:
                    self.scan_progress.emit(f"Thử mô hình: {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    
                    response = model.generate_content(
                        [self.EXTRACTION_PROMPT, image],
                        generation_config=generation_config
                    )
                    
                    if response and response.text:
                        success_model = model_name
                        break 
                        
                except Exception as e:
                    error_str = str(e)
                    print(f"[WARNING] Model {model_name} failed: {error_str.splitlines()[0]}")
                    
                    # QUOTA EXCEEDED ROTATION
                    if ("429" in error_str or "quota" in error_str.lower()) and len(self.config_manager.api_keys) > 1:
                        print(f"[GeminiScanWorker] 🚀 Quota exceeded for {model_name}. Rotating key...")
                        if self.config_manager.rotate_api_key():
                            self.api_key = self.config_manager.api_key
                            genai.configure(api_key=self.api_key)
                            print(f"[GeminiScanWorker] 🔄 Rotated! Retrying model {model_name}...")
                            # Retry SAME model once
                            try:
                                response = model.generate_content(
                                    [self.EXTRACTION_PROMPT, image],
                                    generation_config=generation_config
                                )
                                if response and response.text:
                                    success_model = model_name
                                    break
                            except Exception as retry_e:
                                print(f"[GeminiScanWorker] ! Retry failed: {retry_e}")
                    
                    last_error = e
            
            if not response:
                error_msg = str(last_error) if last_error else "Tất cả các mô hình đều thất bại"
                if "429" in error_msg or "quota" in error_msg.lower():
                     error_msg = "Hết hạn mức API (Quota exceeded). Vui lòng đổi API Key hoặc chờ model reset."
                
                self.scan_error.emit(f"Lỗi: {error_msg}")
                return
            
            self.scan_progress.emit(f"Thành công ({success_model}). Đang xử lý...")
            
            vocab_list = self._parse_response(response.text)
            
            if vocab_list is not None:
                # Emit result AND the successful model name
                self.scan_finished.emit((vocab_list, success_model))
            else:
                self.scan_error.emit("Không thể phân tích kết quả từ AI")
                
        except Exception as e:
            import traceback
            print(f"[ERROR GeminiScanWorker] {str(e)}\n{traceback.format_exc()}")
            self.scan_error.emit(str(e))
    
    def _parse_response(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """Parse the Gemini API response to extract vocabulary list."""
        try:
            text = response_text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            text = text.strip()
            
            try:
                result = json.loads(text)
                if isinstance(result, list): return self._validate(result)
            except json.JSONDecodeError: pass
            
            json_match = re.search(r'\[[\s\S]*\]', text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    if isinstance(result, list): return self._validate(result)
                except json.JSONDecodeError: pass
            
            return []
        except Exception: return None
    
    def _validate(self, vocab_list: List[Dict]) -> List[Dict[str, Any]]:
        """Validate and normalize vocabulary list."""
        validated = []
        for item in vocab_list:
            if not isinstance(item, dict): continue
            
            v_item = {
                "kanji": str(item.get("kanji", "")).strip(),
                "furigana": str(item.get("furigana", "")).strip(),
                "meaning_vi": str(item.get("meaning_vi", "")).strip(),
                "sino_vietnamese": str(item.get("sino_vietnamese", "")).strip(),
            }
            if v_item["kanji"] or v_item["furigana"]:
                validated.append(v_item)
        return validated
