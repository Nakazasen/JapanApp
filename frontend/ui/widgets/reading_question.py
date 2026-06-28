from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QRadioButton, QButtonGroup, QPushButton, QFrame,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal
from frontend.ui.styles.theme import ThemeColors

class ReadingPart5Widget(QWidget):
    """
    Widget for TOEIC Reading Part 5 (Incomplete Sentences).
    Displays a question, 4 options, and checks the answer.
    """
    answer_checked = Signal(bool) # True if correct

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_question = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 1. Question Card
        self.question_card = QFrame()
        self.question_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                padding: 20px;
                border: 1px solid {ThemeColors.BORDER};
            }}
        """)
        q_layout = QVBoxLayout(self.question_card)
        
        self.lb_question = QLabel("Question text goes here...")
        self.lb_question.setWordWrap(True)
        self.lb_question.setStyleSheet(f"font-size: 18px; color: {ThemeColors.TEXT_PRIMARY}; font-weight: 500;")
        q_layout.addWidget(self.lb_question)

        layout.addWidget(self.question_card)

        # 2. Options Area
        self.options_group = QButtonGroup(self)
        self.radio_buttons = []
        
        options_layout = QVBoxLayout()
        options_layout.setSpacing(10)
        
        for i in range(4):
            rb = QRadioButton(f"Option {i}")
            rb.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 8px;
                    border: 1px solid {ThemeColors.BORDER};
                    background-color: {ThemeColors.BG_SECONDARY};
                }}
                QRadioButton::indicator {{
                    width: 20px;
                    height: 20px;
                }}
                QRadioButton:checked {{
                    background-color: {ThemeColors.BG_TERTIARY};
                    border-color: {ThemeColors.PRIMARY};
                }}
            """)
            self.options_group.addButton(rb, i)
            self.radio_buttons.append(rb)
            options_layout.addWidget(rb)
            
        layout.addLayout(options_layout)

        # 3. Utilities (Check Button)
        self.btn_check = QPushButton("Kiểm tra")
        self.btn_check.setCursor(Qt.PointingHandCursor)
        self.btn_check.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY};
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.PRIMARY_HOVER};
            }}
        """)
        self.btn_check.clicked.connect(self.check_answer)
        layout.addWidget(self.btn_check)

        # 4. Explanation Area (Hidden initially)
        self.explanation_frame = QFrame()
        self.explanation_frame.setVisible(False)
        self.explanation_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 8px;
                padding: 15px;
                border-left: 4px solid {ThemeColors.ACCENT};
                margin-top: 10px;
            }}
        """)
        exp_layout = QVBoxLayout(self.explanation_frame)
        
        lbl_exp_title = QLabel("💡 Giải thích:")
        lbl_exp_title.setStyleSheet(f"font-weight: bold; color: {ThemeColors.ACCENT}; font-size: 14px;")
        exp_layout.addWidget(lbl_exp_title)
        
        self.lb_explanation = QLabel("Explanation text...")
        self.lb_explanation.setWordWrap(True)
        self.lb_explanation.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 14px; margin-top: 5px;")
        exp_layout.addWidget(self.lb_explanation)
        
        layout.addWidget(self.explanation_frame)
        layout.addStretch()

    def load_question(self, data):
        """Load question data into UI."""
        self.current_question = data
        self.lb_question.setText(data['question'])
        self.explanation_frame.setVisible(False)
        self.btn_check.setEnabled(True)
        
        # Reset radio buttons
        self.options_group.setExclusive(False)
        for i, rb in enumerate(self.radio_buttons):
            rb.setText(f"{chr(65+i)}. {data['options'][i]}")
            rb.setChecked(False)
            # Reset style
            rb.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 16px;
                    padding: 10px;
                    border-radius: 8px;
                    border: 1px solid {ThemeColors.BORDER};
                    background-color: {ThemeColors.BG_SECONDARY};
                }}
            """)
            rb.setEnabled(True)
        self.options_group.setExclusive(True)

    def check_answer(self):
        """Validate the selected answer."""
        if not self.current_question: return
        
        selected_id = self.options_group.checkedId()
        if selected_id == -1: return # No selection
        
        correct_id = self.current_question['correct_index']
        is_correct = (selected_id == correct_id)
        
        # lock inputs
        self.btn_check.setEnabled(False)
        for rb in self.radio_buttons:
            rb.setEnabled(False)
            
        # Style the correct/incorrect answers
        correct_rb = self.radio_buttons[correct_id]
        correct_rb.setStyleSheet(correct_rb.styleSheet() + f"background-color: {ThemeColors.SUCCESS_BG}; border-color: {ThemeColors.SUCCESS};")
        
        if not is_correct:
            wrong_rb = self.radio_buttons[selected_id]
            wrong_rb.setStyleSheet(wrong_rb.styleSheet() + f"background-color: {ThemeColors.ERROR_BG}; border-color: {ThemeColors.ERROR};")
            
        # Show explanation
        self.lb_explanation.setText(self.current_question.get('explanation', ''))
        self.explanation_frame.setVisible(True)
        
        self.answer_checked.emit(is_correct)
