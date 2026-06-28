"""TOEIC Question Card Widget.

Reusable widget for displaying a single TOEIC listening question.
"""
from typing import Dict, Any, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QButtonGroup, QRadioButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from frontend.ui.styles.theme import ThemeColors


class ToeicQuestionCard(QFrame):
    """Widget for displaying a TOEIC question with options."""
    
    answer_selected = Signal(str)  # Emits the selected answer (A, B, C, D)
    analysis_requested = Signal()  # Emits when AI Analysis is requested
    flashcard_requested = Signal(str) # Emits question text/context for vocab extraction
    
    def __init__(self, question_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.question = question_data
        self.selected_answer: Optional[str] = None
        self.answered = False
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI."""
        self.setObjectName("ToeicQuestionCard")
        self.setStyleSheet(f"""
            #ToeicQuestionCard {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Question number and topic
        header = QHBoxLayout()
        
        q_num = self.question.get("question_number", "?")
        part = self.question.get("part", 1)
        self.question_label = QLabel(f"Question {q_num} (Part {part})")
        self.question_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {ThemeColors.PRIMARY};
        """)
        header.addWidget(self.question_label)
        
        topic = self.question.get("topic", "")
        if topic:
            topic_label = QLabel(f"📂 {topic}")
            topic_label.setStyleSheet(f"font-size: 12px; color: {ThemeColors.TEXT_MUTED};")
            header.addWidget(topic_label)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Image (for Part 1)
        if self.question.get("image_path"):
            self.image_label = QLabel()
            self.image_label.setFixedHeight(200)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setStyleSheet(f"""
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 8px;
                padding: 8px;
            """)
            # Try to load image
            pixmap = QPixmap(self.question.get("image_path", ""))
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.image_label.setText("📷 [Image placeholder]")
            layout.addWidget(self.image_label)
        
        # Question text
        q_text = self.question.get("question_text", "")
        if q_text:
            self.text_label = QLabel(q_text)
            self.text_label.setWordWrap(True)
            self.text_label.setStyleSheet(f"""
                font-size: 15px;
                color: {ThemeColors.TEXT_PRIMARY};
                padding: 8px;
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 8px;
            """)
            layout.addWidget(self.text_label)
        
        # Options
        self.options_group = QButtonGroup(self)
        self.option_buttons: Dict[str, QRadioButton] = {}
        
        options = self.question.get("options", [])
        labels = ["A", "B", "C", "D"][:len(options)]
        
        for label, option_text in zip(labels, options):
            btn = QRadioButton(f"{label}. {option_text}")
            btn.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 14px;
                    color: {ThemeColors.TEXT_PRIMARY};
                    padding: 12px;
                    background-color: {ThemeColors.BG_TERTIARY};
                    border-radius: 8px;
                    margin: 4px 0;
                }}
                QRadioButton:hover {{
                    background-color: {ThemeColors.PRIMARY}22;
                }}
                QRadioButton:checked {{
                    background-color: {ThemeColors.PRIMARY}44;
                    font-weight: bold;
                }}
            """)
            btn.clicked.connect(lambda checked, l=label: self._on_option_selected(l))
            self.options_group.addButton(btn)
            self.option_buttons[label] = btn
            layout.addWidget(btn)
        
        # Feedback area (hidden initially)
        self.feedback_frame = QFrame()
        self.feedback_frame.setVisible(False)
        self.feedback_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        feedback_layout = QVBoxLayout(self.feedback_frame)
        
        self.result_label = QLabel()
        self.result_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        feedback_layout.addWidget(self.result_label)
        
        self.explanation_label = QLabel()
        self.explanation_label.setWordWrap(True)
        self.explanation_label.setStyleSheet(f"font-size: 13px; color: {ThemeColors.TEXT_SECONDARY};")
        feedback_layout.addWidget(self.explanation_label)
        
        layout.addWidget(self.feedback_frame)
        
        # Transcript area (hidden initially)
        self.transcript_frame = QFrame()
        self.transcript_frame.setVisible(False)
        self.transcript_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 8px;
                padding: 12px;
                margin-top: 8px;
                border-left: 4px solid {ThemeColors.PRIMARY};
            }}
        """)
        transcript_layout = QVBoxLayout(self.transcript_frame)
        
        transcript_title = QLabel("📜 Transcript")
        transcript_title.setStyleSheet("font-weight: bold; color: {ThemeColors.PRIMARY};")
        transcript_layout.addWidget(transcript_title)
        
        self.transcript_label = QLabel()
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setStyleSheet(f"font-style: italic; color: {ThemeColors.TEXT_SECONDARY};")
        transcript_layout.addWidget(self.transcript_label)
        
        layout.addWidget(self.transcript_frame)
        
        self.ai_btn = QPushButton("✨ AI Analysis")
        self.ai_btn.setProperty("class", "ai-btn") 
        self.ai_btn.clicked.connect(self._analyze_with_ai)
        self.ai_btn.setVisible(False)
        self.ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.ACCENT};
                color: {ThemeColors.TEXT_INVERSE};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.ACCENT_HOVER};
            }}
        """)
        action_layout.addWidget(self.ai_btn)
        
        # Flashcard Button
        self.flashcard_btn = QPushButton("⚡ Create Flashcard")
        self.flashcard_btn.clicked.connect(self._request_flashcard)
        self.flashcard_btn.setVisible(False)
        self.flashcard_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.WARNING};
                color: {ThemeColors.TEXT_PRIMARY};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.WARNING_HOVER};
            }}
        """)
        action_layout.addWidget(self.flashcard_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        layout.addStretch()
    
    def _on_option_selected(self, label: str):
        """Handle option selection."""
        self.selected_answer = label
        self.answer_selected.emit(label)

    def _toggle_transcript(self):
        """Toggle transcript visibility."""
        is_visible = self.transcript_btn.isChecked()
        self.transcript_frame.setVisible(is_visible)
        self.transcript_btn.setText("📜 Hide Transcript" if is_visible else "📜 Show Transcript")
        
        # Load transcript text if needed
        if is_visible and not self.transcript_label.text():
             transcript = self.question.get("transcript", "No transcript available.")
             self.transcript_label.setText(transcript)
    
    def _analyze_with_ai(self):
        """Trigger AI analysis."""
        self.ai_btn.setText("✨ Analyzing...")
        self.ai_btn.setEnabled(False)
        self.analysis_requested.emit()

    def _request_flashcard(self):
        """Request flashcard creation context."""
        # Combine question text and passage if available
        context = self.question.get("question_text", "")
        if self.question.get("passage"):
            context += "\n" + self.question.get("passage")
        self.flashcard_requested.emit(context)
    
    def show_result(self, is_correct: bool, correct_answer: str, explanation: str = ""):
        """Show the result after answering."""
        self.answered = True
        
        if is_correct:
            self.result_label.setText("✅ Correct!")
            self.result_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.SUCCESS};")
        else:
            self.result_label.setText(f"❌ Incorrect. The answer is {correct_answer}.")
            self.result_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.DANGER};")
        
        if explanation:
            self.explanation_label.setText(explanation)
        
        # Highlight correct answer
        for label, btn in self.option_buttons.items():
            btn.setEnabled(False)
            if label == correct_answer:
                btn.setStyleSheet(f"""
                    QRadioButton {{
                        font-size: 14px;
                        color: {ThemeColors.TEXT_PRIMARY};
                        padding: 12px;
                        background-color: {ThemeColors.SUCCESS}44;
                        border-radius: 8px;
                        font-weight: bold;
                    }}
                """)
            elif label == self.selected_answer and not is_correct:
                btn.setStyleSheet(f"""
                    QRadioButton {{
                        font-size: 14px;
                        color: {ThemeColors.TEXT_PRIMARY};
                        padding: 12px;
                        background-color: {ThemeColors.DANGER}44;
                        border-radius: 8px;
                    }}
                """)
        
        self.feedback_frame.setVisible(True)
        self.ai_btn.setVisible(True)  # Show AI button after answering
        self.flashcard_btn.setVisible(True) # Show Flashcard button after answering
    
    def reset(self):
        """Reset the card for reuse."""
        self.answered = False
        self.selected_answer = None
        self.feedback_frame.setVisible(False)
        self.transcript_frame.setVisible(False)
        self.transcript_btn.setChecked(False)
        self.transcript_btn.setText("📜 Show Transcript")
        self.ai_btn.setVisible(False)
        self.flashcard_btn.setVisible(False)
        self.options_group.setExclusive(False)
        for btn in self.option_buttons.values():
            btn.setChecked(False)
            btn.setEnabled(True)
        self.options_group.setExclusive(True)
