"""TOEIC Listening Practice Tab.

Tab for practicing TOEIC Listening Parts 1-4.
Refactored to use ToeicPracticeLayout.
"""
import os
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget, QScrollArea, QGridLayout,
    QSizePolicy, QHBoxLayout
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from frontend.services.toeic_listening_service import get_toeic_listening_service
from frontend.ui.widgets.toeic_question_card import ToeicQuestionCard
from frontend.ui.styles.theme import ThemeColors
from frontend.core.config import settings
from frontend.utils.toast_helper import toast_success, toast_error, toast_info
from frontend.ui.widgets.toeic_practice_layout import ToeicPracticeLayout

class PartCard(QFrame):
    """Card widget for selecting a TOEIC Listening part."""
    
    def __init__(self, part_data: Dict[str, Any], on_click, parent=None):
        super().__init__(parent)
        self.part_data = part_data
        self.on_click = on_click
        
        self.setObjectName("PartCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            #PartCard {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                padding: 16px;
                border: 2px solid transparent;
            }}
            #PartCard:hover {{
                border: 2px solid {ThemeColors.PRIMARY};
                background-color: {ThemeColors.BG_TERTIARY};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Icon and title
        header = QHBoxLayout()
        icon_label = QLabel(part_data.get("icon", "🎧"))
        icon_label.setStyleSheet("font-size: 24px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(part_data.get("name", "Part"))
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {ThemeColors.TEXT_PRIMARY};
        """)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        # Description
        desc_label = QLabel(part_data.get("description", ""))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {ThemeColors.TEXT_SECONDARY};
        """)
        layout.addWidget(desc_label)
        
        # Question count
        count = part_data.get("count", 0)
        count_label = QLabel(f"📝 {count} questions available")
        count_label.setStyleSheet(f"""
            font-size: 12px;
            color: {ThemeColors.TEXT_MUTED};
            margin-top: 8px;
        """)
        layout.addWidget(count_label)
    
    def mousePressEvent(self, event):
        """Handle click event."""
        if event.button() == Qt.LeftButton:
            self.on_click(self.part_data)
        super().mousePressEvent(event)


