from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QGraphicsOpacityEffect, QMessageBox, QStackedWidget, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRect, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from frontend.ui.styles.theme import ThemeColors
from frontend.services import get_vocab_service, get_tts_service
from frontend.services.ai_service import get_ai_service
from frontend.models.vocab import MasteryStatus
from frontend.utils.async_helpers import run_async

class TinderCard(QFrame):
    """Single Card for Tinder Mode."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Responsive sizing instead of fixed
        self.setMinimumSize(350, 450)  # Minimum readable size
        self.setMaximumSize(650, 600)  # Max height reduced to 600 to save space for buttons
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.setStyleSheet(f"""
            QFrame#TinderCard {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 20px;
                border: 1px solid {ThemeColors.BORDER};
            }}
        """)
        self.setObjectName("TinderCard")
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Header (Word + Pronunciation)
        self.header = QWidget()
        self.header.setStyleSheet("background-color: transparent; border-bottom: 1px solid #ddd;")
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(15, 15, 15, 10)
        
        self.word_lbl = QLabel("")
        self.word_lbl.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {ThemeColors.PRIMARY};")
        self.word_lbl.setAlignment(Qt.AlignCenter)
        self.word_lbl.setWordWrap(True)
        
        self.pronun_lbl = QLabel("")
        self.pronun_lbl.setStyleSheet(f"font-size: 18px; color: {ThemeColors.TEXT_SECONDARY};")
        self.pronun_lbl.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(self.word_lbl)
        header_layout.addWidget(self.pronun_lbl)
        
        self.main_layout.addWidget(self.header)
        
        # 2. Content Area (Scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QWidget { background: transparent; }
        """)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        
        # Meaning
        self.meaning_lbl = QLabel("")
        self.meaning_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        self.meaning_lbl.setAlignment(Qt.AlignCenter)
        self.meaning_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.meaning_lbl)
        
        # Separator (Han Viet if JP)
        self.han_viet_lbl = QLabel("")
        self.han_viet_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeColors.ACCENT}; font-style: italic;")
        self.han_viet_lbl.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.han_viet_lbl)
        
        # Examples
        self.example_lbl = QLabel("")
        self.example_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeColors.TEXT_SECONDARY}; margin-top: 10px;")
        self.example_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.example_lbl)
        
        # Note
        self.note_lbl = QLabel("")
        self.note_lbl.setStyleSheet(f"font-size: 13px; color: #777; font-style: italic; border-top: 1px dashed #ccc; padding-top: 10px;")
        self.note_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.note_lbl)
        
        self.content_layout.addStretch()
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        # 3. Footer (Level Badge)
        self.footer = QWidget()
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(20, 10, 20, 20)
        
        self.level_badge = QLabel("")
        self.level_badge.setStyleSheet(f"background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_SECONDARY}; border-radius: 10px; padding: 4px 12px; font-size: 12px; font-weight: bold;")
        self.level_badge.setAlignment(Qt.AlignCenter)
        self.level_badge.setFixedSize(80, 25)
        
        footer_layout.addStretch()
        footer_layout.addWidget(self.level_badge)
        footer_layout.addStretch()
        
        self.main_layout.addWidget(self.footer)
        
        # Overlay for Swipe Feedback (Like/Nope)
        self.overlay_icon = QLabel(self)
        self.overlay_icon.setAlignment(Qt.AlignCenter)
        self.overlay_icon.setStyleSheet("font-size: 80px; font-weight: bold;")
        self.overlay_icon.hide()
        self.overlay_icon.resize(360, 520) # Cover whole card
        
    def set_data(self, item: Dict[str, Any]):
        self.word_lbl.setText(item.get("word", ""))
        
        # Handle 'nan' or empty pronunciation
        pronun = item.get("pronunciation") or item.get("kanji") or ""
        if str(pronun).lower() == 'nan':
            pronun = ""
        self.pronun_lbl.setText(pronun)
        
        # Meaning
        self.meaning_lbl.setText(item.get("meaning", ""))
        
        # Han Viet
        han_viet = item.get("han_viet")
        if han_viet and str(han_viet).lower() != 'nan':
            self.han_viet_lbl.setText(str(han_viet).upper())
            self.han_viet_lbl.show()
        else:
            self.han_viet_lbl.hide()
            
        # Examples
        ex = item.get("examples")
        if ex and str(ex).lower() != 'nan':
            # Clean up example formatting if needed
            self.example_lbl.setText(f"📝 {ex}")
            self.example_lbl.show()
        else:
            self.example_lbl.hide()
            
        # Notes
        note = item.get("user_note")
        if note and str(note).lower() != 'nan':
             self.note_lbl.setText(f"💡 {note}")
             self.note_lbl.show()
        else:
             self.note_lbl.hide()
             
        self.level_badge.setText(item.get("level", "N/A") or "N/A")
        self.overlay_icon.hide()
        
        # Reset scroll
        self.scroll_area.verticalScrollBar().setValue(0)
        
    def show_feedback(self, is_like: bool):
        self.overlay_icon.show()
        if is_like:
            self.overlay_icon.setText("👍")
            self.overlay_icon.setStyleSheet("font-size: 100px; color: #4CAF50; background: rgba(255, 255, 255, 0.9); border-radius: 20px;")
        else:
            self.overlay_icon.setText("👎")
            self.overlay_icon.setStyleSheet("font-size: 100px; color: #F44336; background: rgba(255, 255, 255, 0.9); border-radius: 20px;")

