"""Dictionary lookup service for various online dictionaries."""
from typing import Dict, Optional, Any
from urllib.parse import quote
import httpx


class DictionaryService:
    """Service for generating dictionary lookup URLs."""
    
    DICTIONARIES = {
        "google_translate": {
            "name": "Google Translate",
            "url_template": "https://translate.google.com/?sl={source_lang}&tl={target_lang}&text={word}",
            "default_source": "auto",
            "default_target": "vi"
        },
        "mazii": {
            "name": "Mazii",
            "url_template": "https://mazii.net/search?dict=javi&query={word}",
            "default_source": "ja",
            "default_target": "vi"
        },
        "google_dictionary": {
            "name": "Google Dictionary",
            "url_template": "https://www.google.com/search?q=define+{word}",
            "default_source": "en",
            "default_target": "en"
        },
        "jdict": {
            "name": "JDict",
            "url_template": "https://jdict.net/search?keyword={word}",
            "default_source": "ja",
            "default_target": "en"
        },
        "wordnik": {
            "name": "Wordnik",
            "url_template": "https://www.wordnik.com/words/{word}",
            "default_source": "en",
            "default_target": "en"
        },
        "google_search": {
            "name": "Google Search",
            "url_template": "https://www.google.com/search?q={word}",
            "default_source": "auto",
            "default_target": "auto"
        },
        "jisho": {
            "name": "Jisho",
            "url_template": "https://jisho.org/search/{word}",
            "default_source": "ja",
            "default_target": "en"
        },
        "weblio": {
            "name": "Weblio",
            "url_template": "https://ejje.weblio.jp/content/{word}",
            "default_source": "ja",
            "default_target": "en"
        },
        "chatgpt": {
            "name": "ChatGPT",
            "url_template": "https://chat.openai.com/",
            "default_source": "auto",
            "default_target": "auto"
        },
        "gemini": {
            "name": "Gemini",
            "url_template": "https://gemini.google.com/app",
            "default_source": "auto",
            "default_target": "auto"
        },
        "copilot": {
            "name": "Copilot",
            "url_template": "https://copilot.microsoft.com/",
            "default_source": "auto",
            "default_target": "auto"
        }
    }
    
    @staticmethod
    def get_dictionary_url(dictionary_id: str, word: str, source_lang: str = None, target_lang: str = None) -> Optional[str]:
        """Get lookup URL for a dictionary.
        
        Args:
            dictionary_id: ID of the dictionary (e.g., "mazii", "google_dictionary")
            word: Word to look up
            source_lang: Source language code (optional)
            target_lang: Target language code (optional)
        
        Returns:
            URL string or None if dictionary not found
        """
        if dictionary_id not in DictionaryService.DICTIONARIES:
            return None
        
        dict_info = DictionaryService.DICTIONARIES[dictionary_id]
        url_template = dict_info["url_template"]
        
        # Use defaults if not provided
        if source_lang is None:
            source_lang = dict_info.get("default_source", "auto")
        if target_lang is None:
            target_lang = dict_info.get("default_target", "en")
        
        # Map language codes for different dictionaries
        lang_map = {
            "ja": "ja",
            "en": "en",
            "vi": "vi",
            "auto": "auto"
        }
        
        source_lang = lang_map.get(source_lang, source_lang)
        target_lang = lang_map.get(target_lang, target_lang)
        
        # Encode word for URL
        encoded_word = quote(word)
        
        # Replace placeholders
        url = url_template.format(
            word=encoded_word,
            source_lang=source_lang,
            target_lang=target_lang
        )
        
        return url
    
    @staticmethod
    def get_available_dictionaries() -> Dict[str, str]:
        """Get list of available dictionaries with their display names."""
        return {k: v["name"] for k, v in DictionaryService.DICTIONARIES.items()}
    
    @staticmethod
    def detect_best_dictionary(word: str, source_lang: str = "auto") -> str:
        """Detect the best dictionary for a given word and language.
        
        Args:
            word: Word to look up
            source_lang: Source language code
        
        Returns:
            Dictionary ID
        """
        # Simple heuristic based on language
        if source_lang in ["ja", "japanese", "jp"]:
            # Japanese text detected
            import re
            if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', word):
                return "mazii"  # Best for Japanese
        elif source_lang in ["en", "english"]:
            return "google_dictionary"  # Good for English
        
        # Default to Google Translate for unknown/auto
        return "google_translate"
    
    # ============= API FETCH METHODS =============
    
    JISHO_API = "https://jisho.org/api/v1/search/words"
    FREE_DICT_API = "https://api.dictionaryapi.dev/api/v2/entries/en"
    
    @staticmethod
    def lookup_japanese(word: str) -> Dict[str, Any]:
        """Lookup Japanese word from Jisho API.
        
        Args:
            word: Japanese word to lookup
            
        Returns:
            Dict with word info: reading, meaning, examples, etc.
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    DictionaryService.JISHO_API,
                    params={"keyword": word}
                )
                response.raise_for_status()
                data = response.json()
            
            if not data.get("data"):
                return {"error": "Không tìm thấy từ này"}
            
            first_result = data["data"][0]
            japanese = first_result.get("japanese", [{}])[0]
            senses = first_result.get("senses", [{}])
            
            # Get meanings
            meanings = []
            for sense in senses[:3]:  # Top 3 meanings
                english_defs = sense.get("english_definitions", [])
                if english_defs:
                    meanings.append(", ".join(english_defs))
            
            # Get parts of speech
            pos = []
            for sense in senses:
                pos.extend(sense.get("parts_of_speech", []))
            
            return {
                "success": True,
                "word": japanese.get("word") or word,
                "reading": japanese.get("reading", ""),
                "meaning": "; ".join(meanings),
                "parts_of_speech": ", ".join(set(pos)),
                "is_common": first_result.get("is_common", False),
                "jlpt": first_result.get("jlpt", []),
            }
            
        except httpx.HTTPError as e:
            return {"error": f"Lỗi kết nối: {str(e)}"}
        except Exception as e:
            return {"error": f"Lỗi xử lý: {str(e)}"}
    
    @staticmethod
    def lookup_english(word: str) -> Dict[str, Any]:
        """Lookup English word from Free Dictionary API.
        
        Args:
            word: English word to lookup
            
        Returns:
            Dict with word info: phonetic, meaning, examples, etc.
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{DictionaryService.FREE_DICT_API}/{word}")
            
            if response.status_code == 404:
                return {"error": "Không tìm thấy từ này"}
            
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                return {"error": "Dữ liệu không hợp lệ"}
            
            first_result = data[0]
            
            # Get phonetic
            phonetic = first_result.get("phonetic", "")
            if not phonetic:
                phonetics = first_result.get("phonetics", [])
                for p in phonetics:
                    if p.get("text"):
                        phonetic = p["text"]
                        break
            
            # Get meanings
            meanings = []
            examples = []
            for meaning in first_result.get("meanings", []):
                pos = meaning.get("partOfSpeech", "")
                definitions = meaning.get("definitions", [])
                
                for defn in definitions[:2]:  # Top 2 definitions per POS
                    meaning_text = defn.get("definition", "")
                    if meaning_text:
                        meanings.append(f"({pos}) {meaning_text}")
                    
                    example = defn.get("example")
                    if example:
                        examples.append(example)
            
            return {
                "success": True,
                "word": first_result.get("word", word),
                "reading": phonetic,  # phonetic as reading
                "meaning": "\n".join(meanings[:4]),  # Top 4 meanings
                "examples": "\n".join(examples[:3]),  # Top 3 examples
            }
            
        except httpx.HTTPError as e:
            return {"error": f"Lỗi kết nối: {str(e)}"}
        except Exception as e:
            return {"error": f"Lỗi xử lý: {str(e)}"}
    
    @staticmethod
    def lookup(word: str, lang: str) -> Dict[str, Any]:
        """Universal lookup method.
        
        Args:
            word: Word to lookup
            lang: Language ("jp" for Japanese, "en" for English)
            
        Returns:
            Lookup result
        """
        if lang == "jp":
            return DictionaryService.lookup_japanese(word)
        else:
            return DictionaryService.lookup_english(word)

