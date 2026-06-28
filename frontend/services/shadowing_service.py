"""Shadowing Service - AI Script Generation and Audio Synthesis.

Generates Japanese shadowing scripts using Gemini AI and creates audio
using edge-tts for practice sessions.
"""
import asyncio
import tempfile
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from frontend.services.ai_service import WaterfallGeminiService, get_ai_service
from frontend.services.tts import TTSService, get_tts_service


class ShadowingService:
    """Service for generating shadowing scripts and audio.
    
    Uses Gemini AI to generate Japanese conversation scripts with readings
    and meanings, then synthesizes audio using edge-tts.
    """
    
    # JLPT Level descriptions for better AI prompts
    LEVEL_DESCRIPTIONS = {
        "N5": "beginner level, basic greetings and simple phrases",
        "N4": "elementary level, everyday conversations",
        "N3": "intermediate level, common situations and topics",
        "N2": "upper intermediate, complex conversations and opinions",
        "N1": "advanced level, nuanced and sophisticated language"
    }
    
    def __init__(self):
        """Initialize the ShadowingService."""
        self.ai_service: Optional[WaterfallGeminiService] = None
        self.tts_service: Optional[TTSService] = None
    
    def _get_ai_service(self) -> WaterfallGeminiService:
        """Get or create AI service instance."""
        if self.ai_service is None:
            self.ai_service = get_ai_service()
        return self.ai_service
    
    def _get_tts_service(self) -> TTSService:
        """Get or create TTS service instance."""
        if self.tts_service is None:
            self.tts_service = get_tts_service()
        return self.tts_service
    
    async def generate_script_async(
        self,
        topic: str,
        level: str = "N4",
        num_sentences: int = 5
    ) -> Dict[str, Any]:
        """Generate a shadowing script using AI.
        
        Args:
            topic: The conversation topic/scenario.
            level: JLPT level (N5-N1).
            num_sentences: Number of sentences to generate.
            
        Returns:
            Dictionary containing script data with sentences.
        """
        try:
            level_desc = self.LEVEL_DESCRIPTIONS.get(level, self.LEVEL_DESCRIPTIONS["N4"])
            
            prompt = f"""You are a Japanese language teacher creating a shadowing practice script for Vietnamese students.

Topic: {topic}
Level: {level} ({level_desc})
Number of sentences: {num_sentences}

Generate a natural Japanese conversation or monologue for shadowing practice.
Output ONLY valid JSON in this exact format:
{{
    "title": "Script title in Japanese",
    "sentences": [
        {{
            "japanese": "Japanese sentence with kanji",
            "reading": "Full sentence in hiragana/katakana",
            "meaning": "Vietnamese translation"
        }}
    ]
}}

Rules:
1. Use vocabulary and grammar appropriate for {level}
2. Make it natural and useful for real conversations
3. Include common expressions and phrases
4. Keep sentences at a speakable length for shadowing"""

            ai = self._get_ai_service()
            response = ai.generate_response(prompt)
            
            if response.get('status') == 'success':
                text = response.get('text', '')
                
                # Parse JSON from response
                import json
                import re
                
                # Try to extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    script_data = json.loads(json_match.group())
                    return {
                        'success': True,
                        'script': script_data,
                        'model_used': response.get('model_used', 'unknown')
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to parse AI response as JSON',
                        'raw_response': text
                    }
            else:
                return {
                    'success': False,
                    'error': response.get('error', 'AI generation failed')
                }
                
        except Exception as e:
            print(f"[ERROR ShadowingService] Script generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_script(
        self,
        topic: str,
        level: str = "N4",
        num_sentences: int = 5
    ) -> Dict[str, Any]:
        """Synchronous wrapper for generate_script_async.
        
        Args:
            topic: The conversation topic/scenario.
            level: JLPT level (N5-N1).
            num_sentences: Number of sentences to generate.
            
        Returns:
            Dictionary containing script data with sentences.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_script_async(topic, level, num_sentences)
        )
    
    async def generate_audio_async(
        self,
        script_content: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate audio for a shadowing script.
        
        Args:
            script_content: Script dictionary containing sentences.
            output_path: Optional path to save the audio file.
            
        Returns:
            Dictionary with audio file path or error.
        """
        try:
            # Extract Japanese text from all sentences
            sentences = script_content.get('sentences', [])
            if not sentences:
                return {
                    'success': False,
                    'error': 'No sentences in script'
                }
            
            # Combine all Japanese sentences with pauses
            # Using "。" (period) naturally creates pauses in TTS
            japanese_text = " ".join(
                s.get('japanese', '') for s in sentences
            )
            
            if not japanese_text.strip():
                return {
                    'success': False,
                    'error': 'No Japanese text to synthesize'
                }
            
            # Generate audio path if not provided
            if output_path is None:
                fd, output_path = tempfile.mkstemp(suffix='.mp3')
                os.close(fd)
            
            # Use edge-tts with Japanese voice
            tts = self._get_tts_service()
            audio_path = await tts.speak_async(japanese_text, lang="ja")
            
            # If we need to save to a specific path, copy the file
            if audio_path != output_path:
                import shutil
                shutil.copy2(audio_path, output_path)
                # Clean up temp file
                if os.path.exists(audio_path) and audio_path != output_path:
                    try:
                        os.remove(audio_path)
                    except:
                        pass
            
            return {
                'success': True,
                'audio_path': output_path
            }
            
        except Exception as e:
            print(f"[ERROR ShadowingService] Audio generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_audio(
        self,
        script_content: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous wrapper for generate_audio_async.
        
        Args:
            script_content: Script dictionary containing sentences.
            output_path: Optional path to save the audio file.
            
        Returns:
            Dictionary with audio file path or error.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_audio_async(script_content, output_path)
        )
    
    def generate_full_lesson(
        self,
        topic: str,
        level: str = "N4",
        num_sentences: int = 5
    ) -> Dict[str, Any]:
        """Generate a complete shadowing lesson with script and audio.
        
        Args:
            topic: The conversation topic/scenario.
            level: JLPT level (N5-N1).
            num_sentences: Number of sentences to generate.
            
        Returns:
            Dictionary with script and audio path, or error.
        """
        # Generate script
        script_result = self.generate_script(topic, level, num_sentences)
        if not script_result.get('success'):
            return script_result
        
        script = script_result.get('script', {})
        
        # Generate audio
        audio_result = self.generate_audio(script)
        if not audio_result.get('success'):
            return {
                'success': True,  # Script succeeded, audio failed
                'script': script,
                'audio_path': None,
                'audio_error': audio_result.get('error')
            }
        
        return {
            'success': True,
            'script': script,
            'audio_path': audio_result.get('audio_path'),
            'model_used': script_result.get('model_used')
        }


# Singleton instance
_shadowing_service: Optional[ShadowingService] = None


def get_shadowing_service() -> ShadowingService:
    """Get global ShadowingService instance.
    
    Returns:
        Singleton ShadowingService instance.
    """
    global _shadowing_service
    if _shadowing_service is None:
        _shadowing_service = ShadowingService()
    return _shadowing_service
