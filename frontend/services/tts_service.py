import asyncio
import os
import edge_tts
from pathlib import Path

class TTSService:
    """
    Service to convert text to speech using Microsoft Edge's free TTS API.
    Does not require an API key.
    """
    
    def __init__(self, output_dir: str = "data/toeic/audio/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Recommended generic voices
        self.voices = {
            "US_Male": "en-US-GuyNeural",
            "US_Female": "en-US-JennyNeural",
            "UK_Male": "en-GB-RyanNeural",
            "UK_Female": "en-GB-SoniaNeural"
        }

    async def generate_audio(self, text: str, filename: str, voice: str = "en-US-JennyNeural") -> str:
        """
        Generates an MP3 file from text.
        
        Args:
            text (str): The text to speak.
            filename (str): The output filename (e.g., "part1_q1.mp3").
            voice (str): The voice ID to use.
            
        Returns:
            str: Absolute path to the generated audio file.
        """
        output_path = self.output_dir / filename
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        
        return str(output_path.absolute())

    def get_available_voices(self):
        return self.voices

# Singleton instance
_tts_service = None

def get_tts_service():
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
