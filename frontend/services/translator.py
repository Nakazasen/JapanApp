"""Translation service using deep-translator.

Provides translation between languages (EN, JA, VI) using Google Translator.
"""
from typing import Optional, Dict

from deep_translator import GoogleTranslator

# Use centralized language detection from frontend
from frontend.utils.language_utils import detect_language, is_japanese

# Constants
LANG_UNKNOWN = "unknown"


try:
    import pykakasi
    PYKAKASI_AVAILABLE = True
except ImportError:
    PYKAKASI_AVAILABLE = False


class TranslatorService:
    """Translation service with caching support."""
    
    @staticmethod
    def translate(text: str, source_lang: str = "auto", target_lang: str = "vi") -> str:
        """Translate text using Google Translator.
        
        Args:
            text: Text to translate
            source_lang: Source language code (auto, en, ja, vi)
            target_lang: Target language code (en, ja, vi)
        
        Returns:
            Translated text
        """
        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            return translator.translate(text)
        except Exception as e:
            raise RuntimeError(f"Translation failed: {e}")
    
    @staticmethod
    def translate_en_to_vi(text: str) -> str:
        """Translate English to Vietnamese."""
        return TranslatorService.translate(text, source_lang="en", target_lang="vi")
    
    @staticmethod
    def translate_jp_to_vi(text: str) -> str:
        """Translate Japanese to Vietnamese."""
        return TranslatorService.translate(text, source_lang="ja", target_lang="vi")
    
    @staticmethod
    def translate_vi_to_en(text: str) -> str:
        """Translate Vietnamese to English."""
        return TranslatorService.translate(text, source_lang="vi", target_lang="en")
    
    @staticmethod
    def translate_vi_to_jp(text: str) -> str:
        """Translate Vietnamese to Japanese."""
        return TranslatorService.translate(text, source_lang="vi", target_lang="ja")
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect language of text.
        
        Uses centralized language detection utility.
        
        Args:
            text: Text to detect language
            
        Returns:
            Language code (en, ja, vi, etc.) or 'unknown'
        """
        if not text or len(text.strip()) < 3:
            return LANG_UNKNOWN
        
        return detect_language(text)
    
    @staticmethod
    def add_hiragana(japanese_text: str) -> str:
        """Add hiragana reading (furigana) to Japanese text.
        
        Args:
            japanese_text: Japanese text (may contain kanji, hiragana, katakana)
            
        Returns:
            Text with hiragana readings added in parentheses after kanji words
        """
        if not PYKAKASI_AVAILABLE:
            return japanese_text
        
        if not japanese_text or not japanese_text.strip():
            return japanese_text
        
        try:
            kks = pykakasi.kakasi()
            result = kks.convert(japanese_text)
            
            # Combine original text with hiragana readings
            output_parts = []
            for item in result:
                orig = item['orig']
                hira = item.get('hira', '')
                kana = item.get('kana', '')
                
                # Use hiragana if available, otherwise use katakana
                reading = hira if hira else kana
                
                # If there's kanji and we have a reading, add it in parentheses
                if orig and reading and orig != reading:
                    # Check if orig contains kanji
                    import re
                    if re.search(r'[\u4E00-\u9FAF]', orig):
                        output_parts.append(f"{orig}({reading})")
                    else:
                        output_parts.append(orig)
                else:
                    output_parts.append(orig)
            
            return ''.join(output_parts)
        except Exception as e:
            # If conversion fails, return original text
            print(f"Warning: Failed to add hiragana: {e}")
            return japanese_text


# Singleton instance
_translator_service: Optional[TranslatorService] = None


def get_translator_service() -> TranslatorService:
    """Get global TranslatorService instance."""
    global _translator_service
    if _translator_service is None:
        _translator_service = TranslatorService()
    return _translator_service
