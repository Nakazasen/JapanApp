"""Japanese language processing module.

This module provides:
- Furigana annotation service (Kanji → Hiragana reading)
- Japanese-Vietnamese dictionary (future)
- Text normalization utilities

Dependencies:
- pykakasi: Pure Python Kanji-Kana converter
- fugashi: MeCab wrapper for better morphological analysis
- jaconv: Japanese character type conversion
"""

from frontend.services.japanese.furigana_service import FuriganaService

__all__ = ['FuriganaService']
