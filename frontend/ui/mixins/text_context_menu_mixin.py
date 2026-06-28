"""Context menu mixin for text widgets.

This mixin provides reusable context menu functionality for text widgets,
including translation, TTS, and dictionary lookup features.
"""
from typing import Optional, Dict, Callable, Any
from PySide6.QtWidgets import QMenu, QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtCore import QUrl, Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from frontend.utils.language_utils import detect_language
from frontend.utils.async_helpers import run_async
from frontend.services.dictionary_service import DictionaryService
from frontend.services.translator import get_translator_service
from frontend.services.tts import get_tts_service
import base64
import tempfile
import os


class TextContextMenuMixin:
    """
    This mixin provides context menu functionality for text widgets.
    
    This mixin works with local services and does NOT require self.client anymore.
    
    Optional attributes:
    - self.dictionary_dialog: Dialog for dictionary lookup
    - self._mixin_media_player: QMediaPlayer for TTS
    - self._mixin_audio_output: QAudioOutput for TTS
    """
    
    # Translation action definitions
    TRANSLATION_ACTIONS = [
        ("🇻🇳 Dịch sang Tiếng Việt", "auto-vi", None),  # NEW: Quick translate to Vietnamese
        ("🌐 Dịch (Tự phát hiện ngôn ngữ)", "auto", None),
        ("✨ Dịch bằng Gemini AI", "gemini-ai", None),  # NEW: Gemini AI Translation
        None,  # Separator
        ("🇬🇧 → 🇻🇳 Dịch Anh → Việt", "en", "vi"),
        ("🇬🇧 → 🇯🇵 Dịch Anh → Nhật", "en", "ja"),
        ("🇯🇵 → 🇬🇧 Dịch Nhật → Anh", "ja", "en"),
        ("🇯🇵 → 🇻🇳 Dịch Nhật → Việt", "ja", "vi"),
        ("🇻🇳 → 🇬🇧 Dịch Việt → Anh", "vi", "en"),
        ("🇻🇳 → 🇯🇵 Dịch Việt → Nhật", "vi", "ja"),
    ]
    
    # Language name mapping
    LANG_NAMES = {
        "en": "English",
        "ja": "日本語",
        "vi": "Tiếng Việt",
        "auto": "Tự động"
    }
    
    # Context menu styling - light theme for readability
    CONTEXT_MENU_STYLE = """
        QMenu {
            background-color: #ffffff;
            color: #1a1a1a;
            border: 1px solid #d4d4d4;
            border-radius: 8px;
            padding: 6px 0;
        }
        QMenu::item {
            padding: 8px 20px;
            background: transparent;
            color: #1a1a1a;
        }
        QMenu::item:selected {
            background-color: #e8f4fd;
            color: #0066cc;
        }
        QMenu::separator {
            height: 1px;
            background: #e0e0e0;
            margin: 6px 10px;
        }
        QMenu::icon {
            margin-left: 10px;
        }
    """
    
    def _get_selected_text_from_widget(self, text_widget) -> str:
        """Get selected text or word at cursor from a text widget.
        
        Args:
            text_widget: QTextEdit or similar widget with textCursor() method
            
        Returns:
            Selected text or empty string
        """
        cursor = text_widget.textCursor()
        if cursor.hasSelection():
            return cursor.selectedText().strip()
        else:
            # Get word at cursor position
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            return cursor.selectedText().strip()
    
    def _create_translation_menu_items(self, menu: QMenu, selected_text: str) -> None:
        """Add translation actions to the menu.
        
        Args:
            menu: QMenu to add actions to
            selected_text: Text that will be translated
        """
        for action_def in self.TRANSLATION_ACTIONS:
            if action_def is None:
                menu.addSeparator()
            else:
                label, source, target = action_def
                action = QAction(label, self)
                action.triggered.connect(
                    lambda checked, s=source, t=target: self._mixin_translate_text(
                        selected_text, s, t
                    )
                )
                menu.addAction(action)
    
    def _create_dictionary_submenu(self, menu: QMenu, selected_text: str) -> None:
        """Add dictionary lookup submenu to the menu.
        
        Args:
            menu: QMenu to add submenu to
            selected_text: Word to look up
        """
        dict_submenu = QMenu("📚 Tra từ", self)
        
        # Detect language for dictionary selection
        detected_lang = detect_language(selected_text)
        
        # Add dictionary options
        dictionaries = DictionaryService.get_available_dictionaries()
        for dict_id, dict_name in dictionaries.items():
            dict_action = QAction(f"📖 {dict_name}", self)
            dict_action.triggered.connect(
                lambda checked, d=dict_id, lang=detected_lang: self._mixin_lookup_word(
                    selected_text, d, lang
                )
            )
            dict_submenu.addAction(dict_action)
        
        menu.addMenu(dict_submenu)
    
    def _create_tts_action(self, menu: QMenu, selected_text: str) -> None:
        """Add TTS action to the menu.
        
        Args:
            menu: QMenu to add action to
            selected_text: Text to speak
        """
        speak_action = QAction("🔊 Đọc văn bản", self)
        speak_action.triggered.connect(
            lambda: self._mixin_speak_text(selected_text)
        )
        menu.addAction(speak_action)
    
    def create_text_context_menu(self, selected_text: str) -> QMenu:
        """Create a complete context menu for text operations.
        
        Args:
            selected_text: Text that menu actions will operate on
            
        Returns:
            QMenu with all text-related actions
        """
        menu = QMenu(self)
        menu.setStyleSheet(self.CONTEXT_MENU_STYLE)
        
        # Add translation actions
        self._create_translation_menu_items(menu, selected_text)
        menu.addSeparator()
        
        # Add dictionary submenu
        self._create_dictionary_submenu(menu, selected_text)
        
        # Add IT Dictionary action
        it_dict_action = QAction("💻 Tra từ điển IT", self)
        it_dict_action.triggered.connect(
            lambda: self._mixin_lookup_it_term(selected_text)
        )
        menu.addAction(it_dict_action)
        
        menu.addSeparator()
        
        # Add TTS action
        self._create_tts_action(menu, selected_text)
        
        return menu
    
    def show_text_context_menu(self, text_widget, position) -> None:
        """Show context menu for a text widget at the given position.
        
        This is a convenience method that gets selected text and shows the menu.
        
        Args:
            text_widget: QTextEdit or similar widget
            position: Position to show menu at (in widget coordinates)
        """
        selected_text = self._get_selected_text_from_widget(text_widget)
        if not selected_text:
            return
        
        menu = self.create_text_context_menu(selected_text)
        menu.exec(text_widget.mapToGlobal(position))
    
    # ========== Translation Methods ==========
    
    def _mixin_translate_text(
        self, 
        text: str, 
        source_lang: str = "auto", 
        target_lang: Optional[str] = None
    ) -> None:
        """Translate text using the API client.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code (None for auto-detect)
        """
        if not text:
            QMessageBox.warning(self, "Cảnh báo", "Không có văn bản được chọn!")
            return
        
        if source_lang == "auto" and target_lang is None:
            self._mixin_auto_translate(text)
        elif source_lang == "auto-vi":
            self._mixin_auto_translate_to_vi(text)
        elif source_lang == "gemini-ai":
            self._mixin_gemini_translate(text)
        else:
            self._mixin_manual_translate(text, source_lang, target_lang)
    
    def _mixin_gemini_translate(self, text: str) -> None:
        """Translate text using Gemini AI directly (không qua backend)."""
        async def gemini_translate():
            try:
                from frontend.utils.language_utils import detect_language
                from frontend.core.gemini_client import get_gemini_handler
                
                detected_lang = detect_language(text)

                # Build prompt based on source language
                if detected_lang in ["ja", "japanese", "jp"]:
                    prompt = f"""Translate the following Japanese text to Vietnamese and English.

Japanese text:
{text}

Output format (exactly):
Vietnamese: <vietnamese translation>
English: <english translation>"""
                elif detected_lang in ["en", "english"]:
                    prompt = f"""Translate the following English text to Vietnamese and Japanese.

English text:
{text}

Output format (exactly):
Vietnamese: <vietnamese translation>
Japanese: <japanese translation with furigana for kanji>"""
                else:
                    prompt = f"""Translate the following text to Vietnamese and English.

Text:
{text}

Output format (exactly):
Vietnamese: <vietnamese translation>
English: <english translation>"""
                
                # Gọi Gemini trực tiếp (không dùng system instruction phức tạp)
                handler = get_gemini_handler()
                response_text = handler.generate_text(prompt, temperature=0.3)

                
                print(f"[GeminiTranslate] Raw response:\n{response_text}")
                
                # Robust parsing - tìm các dòng có "Vietnamese:", "English:", "Japanese:"
                translations = {}
                lines = response_text.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    for lang_key in ["Vietnamese:", "Tiếng Việt:", "English:", "Japanese:", "日本語:"]:
                        if line.lower().startswith(lang_key.lower()):
                            key = lang_key.rstrip(":")
                            value = line[len(lang_key):].strip()
                            if value:
                                translations[key] = value
                            break
                
                # Fallback nếu không parse được
                if not translations:
                    translations["Bản dịch"] = response_text
                
                return {
                    "success": True,
                    "original": text,
                    "detected_lang": detected_lang,
                    "translations": translations,
                    "engine": "Gemini AI"
                }

            except Exception as e:
                import traceback
                print(f"[ERROR] Gemini translate failed: {e}\n{traceback.format_exc()}")
                return {"success": False, "error": str(e)}
        
        def show_result(result):
            if result.get("success"):
                self._show_mixin_translation_dialog(
                    text,
                    result.get("detected_lang", "auto"),
                    result.get("translations", {}),
                    engine="Gemini AI"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Lỗi dịch Gemini AI",
                    f"Không thể dịch văn bản: {result.get('error', 'Unknown')}"
                )
        
        run_async(gemini_translate, show_result)

    
    def _mixin_auto_translate(self, text: str) -> None:
        """Auto-detect language and translate to all other languages."""
        async def auto_translate():
            try:
                translations = {}
                translator = get_translator_service()
                
                # First, detect language
                detected_lang = detect_language(text)
                
                # Translate based on detected language
                if detected_lang in ["ja", "japanese", "jp"]:
                    result_en = translator.translate(text, "ja", "en")
                    result_vi = translator.translate(text, "ja", "vi")
                    translations["English"] = result_en
                    translations["Tiếng Việt"] = result_vi
                elif detected_lang in ["en", "english"]:
                    result_vi = translator.translate(text, "en", "vi")
                    result_jp = translator.translate(text, "en", "ja")
                    translations["Tiếng Việt"] = result_vi
                    translations["日本語"] = self._format_japanese_translation({"translated": result_jp})
                elif detected_lang in ["vi", "vietnamese"]:
                    result_en = translator.translate(text, "vi", "en")
                    result_jp = translator.translate(text, "vi", "ja")
                    translations["English"] = result_en
                    translations["日本語"] = self._format_japanese_translation({"translated": result_jp})
                else:
                    result_en = translator.translate(text, detected_lang, "en")
                    result_vi = translator.translate(text, detected_lang, "vi")
                    result_jp = translator.translate(text, detected_lang, "ja")
                    translations["English"] = result_en
                    translations["Tiếng Việt"] = result_vi
                    translations["日本語"] = self._format_japanese_translation({"translated": result_jp})
                
                return {
                    "success": True, 
                    "original": text, 
                    "detected_lang": detected_lang, 
                    "translations": translations
                }
            except Exception as e:
                import traceback
                print(f"[ERROR] Auto-translate failed: {e}\n{traceback.format_exc()}")
                return {"success": False, "error": str(e)}
        
        def show_result(result):
            if result.get("success"):
                self._show_mixin_translation_dialog(
                    text, 
                    result.get("detected_lang", "auto"), 
                    result.get("translations", {})
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Lỗi dịch", 
                    f"Không thể dịch văn bản: {result.get('error', 'Unknown')}"
                )
        
        run_async(auto_translate, show_result)
    
    def _mixin_auto_translate_to_vi(self, text: str) -> None:
        """Auto-detect language and translate to Vietnamese only."""
        async def translate_to_vi():
            try:
                translator = get_translator_service()
                
                # Detect source language
                detected_lang = detect_language(text)
                
                # Map detected language to source code
                if detected_lang in ["ja", "japanese", "jp"]:
                    source = "ja"
                elif detected_lang in ["en", "english"]:
                    source = "en"
                elif detected_lang in ["vi", "vietnamese"]:
                    # Already Vietnamese - no need to translate
                    return {
                        "success": True,
                        "original": text,
                        "detected_lang": detected_lang,
                        "translations": {"Tiếng Việt": text + " (đã là tiếng Việt)"}
                    }
                else:
                    source = detected_lang
                
                # Translate to Vietnamese
                result_vi = translator.translate(text, source, "vi")
                
                return {
                    "success": True,
                    "original": text,
                    "detected_lang": detected_lang,
                    "translations": {"Tiếng Việt": result_vi}
                }
            except Exception as e:
                import traceback
                print(f"[ERROR] Auto-translate to Vietnamese failed: {e}\n{traceback.format_exc()}")
                return {"success": False, "error": str(e)}
        
        def show_result(result):
            if result.get("success"):
                self._show_mixin_translation_dialog(
                    text,
                    result.get("detected_lang", "auto"),
                    result.get("translations", {})
                )
            else:
                QMessageBox.warning(
                    self,
                    "Lỗi dịch",
                    f"Không thể dịch văn bản: {result.get('error', 'Unknown')}"
                )
        
        run_async(translate_to_vi, show_result)
    
    def _mixin_manual_translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> None:
        """Translate text with specified source and target languages."""
        async def translate():
            try:
                translator = get_translator_service()
                result = translator.translate(text, source_lang, target_lang)
                return {"success": True, "result": {"translated": result}}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def show_result(result):
            if result.get("success"):
                trans_result = result.get("result", {})
                translated_text = trans_result.get("translated", "")
                
                if target_lang == "ja":
                    translations = {
                        self.LANG_NAMES.get(target_lang, target_lang): 
                        self._format_japanese_translation(trans_result)
                    }
                else:
                    translations = {
                        self.LANG_NAMES.get(target_lang, target_lang): translated_text
                    }
                
                self._show_mixin_translation_dialog(text, source_lang, translations)
            else:
                QMessageBox.warning(
                    self, 
                    "Lỗi dịch", 
                    f"Không thể dịch văn bản: {result.get('error', 'Unknown')}"
                )
        
        run_async(translate, show_result)
    
    def _format_japanese_translation(self, result: dict) -> Any:
        """Format Japanese translation result with hiragana if available."""
        jp_text = result.get("translated", "")
        
        # Add hiragana using local service
        try:
            translator = get_translator_service()
            jp_with_hira = translator.add_hiragana(jp_text)
            
            if jp_with_hira and jp_with_hira != jp_text:
                return {"original": jp_text, "with_hiragana": jp_with_hira}
        except Exception as e:
            print(f"[WARNING] Failed to add hiragana: {e}")
            
        return jp_text
    
    def _show_mixin_translation_dialog(
        self, 
        original_text: str, 
        source_lang: str, 
        translations: dict,
        engine: str = "Google Translate"
    ) -> None:
        """Show translation result in a themed dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"✨ Kết quả dịch ({engine})")
        dialog.setMinimumWidth(550)
        
        # Cyberpunk styling for the dialog
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0a0a0f;
                color: #e4e4e7;
                border: 1px solid #2a2a3e;
            }
            QLabel {
                color: #e4e4e7;
                font-size: 13px;
            }
            QPushButton {
                background-color: #a855f7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #9333ea;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Original text section
        lang_name = self.LANG_NAMES.get(source_lang, source_lang.upper())
        orig_title = QLabel(f"<b style='color: #00f5ff;'>Văn bản gốc ({lang_name}):</b>")
        layout.addWidget(orig_title)
        
        original_box = QLabel(original_text)
        original_box.setWordWrap(True)
        original_box.setStyleSheet("""
            background-color: #16161e;
            color: #c0caf5;
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #00f5ff;
        """)
        layout.addWidget(original_box)
        
        # Translations results
        trans_title = QLabel("<b style='color: #ff00a0;'>Bản dịch:</b>")
        layout.addWidget(trans_title)
        
        for lang, translated_text in translations.items():
            lang_label = QLabel(f"<b>{lang}:</b>")
            lang_label.setStyleSheet("color: #71717a; font-size: 11px; margin-top: 5px;")
            layout.addWidget(lang_label)
            
            if isinstance(translated_text, dict) and "with_hiragana" in translated_text:
                # Japanese with hiragana support
                content_html = f"<div style='line-height: 1.6;'>{translated_text['with_hiragana']}</div>"
                trans_box = QLabel(content_html)
                trans_box.setWordWrap(True)
                trans_box.setStyleSheet("""
                    background-color: #1a1b26;
                    color: #e4e4e7;
                    padding: 12px;
                    border-radius: 8px;
                    border: 1px solid #2a2a3e;
                    font-size: 15px;
                """)
                layout.addWidget(trans_box)
                
                if translated_text.get("original"):
                    orig_sub = QLabel(f"<i>Kanji: {translated_text['original']}</i>")
                    orig_sub.setStyleSheet("color: #565f89; font-size: 11px;")
                    orig_sub.setWordWrap(True)
                    layout.addWidget(orig_sub)
            else:
                # Plain text translation
                trans_box = QLabel(translated_text)
                trans_box.setWordWrap(True)
                trans_box.setStyleSheet("""
                    background-color: #1a1b26;
                    color: #e4e4e7;
                    padding: 12px;
                    border-radius: 8px;
                    border: 1px solid #2a2a3e;
                    font-size: 14px;
                """)
                layout.addWidget(trans_box)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    # ========== Dictionary Methods ==========
    
    def _mixin_lookup_word(
        self, 
        word: str, 
        dictionary_id: Optional[str] = None, 
        source_lang: str = "auto"
    ) -> None:
        """Look up word in dictionary.
        
        Args:
            word: Word to look up
            dictionary_id: Optional dictionary to use
            source_lang: Source language of the word
        """
        if not word:
            QMessageBox.warning(self, "Cảnh báo", "Không có từ được chọn!")
            return
        
        # Check if class has dictionary_dialog, create if needed
        if not hasattr(self, 'dictionary_dialog') or self.dictionary_dialog is None:
            from frontend.ui.widgets.dictionary_dialog import DictionaryLookupDialog
            self.dictionary_dialog = DictionaryLookupDialog(self)
            self.dictionary_dialog.finished.connect(
                lambda _: setattr(self, "dictionary_dialog", None)
            )
        
        self.dictionary_dialog.set_lookup(word, source_lang, dictionary_id)
        self.dictionary_dialog.show()
        self.dictionary_dialog.raise_()
        self.dictionary_dialog.activateWindow()
    
    # ========== TTS Methods ==========
    
    def _mixin_speak_text(self, text: str) -> None:
        """Convert text to speech and play it.
        
        Args:
            text: Text to speak
        """
        if not text:
            QMessageBox.warning(self, "Cảnh báo", "Không có văn bản được chọn!")
            return
        
        # Detect language
        language = detect_language(text)
        
        # For long texts, use chunking approach with gTTS locally
        MAX_TTS_CHARS = 500
        if len(text) > MAX_TTS_CHARS:
            self._mixin_speak_long_text(text, language)
            return
        
        # Short text - use local TTS service
        async def generate_speech():
            try:
                tts = get_tts_service()
                audio_path = await tts.speak_async(text, lang=language)
                
                # TTSService.speak_async returns a path to the audio file
                if not os.path.exists(audio_path):
                    return {"success": False, "error": "Không thể tạo file âm thanh"}
                
                with open(audio_path, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up the service-provided temp file
                try:
                    os.remove(audio_path)
                except:
                    pass
                
                return {
                    "success": True,
                    "audio": base64.b64encode(audio_data).decode("utf-8"),
                    "format": "mp3"
                }
            except Exception as e:
                import traceback
                print(f"[ERROR] TTS failed: {e}\n{traceback.format_exc()}")
                return {"success": False, "error": str(e)}

        
        def play_audio(result):
            if not result.get("success"):
                QMessageBox.warning(
                    self, 
                    "Lỗi", 
                    f"Không thể đọc văn bản: {result.get('error', 'Unknown')}"
                )
                return
            
            try:
                audio_base64 = result.get("audio", "")
                if not audio_base64:
                    QMessageBox.warning(self, "Lỗi", "Không nhận được dữ liệu audio")
                    return
                
                audio_data = base64.b64decode(audio_base64)
                
                # Determine file extension based on format
                audio_format = result.get("format", "mp3")
                suffix = f".{audio_format}"
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                temp_file.write(audio_data)
                temp_file.close()
                temp_path = temp_file.name
                
                # Ensure media player exists
                if not hasattr(self, '_mixin_media_player') or self._mixin_media_player is None:
                    self._mixin_media_player = QMediaPlayer(self)
                    self._mixin_audio_output = QAudioOutput(self)
                    self._mixin_media_player.setAudioOutput(self._mixin_audio_output)
                
                self._mixin_audio_output.setVolume(0.8)
                self._mixin_media_player.setSource(QUrl.fromLocalFile(temp_path))
                
                # Cleanup temp file after playback
                def cleanup_on_finished():
                    try:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                    except Exception as e:
                        print(f"[WARNING] Failed to cleanup temp file: {e}")
                
                self._mixin_media_player.playbackStateChanged.connect(
                    lambda state: cleanup_on_finished() 
                    if state == QMediaPlayer.PlaybackState.StoppedState else None
                )
                
                print(f"[DEBUG mixin] Playing audio from {temp_path}")
                self._mixin_media_player.play()
                
            except Exception as e:
                import traceback
                print(f"[ERROR] Play audio failed: {e}\n{traceback.format_exc()}")
                QMessageBox.warning(self, "Lỗi", f"Không thể phát audio: {str(e)}")
        
        run_async(generate_speech, play_audio)
    
    def _mixin_speak_long_text(self, text: str, language: str) -> None:
        """Handle long text TTS using gTTS with chunking.
        
        Args:
            text: Long text to speak
            language: Language code (en, ja, vi, etc.)
        """
        try:
            from gtts import gTTS
            import io
            
            # Show progress notification
            print(f"[TTS] Speaking long text ({len(text)} chars) in {language}...")
            
            # For gTTS, map language codes
            gtts_lang_map = {
                "en": "en",
                "ja": "ja", 
                "vi": "vi",
                "korean": "ko",
                "ko": "ko",
            }
            gtts_lang = gtts_lang_map.get(language, language)
            
            # gTTS can handle longer text - it chunks internally
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(temp_file.name)
            temp_path = temp_file.name
            
            print(f"[TTS] Audio saved to {temp_path}")
            
            # Play using QMediaPlayer
            if not hasattr(self, '_mixin_media_player') or self._mixin_media_player is None:
                self._mixin_media_player = QMediaPlayer(self)
                self._mixin_audio_output = QAudioOutput(self)
                self._mixin_media_player.setAudioOutput(self._mixin_audio_output)
            
            self._mixin_audio_output.setVolume(0.8)
            self._mixin_media_player.setSource(QUrl.fromLocalFile(temp_path))
            
            # Cleanup temp file after playback
            def cleanup_on_finished():
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        print(f"[TTS] Cleaned up temp file")
                except Exception as e:
                    print(f"[WARNING] Failed to cleanup temp file: {e}")
            
            self._mixin_media_player.playbackStateChanged.connect(
                lambda state: cleanup_on_finished() 
                if state == QMediaPlayer.PlaybackState.StoppedState else None
            )
            
            self._mixin_media_player.play()
            
        except ImportError:
            QMessageBox.warning(
                self,
                "Thiếu thư viện",
                "Không tìm thấy gTTS. Vui lòng cài đặt: pip install gtts"
            )
        except Exception as e:
            import traceback
            print(f"[ERROR] Long text TTS failed: {e}\n{traceback.format_exc()}")
            QMessageBox.warning(
                self, 
                "Lỗi TTS", 
                f"Không thể đọc văn bản dài:\n{str(e)}"
            )

    # ========== IT Dictionary Methods ==========
    
    def _mixin_lookup_it_term(self, term: str) -> None:
        """Look up term in IT/Tech Dictionary.
        
        Args:
            term: Technical term to look up
        """
        if not term:
            QMessageBox.warning(self, "Cảnh báo", "Không có từ được chọn!")
            return
        
        try:
            from frontend.services.japanese.it_dictionary import get_it_dictionary, TermDefinition
            
            it_dict = get_it_dictionary()
            result = it_dict.lookup(term)
            
            if result:
                self._show_it_dict_dialog(result)
            else:
                # Try search
                results = it_dict.search(term, limit=3)
                if results:
                    QMessageBox.information(
                        self,
                        "💻 Không tìm thấy chính xác",
                        f"Không tìm thấy '{term}' trong từ điển IT.\n\n"
                        f"Có thể bạn muốn tìm:\n" +
                        "\n".join([f"• {r.term}" for r in results])
                    )
                else:
                    QMessageBox.information(
                        self,
                        "💻 Từ điển IT",
                        f"Không tìm thấy thuật ngữ '{term}' trong từ điển IT.\n\n"
                        f"Thử tra các từ như: machine learning, API, Docker, LLM, GPU..."
                    )
        except Exception as e:
            import traceback
            print(f"[ERROR] IT Dictionary lookup failed: {e}\n{traceback.format_exc()}")
            QMessageBox.warning(self, "Lỗi", f"Không thể tra từ điển IT: {e}")
    
    def _show_it_dict_dialog(self, term) -> None:
        """Show IT Dictionary result in a styled dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"💻 {term.term}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0f0f18;
            }
            QLabel {
                color: #e4e4e7;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(f"<h2 style='color: #00f5ff;'>{term.term}</h2>")
        layout.addWidget(title)
        
        # Category
        cat_label = QLabel(f"<span style='color: #a855f7;'>📂 {term.category}</span>")
        layout.addWidget(cat_label)
        
        # Translations container
        trans_box = QLabel()
        trans_box.setWordWrap(True)
        trans_box.setStyleSheet("""
            background-color: #12121a;
            border: 1px solid #2a2a3e;
            border-radius: 8px;
            padding: 16px;
        """)
        
        trans_html = f"""
        <p><b style='color: #ff9500;'>🇯🇵 Tiếng Nhật:</b><br>
        <span style='font-size: 16px;'>{term.japanese}</span></p>
        
        <p><b style='color: #10b981;'>🇻🇳 Tiếng Việt:</b><br>
        <span style='font-size: 16px;'>{term.vietnamese}</span></p>
        """
        trans_box.setText(trans_html)
        layout.addWidget(trans_box)
        
        # Definition
        def_label = QLabel(f"<b>📝 Định nghĩa:</b><br>{term.definition}")
        def_label.setWordWrap(True)
        def_label.setStyleSheet("""
            background-color: #1a1a2e;
            border-radius: 8px;
            padding: 12px;
        """)
        layout.addWidget(def_label)
        
        # Example
        if term.example:
            ex_label = QLabel(f"<b style='color: #fbbf24;'>💡 Ví dụ:</b><br>{term.example}")
            ex_label.setWordWrap(True)
            ex_label.setStyleSheet("padding: 8px;")
            layout.addWidget(ex_label)
        
        # Related terms
        if term.related:
            rel_label = QLabel(f"<b style='color: #6366f1;'>🔗 Liên quan:</b> {', '.join(term.related)}")
            rel_label.setWordWrap(True)
            rel_label.setStyleSheet("padding: 8px;")
            layout.addWidget(rel_label)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #00f5ff;
                color: #0a0a0f;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #33f7ff;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
