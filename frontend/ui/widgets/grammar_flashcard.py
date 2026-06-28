from typing import Optional, Dict, Any
import markdown
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QStackedWidget, QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt, Signal

# Services
from frontend.services.tts import get_tts_service
from frontend.ui.styles.theme import ThemeColors
from frontend.ui.styles.animations import AnimationService

class GrammarFlashcardView(QFrame):
    """Anki-style Flashcard for Grammar with animations extracted from GrammarTab."""
    
    # Signal emitted when a review is completed (grammar_id, rating)
    review_completed = Signal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            GrammarFlashcardView {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                border: 1px solid {ThemeColors.BORDER};
            }}
            QLabel#PatternLabel {{
                font-size: 32px;
                font-weight: bold;
                color: {ThemeColors.PRIMARY};
            }}
            QLabel#TitleLabel {{
                font-size: 20px;
                color: {ThemeColors.TEXT_SECONDARY};
            }}
            QLabel#MeaningLabel {{
                font-size: 22px;
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
        
        # --- Front Side ---
        self.front_container = QWidget()
        self.front_container.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 12px;")
        self.front_container.setCursor(Qt.PointingHandCursor)
        self.front_layout = QVBoxLayout(self.front_container)
        self.front_layout.setAlignment(Qt.AlignCenter)
        self.front_layout.setSpacing(15)
        
        self.pattern_label = QLabel("Sẵn sàng học")
        self.pattern_label.setObjectName("PatternLabel")
        self.pattern_label.setAlignment(Qt.AlignCenter)
        self.pattern_label.setWordWrap(True)
        self.front_layout.addWidget(self.pattern_label)
        
        self.title_label = QLabel("")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.front_layout.addWidget(self.title_label)
        
        self.click_hint = QLabel("👆 Bấm để xem giải thích")
        self.click_hint.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 12px; margin-top: 20px;")
        self.click_hint.setAlignment(Qt.AlignCenter)
        self.front_layout.addWidget(self.click_hint)
        
        self.stack.addWidget(self.front_container)
        
        # --- Back Side ---
        self.back_container = QWidget()
        self.back_container.setStyleSheet(f"background-color: {ThemeColors.BG_TERTIARY}; border-radius: 12px;")
        self.back_layout = QVBoxLayout(self.back_container)
        self.back_layout.setContentsMargins(20, 25, 20, 20)
        self.back_layout.setAlignment(Qt.AlignTop)
        self.back_layout.setSpacing(10)
        
        self.back_pattern_label = QLabel("")
        self.back_pattern_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ThemeColors.PRIMARY};")
        self.back_pattern_label.setAlignment(Qt.AlignCenter)
        self.back_layout.addWidget(self.back_pattern_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {ThemeColors.BORDER}; min-height: 1px;")
        self.back_layout.addWidget(line)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFrameShape(QFrame.NoFrame)
        self.details_text.setStyleSheet("background: transparent;")
        self.scroll_layout.addWidget(self.details_text)
        
        self.scroll.setWidget(self.scroll_content)
        self.back_layout.addWidget(self.scroll)
        
        self.stack.addWidget(self.back_container)

    def set_card(self, topic):
        """Set card from dict or ORM object."""
        self.current_card = topic
        self.is_flipped = False
        
        title = topic.get("title") if isinstance(topic, dict) else getattr(topic, "title", "")
        pattern = topic.get("pattern") if isinstance(topic, dict) else getattr(topic, "pattern", "")
        desc = topic.get("description") if isinstance(topic, dict) else getattr(topic, "description", "")
        usage = topic.get("usage_notes") if isinstance(topic, dict) else getattr(topic, "usage_notes", "")
        level = topic.get("level") if isinstance(topic, dict) else getattr(topic, "level", "")
        common_mistakes = topic.get("common_mistakes") if isinstance(topic, dict) else getattr(topic, "common_mistakes", "")
        topic_id = topic.get("id") if isinstance(topic, dict) else getattr(topic, "id", None)
        
        display_title = title
        display_pattern = pattern if pattern else ""
             
        self.pattern_label.setText(display_title)
        self.title_label.setText(display_pattern)
        self.title_label.setVisible(bool(display_pattern))
        
        self.back_pattern_label.setText(display_title)
        
        # Build HTML content
        desc_html = markdown.markdown(desc or "") if desc else ""
        usage_html = markdown.markdown(usage or "") if usage else ""
        mistakes_html = markdown.markdown(common_mistakes or "") if common_mistakes else ""
        
        # Fetch examples from database
        examples_html = self._fetch_and_render_examples(topic_id) if topic_id else ""
        
        full_html = f"""
        <div style='font-family: sans-serif;'>
            <div style='color: {ThemeColors.SUCCESS}; font-weight: bold; font-size: 18px; margin-bottom: 10px;'>
                {level if level else ""}
            </div>
            {desc_html}
            {f"<hr style='border: 0; border-top: 1px solid {ThemeColors.BORDER};'><h4>📝 Cách dùng:</h4>{usage_html}" if usage else ""}
            {f"<hr style='border: 0; border-top: 1px solid {ThemeColors.BORDER};'><h4>⚠️ Lỗi thường gặp:</h4>{mistakes_html}" if common_mistakes else ""}
            {examples_html}
        </div>
        """
        self.details_text.setHtml(full_html)
        self.stack.setCurrentIndex(0)
    
    def _fetch_and_render_examples(self, topic_id: int) -> str:
        """Fetch grammar examples from database and render as HTML."""
        try:
            from sqlmodel import select, Session
            from frontend.core.database import engine
            from frontend.models.grammar import GrammarExample
            
            with Session(engine) as session:
                stmt = select(GrammarExample).where(GrammarExample.topic_id == topic_id)
                examples = session.exec(stmt).all()
                
                if not examples:
                    return ""
                
                html_parts = [f"<hr style='border: 0; border-top: 1px solid {ThemeColors.BORDER};'>"]
                html_parts.append("<h4>📚 Ví dụ:</h4>")
                html_parts.append("<div style='margin-left: 10px;'>")
                
                for i, ex in enumerate(examples, 1):
                    html_parts.append(f"<div style='margin-bottom: 15px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px;'>")
                    html_parts.append(f"<div style='font-size: 16px; font-weight: bold; color: #FFD700;'>{i}. {ex.example_text}</div>")
                    
                    if ex.reading:
                        html_parts.append(f"<div style='font-size: 14px; color: #888; font-style: italic;'>📖 {ex.reading}</div>")
                    
                    if ex.translation_vi:
                        html_parts.append(f"<div style='font-size: 14px; color: #4FC3F7;'>🇻🇳 {ex.translation_vi}</div>")
                    elif ex.translation_en:
                        html_parts.append(f"<div style='font-size: 14px; color: #4FC3F7;'>🇬🇧 {ex.translation_en}</div>")
                    
                    if ex.notes:
                        html_parts.append(f"<div style='font-size: 12px; color: #999; margin-top: 5px;'>💡 {ex.notes}</div>")
                    
                    html_parts.append("</div>")
                
                html_parts.append("</div>")
                return "".join(html_parts)
                
        except Exception as e:
            print(f"[GrammarFlashcard] Error fetching examples: {e}")
            return ""

    
    def set_grammar(self, grammar):
        """Alias for set_card, used by Learning Map integration."""
        self.set_card(grammar)

    def flip(self):
        if not self.current_card or self.is_flipped:
            return
        
        self.is_flipped = True
        anim_group = AnimationService.flip_stacked_widget(self.stack)
        
        def on_flip_finished():
            self._check_auto_pronounce()
        
        anim_group.finished.connect(on_flip_finished)

    def _check_auto_pronounce(self):
        target = self.parent()
        while target:
            if hasattr(target, 'auto_pronounce_cb'):
                if target.auto_pronounce_cb.isChecked():
                    self._play_audio()
                break
            target = target.parent()

    def _play_audio(self):
        if not self.current_card:
            return
        pattern = self.current_card.get("pattern") if isinstance(self.current_card, dict) else getattr(self.current_card, "pattern", "")
        if not pattern:
            return
        target = self.parent()
        while target:
            if hasattr(target, '_mixin_speak_text'):
                target._mixin_speak_text(pattern)
                return
            target = target.parent()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.is_flipped:
            self.flip()
            target = self.parent()
            while target:
                if hasattr(target, '_on_show_answer'):
                    target._on_show_answer()
                    break
                target = target.parent()
        super().mousePressEvent(event)
