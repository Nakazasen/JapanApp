"""Study Session Dialog for Flashcard-style vocabulary review with SRS.

This module provides a modal dialog for reviewing saved vocabulary
using a flashcard interface with SM-2 spaced repetition algorithm.
"""
import random
import base64
import tempfile
import os
from typing import List, Dict, Any, Optional, Callable

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from frontend.services.tts import get_tts_service


class StudySessionDialog(QDialog):
    """Flashcard-style study session dialog with SRS support."""
    
    # States
    STATE_QUESTION = 1
    STATE_ANSWER = 2
    
    # Signal emitted when a card is rated (vocab_id, rating)
    card_rated = Signal(int, int)
    
    def __init__(
        self, 
        parent=None, 
        vocab_list: List[Dict[str, Any]] = None,
        on_rate_callback: Optional[Callable[[int, int], None]] = None
    ):
        """Initialize the study session.
        
        Args:
            parent: Parent widget
            vocab_list: List of vocabulary items to study (from /vocab/due endpoint)
            on_rate_callback: Optional callback function(vocab_id, rating) to call when rating
        """
        super().__init__(parent)
        self.vocab_list = list(vocab_list) if vocab_list else []
        self.on_rate_callback = on_rate_callback
        
        # Don't shuffle SRS list - it's already ordered by due date
        # But we can shuffle new cards
        self.current_index = 0
        self.state = self.STATE_QUESTION
        self.results = {"again": 0, "hard": 0, "good": 0, "easy": 0}
        self.reviewed_count = 0
        
        # TTS components
        self.tts_service = get_tts_service()
        self.media_player = None
        self.audio_output = None
        self._temp_audio_file = None
        
        self._init_ui()
        self._load_card()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("🧠 Chế độ Luyện tập (SRS)")
        self.setFixedSize(700, 600)
        self.setModal(True)
        
        # Dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)
        
        # Stats header
        stats_layout = QHBoxLayout()
        
        self.progress_label = QLabel("Thẻ 1/1")
        self.progress_label.setStyleSheet("color: #888; font-size: 14px;")
        stats_layout.addWidget(self.progress_label)
        
        stats_layout.addStretch()
        
        # SRS info badge
        self.srs_badge = QLabel("")
        self.srs_badge.setStyleSheet("""
            background-color: #2d2d2d;
            color: #888;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
        """)
        stats_layout.addWidget(self.srs_badge)
        
        self.hint_label = QLabel("Bấm Space để lật thẻ")
        self.hint_label.setStyleSheet("color: #666; font-size: 12px; font-style: italic;")
        stats_layout.addWidget(self.hint_label)
        
        layout.addLayout(stats_layout)
        
        # Flashcard frame
        self.card_frame = QFrame()
        self.card_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 16px;
                border: 1px solid #404040;
            }
        """)
        self.card_frame.setMinimumHeight(300)
        
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(30, 35, 30, 35)
        
        # Front side - Kanji/Word (Question)
        self.front_label = QLabel()
        self.front_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.front_label.setFont(QFont("Yu Gothic UI", 48, QFont.Weight.Bold))
        self.front_label.setStyleSheet("color: #ffffff;")
        self.front_label.setWordWrap(True)
        card_layout.addWidget(self.front_label)
        
        # Divider
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.HLine)
        self.divider.setStyleSheet("background-color: #444;")
        self.divider.setFixedHeight(1)
        self.divider.hide()
        card_layout.addWidget(self.divider)
        
        # Back side container (Answer)
        self.back_container = QWidget()
        back_layout = QVBoxLayout(self.back_container)
        back_layout.setSpacing(8)
        back_layout.setContentsMargins(0, 0, 0, 0)
        
        # Furigana
        self.furigana_label = QLabel()
        self.furigana_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.furigana_label.setFont(QFont("Yu Gothic UI", 18))
        self.furigana_label.setStyleSheet("color: #aaa;")
        back_layout.addWidget(self.furigana_label)
        
        # Meaning
        self.meaning_label = QLabel()
        self.meaning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meaning_label.setFont(QFont("Segoe UI", 16))
        self.meaning_label.setStyleSheet("color: #4fc3f7;")
        self.meaning_label.setWordWrap(True)
        back_layout.addWidget(self.meaning_label)
        
        # Example sentence (original language)
        self.example_orig_label = QLabel()
        self.example_orig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.example_orig_label.setFont(QFont("Yu Gothic UI", 13))
        self.example_orig_label.setStyleSheet("color: #888; font-style: italic;")
        self.example_orig_label.setWordWrap(True)
        self.example_orig_label.hide()
        back_layout.addWidget(self.example_orig_label)
        
        # Example sentence (Vietnamese translation)
        self.example_vi_label = QLabel()
        self.example_vi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.example_vi_label.setFont(QFont("Segoe UI", 12))
        self.example_vi_label.setStyleSheet("color: #666; font-style: italic;")
        self.example_vi_label.setWordWrap(True)
        self.example_vi_label.hide()
        back_layout.addWidget(self.example_vi_label)
        
        # Audio replay button
        audio_layout = QHBoxLayout()
        audio_layout.addStretch()
        self.replay_btn = QPushButton("🔊")
        self.replay_btn.setToolTip("Phát lại âm thanh")
        self.replay_btn.setFixedSize(40, 40)
        self.replay_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.replay_btn.clicked.connect(self._speak_current_word)
        self.replay_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #4fc3f7;
            }
        """)
        audio_layout.addWidget(self.replay_btn)
        audio_layout.addStretch()
        back_layout.addLayout(audio_layout)
        
        # Sino-Vietnamese badge
        badge_layout = QHBoxLayout()
        badge_layout.addStretch()
        self.sino_badge = QLabel()
        self.sino_badge.setStyleSheet("""
            background-color: #ff6b6b;
            color: white;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
            font-size: 13px;
        """)
        badge_layout.addWidget(self.sino_badge)
        badge_layout.addStretch()
        back_layout.addLayout(badge_layout)
        
        self.back_container.hide()
        card_layout.addWidget(self.back_container)
        
        card_layout.addStretch()
        layout.addWidget(self.card_frame)
        
        # Flip button
        self.flip_btn = QPushButton("👆 Lật thẻ (Space)")
        self.flip_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent capturing Space key
        self.flip_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.flip_btn.clicked.connect(self._flip_card)
        layout.addWidget(self.flip_btn)
        
        # Rating buttons with interval preview
        self.rating_container = QWidget()
        rating_layout = QHBoxLayout(self.rating_container)
        rating_layout.setSpacing(8)
        
        # Create rating buttons with interval labels
        self.btn_again = self._create_rating_btn("1. Quên", "#e74c3c", "<10 phút")
        self.btn_hard = self._create_rating_btn("2. Khó", "#e67e22", "")
        self.btn_good = self._create_rating_btn("3. Được", "#3498db", "")
        self.btn_easy = self._create_rating_btn("4. Dễ", "#2ecc71", "")
        
        self.btn_again.clicked.connect(lambda: self._rate(1))
        self.btn_hard.clicked.connect(lambda: self._rate(2))
        self.btn_good.clicked.connect(lambda: self._rate(3))
        self.btn_easy.clicked.connect(lambda: self._rate(4))
        
        rating_layout.addWidget(self.btn_again)
        rating_layout.addWidget(self.btn_hard)
        rating_layout.addWidget(self.btn_good)
        rating_layout.addWidget(self.btn_easy)
        
        self.rating_container.hide()
        layout.addWidget(self.rating_container)
        
        # Skip button
        skip_layout = QHBoxLayout()
        skip_layout.addStretch()
        self.skip_btn = QPushButton("Bỏ qua phiên học")
        self.skip_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent capturing Space key
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #444;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #333;
                color: #888;
            }
        """)
        self.skip_btn.clicked.connect(self.reject)
        skip_layout.addWidget(self.skip_btn)
        skip_layout.addStretch()
        layout.addLayout(skip_layout)
    
    def _create_rating_btn(self, text: str, color: str, interval_hint: str = "") -> QPushButton:
        """Create a styled rating button."""
        btn_text = f"{text}\n{interval_hint}" if interval_hint else text
        btn = QPushButton(btn_text)
        btn.setFixedHeight(55 if interval_hint else 45)
        # CRITICAL: Prevent button from capturing Space/Enter key
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 15px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
        """)
        return btn
    
    def _load_card(self):
        """Load current card data."""
        if self.current_index >= len(self.vocab_list):
            self._show_summary()
            return
        
        card = self.vocab_list[self.current_index]
        
        # Update progress
        self.progress_label.setText(f"Thẻ {self.current_index + 1}/{len(self.vocab_list)}")
        
        # Show SRS info
        streak = card.get("srs_streak", 0)
        is_new = card.get("is_new", streak == 0)
        if is_new:
            self.srs_badge.setText("🆕 Mới")
            self.srs_badge.setStyleSheet("""
                background-color: #27ae60;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
            """)
        else:
            interval = card.get("srs_interval", 0)
            self.srs_badge.setText(f"🔥 Chuỗi: {streak} | {self._interval_display(interval)}")
            self.srs_badge.setStyleSheet("""
                background-color: #2d2d2d;
                color: #888;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
            """)
        
        # Get display text - Handle None values safely
        kanji = (card.get("word_kanji") or "").strip()
        kana = (card.get("word_kana") or "").strip()
        word = (card.get("word") or "").strip()  # For English
        meaning = (card.get("meaning_vi") or "").strip()
        note = (card.get("user_note") or "").strip()
        
        # Extract Sino-Vietnamese from note
        sino = ""
        if "Âm Hán Việt:" in note:
            sino = note.replace("Âm Hán Việt:", "").strip()
        
        # Front: Kanji > Kana > Word
        front_text = kanji if kanji else (kana if kana else word)
        self.front_label.setText(front_text)
        
        # Back: Furigana
        if kanji and kana:
            self.furigana_label.setText(kana)
            self.furigana_label.show()
        else:
            self.furigana_label.hide()
        
        self.meaning_label.setText(meaning)
        
        # Example sentences
        example_orig = card.get("example_jp", "") or card.get("example_en", "") or ""
        example_vi = card.get("example_vi", "") or ""
        
        if example_orig.strip():
            self.example_orig_label.setText(f"📖 {example_orig.strip()}")
            self.example_orig_label.show()
        else:
            self.example_orig_label.hide()
        
        if example_vi.strip():
            self.example_vi_label.setText(f"→ {example_vi.strip()}")
            self.example_vi_label.show()
        else:
            self.example_vi_label.hide()
        
        # Badge
        if sino:
            self.sino_badge.setText(f"Âm HV: {sino}")
            self.sino_badge.show()
        else:
            self.sino_badge.hide()
        
        # Reset to question state
        self.state = self.STATE_QUESTION
        self.back_container.hide()
        self.divider.hide()
        self.rating_container.hide()
        self.flip_btn.show()
        self.hint_label.setText("Bấm Space hoặc click Lật thẻ")
        
        # CRITICAL: Set focus back to dialog to capture keyboard events
        # This prevents buttons from capturing Space/Enter and closing dialog
        self.setFocus()
    
    def _interval_display(self, days: int) -> str:
        """Convert days to human-readable Vietnamese interval."""
        if days == 0:
            return "Mới"
        elif days == 1:
            return "1 ngày"
        elif days < 7:
            return f"{days} ngày"
        elif days < 30:
            return f"{days // 7} tuần"
        elif days < 365:
            return f"{days // 30} tháng"
        else:
            return f"{days // 365} năm"
    
    def _flip_card(self):
        """Flip the card to show the answer."""
        if self.state == self.STATE_QUESTION:
            self.state = self.STATE_ANSWER
            self.divider.show()
            self.back_container.show()
            self.rating_container.show()
            self.flip_btn.hide()
            self.hint_label.setText("Đang phát âm...")
            
            # Auto-TTS: read the word aloud
            self._speak_current_word()
    
    def _speak_current_word(self):
        """Speak the current vocabulary word using TTS."""
        from frontend.utils.async_helpers import run_async
        
        if self.current_index >= len(self.vocab_list):
            return
        
        card = self.vocab_list[self.current_index]
        
        # Get word to speak (Kanji > Kana > Word)
        kanji = card.get("word_kanji", "").strip()
        kana = card.get("word_kana", "").strip()
        word = card.get("word", "").strip()
        
        text_to_speak = kanji if kanji else (kana if kana else word)
        if not text_to_speak:
            self.hint_label.setText("Bấm 1-4 hoặc click để đánh giá")
            return
        
        # Determine language
        lang = "ja" if (kanji or kana) else "en"
        
        async def get_tts():
            try:
                # Use TTSService to get audio bytes
                voice = self.tts_service.get_voice_for_lang(lang)
                audio_bytes = await self.tts_service.synthesize_async(text_to_speak, voice)
                
                if audio_bytes:
                    # Construct result dict to match old API for compatibility
                    return {
                        "audio": audio_bytes,
                        "format": "mp3", 
                        "engine": "edge-tts"
                    }
                return None
            except Exception as e:
                print(f"[WARNING] TTS failed: {e}")
                return None
        
        def play_audio(result):
            if not result or "audio" not in result:
                self.hint_label.setText("Bấm 1-4 hoặc click để đánh giá")
                return
            
            try:
                # Get audio format from response (default: mp3)
                audio_format = result.get("format", "mp3")
                suffix = f".{audio_format}"
                engine = result.get("engine", "unknown")
                
                # Decode audio data
                raw_audio = result["audio"]
                if isinstance(raw_audio, str):
                    # Base64 encoded
                    audio_data = base64.b64decode(raw_audio)
                elif isinstance(raw_audio, bytes):
                    audio_data = raw_audio
                else:
                    print(f"[WARNING] Unknown audio_data type: {type(raw_audio)}")
                    self.hint_label.setText("Bấm 1-4 hoặc click để đánh giá")
                    return
                
                # Check if audio is mostly silence (pyttsx3 fallback issue)
                if len(audio_data) < 1000 or audio_data.count(b'\x00') > len(audio_data) * 0.9:
                    print(f"[WARNING] TTS returned empty/silent audio from {engine}")
                    self.hint_label.setText("TTS không hỗ trợ ngôn ngữ này")
                    return
                
                print(f"[DEBUG TTS] Audio: {engine}, format: {audio_format}, size: {len(audio_data)} bytes")
                
                # Clean up previous temp file
                if self._temp_audio_file and os.path.exists(self._temp_audio_file):
                    try:
                        os.remove(self._temp_audio_file)
                    except:
                        pass
                
                # Save to temp file with correct extension
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                    f.write(audio_data)
                    self._temp_audio_file = f.name
                
                print(f"[DEBUG TTS] Saved audio to: {self._temp_audio_file}")
                
                # Play audio using pygame (more reliable than QMediaPlayer)
                try:
                    import pygame
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    pygame.mixer.music.load(self._temp_audio_file)
                    pygame.mixer.music.play()
                    print(f"[DEBUG TTS] Playing audio with pygame")
                except Exception as pygame_err:
                    print(f"[WARNING] pygame failed: {pygame_err}, trying QMediaPlayer")
                    # Fallback to QMediaPlayer
                    if not self.media_player:
                        self.media_player = QMediaPlayer(self)
                        self.audio_output = QAudioOutput(self)
                        self.media_player.setAudioOutput(self.audio_output)
                    self.audio_output.setVolume(1.0)
                    self.media_player.setSource(QUrl.fromLocalFile(self._temp_audio_file))
                    self.media_player.play()
                
                self.hint_label.setText("Bấm 1-4 hoặc click để đánh giá")
                
            except Exception as e:
                import traceback
                print(f"[WARNING] Failed to play TTS audio: {e}")
                traceback.print_exc()
                self.hint_label.setText("Bấm 1-4 hoặc click để đánh giá")
        
        run_async(get_tts, play_audio)
    
    def _rate(self, rating: int):
        """Rate current card and move to next - Optimistic UI."""
        if self.state != self.STATE_ANSWER:
            return
        
        # Visual feedback: flash the button
        self._flash_rating_button(rating)
        
        # Record result locally (Optimistic)
        rating_map = {1: "again", 2: "hard", 3: "good", 4: "easy"}
        self.results[rating_map[rating]] += 1
        self.reviewed_count += 1
        
        # Get current card info BEFORE moving
        current_card = self.vocab_list[self.current_index]
        vocab_id = current_card.get("id")
        
        # IMMEDIATELY move to next card (Optimistic UI - don't wait for API)
        self.current_index += 1
        self._load_card()
        
        # Fire-and-forget: call callback in background (non-blocking)
        if vocab_id and self.on_rate_callback:
            try:
                self.on_rate_callback(vocab_id, rating)
            except Exception as e:
                print(f"[WARNING] Failed to queue review: {e}")
        
        # Emit signal
        if vocab_id:
            self.card_rated.emit(vocab_id, rating)
    
    def _flash_rating_button(self, rating: int):
        """Flash the rating button for visual feedback."""
        from PySide6.QtCore import QTimer
        
        button_map = {
            1: (self.btn_again, "#e74c3c"),
            2: (self.btn_hard, "#e67e22"),
            3: (self.btn_good, "#3498db"),
            4: (self.btn_easy, "#2ecc71")
        }
        
        if rating not in button_map:
            return
            
        btn, original_color = button_map[rating]
        
        # Flash to white
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 15px;
            }}
        """)
        
        # Restore after 100ms
        def restore():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {original_color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 0 15px;
                }}
                QPushButton:hover {{
                    background-color: {original_color}dd;
                }}
            """)
        
        QTimer.singleShot(100, restore)
    
    def _show_summary(self):
        """Show session summary."""
        total = self.reviewed_count
        
        msg = f"""
        <h2>🎉 Hoàn thành phiên ôn tập!</h2>
        <p>Bạn đã ôn tập <b>{total}</b> từ vựng.</p>
        <hr>
        <table style="margin: 10px 0; font-size: 14px;">
            <tr><td style="color: #e74c3c;">❌ Quên:</td><td style="padding-left: 10px;"><b>{self.results['again']}</b></td></tr>
            <tr><td style="color: #e67e22;">⚠️ Khó:</td><td style="padding-left: 10px;"><b>{self.results['hard']}</b></td></tr>
            <tr><td style="color: #3498db;">✓ Được:</td><td style="padding-left: 10px;"><b>{self.results['good']}</b></td></tr>
            <tr><td style="color: #2ecc71;">✅ Dễ:</td><td style="padding-left: 10px;"><b>{self.results['easy']}</b></td></tr>
        </table>
        <p style="color: #888; font-size: 12px;">Các từ đánh giá "Quên" sẽ xuất hiện lại sớm hơn.<br>
        Các từ đánh giá "Dễ" sẽ xuất hiện lại sau nhiều ngày.</p>
        """
        
        QMessageBox.information(self, "Kết quả Ôn tập SRS", msg)
        self.accept()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        key = event.key()
        
        # Space or Enter to flip
        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._flip_card()
            event.accept()
            return
        
        # Number keys to rate (only in answer state)
        if self.state == self.STATE_ANSWER:
            if key == Qt.Key.Key_1:
                self._rate(1)
                event.accept()
                return
            elif key == Qt.Key.Key_2:
                self._rate(2)
                event.accept()
                return
            elif key == Qt.Key.Key_3:
                self._rate(3)
                event.accept()
                return
            elif key == Qt.Key.Key_4:
                self._rate(4)
                event.accept()
                return
        
        # Escape to close
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        
        super().keyPressEvent(event)
