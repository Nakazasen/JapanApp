"""
Text-to-Speech Engine
Hỗ trợ nhiều engine TTS khác nhau
"""
from abc import ABC, abstractmethod
from typing import Optional
import threading

class TTSEngine(ABC):
    """Lớp cơ sở cho TTS engine"""
    
    def __init__(self):
        self.is_speaking = False
        self.is_paused = False
        self._stop_event = threading.Event()
    
    @abstractmethod
    def speak(self, text: str):
        """Đọc văn bản"""
        pass
    
    @abstractmethod
    def stop(self):
        """Dừng đọc"""
        pass
    
    @abstractmethod
    def pause(self):
        """Tạm dừng"""
        pass
    
    @abstractmethod
    def resume(self):
        """Tiếp tục"""
        pass
    
    @abstractmethod
    def set_rate(self, rate: int):
        """Thiết lập tốc độ đọc (words per minute)"""
        pass
    
    @abstractmethod
    def set_voice(self, voice_type: str):
        """Thiết lập giọng đọc (male/female)"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> list:
        """Lấy danh sách giọng có sẵn"""
        pass

