"""
AI Service - Dynamic Configuration with Waterfall Fallback
============================================================
Port from leetcode_mastery for EnglishApp.
Reads model configuration from external JSON file.
Supports runtime changes without recompiling.

Config file: data/config/ai_settings.json
"""

import os
import sys
import json
import time
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_app_root() -> Path:
    """
    Lấy đường dẫn gốc của ứng dụng.
    Hỗ trợ cả:
    - Chạy từ source code (dev mode)
    - Chạy từ PyInstaller exe (production)
    """
    if getattr(sys, 'frozen', False):
        # Đang chạy từ PyInstaller exe
        # sys.executable là đường dẫn đến file .exe
        return Path(sys.executable).parent
    else:
        # Đang chạy từ source code
        # __file__ = frontend/services/ai_service.py
        # -> parent.parent.parent = project root
        return Path(__file__).parent.parent.parent



# Default config path for EnglishApp (hỗ trợ PyInstaller)
DEFAULT_CONFIG_PATH = get_app_root() / "data" / "config" / "ai_settings.json"
print(f"[ai_service] DEFAULT_CONFIG_PATH = {DEFAULT_CONFIG_PATH}")
print(f"[ai_service] File exists: {DEFAULT_CONFIG_PATH.exists()}")


# Default models if config is missing
DEFAULT_MODELS = [
    {"model_id": "gemini-2.5-flash", "is_active": True, "timeout": 15},
    {"model_id": "gemini-robotics-er-1.5-preview", "is_active": True, "timeout": 30},
    {"model_id": "gemma-3-27b-it", "is_active": True, "timeout": 20},
    {"model_id": "gemma-3-12b-it", "is_active": True, "timeout": 20},
    {"model_id": "gemini-2.5-flash-lite", "is_active": True, "timeout": 10}
]