class ToeicListeningTab(QWidget):
    """TOEIC Listening Practice Tab."""
    
    def __init__(self):
        super().__init__()
        self.service = get_toeic_listening_service()
        
        # State
        self.current_part: Optional[int] = None
        self.items: List[Dict[str, Any]] = [] 
        self.current_idx: int = 0
        self.correct_count: int = 0
        self.answered_count: int = 0
        self.total_questions_count: int = 0
        
        # Audio Player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self._init_ui()
        self._load_parts()
    
    @property
    def is_set_mode(self) -> bool:
        return self.current_part in [3, 4]
    
    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Use Stacked Widget for Part Selection vs Practice Mode
        self.content_stack = QStackedWidget()
        
        # Page 0: Part Selection
        self.part_selection_page = self._create_part_selection_page()
        self.content_stack.addWidget(self.part_selection_page)
        
        # Page 1: Practice View (Using ToeicPracticeLayout)
        self.practice_view = ToeicPracticeLayout()
        # Connect Navigation
        self.practice_view.prev_clicked.connect(self._prev_question)
        self.practice_view.next_clicked.connect(self._next_question)
        self.practice_view.submit_clicked.connect(self._check_current_answer)
        # Custom Back Button logic? The layout doesn't have a "Back to Menu" button. 
        # We can add one or use a separate way.
        # But we need to inject the Audio Controls into the layout or the content area.
        
        # Let's customize the practice_view navigation: add "Back" check if needed or just handle it.
        # Navigation logic handles Prev/Next. Back to menu is usually distinct.
        # We can add a "Back" button to the header of the layout dynamically?
        # Or just keep it simpler.
        
        # Create Content Container for inside the layout
        self.practice_content = QWidget()
        prac_layout = QVBoxLayout(self.practice_content)
        
        # Audio Controls Row
        audio_frame = QFrame()
        audio_frame.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 12px; padding: 10px;")
        audio_layout = QHBoxLayout(audio_frame)
        
        self.btn_back_menu = QPushButton("📋 Menu")
        self.btn_back_menu.setStyleSheet("border: none; color: gray; font-weight: bold;")
        self.btn_back_menu.clicked.connect(self._go_back)
        audio_layout.addWidget(self.btn_back_menu)
        
        self.play_btn = QPushButton("▶️ Play Audio")
        self.play_btn.clicked.connect(self._toggle_audio)
        self.play_btn.setStyleSheet(f"background-color: {ThemeColors.PRIMARY}; color: white; border-radius: 15px; padding: 5px 15px;")
        audio_layout.addWidget(self.play_btn)
        
        self.audio_status = QLabel("Ready")
        audio_layout.addWidget(self.audio_status)
        audio_layout.addStretch()
        
        prac_layout.addWidget(audio_frame)
        
        # Question Scroll Area
        self.question_scroll = QScrollArea()
        self.question_scroll.setWidgetResizable(True)
        self.question_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.question_container = QWidget()
        self.question_layout = QVBoxLayout(self.question_container)
        self.question_scroll.setWidget(self.question_container)
        
        prac_layout.addWidget(self.question_scroll)
        
        self.practice_view.set_content(self.practice_content)
        self.content_stack.addWidget(self.practice_view)
        
        self.main_layout.addWidget(self.content_stack)

    def _create_part_selection_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        header = QLabel("🎧 TOEIC Listening Practice")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        layout.addWidget(header)
        
        self.stats_label = QLabel("Loading stats...")
        layout.addWidget(self.stats_label)
        
        self.parts_grid = QGridLayout()
        layout.addLayout(self.parts_grid)
        layout.addStretch()
        
        return page

    def _load_parts(self):
        parts = self.service.list_parts()
        
        while self.parts_grid.count():
            item = self.parts_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for idx, part in enumerate(parts):
            card = PartCard(part, self._on_part_selected)
            self.parts_grid.addWidget(card, idx // 2, idx % 2)
            
        stats = self.service.get_stats()
        self.stats_label.setText(f"📊 Answered: {stats['answered']}/{stats['total_questions']} | Accuracy: {stats['accuracy']}%")

    def _on_part_selected(self, part_data: Dict[str, Any]):
        self.current_part = part_data["part"]
        
        if self.is_set_mode:
            self.items = self.service.list_question_sets(self.current_part)
            self.total_questions_count = sum(len(item["questions"]) for item in self.items)
        else:
            self.items = self.service.list_questions(self.current_part)
            self.total_questions_count = len(self.items)
            
        self.current_idx = 0
        self.correct_count = 0
        self.answered_count = 0
        
        if not self.items:
            toast_error(f"No data available for Part {self.current_part}.")
            return
            
        self.service.start_session(self.current_part)
        
        # Setup Layout
        self.practice_view.set_title(part_data["name"])
        self.practice_view.progress_bar.setMaximum(self.total_questions_count)
        self.practice_view.progress_bar.setValue(0)
        self.practice_view.btn_submit.show()
        
        self._load_current_item()
        self.content_stack.setCurrentIndex(1)
        toast_info(f"Starting {part_data['name']}")

    def _load_current_item(self):
        if not self.items or self.current_idx >= len(self.items): return
        
        # Clear questions
        while self.question_layout.count():
            item = self.question_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        item = self.items[self.current_idx]
        self.current_cards = []
        
        if self.is_set_mode:
            for q in item.get("questions", []):
                card = ToeicQuestionCard(q)
                self.question_layout.addWidget(card)
                self.current_cards.append(card)
        else:
            card = ToeicQuestionCard(item)
            # Signal connections if needed
            self.question_layout.addWidget(card)
            self.current_cards.append(card)
            
        self.question_layout.addStretch()
        
        # Update Stats/Progress in Layout
        current_display = self.current_idx + 1
        total_display = len(self.items)
        self.practice_view.update_stats(f"Item {current_display}/{total_display}")
        
        # Nav Buttons State
        self.practice_view.btn_prev.setEnabled(self.current_idx > 0)
        self.practice_view.btn_next.setEnabled(self.current_idx < len(self.items) - 1)
        self.practice_view.btn_submit.setEnabled(True)
        
        # Audio
        audio_path = item.get("audio_path")
        if audio_path:
            full_path = os.path.join(settings.project_root, audio_path.lstrip('/'))
            if os.path.exists(full_path):
                self.media_player.setSource(QUrl.fromLocalFile(full_path))
                self.audio_status.setText("Audio Ready")
            else:
                self.audio_status.setText("Audio Missing")
        else:
            self.audio_status.setText("No Audio")
            
        self.play_btn.setText("▶️ Play")

    def _check_current_answer(self):
        cards = self.current_cards
        
        # Validation
        if not all(c.selected_answer or c.answered for c in cards):
            toast_info("Please answer all questions first")
            return
            
        # Check
        any_correct = False
        for card in cards:
            if card.answered: continue
            
            q_id = card.question.get("id")
            user_ans = card.selected_answer
            
            result = self.service.check_answer(q_id, user_ans)
            if result.get("success"):
                is_correct = result["is_correct"]
                self.answered_count += 1
                if is_correct: 
                    self.correct_count += 1
                    any_correct = True
                    
                self.service.save_progress(q_id, user_ans, is_correct)
                card.show_result(is_correct, result["correct_answer"], result.get("explanation", ""))
                
        self.practice_view.update_progress(self.answered_count, self.total_questions_count)
        self.practice_view.btn_submit.setEnabled(False)

    def _prev_question(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self._load_current_item()

    def _next_question(self):
        if self.current_idx < len(self.items) - 1:
            self.current_idx += 1
            self._load_current_item()
        else:
            self._show_summary()

    def _show_summary(self):
        self.service.end_session(self.correct_count, self.total_questions_count)
        toast_success(f"Complete! Correct: {self.correct_count}/{self.total_questions_count}")
        self._go_back()

    def _go_back(self):
        self.media_player.stop()
        self.content_stack.setCurrentIndex(0)
        self._load_parts()

    def _toggle_audio(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶️ Play")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸️ Pause")
