from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QStackedWidget, QGraphicsOpacityEffect
)
from frontend.ui.styles.theme import ThemeColors
from frontend.services.tts import get_tts_service

class KanjiFlashcardView(QFrame):
    """Anki-style Flashcard for Kanji with animations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            KanjiFlashcardView {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                border: 1px solid {ThemeColors.BORDER};
            }}
            QLabel#KanjiLabel {{
                font-size: 150px;
                font-family: 'Noto Sans JP', 'MS Mincho', serif;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QLabel#ReadingLabel {{
                font-size: 24px;
                color: {ThemeColors.PRIMARY};
            }}
            QLabel#HanVietLabel {{
                font-size: 26px;
                color: {ThemeColors.SUCCESS};
                font-weight: bold;
            }}
            QLabel#MeaningLabel {{
                font-size: 22px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """)
        self._init_ui()
        self.current_card: Optional[Dict[str, Any]] = None
        self.is_flipped = False
        self.tts_service = get_tts_service()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # --- Front Side ---
        self.front_container = QWidget()
        self.front_container.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 12px;")
        self.front_container.setCursor(Qt.PointingHandCursor)
        front_layout = QVBoxLayout(self.front_container)
        front_layout.setAlignment(Qt.AlignCenter)
        front_layout.setSpacing(15)
        
        self.kanji_label = QLabel("漢")
        self.kanji_label.setObjectName("KanjiLabel")
        self.kanji_label.setAlignment(Qt.AlignCenter)
        front_layout.addWidget(self.kanji_label)
        
        # Hint
        self.click_hint = QLabel("👆 Bấm để xem đáp án")
        self.click_hint.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 14px; margin-top: 20px;")
        self.click_hint.setAlignment(Qt.AlignCenter)
        front_layout.addWidget(self.click_hint)
        
        self.stack.addWidget(self.front_container)
        
        # --- Back Side ---
        self.back_container = QWidget()
        self.back_container.setStyleSheet(f"background-color: {ThemeColors.BG_TERTIARY}; border-radius: 12px;")
        back_layout = QVBoxLayout(self.back_container)
        back_layout.setContentsMargins(30, 30, 30, 30)
        back_layout.setAlignment(Qt.AlignCenter)
        back_layout.setSpacing(15)
        
        # Kanji (smaller on back)
        self.back_kanji_label = QLabel("")
        self.back_kanji_label.setStyleSheet(f"font-size: 80px; color: {ThemeColors.TEXT_PRIMARY};")
        self.back_kanji_label.setAlignment(Qt.AlignCenter)
        back_layout.addWidget(self.back_kanji_label)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {ThemeColors.BORDER}; height: 1px;")
        back_layout.addWidget(line)
        
        # Readings (On/Kun)
        self.reading_label = QLabel("")
        self.reading_label.setObjectName("ReadingLabel")
        self.reading_label.setAlignment(Qt.AlignCenter)
        self.reading_label.setWordWrap(True)
        back_layout.addWidget(self.reading_label)
        
        # Hán Việt
        self.hanviet_label = QLabel("")
        self.hanviet_label.setObjectName("HanVietLabel")
        self.hanviet_label.setAlignment(Qt.AlignCenter)
        back_layout.addWidget(self.hanviet_label)
        
        # Meaning
        self.meaning_label = QLabel("")
        self.meaning_label.setObjectName("MeaningLabel")
        self.meaning_label.setAlignment(Qt.AlignCenter)
        self.meaning_label.setWordWrap(True)
        back_layout.addWidget(self.meaning_label)
        
        # Components & Mnemonic if available
        self.extra_label = QLabel("")
        self.extra_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-style: italic; font-size: 14px;")
        self.extra_label.setAlignment(Qt.AlignCenter)
        self.extra_label.setWordWrap(True)
        back_layout.addWidget(self.extra_label)
        
        self.stack.addWidget(self.back_container)

    def set_card(self, kanji_data: Dict[str, Any]):
        """Set card data."""
        self.current_card = kanji_data
        self.is_flipped = False
        
        char = kanji_data.get("kanji", "")
        self.kanji_label.setText(char)
        self.back_kanji_label.setText(char)
        
        # Readings
        onyomi = kanji_data.get("onyomi", "")
        kunyomi = kanji_data.get("kunyomi", "")
        readings = []
        if onyomi: readings.append(f"On: {onyomi}")
        if kunyomi: readings.append(f"Kun: {kunyomi}")
        self.reading_label.setText(" | ".join(readings))
        
        # Hán Việt
        self.hanviet_label.setText(kanji_data.get("han_viet", ""))
        
        # Meaning
        self.meaning_label.setText(kanji_data.get("meaning_vi", ""))
        
        # Extra
        comp = kanji_data.get("components", "")
        mnemonic = kanji_data.get("mnemonic", "")
        extra = ""
        if comp: extra += f"Bộ: {comp}"
        if mnemonic: extra += f"\n💡 {mnemonic}"
        self.extra_label.setText(extra)
        
        self.stack.setCurrentIndex(0)
        
    def flip(self):
        """Flip animation."""
        if not self.current_card or self.is_flipped:
            return
        
        self.is_flipped = True
        
        effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(effect)
        
        # Fade out
        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(150)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InQuad)
        
        def on_fade_out():
            self.stack.setCurrentIndex(1)
            # Fade in
            self.anim2 = QPropertyAnimation(effect, b"opacity")
            self.anim2.setDuration(150)
            self.anim2.setStartValue(0.0)
            self.anim2.setEndValue(1.0)
            self.anim2.setEasingCurve(QEasingCurve.OutQuad)
            
            def on_finished():
                self.stack.setGraphicsEffect(None)
                # Auto-pronounce
                self._check_auto_pronounce()
                
            self.anim2.finished.connect(on_finished)
            self.anim2.start()
            
        self.anim.finished.connect(on_fade_out)
        self.anim.start()

    def mousePressEvent(self, event):
        """Click to flip."""
        if event.button() == Qt.LeftButton and not self.is_flipped:
            self.flip()
            # Notify parent
            target = self.parent()
            while target:
                if hasattr(target, '_show_answer'):
                    target._show_answer()
                    break
                target = target.parent()
        super().mousePressEvent(event)

    def _check_auto_pronounce(self):
        """Play TTS if auto-pronounce is enabled."""
        target = self.parent()
        while target:
            if hasattr(target, 'auto_pronounce_cb'):
                if target.auto_pronounce_cb.isChecked():
                    self._play_audio()
                break
            target = target.parent()

    def _play_audio(self):
        """Play TTS for Kanji reading."""
        if not self.current_card:
            return
            
        char = self.current_card.get("kanji", "")
        if not char:
            return
            
        # Try to find speak mixin
        target = self.parent()
        while target:
            if hasattr(target, '_mixin_speak_text'):
                target._mixin_speak_text(char)
                return
            target = target.parent()
