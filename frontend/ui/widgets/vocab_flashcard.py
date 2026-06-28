from typing import Optional, List, Dict, Any
import tempfile
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QScrollArea, QStackedWidget, QTextEdit
)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# Services
from frontend.services import get_tts_service
from frontend.ui.styles.theme import ThemeColors
from frontend.ui.styles.animations import AnimationService
from frontend.utils.async_helpers import run_async

class VocabFlashcardView(QFrame):
    """Anki-style Flashcard Widget extracted from VocabTab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            VocabFlashcardView {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 10px;
                border: 1px solid {ThemeColors.BORDER};
            }}
            QLabel#WordLabel {{
                font-size: 32px;
                font-weight: bold;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QLabel#ReadingLabel {{
                font-size: 18px;
                color: {ThemeColors.TEXT_SECONDARY};
            }}
            QLabel#MeaningLabel {{
                font-size: 20px;
                color: {ThemeColors.SUCCESS};
                font-weight: bold;
            }}
            QTextEdit {{
                border: none;
                background: transparent;
                font-size: 16px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """)
        self._init_ui()
        self.current_card = None
        self.is_flipped = False
        self.tts_service = get_tts_service()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # --- Front Side Content ---
        self.front_container = QWidget()
        self.front_container.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 12px;")
        self.front_container.setCursor(Qt.PointingHandCursor)
        front_layout = QVBoxLayout(self.front_container)
        front_layout.setAlignment(Qt.AlignCenter)
        front_layout.setSpacing(15)
        
        self.word_label = QLabel("Sẵn sàng học")
        self.word_label.setObjectName("WordLabel")
        self.word_label.setAlignment(Qt.AlignCenter)
        self.word_label.setWordWrap(True)
        front_layout.addWidget(self.word_label)
        
        self.reading_label = QLabel("") 
        self.reading_label.setObjectName("ReadingLabel")
        self.reading_label.setAlignment(Qt.AlignCenter)
        front_layout.addWidget(self.reading_label)
        
        self.click_hint = QLabel("👆 Bấm để lật thẻ")
        self.click_hint.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 12px; margin-top: 20px;")
        self.click_hint.setAlignment(Qt.AlignCenter)
        front_layout.addWidget(self.click_hint)
        
        self.stack.addWidget(self.front_container)
        
        # --- Back Side Content ---
        self.back_container = QWidget()
        self.back_container.setStyleSheet(f"background-color: {ThemeColors.BG_TERTIARY}; border-radius: 12px;")
        back_layout = QVBoxLayout(self.back_container)
        back_layout.setContentsMargins(20, 30, 20, 20)
        back_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        back_layout.setSpacing(10)
        
        self.back_word_label = QLabel("")
        self.back_word_label.setObjectName("WordLabel")
        self.back_word_label.setStyleSheet("font-size: 28px;")
        self.back_word_label.setAlignment(Qt.AlignCenter)
        back_layout.addWidget(self.back_word_label)
        
        self.back_reading_label = QLabel("")
        self.back_reading_label.setObjectName("ReadingLabel")
        self.back_reading_label.setAlignment(Qt.AlignCenter)
        back_layout.addWidget(self.back_reading_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setStyleSheet(f"background-color: {ThemeColors.BORDER}; min-height: 1px; max-height: 1px; margin: 10px 0;")
        back_layout.addWidget(line)
        
        self.meaning_label = QLabel("")
        self.meaning_label.setObjectName("MeaningLabel")
        self.meaning_label.setAlignment(Qt.AlignCenter)
        self.meaning_label.setWordWrap(True)
        back_layout.addWidget(self.meaning_label)
        
        self.han_viet_label = QLabel("")
        self.han_viet_label.setStyleSheet(f"font-size: 18px; color: {ThemeColors.ACCENT}; font-weight: bold; margin-bottom: 10px;")
        self.han_viet_label.setAlignment(Qt.AlignCenter)
        back_layout.addWidget(self.han_viet_label)
        
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFrameShape(QFrame.NoFrame)
        self.details_scroll.setStyleSheet("background: transparent;")
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setAlignment(Qt.AlignCenter)
        self.details_text.setStyleSheet("QTextEdit { border: none; background: transparent; font-size: 15px; }")
        
        self.details_scroll.setWidget(self.details_text)
        back_layout.addWidget(self.details_scroll)
        
        self.stack.addWidget(self.back_container)
        
        # --- Audio Buttons ---
        self.controls_container = QWidget()
        controls_layout = QHBoxLayout(self.controls_container)
        controls_layout.setContentsMargins(0, 5, 0, 5)
        controls_layout.setAlignment(Qt.AlignCenter)
        controls_layout.setSpacing(15)
        
        self.audio_btn = QPushButton("🔊 Nghe từ")
        self.audio_btn.setFixedWidth(110)
        self.audio_btn.setStyleSheet(f"padding: 5px; border-radius: 15px; background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; border: 1px solid {ThemeColors.BORDER};")
        self.audio_btn.clicked.connect(self._play_audio)
        self.audio_btn.hide() 
        controls_layout.addWidget(self.audio_btn)
        
        self.example_audio_btn = QPushButton("💬 Nghe ví dụ")
        self.example_audio_btn.setFixedWidth(120)
        self.example_audio_btn.setStyleSheet(f"padding: 5px; border-radius: 15px; background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; border: 1px solid {ThemeColors.BORDER};")
        self.example_audio_btn.clicked.connect(self._play_example_audio)
        self.example_audio_btn.hide()
        controls_layout.addWidget(self.example_audio_btn)
        
        layout.addWidget(self.controls_container)

    def set_card(self, word_data: Dict[str, Any]):
        self.current_card = word_data
        self.is_flipped = False
        
        word = word_data.get("word", "")
        reading = word_data.get("reading", "")
        han_viet = word_data.get("han_viet") or ""
        meaning = word_data.get("meaning", "")
        
        self.word_label.setText(word)
        self.reading_label.setText(reading)
        self.reading_label.hide() 
        
        self.back_word_label.setText(word)
        self.back_reading_label.setText(reading)
        self.meaning_label.setText(meaning)
        
        if han_viet:
            self.han_viet_label.setText(f"Hán Việt: {han_viet}")
            self.han_viet_label.show()
        else:
            self.han_viet_label.hide()
            
        details = ""
        if word_data.get("user_note"):
             details += f"<b>Ghi chú:</b> {word_data['user_note']}<br>"
        if word_data.get("examples"): 
             details += f"<br><b>Ví dụ:</b><br>{word_data['examples'].replace('\\n', '<br>')}"
        self.details_text.setHtml(details)
        
        self.stack.setCurrentIndex(0)
        self.audio_btn.show()
        
        if word_data.get("examples"):
            self.example_audio_btn.show()
        else:
            self.example_audio_btn.hide()

    def flip(self):
        if not self.current_card or self.is_flipped:
            return
        
        self.is_flipped = True
        anim_group = AnimationService.flip_stacked_widget(self.stack)
        
        def on_flip_finished():
            self.reading_label.show()
            target = self.parent()
            while target:
                if hasattr(target, 'auto_pronounce_cb'):
                    if target.auto_pronounce_cb.isChecked():
                        self._play_word_and_example()
                    break
                target = target.parent()
        
        anim_group.finished.connect(on_flip_finished)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.is_flipped and self.current_card:
                self.flip()
                target = self.parent()
                while target:
                    if hasattr(target, '_on_show_answer'):
                        if hasattr(target, 'show_answer_btn'):
                            target.show_answer_btn.hide()
                        if hasattr(target, 'rating_container'):
                            target.rating_container.show()
                        if hasattr(target, 'btn_good'):
                            target.btn_good.setFocus()
                        break
                    target = target.parent()
        super().mousePressEvent(event)

    def _play_word_and_example(self):
        if not self.current_card:
            return
        self._play_audio()
        examples = self.current_card.get("examples", "")
        if examples:
            QTimer.singleShot(1500, self._play_example_audio)

    def _play_audio(self):
        if self.current_card and self.current_card.get("word"):
            text = self.current_card.get("word")
            target = self.parent()
            while target:
                if hasattr(target, '_mixin_speak_text'):
                    target._mixin_speak_text(text)
                    return
                target = target.parent()
            
            from frontend.utils.language_utils import detect_language
            lang = detect_language(text)
            self._play_tts_direct(text, lang)
            
    def _play_example_audio(self):
        if not self.current_card:
            return
        
        examples_text = self.current_card.get("examples", "")
        if not examples_text:
            return
        
        lines = examples_text.split("\n")
        sentences_to_speak = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if " - " in line:
                part = line.split(" - ")[0].strip()
                if part: sentences_to_speak.append(part)
            else:
                sentences_to_speak.append(line)
        
        if not sentences_to_speak: return
            
        word = self.current_card.get("word", "")
        from frontend.utils.language_utils import detect_language
        lang = detect_language(word)
        
        separator = " ... " if lang != "jp" else "、、、" 
        full_text = separator.join(sentences_to_speak)
        
        target = self.parent()
        while target:
            if hasattr(target, '_mixin_speak_text'):
                target._mixin_speak_text(full_text)
                return
            target = target.parent()
            
    def _play_tts_direct(self, text, lang):
        async def speak():
            return await self.tts_service.speak_async(text, lang)
        
        def play(audio_result):
            if not audio_result: return
            path = None
            if isinstance(audio_result, bytes):
                temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                temp.write(audio_result)
                temp.close()
                path = temp.name
            elif isinstance(audio_result, str):
                path = audio_result
                
            if path:
                if not hasattr(self, '_media_player'):
                    self._media_player = QMediaPlayer(self)
                    self._audio_output = QAudioOutput(self)
                    self._media_player.setAudioOutput(self._audio_output)
                self._media_player.setSource(QUrl.fromLocalFile(path))
                self._media_player.play()
        run_async(speak, play)
