"""Language detection utilities for frontend.

This module provides language detection functions that can be used
directly in the frontend without making API calls.
"""
import re
from typing import Optional


# Pre-compiled regex patterns for better performance
JAPANESE_PATTERN = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
"""Matches Japanese characters: Hiragana, Katakana, and Kanji."""

VIETNAMESE_PATTERN = re.compile(
    r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]',
    re.IGNORECASE
)
"""Matches Vietnamese diacritical characters."""


def detect_language(text: str) -> str:
    """
    Detect language from text using character pattern matching.
    
    This function uses regex patterns to quickly detect language by
    checking for language-specific characters. It prioritizes Japanese
    detection, then Vietnamese, and defaults to English.
    
    Args:
        text: Text to analyze
        
    Returns:
        Language code: 'ja' for Japanese, 'vi' for Vietnamese, 
        or 'en' for English (default)
    """
    if not text or not text.strip():
        return "en"
    
    # Check for Japanese characters (Hiragana, Katakana, Kanji)
    if JAPANESE_PATTERN.search(text):
        return "ja"
    
    # Check for Vietnamese diacritical characters
    if VIETNAMESE_PATTERN.search(text):
        return "vi"
    
    # Default to English
    return "en"


def is_japanese(text: str) -> bool:
    """Check if text contains Japanese characters."""
    return bool(JAPANESE_PATTERN.search(text)) if text else False


def is_vietnamese(text: str) -> bool:
    """Check if text contains Vietnamese diacritical characters."""
    return bool(VIETNAMESE_PATTERN.search(text)) if text else False