class TinderSessionWidget(QWidget):
    """
    Tinder-style rapid review session.
    Features:
    - Stack of cards
    - Swipe Left (Hard/Again) / Swipe Right (Easy/Good)
    - Auto-fetch
    """
    session_finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vocab_service = get_vocab_service()
        self.tts_service = get_tts_service()
        self.queue = []
        self.current_index = 0
        self.results = [] # To sync back to DB
        self.current_item_data = {}  # For TTS
        
        self.setStyleSheet(f"background-color: {ThemeColors.BG_PRIMARY};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 120) # Huge bottom margin to clear Pomodoro Timer
        
        # Toolbar
        tb = QHBoxLayout()
        back_btn = QPushButton("❌ Thoát")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {ThemeColors.TEXT_SECONDARY}; 
                border: 1px solid {ThemeColors.BORDER}; border-radius: 15px; padding: 5px 15px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.BG_TERTIARY}; color: #F44336; border: 1px solid #F44336; }}
        """)
        back_btn.clicked.connect(self.end_session)
        
        self.progress_lbl = QLabel("0/0")
        self.progress_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-weight: bold; font-size: 16px;")
        
        tb.addWidget(back_btn)
        tb.addStretch()
        tb.addWidget(self.progress_lbl)
        layout.addLayout(tb)
        
        # Card Area (Centered)
        card_area = QWidget()
        card_layout = QVBoxLayout(card_area)
        card_layout.setAlignment(Qt.AlignCenter)
        
        # We use a container to hold the card for simple animation
        self.card_container = QWidget()
        # Responsive container, remove fixed size
        layout_container = QVBoxLayout(self.card_container)
        layout_container.setContentsMargins(0, 0, 0, 0)
        
        self.card = TinderCard(self.card_container)
        layout_container.addWidget(self.card)
        
        card_layout.addWidget(self.card_container)
        layout.addWidget(card_area)
        
        # Controls (Swipe Buttons)
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(20)
        ctrl_layout.setAlignment(Qt.AlignCenter)
        
        # Responsive buttons
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        self.btn_no = QPushButton("👎 Chưa thuộc")
        self.btn_no.setMinimumHeight(50)
        self.btn_no.setSizePolicy(size_policy)
        self.btn_no.setCursor(Qt.PointingHandCursor)
        self.btn_no.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.BG_SECONDARY}; border: 2px solid #F44336;
                color: #F44336; border-radius: 25px; font-weight: bold; font-size: 14px;
                padding: 0 15px;
            }}
            QPushButton:hover {{ background-color: #FFEBEE; }}
        """)
        self.btn_no.clicked.connect(lambda: self.swipe(False))
        
        self.btn_yes = QPushButton("👍 Đã thuộc")
        self.btn_yes.setMinimumHeight(50)
        self.btn_yes.setSizePolicy(size_policy)
        self.btn_yes.setCursor(Qt.PointingHandCursor)
        self.btn_yes.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.BG_SECONDARY}; border: 2px solid #4CAF50;
                color: #4CAF50; border-radius: 25px; font-weight: bold; font-size: 14px;
                padding: 0 15px;
            }}
            QPushButton:hover {{ background-color: #E8F5E9; }}
        """)
        self.btn_yes.clicked.connect(lambda: self.swipe(True))
        
        # TTS Button
        self.btn_speak = QPushButton("🔊 Đọc")
        self.btn_speak.setFixedSize(60, 50)
        self.btn_speak.setCursor(Qt.PointingHandCursor)
        self.btn_speak.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.BG_SECONDARY}; border: 2px solid {ThemeColors.PRIMARY};
                color: {ThemeColors.PRIMARY}; border-radius: 25px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #E3F2FD; }}
        """)
        self.btn_speak.clicked.connect(self._read_aloud)
        
        # AI Enrich Button
        self.btn_enrich = QPushButton("✨ AI")
        self.btn_enrich.setFixedSize(60, 50)
        self.btn_enrich.setCursor(Qt.PointingHandCursor)
        self.btn_enrich.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.BG_SECONDARY}; border: 2px solid #9C27B0;
                color: #9C27B0; border-radius: 25px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #F3E5F5; }}
        """)
        self.btn_enrich.clicked.connect(self._enrich_current_word)
        
        ctrl_layout.addWidget(self.btn_no, 2) # Stretch factor 2
        ctrl_layout.addWidget(self.btn_speak, 0)
        ctrl_layout.addWidget(self.btn_enrich, 0)
        ctrl_layout.addWidget(self.btn_yes, 2) # Stretch factor 2
        
        layout.addLayout(ctrl_layout)
        layout.addSpacing(20)

    def start_session(self, items: List[Dict[str, Any]], lang: str = "jp"):
        self.queue = items
        self.current_index = 0
        self.results = []
        self.current_lang = lang
        self._update_progress()
        
        if not self.queue:
            QMessageBox.information(self, "Trống", "Không có từ vựng nào để học!")
             # Do NOT emit session_finished here to avoid loop if called from finished handler
             # Just let user click exit
            return
            
        self.show_current_card()
        
    def show_current_card(self):
        if self.current_index >= len(self.queue):
            self.finish_session()
            return
            
        item = self.queue[self.current_index]
        self.current_item_data = item  # Store for TTS
        self.card.set_data(item)
        
        # Reset position
        self.card.move(0, 0)
        self.card.setGraphicsEffect(None)
        
    def swipe(self, is_like: bool):
        # 1. Visual Feedback
        self.card.show_feedback(is_like)
        
        # 2. Logic Result
        item = self.queue[self.current_index]
        self.results.append({
            "id": item["id"],
            "status": MasteryStatus.MASTERED.value if is_like else MasteryStatus.LEARNING.value
        })
        
        # 3. Animate Slide Out
        anim = QPropertyAnimation(self.card, b"pos")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        
        target_x = 500 if is_like else -500
        anim.setEndValue(QPoint(target_x, 0))
        anim.finished.connect(self._on_swipe_finished)
        anim.start()
        
        # Keep reference to avoid GC
        self.current_anim = anim
        
    def _on_swipe_finished(self):
        self.current_index += 1
        self._update_progress()
        self.show_current_card()

    def _update_progress(self):
        self.progress_lbl.setText(f"{self.current_index}/{len(self.queue)}")

    def finish_session(self):
        # Save results to DB
        run_async(self._save_results, self._on_saved)
        
    def _save_results(self):
        # TODO: Batch update vocabulary status
        # For MVP, we just iterate (not efficient but works)
        # In real app, service should have batch_update
        count = 0
        for res in self.results:
            self.vocab_service.update_mastery_status(res["id"], res["status"])
            count += 1
        return count
        
    def _on_saved(self, count):
        QMessageBox.information(self, "Hoàn thành", f"Đã lướt xong {count} từ! 🔥")
        self.session_finished.emit()
        
    def end_session(self):
        # Stop any ongoing TTS
        if self.tts_service:
            self.tts_service.stop()
        self.session_finished.emit()
    
    def _read_aloud(self):
        """Read current card content aloud using TTS (multi-language, in background thread)."""
        if not self.current_item_data or not self.tts_service:
            print("[Tinder TTS] No current_item_data or tts_service")
            return
        
        item = self.current_item_data
        
        # Build speech segments with language tags
        segments = []
        
        # Word
        word = item.get("word", "")
        if word:
            # Use self.current_language for the main word, default to 'ja' if not set
            lang_to_use = getattr(self, 'current_lang', 'ja')
            segments.append((word, lang_to_use))
        
        # Meaning (Vietnamese)
        meaning = item.get("meaning", "")
        if meaning and str(meaning).lower() != 'nan':
            segments.append((f"{meaning}", "vi"))
        
        # Examples (Japanese + Vietnamese - read BOTH parts with correct voices)
        examples = item.get("examples", "")
        if examples and str(examples).lower() != 'nan':
            import re
            # Split by newlines first to get individual example pairs
            lines = str(examples).split('\n')
            
            example_count = 0
            for line in lines:
                if example_count >= 2:  # Limit to 2 examples
                    break
                    
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                
                # If lang is English, just read the whole line as English usually
                if self.current_lang == 'en':
                    segments.append((line, "en"))
                else:
                    # Japanese logic: Try to split JP - VI
                    # Each line might be: "日本語。 - tiếng việt" or just one language
                    # Split by " - " to separate JP and VI
                    parts = re.split(r'\s+-\s+', line)
                    
                    for part in parts:
                        part = part.strip()
                        if not part or len(part) < 2:
                            continue
                        
                        # Detect language: count Japanese characters
                        jp_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', part))
                        vi_chars = len(re.findall(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', part.lower()))
                        
                        if jp_chars > 3:
                            # Japanese part
                            clean = re.sub(r'[。、]+$', '', part)
                            segments.append((clean, "ja"))
                        elif vi_chars > 0 or (jp_chars == 0 and len(part) > 5):
                            # Vietnamese part
                            segments.append((part, "vi"))
                
                example_count += 1
        
        # User notes (Vietnamese) - read explanation/usage notes
        user_note = item.get("user_note", "")
        if user_note and str(user_note).lower() != 'nan':
            # Clean up note, take first 200 chars to avoid too long TTS
            note_text = str(user_note).strip()[:200]
            if note_text:
                segments.append((note_text, "vi"))
        
        if not segments:
            return
        
        print(f"[Tinder TTS] Speaking {len(segments)} segments")
        
        # Run TTS in background thread to prevent UI freeze
        import threading
        import time
        
        def speak_in_background():
            try:
                for text, lang in segments:
                    print(f"[Tinder TTS] Playing ({lang}): {text[:30]}...")
                    self.tts_service.speak_and_play(text, lang=lang)
                    time.sleep(0.3)  # Small pause between segments
            except Exception as e:
                print(f"[Tinder TTS] Error: {e}")
        
        tts_thread = threading.Thread(target=speak_in_background, daemon=True)
        tts_thread.start()
    
    def _enrich_current_word(self):
        """AI Enrich the current word being displayed."""
        if not self.current_item_data:
            return
        
        item = self.current_item_data
        word_id = item.get("id")
        word = item.get("word", "")
        
        if not word_id or not word:
            return
        
        # Disable button during processing
        self.btn_enrich.setEnabled(False)
        self.btn_enrich.setText("⏳")
        
        print(f"[Tinder AI] Enriching word: {word}")
        
        ai_service = get_ai_service()
        
        async def enrich():
            return await ai_service.enrich_vocabulary(word, "jp")
        
        def on_enriched(result):
            self.btn_enrich.setEnabled(True)
            self.btn_enrich.setText("✨ AI")
            
            if result.get("success"):
                enriched_data = result.get("data", {})
                
                # Build update data
                update_data = {"is_ai_enriched": True}
                if enriched_data.get("meaning"):
                    update_data["meaning"] = enriched_data["meaning"]
                if enriched_data.get("reading"):
                    update_data["reading"] = enriched_data["reading"]
                if enriched_data.get("examples"):
                    update_data["examples"] = enriched_data["examples"]
                if enriched_data.get("han_viet"):
                    update_data["han_viet"] = enriched_data["han_viet"]
                if enriched_data.get("user_note"):
                    existing_note = item.get("user_note", "") or ""
                    new_note = enriched_data["user_note"]
                    if new_note and new_note not in existing_note:
                        update_data["user_note"] = f"{existing_note}\n{new_note}" if existing_note else new_note
                
                if update_data:
                    # Save to DB
                    self.vocab_service.update_vocab(word_id, update_data, "jp")
                    
                    # Update local data
                    for key, value in update_data.items():
                        self.current_item_data[key] = value
                    
                    # Update queue item too
                    if self.current_index < len(self.queue):
                        self.queue[self.current_index].update(update_data)
                    
                    # Refresh card display
                    self.card.set_data(self.current_item_data)
                    
                    print(f"[Tinder AI] Enriched: {word}")
                    QMessageBox.information(self, "AI Làm giàu", f"Đã làm giàu từ '{word}'! ✨")
            else:
                error_msg = result.get("error", "Không xác định")
                print(f"[Tinder AI] Error: {error_msg}")
                QMessageBox.warning(self, "Lỗi AI", f"Không thể làm giàu từ vựng:\n{error_msg}")
        
        run_async(enrich, on_enriched)
