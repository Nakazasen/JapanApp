from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal
from frontend.ui.styles.theme import ThemeColors, Fonts

class ToeicPracticeLayout(QWidget):
    """
    Standardized Layout for TOEIC Practice Tabs.
    
    Structure:
    - Header (Title + Stats)
    - Content Area (Splitter or Main Widget)
    - Footer/Navigation (Prev, Next, Submit, Progress)
    """
    
    # Signals for navigation interaction
    prev_clicked = Signal()
    next_clicked = Signal()
    submit_clicked = Signal()
    
    def __init__(self, title: str = "TOEIC Practice"):
        super().__init__()
        self.title_text = title
        self._init_ui()
        
    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(16)
        
        # --- 1. Header ---
        self.header_layout = QHBoxLayout()
        
        self.lbl_title = QLabel(self.title_text)
        self.lbl_title.setFont(Fonts.HEADER)
        self.lbl_title.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-weight: bold; font-size: 24px;")
        self.header_layout.addWidget(self.lbl_title)
        
        self.header_layout.addStretch()
        
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 14px;")
        self.header_layout.addWidget(self.lbl_stats)
        
        self.main_layout.addLayout(self.header_layout)
        
        # --- 2. Content Container ---
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0,0,0,0)
        self.main_layout.addWidget(self.content_container, stretch=1)
        
        # --- 3. Navigation Bar ---
        self.nav_frame = QFrame()
        self.nav_frame.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; border-radius: 10px; padding: 10px;")
        self.nav_layout = QHBoxLayout(self.nav_frame)
        
        self.btn_prev = QPushButton("⬅️ Previous")
        self.btn_prev.clicked.connect(self.prev_clicked.emit)
        self._style_nav_btn(self.btn_prev, ThemeColors.BG_TERTIARY, ThemeColors.TEXT_PRIMARY)
        
        self.btn_next = QPushButton("Next ➡️")
        self.btn_next.clicked.connect(self.next_clicked.emit)
        self._style_nav_btn(self.btn_next, ThemeColors.PRIMARY, ThemeColors.TEXT_INVERSE)
        
        self.btn_submit = QPushButton("✅ Check Answer")
        self.btn_submit.clicked.connect(self.submit_clicked.emit)
        self.btn_submit.setVisible(False) # Hidden by default
        self._style_nav_btn(self.btn_submit, ThemeColors.SUCCESS, ThemeColors.TEXT_INVERSE)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.SUCCESS};
                border-radius: 4px;
            }}
        """)
        
        # Layout Order: Prev -> Stretch -> Progress(Optional? No, let's put progress on top or middle) -> Stretch -> Submit -> Next
        # Better: Prev | ... | Submit | ... | Next
        # And Progress Bar separate or embedded?
        # Let's keep Progress Bar just above buttons or integrated.
        
        self.nav_layout.addWidget(self.btn_prev)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_submit)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_next)
        
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.nav_frame)

    def _style_nav_btn(self, btn, bg_color, text_color):
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:disabled {{
                opacity: 0.5;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)

    def set_content(self, widget: QWidget):
        """Replace central content."""
        # Clear existing
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None) # Don't delete, just remove, caller manages lifecycle if needed
        
        self.content_layout.addWidget(widget)

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def update_stats(self, text: str):
        self.lbl_stats.setText(text)
    
    def set_title(self, text: str):
        self.lbl_title.setText(text)
