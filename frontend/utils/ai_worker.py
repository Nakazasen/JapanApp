
"""
AI Worker - Async Thread Handler for EnglishApp
===============================================
Prevents UI freezing during AI API calls using QThread.
"""

from PySide6.QtCore import QThread, Signal
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AIWorker(QThread):
    """
    Background worker for AI API calls in EnglishApp.
    
    Signals:
        result_ready(str, str, str): Emits (response_text, model_used, status)
        progress_update(str): Emits status updates
    """
    
    result_ready = Signal(str, str, str)
    progress_update = Signal(str)
    
    def __init__(self, prompt: str, image: Optional[object] = None, api_key: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.image = image
        self.api_key = api_key
        self._is_cancelled = False
    
    def run(self):
        """Execute the AI request in background thread."""
        try:
            self.progress_update.emit("🔄 Đang kết nối AI...")
            
            from frontend.services.ai_service import get_ai_service
            
            if self._is_cancelled:
                return
            
            service = get_ai_service(self.api_key)
            
            self.progress_update.emit("🤖 Đang xử lý...")
            
            if self._is_cancelled:
                return
            
            if self._is_cancelled:
                return
            
            result = service.generate_response(self.prompt, self.image)
            
            if self._is_cancelled:
                return
            
            self.result_ready.emit(
                result.get('text', ''), 
                result.get('model_used', ''), 
                result.get('status', 'error')
            )
                
        except Exception as e:
            logger.exception("AI Worker error")
            self.result_ready.emit(
                f"❌ Lỗi: {str(e)}",
                "Error",
                "error"
            )
    
    def cancel(self):
        self._is_cancelled = True
