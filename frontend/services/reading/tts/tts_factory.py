"""
Factory để tạo TTS engine phù hợp
"""
from typing import Optional
from .tts_engine import TTSEngine
from .pyttsx3_engine import Pyttsx3Engine
from .gtts_engine import GTTSEngine

class TTSFactory:
    """Factory để tạo TTS engine"""
    
    @staticmethod
    def create_engine(engine_type: str = "pyttsx3", **kwargs) -> Optional[TTSEngine]:
        """Tạo TTS engine phù hợp"""
        engine_type = engine_type.lower()
        
        if engine_type == "pyttsx3":
            try:
                return Pyttsx3Engine()
            except Exception as e:
                print(f"Không thể khởi tạo pyttsx3: {e}")
                return None
        
        elif engine_type == "gtts" or engine_type == "google":
            try:
                lang = kwargs.get("lang", "vi")
                engine = GTTSEngine(lang=lang)
                print(f"Đã khởi tạo Google TTS với ngôn ngữ: {lang}")
                return engine
            except Exception as e:
                print(f"Không thể khởi tạo Google TTS: {e}")
                print("Lưu ý: Google TTS cần kết nối internet")
                return None
        
        else:
            raise ValueError(f"TTS engine không được hỗ trợ: {engine_type}")

    @staticmethod
    def get_available_voices(engine_type: str = "pyttsx3"):
        """Lấy danh sách giọng đọc có sẵn cho từng engine."""
        engine_type = engine_type.lower()
        
        if engine_type == "pyttsx3":
            return Pyttsx3Engine.list_voices()
        elif engine_type in ["gtts", "google"]:
            # Google TTS hiện chỉ dùng giọng mặc định tiếng Việt
            return [{
                "id": "gtts_vi",
                "name": "Google TTS (vi-VN)",
                "lang": "vi-VN",
                "provider": "Google"
            }]
        else:
            return []

