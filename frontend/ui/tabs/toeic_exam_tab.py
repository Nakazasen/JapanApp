"""TOEIC Exam Tab.

Simulates a full TOEIC test environment with timer and no immediate feedback.
"""
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget, QScrollArea, QGridLayout,
    QProgressBar, QLCDNumber, QSplitter, QListWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QTime
from frontend.services.toeic_listening_service import get_toeic_listening_service
from frontend.ui.widgets.toeic_question_card import ToeicQuestionCard
from frontend.ui.styles.theme import ThemeColors
from frontend.utils.toast_helper import toast_success, toast_error, toast_info
from frontend.services.content_generator_service import get_content_service
from frontend.ui.dialogs.flashcard_creation_dialog import FlashcardCreationDialog
from frontend.utils.async_helpers import AsyncHelper

class ToeicExamTab(QWidget):
    """Full TOEIC Exam Simulation Tab."""
    
    def __init__(self):
        super().__init__()
        self.service = get_toeic_listening_service()
        self.test_id = 1 # Hardcoded for MVP (Mock Test 1)
        
        # State
        self.test_data: Dict[str, Any] = {}
        self.user_answers: Dict[int, str] = {} # question_id -> answer
        self.time_seconds: int = 0
        self.total_time: int = 120 * 60 # 120 minutes default
        self.current_part: int = 1
        self.current_items: List[Dict[str, Any]] = [] # Items for current part
        self.current_idx: int = 0
        self.is_review_mode: bool = False
        
        self.content_service = get_content_service()
        self.async_helper = AsyncHelper(self)
        
        # UI Components
        self._init_ui()
        
        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        
    def _init_ui(self):
        """Initialize the UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Header (Timer & Submit) ---
        header = QFrame()
        header.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-bottom: 1px solid {ThemeColors.BORDER};")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        
        title = QLabel("📝 TOEIC Full Test")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Timer Display
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet(f"font-size: 20px; font-weight: bold; font-family: monospace; color: {ThemeColors.ACCENT};")
        header_layout.addWidget(self.timer_label)
        
        header_layout.addStretch()
        
        self.submit_btn = QPushButton("Submit Test")
        self.submit_btn.clicked.connect(self._confirm_submit)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SUCCESS};
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.SUCCESS_HOVER}; }}
        """)
        header_layout.addWidget(self.submit_btn)
        
        main_layout.addWidget(header)
        
        # --- Body (Start Screen vs Exam View) ---
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Page 0: Start Screen
        self.start_page = self._create_start_page()
        self.stack.addWidget(self.start_page)
        
        # Page 1: Exam Interface
        self.exam_page = self._create_exam_page()
        self.stack.addWidget(self.exam_page)
        
    def _create_start_page(self) -> QWidget:
        """Create the landing page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        title = QLabel("TOEIC Simulation Mode")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        info = QLabel(
            "• Full 2-hour timed test\n"
            "• Listening (Part 1-4) & Reading (Part 5-7)\n"
            "• No immediate feedback/answers\n"
            "• Score calculated at the end"
        )
        info.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(info)
        
        start_btn = QPushButton("Start Test")
        start_btn.setFixedSize(200, 50)
        start_btn.clicked.connect(self._start_test)
        start_btn.setStyleSheet(f"""
            background-color: {ThemeColors.PRIMARY}; 
            color: white; 
            font-size: 18px; 
            border-radius: 8px;
        """)
        layout.addWidget(start_btn)
        
        return page

    def _create_exam_page(self) -> QWidget:
        """Create the main exam interface."""
        page = QWidget()
        layout = QHBoxLayout(page)
        
        # --- Left Sidebar (Part Navigation) ---
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY};")
        side_layout = QVBoxLayout(sidebar)
        
        side_layout.addWidget(QLabel("Sections:"))
        self.part_list = QListWidget()
        self.part_list.addItems([
            "Part 1: Photos", 
            "Part 2: Q&A", 
            "Part 3: Conversations", 
            "Part 4: Talks", 
            "Part 5: Sentences", 
            "Part 6: Text Completion", 
            "Part 7: Reading Comp"
        ])
        self.part_list.currentRowChanged.connect(self._on_part_changed)
        side_layout.addWidget(self.part_list)
        
        layout.addWidget(sidebar)
        
        # --- Main Content (Splitter or Single) ---
        content_area = QWidget()
        self.content_layout = QVBoxLayout(content_area)
        
        # Question Rendering Area
        self.question_area = QScrollArea()
        self.question_area.setWidgetResizable(True)
        self.question_container = QWidget()
        self.q_layout = QVBoxLayout(self.question_container)
        self.question_area.setWidget(self.question_container)
        
        self.content_layout.addWidget(self.question_area)
        
        # Bottom Navigation
        nav_bar = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self._prev_item)
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self._next_item)
        
        nav_bar.addWidget(self.prev_btn)
        nav_bar.addStretch()
        self.progress_label = QLabel("Question 1/1")
        nav_bar.addWidget(self.progress_label)
        nav_bar.addStretch()
        nav_bar.addWidget(self.next_btn)
        
        self.content_layout.addLayout(nav_bar)
        
        layout.addWidget(content_area)
        return page

    def _start_test(self):
        """Start the exam session."""
        try:
            details = self.service.get_test_details(self.test_id)
            if not details:
                toast_error("Test data not found!")
                return
            
            self.test_data = details
            self.total_time = (details.get("time_limit") or 120) * 60
            self.time_seconds = self.total_time
            self.user_answers = {}
            
            # Switch view
            self.stack.setCurrentIndex(1)
            self.timer.start(1000)
            self._update_timer_label()
            
            # Select Part 1
            self.part_list.setCurrentRow(0)
            
            # Reset Review Mode
            self.is_review_mode = False
            self.content_layout.setEnabled(True)
            self.header_frame.setVisible(True) # Ensure header visible
            
        except Exception as e:
            toast_error(f"Failed to start test: {e}")

    def _update_timer(self):
        """Update countdown."""
        if self.time_seconds > 0:
            self.time_seconds -= 1
            self._update_timer_label()
        else:
            self.timer.stop()
            toast_info("Time's up!")
            self._submit_test()
            
    def _update_timer_label(self):
        hours = self.time_seconds // 3600
        mins = (self.time_seconds % 3600) // 60
        secs = self.time_seconds % 60
        self.timer_label.setText(f"{hours:02}:{mins:02}:{secs:02}")
        if self.time_seconds < 300: # Red color last 5 mins
            self.timer_label.setStyleSheet("color: red; font-weight: bold; font-size: 20px;")

    def _on_part_changed(self, row: int):
        """Handle part selection."""
        self.current_part = row + 1
        parts_data = self.test_data.get("parts", {})
        self.current_items = parts_data.get(self.current_part, [])
        self.current_idx = 0
        self._load_current_item()

    def _load_current_item(self):
        """Render current question or set."""
        # Clear layout
        while self.q_layout.count():
            item = self.q_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        if not self.current_items:
            self.q_layout.addWidget(QLabel("No questions in this part."))
            return

        item = self.current_items[self.current_idx]
        
        # Check if Set Mode (Part 3,4,6,7) or has 'questions' list
        is_set = "questions" in item and isinstance(item["questions"], list)
        
        if is_set:
            # Render Set
            # 1. Shared Content (Audio/Passage)
            if item.get("passage"):
                from PySide6.QtWidgets import QTextBrowser
                tb = QTextBrowser()
                tb.setHtml(item["passage"])
                tb.setFixedHeight(200) # Simple fixed height for now
                self.q_layout.addWidget(tb)
                
            # 2. Questions
            for q in item["questions"]:
                self._add_question_card(q)
        else:
            # Single Question
            self._add_question_card(item)
            
        self.q_layout.addStretch()
        
        # Update Nav State
        self.prev_btn.setEnabled(self.current_idx > 0)
        self.next_btn.setEnabled(self.current_idx < len(self.current_items) - 1)
        self.progress_label.setText(f"Item {self.current_idx + 1}/{len(self.current_items)}")

    def _add_question_card(self, question_data: Dict):
        """Add a question card (Exam Mode: No check button)."""
        card = ToeicQuestionCard(question_data, minimal=True) # Assuming we can add a minimal mode or just hide buttons
        # Hide standard action buttons if minimal mode not supported
        card.submit_btn.hide()
        if hasattr(card, 'ai_btn'): card.ai_btn.hide()
        
        # Connect Flashcard Request
        card.flashcard_requested.connect(self._handle_flashcard_request)
        
        # Restore answer if previously selected
        
        # Restore answer if previously selected
        q_id = question_data.get("id")
        if q_id in self.user_answers:
            # Need a way to set selected answer programmatically on the card
            # For MVP, we might not update UI selection if we rebuild cards every time.
            # Ideally ToeicQuestionCard should allow setting selection.
            # Let's simple check the radio button matching the answer logic.
            # Assuming card exposes buttons or we modify it.
            # Creating a quick helper assuming standard implementation:
            saved_ans = self.user_answers[q_id]
            # Try to find button with text starting with saved_ans
            pass 

        # Connect click to save
        card.answer_selected.connect(lambda ans, qid=q_id: self._save_answer(qid, ans))
        self.q_layout.addWidget(card)
        
        # If Review Mode, Show Result immediately
        if self.is_review_mode:
            qid = question_data.get("id")
            user_ans = self.user_answers.get(qid)
            correct_ans = question_data.get("correct_answer")
            explanation = question_data.get("explanation", "")
            
            # Mark correct/incorrect
            is_correct = (user_ans == correct_ans)
            card.show_result(is_correct, correct_ans, explanation)
            
            # Show user selection visually if needed (though show_result handles it mostly)
            if user_ans: 
                # Need to manually trigger logic if card doesn't remember selection
                # But card.option_buttons loop in show_result uses self.selected_answer
                # So we must set it.
                card.selected_answer = user_ans
                # Re-run show_result to update UI with user choice
                card.show_result(is_correct, correct_ans, explanation)

    def _save_answer(self, q_id, answer):
        self.user_answers[q_id] = answer

    def _prev_item(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self._load_current_item()
            
    def _next_item(self):
        if self.current_idx < len(self.current_items) - 1:
            self.current_idx += 1
            self._load_current_item()

    def _confirm_submit(self):
        """Ask confirmation."""
        reply = QMessageBox.question(self, "Submit Test", "Are you sure you want to finish the test?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._submit_test()

    def _submit_test(self):
        """Submit to service and show result."""
        self.timer.stop()
        result = self.service.submit_test(self.test_id, self.user_answers)
        
        score = result["score"]
        correct = result["correct_count"]
        total = result["total_count"]
        
        QMessageBox.information(self, "Test Complete", 
                                f"Detailed Score Report:\n\n"
                                f"Score: {score} / ~990\n"
                                f"Correct: {correct}/{total}")
        
        # Reset
        # self.stack.setCurrentIndex(0) # Don't go back to start
        
        # Enter Review Mode
        self.is_review_mode = True
        self.timer_label.setText("REVIEW MODE")
        self.timer_label.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-weight: bold;")
        self.submit_btn.hide()
        
        # Reload current items to show results
        self._load_current_item()
        
        QMessageBox.information(self, "Test Submitted", "You are now in Review Mode. Check your answers and create flashcards!")

    def _handle_flashcard_request(self, context_text):
        """Handle AI Flashcard Generation."""
        if not context_text: return
        
        toast_info("Analysing text for vocabulary...")
        
        # Async call to generate
        self.async_helper.run(
            self.content_service.extract_vocab_from_text(context_text),
            self._show_flashcard_dialog
        )
        
    def _show_flashcard_dialog(self, vocab_list):
        if not vocab_list:
            toast_error("Could not extract vocabulary.")
            return
            
        dialog = FlashcardCreationDialog(vocab_list, self)
        dialog.exec()
