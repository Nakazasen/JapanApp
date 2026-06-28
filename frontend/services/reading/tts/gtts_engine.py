"""
TTS Engine sử dụng Google TTS (gTTS) - cần internet
"""
from gtts import gTTS
import io
import pygame
import threading
import re
from typing import Optional
from .tts_engine import TTSEngine

class GTTSEngine(TTSEngine):
    """TTS Engine sử dụng Google TTS"""
    
    def __init__(self, lang: str = "vi"):
        super().__init__()
        self.lang = lang
        self.current_audio = None
        self._audio_thread = None
        self._current_chunk_index = 0
        self._text_chunks = []
        pygame.mixer.init()
    
    def _clean_text(self, text: str) -> str:
        """Làm sạch văn bản trước khi đọc"""
        if not text:
            return ""
        
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r' +', ' ', text)
        text = text.strip()
        
        return text
    
    def _split_text(self, text: str, max_length: int = 5000) -> list:
        """Chia văn bản thành các đoạn nhỏ"""
        if len(text) <= max_length:
            return [text]
        
        sentences = re.split(r'([.!?。！？]\s+)', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_length]]
    
    def speak(self, text: str):
        """Đọc văn bản"""
        if self.is_paused:
            self.resume()
            return
        
        if not text or not text.strip():
            print("Văn bản trống, không thể đọc")
            return
        
        self.is_speaking = True
        self._stop_event.clear()
        
        def _speak_thread():
            try:
                cleaned_text = self._clean_text(text)
                
                if not cleaned_text:
                    print("Văn bản sau khi làm sạch trống")
                    return
                
                print(f"Đang đọc văn bản tiếng Việt ({len(cleaned_text)} ký tự)...")
                
                text_chunks = self._split_text(cleaned_text, max_length=5000)
                
                print(f"Chia thành {len(text_chunks)} đoạn để đọc")
                
                self._text_chunks = text_chunks
                self._current_chunk_index = 0
                
                for i in range(len(text_chunks)):
                    if self._stop_event.is_set():
                        print("Đã dừng đọc")
                        break
                    
                    while self.is_paused and not self._stop_event.is_set():
                        pygame.time.wait(100)
                    
                    if self._stop_event.is_set():
                        print("Đã dừng đọc")
                        break
                    
                    chunk = text_chunks[i]
                    if not chunk.strip():
                        continue
                    
                    try:
                        print(f"Đang đọc đoạn {i+1}/{len(text_chunks)}...")
                        
                        # Update current chunk index for resume
                        self._current_chunk_index = i
                        
                        tts = gTTS(text=chunk, lang=self.lang, slow=False)
                        
                        audio_buffer = io.BytesIO()
                        tts.write_to_fp(audio_buffer)
                        audio_buffer.seek(0)
                        
                        pygame.mixer.music.load(audio_buffer)
                        pygame.mixer.music.play()
                        
                        # Wait for audio to finish, handling pause/resume
                        while not self._stop_event.is_set():
                            # Check pause state first
                            if self.is_paused:
                                pygame.mixer.music.pause()
                                print(f"[gTTS] Đã tạm dừng ở đoạn {i+1}/{len(text_chunks)}")
                                # Wait while paused
                                while self.is_paused and not self._stop_event.is_set():
                                    pygame.time.wait(100)
                                # Resume if not stopped
                                if not self._stop_event.is_set():
                                    pygame.mixer.music.unpause()
                                    print(f"[gTTS] Tiếp tục đọc đoạn {i+1}/{len(text_chunks)}")
                            
                            # Check if audio is still playing
                            if not pygame.mixer.music.get_busy():
                                break
                            
                            pygame.time.wait(100)
                        
                        if self._stop_event.is_set():
                            pygame.mixer.music.stop()
                            print("Đã dừng đọc")
                            break
                        
                        print(f"Đã đọc xong đoạn {i+1}/{len(text_chunks)}")
                        
                    except Exception as e:
                        print(f"Lỗi khi đọc đoạn {i+1}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                print("Đã đọc xong tất cả")
                
            except Exception as e:
                print(f"Lỗi khi đọc với Google TTS: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.is_speaking = False
        
        self._audio_thread = threading.Thread(target=_speak_thread)
        self._audio_thread.daemon = True
        self._audio_thread.start()
    
    def stop(self):
        """Dừng đọc"""
        self._stop_event.set()
        pygame.mixer.music.stop()
        self.is_speaking = False
        self.is_paused = False
        self._text_chunks = []
        self._current_chunk_index = 0
    
    def pause(self):
        """Tạm dừng"""
        if self.is_speaking and not self.is_paused:
            self.is_paused = True
            pygame.mixer.music.pause()
            print("Đã tạm dừng đọc")
    
    def resume(self):
        """Tiếp tục"""
        if self.is_paused:
            self.is_paused = False
            pygame.mixer.music.unpause()
            print("Đã tiếp tục đọc")
    
    def set_rate(self, rate: int):
        """Thiết lập tốc độ đọc"""
        pass
    
    def set_voice(self, voice_type: str):
        """Thiết lập giọng đọc"""
        pass
    
    def get_available_voices(self) -> list:
        """Lấy danh sách giọng có sẵn"""
        return [{"id": "default", "name": "Google TTS (Tiếng Việt)"}]