class AIConfigManager:
    """
    Manages AI configuration from external JSON file.
    Allows runtime updates without code changes.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"✅ Loaded AI config from: {self.config_path}")
            else:
                logger.warning(f"⚠️ Config not found, using defaults: {self.config_path}")
                self._config = self._get_default_config()
                self.save_config()  # Create default config file
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self._config = self._get_default_config()
        
        return self._config
    
    def save_config(self) -> bool:
        """Save current configuration to JSON file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved AI config to: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "api_key": os.getenv("GEMINI_API_KEY", ""),
            "waterfall_strategy": DEFAULT_MODELS.copy()
        }
    
    @property
    def api_key(self) -> str:
        """Get the current API key from config or environment."""
        keys = self._config.get("api_keys", [])
        if keys and isinstance(keys, list):
            # If we have a list of keys, use the first one from the list as the primary
            return keys[0]
        
        key = self._config.get("api_key", "")
        return key if key else os.getenv("GEMINI_API_KEY", "")

    def rotate_api_key(self) -> bool:
        """
        Cycle to the next API key in the pool.
        Moves the current key to the end of the 'api_keys' list.
        """
        keys = self._config.get("api_keys", [])
        if not keys or not isinstance(keys, list) or len(keys) < 2:
            return False
            
        # Rotate: move first to last
        current_key = keys.pop(0)
        keys.append(current_key)
        self._config["api_keys"] = keys
        
        # Update the single api_key field for backward compatibility
        self._config["api_key"] = keys[0]
        
        self.save_config()
        logger.info("🔄 Rotated to next configured API key: ***MASKED***")
        return True

    @property
    def api_keys(self) -> List[str]:
        """Get the full pool of API keys."""
        return self._config.get("api_keys", [])

    @api_keys.setter
    def api_keys(self, value: List[str]):
        """Set the pool of API keys."""
        self._config["api_keys"] = value
        if value:
            self._config["api_key"] = value[0]
    
    @api_key.setter
    def api_key(self, value: str):
        """Set API key in config."""
        self._config["api_key"] = value
    
    @property
    def active_models(self) -> List[str]:
        """Get list of active model IDs in priority order."""
        strategy = self._config.get("waterfall_strategy", DEFAULT_MODELS)
        return [m["model_id"] for m in strategy if m.get("is_active", True)]
    
    @property
    def waterfall_strategy(self) -> List[Dict]:
        """Get full waterfall strategy configuration."""
        return self._config.get("waterfall_strategy", DEFAULT_MODELS)
    
    @waterfall_strategy.setter
    def waterfall_strategy(self, value: List[Dict]):
        """Set waterfall strategy configuration."""
        self._config["waterfall_strategy"] = value
    
    def add_model(self, model_id: str, is_active: bool = True, timeout: int = 10) -> bool:
        """Add a new model to the strategy."""
        for m in self._config["waterfall_strategy"]:
            if m["model_id"] == model_id:
                logger.warning(f"⚠️ Model already exists: {model_id}")
                return False
        
        self._config["waterfall_strategy"].append({
            "model_id": model_id,
            "is_active": is_active,
            "timeout": timeout
        })
        return True
    
    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the strategy."""
        original_len = len(self._config["waterfall_strategy"])
        self._config["waterfall_strategy"] = [
            m for m in self._config["waterfall_strategy"] 
            if m["model_id"] != model_id
        ]
        return len(self._config["waterfall_strategy"]) < original_len


class WaterfallGeminiService:
    """
    AI Service with Waterfall fallback strategy.
    Reads configuration from external JSON file.
    """
    
    def __init__(self, api_key: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize the AI service.
        
        Args:
            api_key: Override API key (uses config/env if None)
            config_path: Path to config JSON file
        """
        self.config_manager = AIConfigManager(config_path)
        self.api_key = api_key or self.config_manager.api_key
        self._genai = None
        self._configured = False
        
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found! Will use web fallback.")
        else:
            self._configure_genai()
    
    @property
    def models_priority(self) -> List[str]:
        """Get active models from config."""
        return self.config_manager.active_models
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config_manager.load_config()
        self.api_key = self.config_manager.api_key
        if self.api_key and not self._configured:
            self._configure_genai()
    
    def _configure_genai(self, force: bool = False) -> bool:
        """Lazily configure the genai library."""
        if self._configured and not force:
            return True
        
        try:
            import google.generativeai as genai
            logger.info("🔧 Configuring Gemini with key: ***MASKED***")
            genai.configure(api_key=self.api_key)
            self._genai = genai
            self._configured = True
            logger.info("✅ Gemini API configured successfully")
            return True
        except ImportError:
            logger.error("❌ google-generativeai package not installed!")
            logger.error("   Run: pip install google-generativeai")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to configure Gemini: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self._configured and self.api_key is not None
    
    def generate_response(self, prompt: str, image: Any = None) -> dict:
        """
        Execute Waterfall strategy to generate AI response.
        
        Args:
            prompt: Text prompt
            image: Optional PIL Image or image data for multimodal models
            
        Returns:
            dict with keys: 'text', 'model_used', 'status'
        """
        if not self.api_key:
            return {
                "text": "",
                "model_used": "WEB_FALLBACK",
                "status": "fallback"
            }
        
        if not self._configured:
            if not self._configure_genai():
                return {
                    "text": "",
                    "model_used": "WEB_FALLBACK", 
                    "status": "fallback"
                }
        
        last_error = None
        
        for model_name in self.models_priority:
            try:
                logger.info(f"🔄 Attempting model: {model_name}...")
                model = self._genai.GenerativeModel(model_name)
                
                # Prepare content (list if image is present)
                if image:
                    contents = [prompt, image]
                else:
                    contents = prompt
                    
                response = model.generate_content(contents)
                
                logger.info(f"✅ Success with: {model_name}")
                return {
                    "text": response.text,
                    "model_used": model_name,
                    "status": "success"
                }
                
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"⚠️ Model {model_name} failed: {err_msg}")
                
                # If it's a quota error, try rotating the API key if multiple keys exist
                if ("429" in err_msg or "quota" in err_msg.lower()) and len(self.config_manager._config.get("api_keys", [])) > 1:
                    logger.info("🚀 Quota exceeded. Attempting API key rotation...")
                    if self.config_manager.rotate_api_key():
                        # Update current key and reconfigure
                        self.api_key = self.config_manager.api_key
                        self._configure_genai(force=True)
                        # Continue with the next model using the NEW key
                        continue
                
                last_error = e
                continue
        
        logger.warning("⚠️ All API models failed. Triggering Web Fallback.")
        return {
            "text": f"All API models failed. Last error: {str(last_error)}",
            "model_used": "WEB_FALLBACK",
            "status": "fallback"
        }
    
    # =========================================================================
    # PROMPT CONSTRUCTORS FOR LANGUAGE LEARNING
    # =========================================================================
    
    def construct_translation_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        return f"""Translate the following text from {source_lang} to {target_lang}.
Provide the translation only, without explanations.

TEXT: {text}

TRANSLATION:"""

    def construct_grammar_check_prompt(self, text: str, language: str) -> str:
        return f"""You are a {language} grammar expert.
Check the following text for grammar errors and provide corrections with explanations.

TEXT: {text}

FORMAT:
- Original: [sentence with error]
- Corrected: [corrected sentence]
- Explanation: [brief explanation]

RESPONSE:"""

    async def enrich_vocabulary(self, word: str, lang: str = "jp") -> Dict[str, Any]:
        """Get structured information about a word using AI.
        
        Args:
            word: The word to enrich
            lang: Language code ('jp' or 'en')
            
        Returns:
            Dict with enriched data or error
        """
        language_name = "tiếng Nhật" if lang == "jp" else "tiếng Anh"
        
        prompt = f"""Bạn là một chuyên gia ngôn ngữ và giáo viên dạy {language_name} tâm huyết. 
Hãy cung cấp thông tin cực kỳ chi tiết và chuyên sâu cho từ vựng sau:
Từ: {word}
Ngôn ngữ: {language_name}

Yêu cầu trả về định dạng JSON duy nhất, không có văn bản thừa, với các trường sau:
- meaning: Nghĩa tiếng Việt đầy đủ, chính xác và tự nhiên nhất.
- reading: Phiên âm hoặc cách đọc (Kana cho tiếng Nhật, IPA cho tiếng Anh).
- han_viet: (Chỉ áp dụng cho tiếng Nhật) Âm Hán Việt của từ (VIẾT HOA).
- examples: 3-5 ví dụ câu hay, thực tế và phổ dụng nhất (mỗi ví dụ là một chuỗi gồm câu gốc và nghĩa tiếng Việt, cách nhau bởi dấu gạch ngang).
- user_note: Thông tin chuyên sâu để người học làm chủ từ vựng, bao gồm:
    1. 🌸 Ngữ cảnh sử dụng: Khi nào nên dùng, dùng trong đời thường hay trang trọng, văn viết hay văn nói.
    2. ⚖️ Lưu ý sắc thái: So sánh với các từ gần nghĩa để thấy sự khác biệt tinh tế.
    3. 💡 Từ liên quan: Đồng nghĩa, trái nghĩa, hoặc các cụ cụm từ (Collocations) hay đi cùng.
    Hãy trình bày bằng tiếng Việt, trình bày thoáng, sử dụng emoji và xuống dòng hợp lý (\n) để dễ theo dõi.

Ví dụ mục user_note cho từ '葬式':
"🌸 Ngữ cảnh sử dụng: Dùng để nói về việc tham dự hoặc tổ chức đám tang trong đời thường hoặc báo chí. Trong văn hóa Nhật, thường gắn với nghi lễ Phật giáo.\\n⚖️ Lưu ý sắc thái: 葬式 là cách nói phổ biến. Nếu muốn trang trọng hơn dùng 葬儀 (tang lễ). Nếu chỉ việc chôn cất dùng 埋葬.\\n💡 Từ liên quan: 参列 (dự lễ), 仏式 (nghi thức Phật giáo)."

JSON:"""
        
        import asyncio
        result = await asyncio.to_thread(self.generate_response, prompt)
        
        if result.get("status") == "success":
            import json
            import re
            text = result.get("text", "")
            
            # Extract JSON from potential markdown blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                content = json_match.group(0) if json_match else text
            
            try:
                data = json.loads(content)
                # Ensure examples is a string if it's currently a list for DB compatibility
                if isinstance(data.get("examples"), list):
                    data["examples"] = "\n".join(data["examples"])
                
                return {"success": True, "data": data}
            except Exception as e:
                logger.error(f"Failed to parse AI JSON: {e}\nRaw content: {text}")
                return {"success": False, "error": f"Lỗi xử lý dữ liệu AI: {str(e)}", "raw": text}
        
        return {"success": False, "error": "AI Service unavailable or failed"}

    async def enrich_vocabulary_batch(self, words: List[str], lang: str = "jp") -> Dict[str, Any]:
        """Get structured information for multiple words using AI (Batch Processing).
        
        Args:
            words: List of words to enrich
            lang: Language code ('jp' or 'en')
            
        Returns:
            Dict containing success status and results (Dict[word, data])
        """
        language_name = "tiếng Nhật" if lang == "jp" else "tiếng Anh"
        word_list_str = ", ".join(words)
        
        prompt = f"""Bạn là chuyên gia ngôn ngữ. Hãy cung cấp thông tin chi tiết cho danh sách từ vựng sau:
Danh sách từ: {word_list_str}
Ngôn ngữ: {language_name}

Yêu cầu trả về một JSON Object duy nhất, trong đó key là từ vựng gốc, value là thông tin chi tiết.
Định dạng cho mỗi từ:
- meaning: Nghĩa tiếng Việt đầy đủ, chính xác nhất.
- reading: Phiên âm (Kana cho tiếng Nhật hoặc IPA cho tiếng Anh).
- han_viet: (Nếu là tiếng Nhật) Âm Hán Việt (VIẾT HOA).
- examples: Mảng chứa 2 ví dụ chất lượng (câu gốc - nghĩa Việt).
- user_note: Phân tích chuyên sâu về từ vựng (🌸 Ngữ cảnh, ⚖️ Sắc thái, 💡 Từ liên quan). Sử dụng Emoji và \n để trình bày đẹp mắt như một giáo viên thực thụ.

Ví dụ JSON trả về:
{{
  "word1": {{
    "meaning": "...",
    "reading": "...",
    "examples": ["Ex1 - Nghĩa 1"],
    "han_viet": "...",
    "user_note": "🌸 Dùng trong văn nói hàng ngày. ⚖️ Phân biệt với..."
  }},
  "word2": {{
    "meaning": "...",
    ...
  }}
}}

Chỉ trả về JSON thuần túy, không markdown, không lời dẫn."""

        import asyncio
        result = await asyncio.to_thread(self.generate_response, prompt)
        
        if result.get("status") == "success":
            import json
            import re
            text = result.get("text", "")
            
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                content = json_match.group(0) if json_match else text
            
            try:
                data = json.loads(content)
                # Normalize data (convert example lists to strings)
                for word, details in data.items():
                    if isinstance(details.get("examples"), list):
                        details["examples"] = "\n".join(details["examples"])
                
                return {"success": True, "results": data}
            except Exception as e:
                logger.error(f"Failed to parse Batch AI JSON: {e}\nRaw content: {text}")
                return {"success": False, "error": f"Lỗi xử lý dữ liệu AI: {str(e)}"}
        
        return {"success": False, "error": "AI Service unavailable"}

    async def enrich_kanji_batch(self, kanjis: List[str]) -> Dict[str, Any]:
        """Get structured information for multiple Kanji characters using AI.
        
        Args:
            kanjis: List of kanji characters (e.g., ["食", "飲"])
            
        Returns:
            Dict containing success status and results (Dict[kanji, data])
        """
        kanji_list_str = ", ".join(kanjis)
        
        prompt = f"""Bạn là một chuyên gia về Hán tự và là một giáo viên dạy tiếng Nhật cực kỳ tâm huyết. 
Hãy cung cấp thông tin chi tiết và "có hồn" cho danh sách chữ Hán sau:
Danh sách chữ: {kanji_list_str}

Yêu cầu trả về một JSON Object duy nhất, trong đó key là chữ Hán gốc, value là thông tin chi tiết chuyên sâu. 
Dữ liệu phải tuyệt đối chính xác theo từ điển Hán - Nhật chuẩn.

Định dạng cho mỗi chữ Hán:
- meaning_vi: Nghĩa tiếng Việt cốt lõi, chính xác và đầy đủ nhất.
- han_viet: Âm Hán Việt (BẮT BUỘC VIẾT HOA).
- onyomi: Âm On (Katakana), liệt kê đầy đủ các âm phổ biến.
- kunyomi: Âm Kun (Hiragana), liệt kê đầy đủ các âm phổ biến.
- radicals: Bộ thủ chính (Tên bộ bằng cả chữ Hán, Hiragana và nghĩa Việt).
- components: Các thành phần cấu thành chữ Hán đó (Bẻ nhỏ chữ ra để dễ học).
- mnemonic: Một câu chuyện hoặc mẹo nhớ chữ Hán này thật thông minh, hài hước và dễ đi vào lòng người.
- vocabulary: Mảng chứa 3-5 từ vựng thông dụng quan trọng nhất chứa chữ Hán này (Mỗi phần tử gồm: word, reading, han_viet, meaning).

Ví dụ định dạng JSON trả về:
{{
  "食": {{
    "meaning_vi": "ĂN, thực phẩm",
    "han_viet": "THỰC",
    "onyomi": "ショク, ジキ",
    "kunyomi": "た.べる, く.らう",
    "radicals": "食 (Shoku - Thực / Đồ ăn)",
    "components": "人 (Người) + 良 (Tốt) -> Người ta ăn đồ tốt để khỏe mạnh.",
    "mnemonic": "🍎 Mẹo nhớ: Muốn thành người TỐT (良) thì trước hết phải biết ĂN (食) no đã!",
    "vocabulary": [
      {{"word": "食事", "reading": "しょくじ", "han_viet": "THỰC SỰ", "meaning": "Bữa ăn"}},
      {{"word": "食べ物", "reading": "たべもの", "han_viet": "THỰC VẬT", "meaning": "Đồ ăn"}}
    ]
  }}
}}

Chỉ trả về JSON thuần túy, không markdown, không lời dẫn."""

        import asyncio
        result = await asyncio.to_thread(self.generate_response, prompt)
        
        if result.get("status") == "success":
            import json
            import re
            text = result.get("text", "")
            
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                content = json_match.group(0) if json_match else text
            
            try:
                data = json.loads(content)
                return {"success": True, "results": data}
            except Exception as e:
                logger.error(f"Failed to parse Batch Kanji AI JSON: {e}\nRaw content: {text}")
                return {"success": False, "error": f"Lỗi xử lý dữ liệu AI: {str(e)}"}
        
        return {"success": False, "error": "AI Service unavailable"}

    def construct_vocabulary_prompt(self, word: str, language: str) -> str:
        return f"""Provide detailed information about this {language} word:

WORD: {word}

FORMAT (in Vietnamese):
1. Nghĩa gốc (Definition)
2. Phiên âm (Pronunciation)
3. Loại từ (Part of speech)
4. Ví dụ câu (Example sentences - 2-3 examples)
5. Từ đồng nghĩa (Synonyms)
6. Từ trái nghĩa (Antonyms)
7. Cách sử dụng phổ biến (Common usage patterns)

RESPONSE:"""

    async def enrich_grammar(self, pattern: str, lang: str = "jp") -> Dict[str, Any]:
        """Get structured information about a grammar pattern using AI.
        
        Args:
            pattern: The grammar pattern or title to enrich
            lang: Language code ('jp' or 'en')
            
        Returns:
            Dict with enriched data or error
        """
        language_name = "tiếng Nhật" if lang == "jp" else "tiếng Anh"
        
        prompt = f"""Bạn là một chuyên gia ngôn ngữ và giáo viên dạy {language_name} cực kỳ am hiểu. 
Hãy cung cấp thông tin chi tiết, chính xác và dễ hiểu nhất cho cấu trúc ngữ pháp sau:
Cấu trúc: {pattern}
Ngôn ngữ: {language_name}

Yêu cầu trả về định dạng JSON duy nhất, không có văn bản thừa, với các trường sau:
- meaning: Nghĩa tiếng Việt cốt lõi và chính xác nhất của cấu trúc.
- description: Giải thích sâu về hoàn cảnh sử dụng, sắc thái (nuance), và sự khác biệt với các cấu trúc tương tự nếu có.
- usage_notes: Công thức kết hợp chi tiết (ví dụ: V-te + ..., N + no ...). Trình bày rõ ràng.
- examples: 3-5 ví dụ thực tế, từ đơn giản đến phức tạp (mỗi ví dụ là một chuỗi gồm câu gốc và nghĩa tiếng Việt, cách nhau bởi dấu gạch ngang).
- common_mistakes: Các lỗi mà người học hay mắc phải hoặc những lưu ý cực kỳ quan trọng để không dùng sai.

Hãy trình bày nội dung trong description, usage_notes và common_mistakes bằng tiếng Việt, sử dụng emoji, xuống dòng (\n) để người học dễ dàng tiếp thu.

Ví dụ định dạng trả về:
{{
  "meaning": "...",
  "description": "🌸 Sắc thái: ...\\n⚖️ So sánh: ...",
  "usage_notes": "💡 Cách chia:\\n- Động từ: ...\\n- Danh từ: ...",
  "examples": ["Ví dụ 1 - Nghĩa 1", "Ví dụ 2 - Nghĩa 2"],
  "common_mistakes": "⚠️ Lưu ý: ..."
}}

JSON:"""
        
        import asyncio
        result = await asyncio.to_thread(self.generate_response, prompt)
        
        if result.get("status") == "success":
            import json
            import re
            text = result.get("text", "")
            
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            content = json_match.group(1) if json_match else re.search(r'\{.*\}', text, re.DOTALL).group(0) if re.search(r'\{.*\}', text, re.DOTALL) else text
            
            try:
                data = json.loads(content)
                if isinstance(data.get("examples"), list):
                    data["examples"] = "\n".join(data["examples"])
                return {"success": True, "data": data}
            except Exception as e:
                return {"success": False, "error": f"Lỗi xử lý dữ liệu AI: {str(e)}", "raw": text}
        
        return {"success": False, "error": "AI Service unavailable or failed"}

    async def enrich_grammar_batch(self, patterns: List[str], lang: str = "jp") -> Dict[str, Any]:
        """Get structured information for multiple grammar patterns (Batch Processing)."""
        language_name = "tiếng Nhật" if lang == "jp" else "tiếng Anh"
        # Prepare numbered list for the prompt
        numbered_patterns = [f"{i+1}. {p}" for i, p in enumerate(patterns)]
        pattern_list_str = "\n".join(numbered_patterns)
        
        prompt = f"""Bạn là chuyên gia ngôn ngữ. Hãy cung cấp thông tin chi tiết cho danh sách cấu trúc ngữ pháp sau:
{pattern_list_str}

Ngôn ngữ: {language_name}

YÊU CẦU:
Trả về một JSON Object duy nhất. Trong đó, KEY phải là số thứ tự tương ứng (1, 2, 3...) từ danh sách trên, và VALUE là thông tin chi tiết.
Việc dùng số làm KEY là BẮT BUỘC để đảm bảo đối chiếu chính xác.

Mỗi cấu trúc cần:
- meaning: Nghĩa tiếng Việt.
- description: Giải thích ngắn.
- usage_notes: Cách kết hợp.
- examples: Mảng 2 ví dụ (câu gốc - nghĩa Việt).
- common_mistakes: Lưu ý.

Mẫu JSON trả về:
{{
  "1": {{
    "meaning": "...",
    "description": "...",
    "examples": ["Ex1 - Nghĩa 1"],
    "usage_notes": "...",
    "common_mistakes": "..."
  }},
  "2": {{ ... }}
}}

JSON:"""
        
        import asyncio
        result = await asyncio.to_thread(self.generate_response, prompt)
        
        if result.get("status") == "success":
            import json
            import re
            text = result.get("text", "")
            
            # Robust JSON extraction
            content = ""
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Find first { and last }
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1:
                    content = text[start:end+1]
                else:
                    content = text
            
            try:
                # Clean up common JSON issues from AI
                content = content.strip()
                # Remove trailing commas before closing braces/brackets
                content = re.sub(r',\s*([\]\}])', r'\1', content)
                
                data = json.loads(content)
                return {"success": True, "results": data}
            except Exception as e:
                logger.error(f"Failed to parse Batch Grammar AI JSON: {e}\nRaw content: {text}")
                return {"success": False, "error": f"Lỗi xử lý dữ liệu AI: {str(e)}", "raw": text}
        
        return {"success": False, "error": "AI Service unavailable or failed"}


# =========================================================================
# PLAYGROUND: Test Connection Function
# =========================================================================

def test_single_model_connection(api_key: str, model_name: str, test_prompt: str = "Ping") -> Dict[str, Any]:
    """
    Test connection to a single model.
    Used by Playground UI to validate models before adding to strategy.
    
    Args:
        api_key: Gemini API key to test
        model_name: Model ID to test
        test_prompt: Simple prompt for testing
        
    Returns:
        dict with 'success', 'latency', 'reply' or 'error'
    """
    try:
        import google.generativeai as genai
        
        start_time = time.time()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(test_prompt)
        latency = round((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "latency": f"{latency}ms",
            "reply": response.text[:200]  # Truncate for display
        }
    except ImportError:
        return {
            "success": False,
            "error": "google-generativeai package not installed"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Singleton instance
_ai_service_instance = None


def get_ai_service(api_key: Optional[str] = None) -> WaterfallGeminiService:
    """Get singleton AI service instance."""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = WaterfallGeminiService(api_key=api_key)
    return _ai_service_instance


def get_config_manager() -> AIConfigManager:
    """Get config manager from singleton service."""
    return get_ai_service().config_manager
