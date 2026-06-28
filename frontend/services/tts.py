"""Text-to-Speech service using edge-tts.

Provides TTS functionality using Microsoft Edge TTS (free, no API key needed).
"""
import asyncio
import tempfile
import os
import re
import time
from typing import Optional
import pygame
import edge_tts


def strip_emojis(text: str) -> str:
    """Remove emojis and special unicode symbols from text for cleaner TTS."""
    # Remove emoji ranges
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U00002600-\U000026FF"  # misc symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # extended-A symbols
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()

class TTSService:
    """Text-to-Speech service using Microsoft Edge TTS."""
    
    # Default voices for each language
    DEFAULT_VOICES = {
        "en": "en-US-AriaNeural",
        "ja": "ja-JP-NanamiNeural",
        "vi": "vi-VN-HoaiMyNeural",
    }
    
    # Store temp file for cleanup
    _last_temp_file: Optional[str] = None
    
    @staticmethod
    def get_voice_for_lang(lang: str) -> str:
        """Get default voice for language."""
        return TTSService.DEFAULT_VOICES.get(lang, TTSService.DEFAULT_VOICES["en"])
    
    @staticmethod
    async def get_voices_async(lang: str = "en") -> list:
        """Get available voices for a language (async).
        
        Args:
            lang: Language code (en, ja, vi)
        
        Returns:
            List of voice names
        """
        voices = await edge_tts.list_voices()
        lang_map = {"en": "en-", "ja": "ja-", "vi": "vi-"}
        prefix = lang_map.get(lang, "en-")
        return [v["ShortName"] for v in voices if v["ShortName"].startswith(prefix)]
    
    @staticmethod
    def get_voices(lang: str = "en") -> list:
        """Get available voices for a language (sync)."""
        return asyncio.run(TTSService.get_voices_async(lang))
    
    @staticmethod
    async def synthesize_async(text: str, voice: str = "en-US-AriaNeural", output_path: Optional[str] = None) -> str:
        """Synthesize speech from text (async).
        
        Args:
            text: Text to synthesize
            voice: Voice name (e.g., "en-US-AriaNeural", "ja-JP-NanamiNeural")
            output_path: Optional path to save audio file
        
        Returns:
            Path to the audio file
        """
        communicate = edge_tts.Communicate(text, voice)
        
        if output_path:
            await communicate.save(output_path)
            return output_path
        else:
            # Use a temporary file
            fd, temp_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            await communicate.save(temp_path)
            return temp_path
    
    @staticmethod
    def synthesize(text: str, voice: str = "en-US-AriaNeural", output_path: Optional[str] = None) -> str:
        """Synchronous wrapper for synthesize. Returns path to audio file."""
        return asyncio.run(TTSService.synthesize_async(text, voice, output_path))
    
    # Class-level lock for thread safety
    import threading
    _playback_lock = threading.Lock()
    _is_playing = False
    _is_synthesizing = False
    
    @staticmethod
    def stop_audio():
        """Stop any currently playing audio immediately."""
        with TTSService._playback_lock:
            try:
                TTSService._is_playing = False
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                    print("[INFO TTS] Audio playback stopped and unloaded")
            except Exception as e:
                print(f"[WARN TTS] Error stopping audio: {e}")

    def stop(self):
        """Instance alias for stop_audio."""
        self.stop_audio()

    @staticmethod
    def pause_audio():
        """Pause currently playing audio."""
        with TTSService._playback_lock:
            try:
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
                    print("[INFO TTS] Audio paused")
            except Exception as e:
                print(f"[WARN TTS] Error pausing audio: {e}")

    @staticmethod
    def resume_audio():
        """Resume paused audio."""
        with TTSService._playback_lock:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.unpause()
                    print("[INFO TTS] Audio resumed")
            except Exception as e:
                print(f"[WARN TTS] Error resuming audio: {e}")
    
    @staticmethod
    def is_playing() -> bool:
        """Check if audio is currently playing in the mixer."""
        try:
            return pygame.mixer.get_init() and pygame.mixer.music.get_busy()
        except:
            return False
    
    @staticmethod
    def play_audio(file_path: str):
        """Play an audio file using pygame with thread safety."""
        
        # Ensure we stop first (though speak_and_play should have handled it)
        TTSService.stop_audio()
        
        with TTSService._playback_lock:
            TTSService._is_playing = True
            try:
                if not pygame.get_init():
                    pygame.init()
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
                
                time.sleep(0.05)
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play()
                print(f"[INFO TTS] Audio playback started")
                
                # Release lock while waiting for playback so Stop can interrupt
            except Exception as e:
                print(f"[ERROR TTS] Failed to start playback: {e}")
                TTSService._is_playing = False
                raise

        # Busy wait outside the lock so other commands (stop/pause) can enter
        def wait_loop():
            while TTSService._is_playing:
                try:
                    if not pygame.mixer.get_init() or not pygame.mixer.music.get_busy():
                        break
                except:
                    break
                time.sleep(0.1)
            
            TTSService._is_playing = False
            print("[INFO TTS] Playback loop ended")

        import threading
        playback_thread = threading.Thread(target=wait_loop, daemon=True)
        playback_thread.start()
        
        # If we are NOT in the main thread (e.g. called from a worker), 
        # we can block here to wait for completion (important for cleanup)
        from PySide6.QtCore import QThread, QCoreApplication
        app = QCoreApplication.instance()
        if not app or QThread.currentThread() != app.thread():
            playback_thread.join()

    @staticmethod
    def speak_and_play(text: str, lang: str = "en"):
        """Synthesize text and play it, ensuring only one instance runs."""
        if not text or not text.strip():
            return
        
        # Strip emojis for Vietnamese to avoid reading icon names
        if lang == "vi":
            text = strip_emojis(text)
            if not text.strip():
                return
        
        def _run_speak_and_play():
            # Prevent overlaps
            TTSService.stop_audio()
            TTSService._is_synthesizing = True
            
            voice = TTSService.get_voice_for_lang(lang)
            temp_path = None
            
            try:
                print(f"[INFO TTS] Synthesizing voice {voice}...")
                fd, temp_path = tempfile.mkstemp(suffix=".mp3")
                os.close(fd)
                
                asyncio.run(TTSService.synthesize_async(text, voice, temp_path))
                TTSService._is_synthesizing = False
                
                # Start playback (will block in this background thread until done)
                TTSService.play_audio(temp_path)
                
            except Exception as e:
                print(f"[ERROR TTS] speak_and_play failed: {e}")
                TTSService._is_synthesizing = False
                TTSService._is_playing = False
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                TTSService._is_synthesizing = False

        # Always run the process in a background thread to avoid blocking UI
        import threading
        threading.Thread(target=_run_speak_and_play, daemon=True).start()
    
    @staticmethod
    async def speak_async(text: str, lang: str = "en") -> str:
        """Async interface to synthesize speech for a language.
        
        Args:
            text: Text to speak
            lang: Language code (en, ja, vi)
            
        Returns:
            Path to audio file
        """
        voice = TTSService.get_voice_for_lang(lang)
        
        # Strip emojis for Vietnamese
        if lang == "vi":
            text = strip_emojis(text)
        
        return await TTSService.synthesize_async(text, voice)

    @staticmethod
    def speak(text: str, lang: str = "en") -> str:
        """Simple interface to synthesize speech for a language.
        
        Args:
            text: Text to speak
            lang: Language code (en, ja, vi)
            
        Returns:
            Path to audio file
        """
        voice = TTSService.get_voice_for_lang(lang)
        
        # Strip emojis for Vietnamese
        if lang == "vi":
            text = strip_emojis(text)
        
        return TTSService.synthesize(text, voice)


# Singleton instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get global TTSService instance."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service

