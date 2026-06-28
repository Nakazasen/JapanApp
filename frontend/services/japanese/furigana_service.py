"""Furigana annotation service for Japanese text.

Furigana (振り仮名) are small hiragana characters placed above Kanji
to show their reading. This is essential for reading Japanese tech articles.

Example:
    Input:  "機械学習の基礎"
    Output: "<ruby>機械<rt>きかい</rt></ruby><ruby>学習<rt>がくしゅう</rt></ruby>の<ruby>基礎<rt>きそ</rt></ruby>"

Rendered in browser:
    機械  (with きかい above)
    学習  (with がくしゅう above)

Dependencies:
- pykakasi: Main converter (simple, reliable)
- fugashi + unidic: More accurate but heavier (optional)
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Pre-check imports at module level
PYKAKASI_AVAILABLE = False
FUGASHI_AVAILABLE = False

try:
    import pykakasi
    PYKAKASI_AVAILABLE = True
except ImportError:
    pass

try:
    import fugashi
    FUGASHI_AVAILABLE = True
except ImportError:
    pass


@dataclass
class FuriganaToken:
    """A token with optional furigana reading."""
    text: str           # Original text (may contain Kanji)
    reading: str        # Hiragana reading
    is_kanji: bool      # True if text contains Kanji
    
    def to_html(self) -> str:
        """Convert to HTML ruby annotation."""
        if self.is_kanji and self.reading and self.reading != self.text:
            return f'<ruby>{self.text}<rt>{self.reading}</rt></ruby>'
        return self.text


class FuriganaService:
    """Service for adding Furigana annotations to Japanese text.
    
    Usage:
        service = FuriganaService()
        
        # Get HTML with ruby annotations
        html = service.add_furigana_html("機械学習を勉強する")
        # Returns: <ruby>機械<rt>きかい</rt></ruby><ruby>学習<rt>がくしゅう</rt></ruby>...
        
        # Get plain reading
        reading = service.get_reading("機械学習")
        # Returns: "きかいがくしゅう"
        
        # Get romanization
        romaji = service.get_romaji("機械学習")
        # Returns: "kikagakushuu"
    """
    
    # Regex to detect Kanji characters
    KANJI_PATTERN = re.compile(r'[\u4e00-\u9fff]')
    
    # Regex to detect Hiragana
    HIRAGANA_PATTERN = re.compile(r'[\u3040-\u309f]')
    
    # Regex to detect Katakana
    KATAKANA_PATTERN = re.compile(r'[\u30a0-\u30ff]')
    
    def __init__(self, use_fugashi: bool = False):
        """Initialize the furigana service.
        
        Args:
            use_fugashi: If True, prefer fugashi (more accurate). 
                         Default is False to use pykakasi for simpler setup.
        """
        self._fugashi_tagger = None
        self._kakasi = None
        self._mode = None
        
        # Try pykakasi first (simpler, always works)
        # Use dynamic import as fallback
        try:
            import pykakasi as pk
            self._kakasi = pk.kakasi()
            self._mode = "pykakasi"
            print("[INFO FuriganaService] Using pykakasi for Kanji conversion")
        except ImportError:
            print("[WARN FuriganaService] pykakasi not available")
        except Exception as e:
            print(f"[WARN FuriganaService] pykakasi init failed: {e}")
        
        # Only try fugashi if pykakasi is not available
        if self._mode is None:
            try:
                import fugashi
                self._fugashi_tagger = fugashi.Tagger()
                self._mode = "fugashi"
                print("[INFO FuriganaService] Using fugashi for accurate morphological analysis")
            except ImportError:
                print("[WARN FuriganaService] fugashi not available")
            except Exception as e:
                print(f"[WARN FuriganaService] fugashi init failed: {e}")
        
        if self._mode is None:
            raise RuntimeError(
                "No Japanese NLP library available. "
                "Please install: pip install pykakasi"
            )
    
    def _contains_kanji(self, text: str) -> bool:
        """Check if text contains any Kanji characters."""
        return bool(self.KANJI_PATTERN.search(text))
    
    def _tokenize_fugashi(self, text: str) -> List[FuriganaToken]:
        """Tokenize using fugashi (MeCab)."""
        tokens = []
        
        for word in self._fugashi_tagger(text):
            surface = word.surface  # Original text
            
            # Get reading from word features
            # fugashi returns reading in katakana, we need to convert to hiragana
            reading_kata = None
            if hasattr(word, 'feature') and word.feature:
                # UniDic format: word.feature.kana or similar
                if hasattr(word.feature, 'kana'):
                    reading_kata = word.feature.kana
                elif hasattr(word.feature, 'pron'):
                    reading_kata = word.feature.pron
            
            # Convert katakana reading to hiragana
            if reading_kata:
                reading = self._kata_to_hira(reading_kata)
            else:
                reading = surface
            
            is_kanji = self._contains_kanji(surface)
            
            tokens.append(FuriganaToken(
                text=surface,
                reading=reading,
                is_kanji=is_kanji
            ))
        
        return tokens
    
    def _tokenize_pykakasi(self, text: str) -> List[FuriganaToken]:
        """Tokenize using pykakasi."""
        tokens = []
        
        result = self._kakasi.convert(text)
        for item in result:
            orig = item['orig']
            hira = item['hira']
            is_kanji = self._contains_kanji(orig)
            
            tokens.append(FuriganaToken(
                text=orig,
                reading=hira,
                is_kanji=is_kanji
            ))
        
        return tokens
    
    def _kata_to_hira(self, text: str) -> str:
        """Convert Katakana to Hiragana."""
        # Katakana to Hiragana offset
        result = []
        for char in text:
            code = ord(char)
            # Katakana range: 0x30A0-0x30FF
            # Hiragana range: 0x3040-0x309F
            if 0x30A1 <= code <= 0x30F6:
                result.append(chr(code - 0x60))
            else:
                result.append(char)
        return ''.join(result)
    
    def tokenize(self, text: str) -> List[FuriganaToken]:
        """Tokenize Japanese text into words with readings.
        
        Args:
            text: Japanese text to tokenize
            
        Returns:
            List of FuriganaToken objects
        """
        if not text:
            return []
        
        if self._mode == "fugashi":
            return self._tokenize_fugashi(text)
        else:
            return self._tokenize_pykakasi(text)
    
    def add_furigana_html(self, text: str) -> str:
        """Add furigana annotations as HTML ruby elements.
        
        Args:
            text: Japanese text
            
        Returns:
            HTML string with <ruby><rt> annotations
            
        Example:
            Input:  "機械学習"
            Output: "<ruby>機械<rt>きかい</rt></ruby><ruby>学習<rt>がくしゅう</rt></ruby>"
        """
        if not text:
            return ""
        
        # Skip if no Japanese text
        if not self._contains_kanji(text):
            return text
        
        tokens = self.tokenize(text)
        return ''.join(token.to_html() for token in tokens)
    
    def get_reading(self, text: str) -> str:
        """Get hiragana reading of text.
        
        Args:
            text: Japanese text
            
        Returns:
            Hiragana reading
            
        Example:
            Input:  "機械学習"
            Output: "きかいがくしゅう"
        """
        if not text:
            return ""
        
        tokens = self.tokenize(text)
        return ''.join(token.reading for token in tokens)
    
    def get_romaji(self, text: str) -> str:
        """Get romanized (romaji) reading of text.
        
        Args:
            text: Japanese text
            
        Returns:
            Romanized text
            
        Example:
            Input:  "機械学習"
            Output: "kikagakushuu"
        """
        if not text:
            return ""
        
        if self._mode == "pykakasi":
            # pykakasi can output romaji directly
            result = self._kakasi.convert(text)
            return ''.join(item['hepburn'] for item in result)
        else:
            # For fugashi, we need to convert hiragana to romaji
            reading = self.get_reading(text)
            return self._hira_to_romaji(reading)
    
    def _hira_to_romaji(self, text: str) -> str:
        """Convert Hiragana to Romaji (basic conversion)."""
        # Basic hiragana to romaji mapping
        HIRA_ROMAJI = {
            'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
            'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
            'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
            'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
            'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
            'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
            'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
            'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
            'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
            'わ': 'wa', 'を': 'wo', 'ん': 'n',
            'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
            'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
            'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
            'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
            'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
            'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
            'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho',
            'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
            'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
            'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
            'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
            'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
            'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
            'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
            'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
            'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
            'っ': '', 'ー': '-',
        }
        
        result = []
        i = 0
        while i < len(text):
            # Try 2-char combinations first (for きゃ, しゃ, etc.)
            if i + 1 < len(text):
                two_char = text[i:i+2]
                if two_char in HIRA_ROMAJI:
                    result.append(HIRA_ROMAJI[two_char])
                    i += 2
                    continue
            
            # Single character
            char = text[i]
            if char in HIRA_ROMAJI:
                romaji = HIRA_ROMAJI[char]
                # Handle small tsu (っ) - doubles the next consonant
                if char == 'っ' and i + 1 < len(text):
                    next_char = text[i + 1]
                    if next_char in HIRA_ROMAJI and HIRA_ROMAJI[next_char]:
                        result.append(HIRA_ROMAJI[next_char][0])
                else:
                    result.append(romaji)
            else:
                result.append(char)
            i += 1
        
        return ''.join(result)
    
    def process_article_content(self, content: str) -> str:
        """Process article content, adding furigana only to Japanese text.
        
        This is smart enough to skip code blocks, URLs, and other non-Japanese content.
        
        Args:
            content: Article content (may be mixed Japanese/English/code)
            
        Returns:
            Content with furigana annotations added to Japanese text
        """
        if not content:
            return ""
        
        # Split by code blocks and process only non-code parts
        # Pattern matches: ```...``` or `...`
        code_pattern = re.compile(r'(```[\s\S]*?```|`[^`]+`)')
        
        parts = code_pattern.split(content)
        result_parts = []
        
        for i, part in enumerate(parts):
            if code_pattern.match(part):
                # This is a code block, keep as-is
                result_parts.append(part)
            else:
                # Process non-code text
                # Further split by URLs and keep them intact
                url_pattern = re.compile(r'(https?://[^\s]+)')
                sub_parts = url_pattern.split(part)
                
                processed_sub = []
                for sub in sub_parts:
                    if url_pattern.match(sub):
                        processed_sub.append(sub)
                    else:
                        processed_sub.append(self.add_furigana_html(sub))
                
                result_parts.append(''.join(processed_sub))
        
        return ''.join(result_parts)


# =============================================================================
# CSS styles for furigana rendering
# =============================================================================

FURIGANA_CSS = """
/* Furigana (Ruby annotation) styles */
ruby {
    ruby-position: over;
    ruby-align: center;
}

rt {
    font-size: 0.5em;
    color: #888;
    font-weight: normal;
    line-height: 1;
}

/* Ensure proper spacing */
ruby > rt {
    display: ruby-text;
    white-space: nowrap;
}

/* For browsers that don't support ruby */
.furigana-fallback {
    display: inline-block;
    text-align: center;
}

.furigana-fallback .reading {
    display: block;
    font-size: 0.5em;
    color: #888;
}

/* Dark mode adjustments */
.dark-mode rt,
.dark-mode .furigana-fallback .reading {
    color: #aaa;
}
"""


# =============================================================================
# Convenience functions
# =============================================================================

_service_instance: Optional[FuriganaService] = None


def get_furigana_service() -> FuriganaService:
    """Get singleton instance of FuriganaService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = FuriganaService()
    return _service_instance


def add_furigana(text: str) -> str:
    """Convenience function to add furigana to text.
    
    Example:
        html = add_furigana("機械学習")
    """
    return get_furigana_service().add_furigana_html(text)


def get_reading(text: str) -> str:
    """Convenience function to get reading of text.
    
    Example:
        reading = get_reading("機械学習")
        # Returns: "きかいがくしゅう"
    """
    return get_furigana_service().get_reading(text)
