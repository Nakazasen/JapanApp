"""
Gemini AI Client - Central Handler with Multi-Model Fallback
=============================================================
Handles ALL AI operations (Text, Vision, JSON) with automatic 
fallback through multiple Gemini models when rate limits occur.

Usage:
    from frontend.core.gemini_client import get_gemini_client
    
    client = get_gemini_client()
    
    # Text generation
    response = await client.generate_content("Your prompt here")
    
    # JSON mode
    data = await client.generate_json("Extract info from: ...")
    
    # Vision (with image)
    result = await client.generate_content([prompt, image_bytes], json_mode=True)
"""
import asyncio
from typing import Optional, Dict, Any, List, Union
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from frontend.core.config import settings


class GeminiClient:
    """
    Central Gemini AI client with multi-model waterfall fallback.
    
    When a model hits rate limit (429) or is overloaded (503),
    automatically switches to the next available model in priority order.
    """
    
    def __init__(self):
        # Lazy import to avoid circular dependency with ai_service
        from frontend.services.ai_service import get_config_manager
        self.config_manager = get_config_manager()
        self._api_key = None
        self._configured = False
        
        # Safety settings - allow educational content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
    def _ensure_configured(self):
        """Lazy configuration to pick up latest API key."""
        current_key = self.config_manager.api_key
        if not current_key:
            raise ValueError(
                "Gemini API Key not found. Please configure it in Settings -> Gemini AI Config."
            )
        
        if not self._configured or current_key != self._api_key:
            genai.configure(api_key=current_key)
            self._api_key = current_key
            self._configured = True
            print(f"[GeminiClient] Configured with key: {current_key[:5]}...{current_key[-5:]}")

    @property
    def models(self) -> List[str]:
        """Get current active models from config manager."""
        return self.config_manager.active_models
    
    def generate_content(
        self,
        contents: Union[str, List[Any]],
        json_mode: bool = False,
        system_instruction: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        model_name: Optional[str] = None
    ) -> Any:

        """
        Generate content using Gemini with automatic multi-model fallback.
        
        Args:
            contents: String prompt OR list containing [prompt, image_bytes, ...]
            json_mode: If True, forces JSON output format
            system_instruction: Optional system prompt
            max_tokens: Maximum output tokens
            temperature: Creativity level (0.0-1.0)
            
        Returns:
            Gemini response object
            
        Raises:
            Exception: If all models are exhausted
        """
        errors = []
        self._ensure_configured()
        
        # Process contents for vision if needed
        processed_contents = self._process_contents(contents)
        
        # Use specific model if provided, else use waterfall
        models_to_try = [model_name] if model_name else self.models
        
        for i, current_model in enumerate(models_to_try):
            try:
                print(f"[GeminiClient] Trying model {i+1}/{len(models_to_try)}: {current_model}")
                
                # Create model instance
                model_kwargs = {}
                if system_instruction:
                    model_kwargs["system_instruction"] = system_instruction
                    
                model = genai.GenerativeModel(
                    current_model,
                    safety_settings=self.safety_settings,
                    **model_kwargs
                )
                
                # Build generation config
                gen_config = {
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
                
                if json_mode:
                    gen_config["response_mime_type"] = "application/json"
                
                # Use SYNC version to avoid event loop issues in Qt threads
                # The async_helpers already runs this in a separate thread
                response = model.generate_content(
                    processed_contents,
                    generation_config=gen_config
                )
                
                print(f"[GeminiClient] Success with model: {model_name}")
                return response

                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limit or overload errors
                is_rate_limit = any(x in error_msg for x in [
                    "429", "resource exhausted", "rate limit", 
                    "quota exceeded", "too many requests",
                    "requests per day", "rpd"
                ])
                is_overload = any(x in error_msg for x in [
                    "503", "overloaded", "service unavailable", 
                    "temporarily unavailable", "capacity"
                ])
                
                if is_rate_limit or is_overload:
                    error_type = "Rate Limited (429)" if is_rate_limit else "Overloaded (503)"
                    print(f"[GeminiClient] WARNING: Model '{current_model}' {error_type}")
                    
                    # Try rotating the API key if multiple keys exist
                    if is_rate_limit and len(self.config_manager.api_keys) > 1:
                        print("[GeminiClient] 🚀 Quota exceeded. Attempting API key rotation...")
                        if self.config_manager.rotate_api_key():
                            # Reconfigure with the new key
                            self._ensure_configured()
                            # Try the SAME model again with the NEW key
                            print(f"[GeminiClient] 🔄 Rotated key! Retrying model '{model_name}' with new key...")
                            # To retry the same model, we can just not increment our position if we use a while loop,
                            # or just recursively call if we want to be simple, but let's just 
                            # use the next model for now to avoid potential infinite loops, 
                            # OR better: just try again once.
                            try:
                                response = model.generate_content(
                                    processed_contents,
                                    generation_config=gen_config
                                )
                                print(f"[GeminiClient] ✅ Success with model: {current_model} after rotation")
                                return response
                            except Exception as retry_e:
                                print(f"[GeminiClient] ! Retry failed: {retry_e}")
                    
                    print(f"[GeminiClient] Switching to next model...")
                    errors.append(f"{model_name}: {error_type}")
                    # Continue to next model (sequential)
                    continue
                else:
                    # Other error - log and try next model anyway
                    print(f"[GeminiClient] ERROR with model '{current_model}': {e}")
                    errors.append(f"{current_model}: {str(e)[:100]}")
                    continue
        
        # All models exhausted
        error_summary = "; ".join(errors)
        raise Exception(f"All AI models exhausted. Errors: {error_summary}")
    
    def _process_contents(self, contents: Union[str, List[Any]]) -> Union[str, List[Any]]:
        """Process contents for vision requests."""
        if isinstance(contents, str):
            return contents
        
        if isinstance(contents, list):
            processed = []
            for item in contents:
                if isinstance(item, str):
                    processed.append(item)
                elif isinstance(item, bytes):
                    # Image bytes - convert to Part
                    import base64
                    processed.append({
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64.b64encode(item).decode("utf-8")
                        }
                    })
                elif isinstance(item, dict) and "inline_data" in item:
                    # Already formatted
                    processed.append(item)
                else:
                    processed.append(item)
            return processed
        
        return contents
    
    def generate_text(
        self, 
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Convenience method to generate plain text response.
        
        Returns:
            The text content of the response
        """
        response = self.generate_content(
            prompt, 
            system_instruction=system_instruction,
            temperature=temperature
        )

        
        # Safe access to text
        try:
            if hasattr(response, 'text'):
                return response.text
            
            # Fallback if .text is blocked/unavailable
            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    return candidate.content.parts[0].text
            
            return "No response text generated (possibly blocked by safety filters)."
        except Exception as e:
            print(f"[GeminiClient] Error accessing response text: {e}")
            if "finish_reason" in str(e).lower() or "safety" in str(e).lower():
                return "Response blocked by safety filters."
            raise

    
    async def generate_json(
        self, 
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON response with strict JSON mode.
        
        Returns:
            Parsed JSON dictionary
        """
        import json
        
        response = self.generate_content(
            prompt,
            json_mode=True,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            model_name=model_name
        )
        
        text = response.text
        
        # Parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[GeminiClient] JSON parse error: {e}")
            print(f"[GeminiClient] Raw response: {text[:500]}")
            
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # Try array format
            array_match = re.search(r'\[.*\]', text, re.DOTALL)
            if array_match:
                try:
                    return {"items": json.loads(array_match.group())}
                except:
                    pass
            
            raise ValueError(f"Failed to parse JSON response: {text[:200]}")
    
    async def generate_with_image(
        self,
        prompt: str,
        image_data: bytes,
        json_mode: bool = False,
        system_instruction: Optional[str] = None
    ) -> Any:
        """
        Generate content with image input (Vision).
        
        Args:
            prompt: Text prompt
            image_data: Image bytes (JPEG, PNG, etc.)
            json_mode: If True, returns JSON
            system_instruction: Optional system prompt
            
        Returns:
            Response object or parsed JSON if json_mode=True
        """
        import base64
        
        contents = [
            prompt,
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_data).decode("utf-8")
                }
            }
        ]
        
        if json_mode:
            response = self.generate_content(
                contents,
                json_mode=True,
                system_instruction=system_instruction
            )
            import json
            try:
                return json.loads(response.text)
            except:
                return {"raw": response.text}
        else:
            return self.generate_content(
                contents,
                system_instruction=system_instruction
            )
    
    async def generate_with_audio(
        self,
        prompt: str,
        audio_data: bytes,
        mime_type: str = "audio/wav",
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate content with audio input (Speech-to-Text).
        
        Args:
            prompt: Text prompt (e.g., "Transcribe this audio")
            audio_data: Audio bytes (WAV, MP3, etc.)
            mime_type: Audio MIME type (audio/wav, audio/mp3, audio/aac)
            system_instruction: Optional system prompt
            
        Returns:
            Text transcription
        """
        import base64
        
        contents = [
            prompt,
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(audio_data).decode("utf-8")
                }
            }
        ]
        
        response = self.generate_content(
            contents,
            system_instruction=system_instruction,
            temperature=0.1  # Low temperature for accurate transcription
        )
        
        # Handle potential empty response
        try:
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    return candidate.content.parts[0].text.strip()
            # Fallback to .text accessor
            return response.text.strip()
        except Exception as e:
            # If no transcription possible (e.g., silent audio)
            print(f"[GeminiClient] Could not get transcription: {e}")
            return "(no speech detected)"
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "en",
        mime_type: str = "audio/wav"
    ) -> str:
        """
        Transcribe audio to text (Speech-to-Text).
        
        Args:
            audio_data: Audio bytes
            language: Language code ("en", "jp", "vi")
            mime_type: Audio MIME type
            
        Returns:
            Transcribed text
        """
        lang_names = {
            "en": "English",
            "jp": "Japanese", 
            "ja": "Japanese",
            "vi": "Vietnamese"
        }
        lang_name = lang_names.get(language, "English")
        
        prompt = f"""Transcribe the following audio to text exactly as spoken in {lang_name}.
Do not add any commentary, punctuation marks should match natural speech.
Return ONLY the transcription, nothing else."""
        
        system_instruction = f"You are a highly accurate speech-to-text transcription assistant for {lang_name}."
        
        return await self.generate_with_audio(
            prompt=prompt,
            audio_data=audio_data,
            mime_type=mime_type,
            system_instruction=system_instruction
        )


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the singleton GeminiClient instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


# Backward compatibility alias
def get_gemini_handler() -> GeminiClient:
    """Alias for get_gemini_client (backward compatibility)."""
    return get_gemini_client()
