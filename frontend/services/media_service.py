"""Media Service - Audio playback and TTS for frontend.

This service provides text-to-speech functionality using the backend TTS API
and pygame for audio playback.
"""
import os
import tempfile
import base64
from typing import Optional, Callable
from pathlib import Path

from frontend.services.base_service import BaseService
from frontend.services.tts import get_tts_service


class MediaService(BaseService):
    """Service for media operations like TTS and audio playback."""
    
    _temp_audio_file: Optional[str] = None
    _mixer_initialized: bool = False
    
    def __init__(self):
        super().__init__()
        self._init_mixer()
    
    def _init_mixer(self):
        """Initialize pygame mixer for audio playback."""
        if not MediaService._mixer_initialized:
            try:
                import pygame
                pygame.mixer.init()
                MediaService._mixer_initialized = True
                print("[MediaService] Pygame mixer initialized")
            except Exception as e:
                print(f"[MediaService] Failed to init mixer: {e}")
    
    async def get_tts_audio(self, text: str, lang: str = "auto") -> Optional[dict]:
        """
        Get TTS audio from backend API.
        
        Args:
            text: Text to speak
            lang: Language code ('en', 'ja', 'vi', or 'auto')
        
        Returns:
            Dict with audio, format, engine, etc. or None if failed
        """
        """
        Get TTS audio using local TTSService.
        """
        try:
            tts = get_tts_service()
            voice = tts.get_voice_for_lang(lang)
            # synthesize_async returns bytes
            audio_bytes = await tts.synthesize_async(text, voice)
            
            # Return dict matching old API structure if needed, or simplified
            return {
                "audio": base64.b64encode(audio_bytes).decode('utf-8'),
                "format": "mp3"
            }
        except Exception as e:
            print(f"[MediaService] TTS failed: {e}")
            return None
    
    def play_audio_data(self, audio_base64: str, audio_format: str = "mp3") -> bool:
        """
        Play audio from base64-encoded data.
        
        Args:
            audio_base64: Base64 encoded audio data
            audio_format: Audio format ('mp3' or 'wav')
        
        Returns:
            True if playback started successfully
        """
        try:
            import pygame
            
            # Ensure mixer is initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # Decode audio data
            audio_data = base64.b64decode(audio_base64)
            
            # Clean up previous temp file
            self._cleanup_temp_file()
            
            # Save to temp file
            suffix = f".{audio_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(audio_data)
                MediaService._temp_audio_file = f.name
            
            # Play audio
            pygame.mixer.music.load(MediaService._temp_audio_file)
            pygame.mixer.music.play()
            
            print(f"[MediaService] Playing {audio_format} audio ({len(audio_data)} bytes)")
            return True
            
        except Exception as e:
            print(f"[MediaService] Failed to play audio: {e}")
            return False
    
    def stop_audio(self):
        """Stop currently playing audio."""
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except:
            pass
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        try:
            import pygame
            if pygame.mixer.get_init():
                return pygame.mixer.music.get_busy()
        except:
            pass
        return False
    
    def _cleanup_temp_file(self):
        """Clean up temporary audio file."""
        if MediaService._temp_audio_file and os.path.exists(MediaService._temp_audio_file):
            try:
                os.remove(MediaService._temp_audio_file)
                MediaService._temp_audio_file = None
            except:
                pass
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_audio()
        self._cleanup_temp_file()


# Global singleton
_media_service: Optional[MediaService] = None


def get_media_service() -> MediaService:
    """Get global MediaService instance."""
    global _media_service
    if _media_service is None:
        _media_service = MediaService()
    return _media_service
