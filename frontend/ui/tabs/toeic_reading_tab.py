from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QLabel, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from frontend.ui.widgets.reading_question import ReadingPart5Widget
from frontend.services.toeic_reading_service import ToeicReadingService
from frontend.ui.styles.theme import ThemeColors

class ToeicReadingTab(QWidget):
    """
    Main tab for TOEIC Reading Practice (Part 5 focused).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = ToeicReadingService()
        self.questions = []
        self.current_index = 0
        self.init_ui()
        self.load_data()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Sidebar (Topics) ---
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-right: 1px solid {ThemeColors.BORDER};")
        side_layout = QVBoxLayout(sidebar)
        
        lbl_topics = QLabel("CHỦ ĐỀ NGỮ PHÁP")
        lbl_topics.setStyleSheet(f"font-weight: bold; color: {ThemeColors.TEXT_SECONDARY}; margin-bottom: 10px;")
        side_layout.addWidget(lbl_topics)
        
        self.topic_list = QListWidget()
        self.topic_list.setStyleSheet(f"""
            QListWidget {{ border: none; background: transparent; }}
            QListWidget::item {{ padding: 10px; border-radius: 6px; }}
            QListWidget::item:selected {{ background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.PRIMARY}; }}
        """)
        self.topic_list.itemClicked.connect(self.filter_by_topic)
        side_layout.addWidget(self.topic_list)
        
        main_layout.addWidget(sidebar)

        # --- Main Content Area ---
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        self.lbl_header = QLabel("Part 5: Incomplete Sentences")
        self.lbl_header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ThemeColors.PRIMARY};")
        content_layout.addWidget(self.lbl_header)
        
        # Question Widget
        self.question_widget = ReadingPart5Widget()
        content_layout.addWidget(self.question_widget)
        
        # Navigation
        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("Previous")
        self.btn_next = QPushButton("Next")
        
        for btn in [self.btn_prev, self.btn_next]:
            btn.setFixedSize(120, 40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.BG_TERTIARY};
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 20px;
                }}
                QPushButton:hover {{ border-color: {ThemeColors.PRIMARY}; }}
            """)
            
        self.btn_prev.clicked.connect(self.prev_question)
        self.btn_next.clicked.connect(self.next_question)
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        self.lbl_counter = QLabel("0/0")
        nav_layout.addWidget(self.lbl_counter)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        
        content_layout.addLayout(nav_layout)
        main_layout.addWidget(content)

    def load_data(self):
        """Load initial topics and all questions."""
        # Load topics
        topics = ["All Topics"] + self.service.get_topics()
        for t in topics:
            self.topic_list.addItem(QListWidgetItem(t))
        self.topic_list.setCurrentRow(0)
        
        # Load questions
        self.questions = self.service.get_part5_questions(limit=20)
        self.current_index = 0
        self.update_view()

    def filter_by_topic(self, item):
        topic = item.text()
        if topic == "All Topics":
            self.questions = self.service.get_part5_questions(limit=20)
        else:
            self.questions = self.service.get_part5_questions(topic=topic, limit=20)
            
        self.current_index = 0
        if not self.questions:
            QMessageBox.information(self, "Info", "No questions found for this topic.")
        self.update_view()

    def update_view(self):
        if not self.questions:
            self.lbl_counter.setText("0/0")
            self.question_widget.setVisible(False)
            return
            
        self.question_widget.setVisible(True)
        q_data = self.questions[self.current_index]
        self.question_widget.load_question(q_data)
        
        self.lbl_counter.setText(f"{self.current_index + 1}/{len(self.questions)}")
        
        self.btn_prev.setEnabled(self.current_index > 0)
        self.btn_next.setEnabled(self.current_index < len(self.questions) - 1)

    def prev_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_view()

    def next_question(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.update_view()
