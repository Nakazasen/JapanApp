
"""Speaking Service - AI-powered pronunciation assessment.

Uses Gemini Multimodal capabilities to assess speaking directly from audio.
"""
import base64
from typing import Dict, Any, Optional
from frontend.services.base_service import BaseService
from frontend.core.gemini_client import get_gemini_client

class SpeakingService(BaseService):
    """Service for speaking assessment."""
    
    def __init__(self):
        super().__init__()
        self.gemini = get_gemini_client()
        
    async def score_speaking(self, audio_base64: str, lang: str = "en") -> Dict[str, Any]:
        """
        Score speaking audio using Gemini.
        
        Args:
            audio_base64: Base64 encoded audio data (WAV/MP3)
            lang: Language code ('en' or 'jp')
            
        Returns:
            Dict with scores and feedback
        """
        try:
            # Decode base64 to bytes
            audio_bytes = base64.b64decode(audio_base64)
            
            # Prepare prompt
            if lang == "jp":
                prompt = """
                この音声を評価してください。日本語学習者の発音練習です。
                以下のJSON形式で出力してください:
                {
                    "transcription": "音声の書き起こし (漢字・かな混じり)",
                    "pronunciation_score": 0.0-1.0 (発音の正確さ),
                    "fluency_score": 0.0-1.0 (流暢さ),
                    "feedback": ["良い点", "改善点1", "改善点2"]
                }
                """
                system_instruction = "You are a Japanese pronunciation teacher."
            else:
                prompt = """
                Assess this audio recording of an English learner.
                Output ONLY JSON in this format:
                {
                    "transcription": "exact transcription of what was said",
                    "pronunciation_score": 0.0-1.0 (accuracy),
                    "fluency_score": 0.0-1.0 (smoothness/speed),
                    "feedback": ["strength", "improvement area 1", "improvement area 2"]
                }
                """
                system_instruction = "You are an English pronunciation coach."

            # Construct multimodal content
            # GeminiClient.generate_content expects list for multimodal
            content = [
                prompt,
                {
                    "inline_data": {
                        "mime_type": "audio/wav",  # Assume WAV from recorder
                        "data": audio_base64
                    }
                }
            ]
            
            # Call Gemini
            response = await self.gemini.generate_content(
                content,
                json_mode=True,
                system_instruction=system_instruction
            )
            
            # Parse JSON
            import json
            try:
                result = json.loads(response.text)
                return result
            except json.JSONDecodeError:
                # Fallback extraction
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return {"error": "Failed to parse AI response", "raw": response.text}
                
        except Exception as e:
            print(f"[ERROR SpeakingService] Score failed: {e}")
            return {"error": str(e)}

# Singleton
_speaking_service: Optional[SpeakingService] = None

def get_speaking_service() -> SpeakingService:
    global _speaking_service
    if _speaking_service is None:
        _speaking_service = SpeakingService()
    return _speaking_service
