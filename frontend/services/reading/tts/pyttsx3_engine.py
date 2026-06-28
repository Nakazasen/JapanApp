"""
TTS Engine sử dụng pyttsx3 (offline, Windows SAPI)
"""
import pyttsx3
from typing import Optional
from .tts_engine import TTSEngine

class Pyttsx3Engine(TTSEngine):
    """TTS Engine sử dụng pyttsx3"""
    
    def __init__(self):
        super().__init__()
        try:
            self.engine = pyttsx3.init()
            self._init_engine()
        except Exception as e:
            print(f"Không thể khởi tạo pyttsx3: {e}")
            self.engine = None
    
    def _init_engine(self):
        """Khởi tạo cài đặt mặc định"""
        if self.engine:
            self.engine.setProperty('rate', 150)
            self._set_vietnamese_voice()
    
    def _set_vietnamese_voice(self):
        """Tự động tìm và thiết lập giọng tiếng Việt"""
        if not self.engine:
            return
        
        voices = self.engine.getProperty('voices')
        if not voices:
            return
        
        vietnamese_voices = []
        for voice in voices:
            voice_id_lower = voice.id.lower()
            voice_name_lower = voice.name.lower() if hasattr(voice, 'name') else ""
            
            if any(keyword in voice_id_lower or keyword in voice_name_lower 
                   for keyword in ['vietnamese', 'vietnam', 'vi-', 'vi_', 'viet']):
                vietnamese_voices.append(voice)
        
        if vietnamese_voices:
            self.engine.setProperty('voice', vietnamese_voices[0].id)
            print(f"Đã chọn giọng tiếng Việt: {vietnamese_voices[0].name if hasattr(vietnamese_voices[0], 'name') else vietnamese_voices[0].id}")
        else:
            if voices:
                self.engine.setProperty('voice', voices[0].id)
                print(f"Không tìm thấy giọng tiếng Việt, dùng giọng mặc định: {voices[0].name if hasattr(voices[0], 'name') else voices[0].id}")
    
    def speak(self, text: str):
        """Đọc văn bản"""
        if not self.engine:
            print("TTS Engine chưa được khởi tạo")
            return
        
        if self.is_paused:
            self.resume()
        
        self.is_speaking = True
        self._stop_event.clear()
        
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Lỗi khi đọc: {e}")
        finally:
            self.is_speaking = False
    
    def stop(self):
        """Dừng đọc"""
        if self.engine:
            self.engine.stop()
        self.is_speaking = False
        self.is_paused = False
        self._stop_event.set()
    
    def pause(self):
        """Tạm dừng"""
        if self.engine:
            self.engine.stop()
        self.is_paused = True
    
    def resume(self):
        """Tiếp tục"""
        self.is_paused = False
    
    def set_rate(self, rate: int):
        """Thiết lập tốc độ đọc (50-300)"""
        if self.engine:
            self.engine.setProperty('rate', max(50, min(300, rate)))
    
    def set_voice(self, voice_type: str):
        """Thiết lập giọng đọc"""
        if not self.engine:
            return
        
        voices = self.engine.getProperty('voices')
        if not voices:
            return
        
        target_gender = "female" if voice_type.lower() == "female" else "male"
        
        for voice in voices:
            voice_id_lower = voice.id.lower()
            voice_name_lower = voice.name.lower() if hasattr(voice, 'name') else ""
            
            is_vietnamese = any(keyword in voice_id_lower or keyword in voice_name_lower 
                               for keyword in ['vietnamese', 'vietnam', 'vi-', 'vi_', 'viet'])
            
            if is_vietnamese:
                is_female = ("female" in voice_id_lower or "nữ" in voice_id_lower or 
                           "female" in voice_name_lower or "nữ" in voice_name_lower)
                is_male = ("male" in voice_id_lower or "nam" in voice_id_lower or 
                          "male" in voice_name_lower or "nam" in voice_name_lower)
                
                if (target_gender == "female" and is_female) or (target_gender == "male" and is_male):
                    self.engine.setProperty('voice', voice.id)
                    return
                elif not is_female and not is_male:
                    self.engine.setProperty('voice', voice.id)
                    return
        
        for voice in voices:
            voice_id_lower = voice.id.lower()
            voice_name_lower = voice.name.lower() if hasattr(voice, 'name') else ""
            
            if target_gender == "female" and ("female" in voice_id_lower or "nữ" in voice_id_lower or 
                                            "female" in voice_name_lower or "nữ" in voice_name_lower):
                self.engine.setProperty('voice', voice.id)
                return
            elif target_gender == "male" and ("male" in voice_id_lower or "nam" in voice_id_lower or 
                                             "male" in voice_name_lower or "nam" in voice_name_lower):
                self.engine.setProperty('voice', voice.id)
                return
        
        if voices:
            self.engine.setProperty('voice', voices[0].id)
    
    def get_available_voices(self) -> list:
        """Lấy danh sách giọng có sẵn"""
        if not self.engine:
            return []
        
        voices = self.engine.getProperty('voices')
        return [{"id": v.id, "name": v.name} for v in voices] if voices else []

