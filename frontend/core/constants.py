"""Application constants and enumerations.

This module provides centralized constants for the EnglishApp application,
ensuring consistency across backend and frontend components.
"""
from enum import Enum
from typing import Dict


class Language(str, Enum):
    """Supported language codes."""
    
    ENGLISH = "en"
    JAPANESE = "ja"
    VIETNAMESE = "vi"
    AUTO = "auto"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_string(cls, lang_code: str) -> "Language":
        """Convert string to Language enum, defaulting to UNKNOWN."""
        code = lang_code.lower() if lang_code else ""
        mapping = {
            "en": cls.ENGLISH,
            "english": cls.ENGLISH,
            "ja": cls.JAPANESE,
            "jp": cls.JAPANESE,
            "japanese": cls.JAPANESE,
            "vi": cls.VIETNAMESE,
            "vietnamese": cls.VIETNAMESE,
            "auto": cls.AUTO,
        }
        return mapping.get(code, cls.UNKNOWN)
    
    def get_display_name(self) -> str:
        """Get human-readable language name."""
        names = {
            Language.ENGLISH: "English",
            Language.JAPANESE: "日本語",
            Language.VIETNAMESE: "Tiếng Việt",
            Language.AUTO: "Tự động",
            Language.UNKNOWN: "Không xác định",
        }
        return names.get(self, self.value.upper())


class TTSVoices:
    """Text-to-Speech voice configurations for edge-tts."""
    
    # Edge-TTS voices (online, high quality)
    EDGE_TTS = {
        Language.ENGLISH: "en-US-AriaNeural",
        Language.JAPANESE: "ja-JP-NanamiNeural",
        Language.VIETNAMESE: "vi-VN-HoaiMyNeural",
    }
    
    # Fallback voices
    FALLBACK = {
        Language.ENGLISH: "en-US-AriaNeural",
        Language.JAPANESE: "ja-JP-NanamiNeural",
        Language.VIETNAMESE: "vi-VN-HoaiMyNeural",
    }
    
    # pyttsx3 voice hints (for offline fallback)
    PYTTSX3_HINTS: Dict[Language, list] = {
        Language.ENGLISH: ["english", "en-us", "en_us", "en"],
        Language.JAPANESE: ["japanese", "ja-jp", "ja_jp", "ja", "haruka", "sayaka", "ichiro", "ayumi"],
        Language.VIETNAMESE: ["vietnamese", "vi-vn", "vi_vn", "vi"],
    }
    
    @classmethod
    def get_edge_voice(cls, language: Language) -> str:
        """Get edge-tts voice for a language."""
        return cls.EDGE_TTS.get(language, cls.EDGE_TTS[Language.ENGLISH])
    
    @classmethod
    def get_fallback_voice(cls, language: Language) -> str:
        """Get fallback voice for a language."""
        return cls.FALLBACK.get(language, cls.FALLBACK[Language.ENGLISH])


class AudioFormat(str, Enum):
    """Supported audio formats."""
    
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"


class DictionaryType(str, Enum):
    """Available dictionary types."""
    
    JISHO = "jisho"
    CAMBRIDGE = "cambridge"
    OXFORD = "oxford"
    VDICT = "vdict"


# API limits and configuration
class APILimits:
    """API rate limits and size constraints."""
    
    TTS_MAX_TEXT_LENGTH = 5000
    TTS_RETRY_ATTEMPTS = 3
    TRANSLATE_MAX_TEXT_LENGTH = 10000
    NEWS_MAX_ARTICLES = 50
    YOUTUBE_MAX_RESULTS = 20


# UI text constants (Vietnamese)
class UIText:
    """Common UI text strings in Vietnamese."""
    
    # Buttons
    BTN_TRANSLATE = "Dịch"
    BTN_SPEAK = "Đọc văn bản"
    BTN_LOOKUP = "Tra từ"
    BTN_CLOSE = "Đóng"
    BTN_OK = "OK"
    BTN_CANCEL = "Hủy"
    BTN_REFRESH = "Làm mới"
    BTN_PREVIOUS = "Trước"
    BTN_NEXT = "Tiếp"
    
    # Labels
    LBL_LOADING = "Đang tải..."
    LBL_NO_DATA = "Không có dữ liệu"
    LBL_ERROR = "Lỗi"
    LBL_SUCCESS = "Thành công"
    LBL_ORIGINAL_TEXT = "Văn bản gốc"
    LBL_TRANSLATION = "Bản dịch"
    
    # Messages
    MSG_NO_TEXT_SELECTED = "Không có văn bản được chọn!"
    MSG_NO_WORD_SELECTED = "Không có từ được chọn!"
    MSG_TTS_ERROR = "Không thể đọc văn bản"
    MSG_TRANSLATE_ERROR = "Không thể dịch văn bản"
    MSG_NETWORK_ERROR = "Lỗi kết nối mạng"
    
    # Context menu
    CTX_AUTO_TRANSLATE = "🌐 Dịch (Tự phát hiện ngôn ngữ)"
    CTX_EN_TO_VI = "🇬🇧 → 🇻🇳 Dịch Anh → Việt"
    CTX_EN_TO_JA = "🇬🇧 → 🇯🇵 Dịch Anh → Nhật"
    CTX_JA_TO_EN = "🇯🇵 → 🇬🇧 Dịch Nhật → Anh"
    CTX_JA_TO_VI = "🇯🇵 → 🇻🇳 Dịch Nhật → Việt"
    CTX_VI_TO_EN = "🇻🇳 → 🇬🇧 Dịch Việt → Anh"
    CTX_VI_TO_JA = "🇻🇳 → 🇯🇵 Dịch Việt → Nhật"
    CTX_DICTIONARY = "📚 Tra từ"
    CTX_TTS = "🔊 Đọc văn bản"
