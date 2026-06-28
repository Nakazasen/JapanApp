"""Vocabulary Tab - Anki-style Flashcard Learning (Vietnamese Interface).

Features:
- Deck/Topic management (Quản lý bộ từ/chủ đề)
- SRS Flashcard Study (Học từ vựng dạng thẻ nhớ)
- Vocabulary lookup and management (Tra cứu và quản lý từ vựng)
- AI-powered image scanning (Scan ảnh bằng AI)
"""
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QListWidget, QLabel, QSplitter, QMenu, QMessageBox,
    QFileDialog, QProgressDialog, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QFrame, QScrollArea, QStackedWidget, QSizePolicy, QCheckBox, QGridLayout,
    QTabWidget, QButtonGroup, QProgressBar
)
from PySide6.QtCore import Qt, QPoint, QUrl, QThread, QSize, QTimer, QObject, Signal
from PySide6.QtGui import QAction, QTextCursor, QFont, QIcon, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import base64
import tempfile
import os

# Services
# Services
from frontend.services import get_vocab_service, get_tts_service
from frontend.core.user_settings import get_user_settings
from frontend.ui.styles.theme import ThemeColors
from frontend.ui.styles.animations import AnimationService

# Utilities
from frontend.utils.async_helpers import AsyncHelper, run_async
from frontend.utils.gemini_scan_worker import GeminiScanWorker

class WorkerSignals(QObject):
    progress = Signal(int, str)
    finished = Signal(dict)

# UI Components
from frontend.ui.widgets.scan_review_dialog import ScanReviewDialog, ApiKeyInputDialog
from frontend.ui.widgets.study_session_dialog import StudySessionDialog
from frontend.ui.widgets.practice_settings_dialog import PracticeSettingsDialog, TopicManagerDialog
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin
from frontend.ui.tabs.vocab_practice_tab import VocabPracticeTab
from frontend.ui.widgets.tinder_session import TinderSessionWidget
from frontend.ui.widgets.vocab_flashcard import VocabFlashcardView

# Models for constants
from frontend.models.vocab import (
    MasteryStatus,
    JAPANESE_LEVELS, ENGLISH_LEVELS
)




class VocabTab(QWidget, TextContextMenuMixin):
    """Vocabulary Lookup & SRS Study Tab (Anki-style)."""
    
    def __init__(self):
        super().__init__()
        
        # Services
        self.vocab_service = get_vocab_service()
        self._gemini_api_key = self._load_api_key()
        
        # State
        self.current_topic_id = None
        self.srs_session_queue = [] # List of words to review
        self.current_review_index = 0
        
        self._init_ui()
        self._load_topics()
    
    def showEvent(self, event):
        """Sync language when tab is shown."""
        super().showEvent(event)
        settings = get_user_settings()
        lang = settings.get_language()  # 'en' or 'jp'
        
        # Sync ComboBox
        index = self.lang_combo.findData(lang)
        if index != -1 and index != self.lang_combo.currentIndex():
            self.lang_combo.setCurrentIndex(index)
            # currentIndexChanged will trigger _on_lang_changed
    
    def _load_api_key(self) -> str:
        try:
            from frontend.services.ai_service import get_config_manager
            config = get_config_manager()
            return config.get_current_api_key() or ""
        except:
            return ""

    def _init_ui(self):
        self.main_tabs = QTabWidget(self)
        self.main_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{
                background: {ThemeColors.BG_SECONDARY}; color: {ThemeColors.TEXT_SECONDARY}; padding: 10px 20px;
                border-top-left-radius: 8px; border-top-right-radius: 8px;
                margin-right: 2px; font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {ThemeColors.BG_PRIMARY}; color: {ThemeColors.PRIMARY};
                border-bottom: 2px solid {ThemeColors.PRIMARY};
            }}
        """)
        
        # --- TAB 1: Kho từ vựng & Học tập ---
        self.study_page = QWidget()
        study_layout = QHBoxLayout(self.study_page)
        study_layout.setSpacing(0)
        study_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- LEFT SIDEBAR (Topics / Decks) ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 8px;
                border-right: none;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QCheckBox {{
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QComboBox {{
                background: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setSpacing(15)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        
        # Header with kanji-style icon
        header_lbl = QLabel("📚 Từ vựng (Vocab)")
        header_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.ACCENT};")
        sidebar_layout.addWidget(header_lbl)
        
        # --- Language Selector ---
        lang_layout = QHBoxLayout()
        lang_lbl = QLabel("Ngôn ngữ:")
        lang_lbl.setStyleSheet(f"font-weight: normal; color: {ThemeColors.TEXT_SECONDARY};")
        lang_layout.addWidget(lang_lbl)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("🇯🇵 Tiếng Nhật", "jp")
        self.lang_combo.addItem("🇬🇧 Tiếng Anh", "en")
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        lang_layout.addWidget(self.lang_combo)
        sidebar_layout.addLayout(lang_layout)
        
        # Action Buttons (Import/Add)
        btn_layout = QHBoxLayout()
        self.add_topic_btn = QPushButton("➕ Topic")
        self.add_topic_btn.setFixedHeight(32)
        self.add_topic_btn.setStyleSheet("""
            QPushButton {{
                background-color: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; border-radius: 6px;
                padding: 0 10px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.SECONDARY}; }}
        """)
        self.add_topic_btn.clicked.connect(self._create_topic_dialog)
        btn_layout.addWidget(self.add_topic_btn)
        
        self.scan_btn = QPushButton("📷 Scan")
        self.scan_btn.setFixedHeight(32)
        self.scan_btn.setStyleSheet("""
            QPushButton {{
                background-color: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; border-radius: 6px;
                padding: 0 10px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.SECONDARY}; }}
        """)
        self.scan_btn.clicked.connect(self._scan_image)
        btn_layout.addWidget(self.scan_btn)
        sidebar_layout.addLayout(btn_layout)
        
        # Today's stats panel (Anki-style, matching KanjiTab)
        self.stats_group = QFrame()
        self.stats_group.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 8px;
                padding: 10px;
            }}
            QLabel {{
                font-size: 13px;
            }}
        """)
        stats_layout = QGridLayout(self.stats_group)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setHorizontalSpacing(10)
        stats_layout.setVerticalSpacing(8)
        
        # Due row
        due_icon = QLabel("🔄")
        due_lbl = QLabel("Cần ôn")
        due_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY};")
        self.due_count_lbl = QLabel("0")
        self.due_count_lbl.setStyleSheet(f"color: {ThemeColors.SUCCESS}; font-size: 18px; font-weight: bold;")
        self.due_count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        stats_layout.addWidget(due_icon, 0, 0)
        stats_layout.addWidget(due_lbl, 0, 1)
        stats_layout.addWidget(self.due_count_lbl, 0, 2)
        
        # New row
        new_icon = QLabel("🆕")
        new_lbl = QLabel("Từ mới")
        new_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY};")
        self.new_count_lbl = QLabel("0")
        self.new_count_lbl.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-size: 18px; font-weight: bold;")
        self.new_count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        stats_layout.addWidget(new_icon, 1, 0)
        stats_layout.addWidget(new_lbl, 1, 1)
        stats_layout.addWidget(self.new_count_lbl, 1, 2)
        
        stats_layout.setColumnStretch(1, 1) # Make the label take remaining space
        
        sidebar_layout.addWidget(self.stats_group)
        
        # Big Study button (Matching KanjiTab)
        self.study_now_btn_large = QPushButton("🚀 Bắt đầu học!")
        self.study_now_btn_large.setFixedHeight(50)
        self.study_now_btn_large.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SUCCESS};
                color: white;
                padding: 10px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """)
        self.study_now_btn_large.clicked.connect(self._start_study_session)
        sidebar_layout.addWidget(self.study_now_btn_large)
        
        # Topic List
        sidebar_layout.addWidget(QLabel("📂 Bộ từ vựng:"))
        self.topic_list = QListWidget()
        self.topic_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                color: {ThemeColors.TEXT_SECONDARY};
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 6px;
                margin-bottom: 2px;
            }}
            QListWidget::item:hover {{
                background-color: {ThemeColors.BG_TERTIARY};
            }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.PRIMARY};
                font-weight: bold;
            }}
        """)
        self.topic_list.itemClicked.connect(self._on_topic_selected)
        sidebar_layout.addWidget(self.topic_list, 1)
        
        # Audio Options
        self.auto_pronounce_cb = QCheckBox("🔊 Tự động phát âm")
        self.auto_pronounce_cb.toggled.connect(self._on_auto_pronounce_toggled)
        self.auto_pronounce_enabled = False
        sidebar_layout.addWidget(self.auto_pronounce_cb)
        
        study_layout.addWidget(self.sidebar)
        
        # ===== RIGHT CONTENT (Stacked: List / Study) =====
        self.right_content = QWidget()
        right_layout = QVBoxLayout(self.right_content)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        # Stacked Widget to switch between List View and Study View
        self.stacked_widget = QStackedWidget()
        
        # --- VIEW 1: Vocab List Manager ---
        self.list_view_widget = self._create_list_view_widget()
        self.stacked_widget.addWidget(self.list_view_widget)
        
        # --- VIEW 2: Study Flashcard ---
        self.study_view_widget = self._create_study_view_widget()
        self.stacked_widget.addWidget(self.study_view_widget)
        
        # --- VIEW 3: Tinder Session ---
        self.tinder_view = TinderSessionWidget()
        self.tinder_view.session_finished.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.tinder_view.session_finished.connect(self._update_stats_ui) # Refresh stats after session
        self.stacked_widget.addWidget(self.tinder_view)
        
        right_layout.addWidget(self.stacked_widget)
        study_layout.addWidget(self.right_content)
        
        self.main_tabs.addTab(self.study_page, "🗂️ Kho từ vựng")
        
        # --- TAB 2: Luyện tập (VocabPracticeTab) ---
        self.practice_tab = VocabPracticeTab()
        self.main_tabs.addTab(self.practice_tab, "🎯 Luyện tập")
        
        # Main layout for VocabTab
        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(self.main_tabs)
        
        # Connect tab change to refresh practice data
        self.main_tabs.currentChanged.connect(self._on_subtab_changed)
        
    def _on_subtab_changed(self, index):
        if index == 1:  # Luyện tập tab
            if hasattr(self, 'practice_tab'):
                self.practice_tab._load_items()
        
    def _create_list_view_widget(self) -> QWidget:
        """
        Wrapper widget that contains:
        1. Top Toggle Bar (Smart Dashboard <-> Dictionary Look up)
        2. Stacked Content (Dashboard vs Dictionary)
        """
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(10)
        
        # --- 1. Toggle Bar ---
        toggle_container = QWidget()
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.addStretch()
        
        self.view_toggle_group = QButtonGroup(self)
        self.view_toggle_group.setExclusive(True)
        
        # Smart Mode Button
        self.btn_view_smart = QPushButton("🚀 Lộ trình học")
        self.btn_view_smart.setCheckable(True)
        self.btn_view_smart.setChecked(True) # Default
        self.btn_view_smart.setFixedSize(140, 36)
        self.btn_view_smart.setCursor(Qt.PointingHandCursor)
        self.btn_view_smart.clicked.connect(lambda: self.view_stack.setCurrentIndex(0))
        
        # Dict Mode Button
        self.btn_view_dict = QPushButton("📖 Tra cứu / List")
        self.btn_view_dict.setCheckable(True)
        self.btn_view_dict.setFixedSize(140, 36)
        self.btn_view_dict.setCursor(Qt.PointingHandCursor)
        self.btn_view_dict.clicked.connect(lambda: self.view_stack.setCurrentIndex(1))
        
        self.view_toggle_group.addButton(self.btn_view_smart)
        self.view_toggle_group.addButton(self.btn_view_dict)
        
        # Style for Toggle
        toggle_style = f"""
            QPushButton {{
                background-color: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.TEXT_SECONDARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 18px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {ThemeColors.PRIMARY};
                color: white;
                border: 1px solid {ThemeColors.PRIMARY};
            }}
            QPushButton:hover:!checked {{
                background-color: {ThemeColors.BG_SECONDARY};
            }}
        """
        self.btn_view_smart.setStyleSheet(toggle_style)
        self.btn_view_dict.setStyleSheet(toggle_style)
        
        toggle_layout.addWidget(self.btn_view_smart)
        toggle_layout.addWidget(self.btn_view_dict)
        toggle_layout.addStretch()
        
        wrapper_layout.addWidget(toggle_container)
        
        # --- 2. Content Stack ---
        self.view_stack = QStackedWidget()
        
        # View 0: Smart Dashboard
        self.smart_dashboard = self._create_smart_dashboard()
        self.view_stack.addWidget(self.smart_dashboard)
        
        # View 1: Dictionary (Old List View)
        self.dictionary_view = self._create_dictionary_view()
        self.view_stack.addWidget(self.dictionary_view)
        
        wrapper_layout.addWidget(self.view_stack)
        
        return wrapper

    def _create_smart_dashboard(self) -> QWidget:
        """Create the 'Level-based' Smart Dashboard."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(20)
        
        # -- Welcome --
        welcome_lbl = QLabel("👋 Chào mừng quay lại! Hôm nay chúng ta sẽ chinh phục mục tiêu nào?")
        welcome_lbl.setStyleSheet(f"font-size: 16px; color: {ThemeColors.TEXT_SECONDARY}; font-style: italic;")
        welcome_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_lbl)
        
        # -- Main Action Cards (Grid) --
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Card 1: Review (Due)
        self.card_review = QFrame()
        self.card_review.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                border: 1px solid {ThemeColors.BORDER};
            }}
            QFrame:hover {{
                border: 2px solid {ThemeColors.ACCENT};
                background-color: {ThemeColors.BG_TERTIARY};
                margin-top: -5px; /* Lift effect */
                margin-bottom: 5px;
            }}
        """)
        c1_layout = QVBoxLayout(self.card_review)
        
        c1_icon = QLabel("🔄")
        c1_icon.setStyleSheet("font-size: 32px;")
        c1_icon.setAlignment(Qt.AlignCenter)
        
        c1_title = QLabel("Ôn tập ngay")
        c1_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        c1_title.setAlignment(Qt.AlignCenter)
        
        self.dash_due_lbl = QLabel("0 từ cần ôn")
        self.dash_due_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeColors.ACCENT}; font-weight: bold;")
        self.dash_due_lbl.setAlignment(Qt.AlignCenter)
        
        c1_btn = QPushButton("Bắt đầu")
        c1_btn.setCursor(Qt.PointingHandCursor)
        c1_btn.setStyleSheet(f"""
            background-color: {ThemeColors.ACCENT}; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;
        """)
        c1_btn.clicked.connect(self._start_study_session)
        
        c1_layout.addWidget(c1_icon)
        c1_layout.addWidget(c1_title)
        c1_layout.addWidget(self.dash_due_lbl)
        c1_layout.addWidget(c1_btn)
        
        cards_layout.addWidget(self.card_review)
        
        # Card 2: Learn New
        self.card_learn = QFrame()
        self.card_learn.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                border: 1px solid {ThemeColors.BORDER};
            }}
            QFrame:hover {{
                border: 2px solid {ThemeColors.PRIMARY};
                background-color: {ThemeColors.BG_TERTIARY};
                margin-top: -5px; /* Lift effect */
                margin-bottom: 5px;
            }}
        """)
        c2_layout = QVBoxLayout(self.card_learn)
        
        c2_icon = QLabel("⚡")
        c2_icon.setStyleSheet("font-size: 32px;")
        c2_icon.setAlignment(Qt.AlignCenter)
        
        c2_title = QLabel("Học từ mới")
        c2_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        c2_title.setAlignment(Qt.AlignCenter)
        
        self.dash_new_lbl = QLabel("Sẵn sàng")
        self.dash_new_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeColors.PRIMARY}; font-weight: bold;")
        self.dash_new_lbl.setAlignment(Qt.AlignCenter)
        
        c2_btn = QPushButton("Học 10 từ")
        c2_btn.setCursor(Qt.PointingHandCursor)
        c2_btn.setStyleSheet(f"""
            background-color: {ThemeColors.PRIMARY}; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;
        """)
        # We can implement a specific 'Learn New' mode later, for now maps to study session
        c2_btn.clicked.connect(self._start_study_session) 
        
        c2_layout.addWidget(c2_icon)
        c2_layout.addWidget(c2_title)
        c2_layout.addWidget(self.dash_new_lbl)
        c2_layout.addWidget(c2_btn)
        
        cards_layout.addWidget(self.card_learn)

        # Card 3: Tinder Mode
        self.card_tinder = QFrame()
        self.card_tinder.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                border: 1px solid {ThemeColors.BORDER};
            }}
            QFrame:hover {{
                border: 2px solid {ThemeColors.WARNING};
                background-color: {ThemeColors.BG_TERTIARY};
                margin-top: -5px; /* Lift effect */
                margin-bottom: 5px;
            }}
        """)
        c3_layout = QVBoxLayout(self.card_tinder)
        
        c3_icon = QLabel("🔥")
        c3_icon.setStyleSheet("font-size: 32px;")
        c3_icon.setAlignment(Qt.AlignCenter)
        
        c3_title = QLabel("Lướt từ tốc độ")
        c3_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        c3_title.setAlignment(Qt.AlignCenter)
        
        self.dash_tinder_lbl = QLabel("Thử thách nhanh")
        self.dash_tinder_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeColors.WARNING}; font-weight: bold;")
        self.dash_tinder_lbl.setAlignment(Qt.AlignCenter)
        
        c3_btn = QPushButton("Lướt ngay")
        c3_btn.setCursor(Qt.PointingHandCursor)
        c3_btn.setStyleSheet(f"""
            background-color: {ThemeColors.WARNING}; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;
        """)
        c3_btn.clicked.connect(self._start_tinder_session)
        
        c3_layout.addWidget(c3_icon)
        c3_layout.addWidget(c3_title)
        c3_layout.addWidget(self.dash_tinder_lbl)
        c3_layout.addWidget(c3_btn)
        
        cards_layout.addWidget(self.card_tinder)
        
        layout.addLayout(cards_layout)
        
        # -- Progress Section --
        layout.addSpacing(20)
        prog_header = QLabel("📊 Tiến độ theo cấp độ (JLPT / CEFR)")
        prog_header.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY}; border-bottom: 2px solid {ThemeColors.BORDER}; padding-bottom: 5px;")
        layout.addWidget(prog_header)
        
        self.dash_progress_container = QWidget()
        self.dash_progress_layout = QVBoxLayout(self.dash_progress_container)
        
        # Placeholder progress (will be populated async)
        # We will load this in _update_dashboard_stats
        
        layout.addWidget(self.dash_progress_container)
        layout.addStretch()
        
        return widget

    def _create_dictionary_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm từ vựng...")
        self.search_input.textChanged.connect(self._filter_vocab_list)
        toolbar.addWidget(self.search_input)
        
        # Add New Word Button
        self.add_word_btn = QPushButton(" Thêm")
        self.add_word_btn.setToolTip("Thêm từ vựng mới")
        self.add_word_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SUCCESS}; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #388E3C; }}
        """)
        self.add_word_btn.clicked.connect(self._show_add_word_dialog)
        toolbar.addWidget(self.add_word_btn)
        
        # Import CSV Button
        self.import_csv_btn = QPushButton(" Import")
        self.import_csv_btn.setToolTip("Nhập từ vựng từ tệp CSV/Excel")
        self.import_csv_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.ACCENT}; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #F57C00; }}
        """)
        self.import_csv_btn.clicked.connect(self._show_import_csv_dialog)
        toolbar.addWidget(self.import_csv_btn)
        
        self.study_now_btn = QPushButton(" Học")
        self.study_now_btn.setToolTip("Bắt đầu phiên học Flashcard")
        self.study_now_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY}; color: white; font-weight: bold; 
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.PRIMARY_HOVER}; }}
        """)
        self.study_now_btn.clicked.connect(self._start_study_session)
        toolbar.addWidget(self.study_now_btn)
        
        # Batch Lookup Button
        self.batch_lookup_btn = QPushButton(" Tra loạt")
        self.batch_lookup_btn.setToolTip("Tra cứu hàng loạt từ vựng")
        self.batch_lookup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_PRESSED}; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.PRIMARY}; }}
        """)
        self.batch_lookup_btn.clicked.connect(self._batch_lookup)
        toolbar.addWidget(self.batch_lookup_btn)
        
        # AI Batch Enrich Button
        self.ai_batch_btn = QPushButton(" AI Làm giàu")
        self.ai_batch_btn.setToolTip("Dùng AI làm giàu hàng loạt từ vựng (nghĩa, ví dụ)")
        self.ai_batch_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ThemeColors.PRIMARY}, stop:1 {ThemeColors.ACCENT}); 
                color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ThemeColors.PRIMARY_HOVER}, stop:1 {ThemeColors.ACCENT});
            }}
        """)
        self.ai_batch_btn.clicked.connect(self._batch_enrich_vocab)
        toolbar.addWidget(self.ai_batch_btn)
        
        # Reset AI Button
        self.reset_ai_btn = QPushButton("🔄 Reset AI")
        self.reset_ai_btn.setToolTip("Reset trạng thái làm giàu AI cho danh sách này")
        self.reset_ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SECONDARY}; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.SECONDARY_HOVER}; }}
        """)
        self.reset_ai_btn.clicked.connect(self._reset_all_visible_ai)
        toolbar.addWidget(self.reset_ai_btn)
        
        layout.addLayout(toolbar)
        
        # ===== FILTER BAR (Curriculum/Level) =====
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)
        
        # Source Filter
        self.source_filter_combo = QComboBox()
        self.source_filter_combo.setPlaceholderText("Giáo trình")
        self.source_filter_combo.setMinimumWidth(120)
        self.source_filter_combo.addItem("📖 Tất cả", None)
        self.source_filter_combo.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.source_filter_combo)
        
        # Level Filter
        self.level_filter_combo = QComboBox()
        self.level_filter_combo.setMinimumWidth(90)
        self.level_filter_combo.addItem("📊 Tất cả", None)
        self.level_filter_combo.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.level_filter_combo)
        
        # Status Filter
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.setMinimumWidth(110)
        self.status_filter_combo.addItem("🎯 Tất cả", None)
        self.status_filter_combo.addItem("🆕 Từ mới", "new")
        self.status_filter_combo.addItem("📖 Đang học", "learning")
        self.status_filter_combo.addItem("❗ Từ khó", "hard")
        self.status_filter_combo.addItem("✅ Đã thuộc", "mastered")
        self.status_filter_combo.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.status_filter_combo)
        
        # Clear Filters Button
        self.clear_filters_btn = QPushButton("🔄 Xóa bộ lọc")
        self.clear_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B; color: white;
                padding: 5px 10px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.clear_filters_btn.clicked.connect(self._clear_filters)
        filter_bar.addWidget(self.clear_filters_btn)
        
        filter_bar.addStretch()
        layout.addLayout(filter_bar)
        
        # ===== SPLITTER: List + Detail Panel =====
        self.list_splitter = QSplitter(Qt.Horizontal)
        
        # Left: Word List
        self.vocab_table = QListWidget()
        self.vocab_table.setAlternatingRowColors(True)
        self.vocab_table.itemClicked.connect(self._on_word_selected)
        self.vocab_table.itemDoubleClicked.connect(self._edit_word)
        self.vocab_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.vocab_table.customContextMenuRequested.connect(self._show_word_context_menu)
        self.list_splitter.addWidget(self.vocab_table)
        
        # Right: Detail Panel
        self.detail_panel = self._create_detail_panel()
        self.list_splitter.addWidget(self.detail_panel)
        
        # Set initial sizes (compact list)
        self.list_splitter.setSizes([250, 750])
        self.list_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.list_splitter, 1)
        
        # Status Bar (Footer)
        footer = QFrame()
        footer.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #ddd; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 5, 15, 5)
        
        self.total_words_lbl = QLabel("Tổng số từ: 0")
        self.total_words_lbl.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        footer_layout.addWidget(self.total_words_lbl)
        footer_layout.addStretch()
        
        layout.addWidget(footer)
        
        return widget
    
    def _create_detail_panel(self) -> QFrame:
        """Create the word detail panel."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QLabel#DetailWord {
                font-size: 24px;
                font-weight: bold;
                color: #1a237e;
            }
            QLabel#DetailReading {
                font-size: 18px;
                color: #666;
            }
            QLabel#DetailMeaning {
                font-size: 20px;
                color: #2e7d32;
                font-weight: bold;
            }
            QLabel#DetailHanViet {
                font-size: 16px;
                color: #e65100;
                font-weight: bold;
            }
            QLabel#SectionHeader {
                font-size: 13px;
                font-weight: bold;
                color: #555;
                margin-top: 4px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Word
        self.detail_word_lbl = QLabel("Chọn một từ để xem chi tiết")
        self.detail_word_lbl.setObjectName("DetailWord")
        self.detail_word_lbl.setAlignment(Qt.AlignCenter)
        self.detail_word_lbl.setWordWrap(True)
        layout.addWidget(self.detail_word_lbl)
        
        # Reading
        self.detail_reading_lbl = QLabel("")
        self.detail_reading_lbl.setObjectName("DetailReading")
        self.detail_reading_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_reading_lbl)
        
        # Hán Việt
        self.detail_hanviet_lbl = QLabel("")
        self.detail_hanviet_lbl.setObjectName("DetailHanViet")
        self.detail_hanviet_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail_hanviet_lbl)
        
        # Audio Button
        audio_layout = QHBoxLayout()
        audio_layout.addStretch()
        self.detail_audio_btn = QPushButton("🔊 Phát âm")
        self.detail_audio_btn.setFixedWidth(120)
        self.detail_audio_btn.clicked.connect(self._play_detail_audio)
        self.detail_audio_btn.hide()
        audio_layout.addWidget(self.detail_audio_btn)
        audio_layout.addStretch()
        layout.addLayout(audio_layout)
        
        # Meaning
        meaning_header = QLabel("📖 Nghĩa:")
        meaning_header.setObjectName("SectionHeader")
        layout.addWidget(meaning_header)
        
        self.detail_meaning_lbl = QLabel("")
        self.detail_meaning_lbl.setObjectName("DetailMeaning")
        self.detail_meaning_lbl.setWordWrap(True)
        layout.addWidget(self.detail_meaning_lbl)
        
        # Examples
        example_header = QLabel("💡 Ví dụ:")
        example_header.setObjectName("SectionHeader")
        layout.addWidget(example_header)
        
        self.detail_examples_txt = QTextEdit()
        self.detail_examples_txt.setReadOnly(True)
        self.detail_examples_txt.setMaximumHeight(100)
        self.detail_examples_txt.setStyleSheet("background: white; border: 1px solid #ddd; border-radius: 4px;")
        layout.addWidget(self.detail_examples_txt)
        
        # Notes
        notes_header = QLabel("📝 Ghi chú:")
        notes_header.setObjectName("SectionHeader")
        layout.addWidget(notes_header)
        
        self.detail_notes_txt = QTextEdit()
        self.detail_notes_txt.setReadOnly(True)
        self.detail_notes_txt.setMinimumHeight(150)
        self.detail_notes_txt.setStyleSheet("background: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px; line-height: 1.5;")
        layout.addWidget(self.detail_notes_txt)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        self.detail_edit_btn = QPushButton("✏️ Sửa")
        self.detail_edit_btn.clicked.connect(self._edit_selected_word)
        self.detail_delete_btn = QPushButton("🗑️ Xóa")
        self.detail_delete_btn.setStyleSheet("color: #d32f2f;")
        self.detail_delete_btn.clicked.connect(self._delete_selected_word)
        action_layout.addWidget(self.detail_edit_btn)
        action_layout.addWidget(self.detail_delete_btn)
        layout.addLayout(action_layout)
        
        # ===== Lookup Sources Section =====
        lookup_header = QLabel("🔍 Tra thêm từ điển:")
        lookup_header.setObjectName("SectionHeader")
        layout.addWidget(lookup_header)
        
        lookup_layout = QHBoxLayout()
        
        # Jisho/Oxford (primary)
        self.lookup_primary_btn = QPushButton("📚 Jisho")
        self.lookup_primary_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 2px; font-size: 11px;")
        self.lookup_primary_btn.clicked.connect(lambda: self._open_dictionary_url("jisho"))
        lookup_layout.addWidget(self.lookup_primary_btn)
        
        # Tatoeba (examples)
        self.lookup_tatoeba_btn = QPushButton("💬 Tatoeba")
        self.lookup_tatoeba_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 2px; font-size: 11px;")
        self.lookup_tatoeba_btn.clicked.connect(lambda: self._open_dictionary_url("tatoeba"))
        lookup_layout.addWidget(self.lookup_tatoeba_btn)
        
        # Google Translate
        self.lookup_translate_btn = QPushButton("🌐 Trans")
        self.lookup_translate_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 2px; font-size: 11px;")
        self.lookup_translate_btn.clicked.connect(lambda: self._open_dictionary_url("google_translate"))
        lookup_layout.addWidget(self.lookup_translate_btn)
        
        layout.addLayout(lookup_layout)
        
        # ===== AI Enrichment Section =====
        ai_layout = QHBoxLayout()
        self.ai_enrich_btn = QPushButton("✨ AI Làm giàu")
        self.ai_enrich_btn.setToolTip("Dùng AI cải thiện nghĩa và thêm ví dụ cho từ này")
        self.ai_enrich_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #DB2777);
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6D28D9, stop:1 #BE185D);
            }
            QPushButton:disabled {
                background: #ccc;
                color: #888;
            }
        """)
        self.ai_enrich_btn.clicked.connect(self._enrich_selected_word)
        ai_layout.addWidget(self.ai_enrich_btn)
        
        self.ai_enrich_btn.clicked.connect(self._enrich_selected_word)
        ai_layout.addWidget(self.ai_enrich_btn)
        
        layout.addLayout(ai_layout)
        
        layout.addStretch()
        
        # Wrap everything in a scroll area for responsiveness
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(panel)
        
        return scroll
    
    def _on_word_selected(self, item: QListWidgetItem):
        """Display word details in the detail panel."""
        word_data = item.data(Qt.UserRole)
        if not word_data:
            return
        
        # Store current selection for edit/delete
        self._selected_word_data = word_data
        
        # Update display
        self._display_word_details(word_data)
        
        # Auto-pronunciation (if enabled)
        if hasattr(self, 'auto_pronounce_enabled') and self.auto_pronounce_enabled:
            word = word_data.get("word") if isinstance(word_data, dict) else getattr(word_data, "word", "")
            if word:
                self._play_word_audio(word)

    def _display_word_details(self, word_data: Any):
        """Update the detail panel with word data."""
        if not word_data:
            return

        # Handle both dict and object
        if isinstance(word_data, dict):
            word = word_data.get("word", "")
            reading = word_data.get("reading", "")
            meaning = word_data.get("meaning", "")
            han_viet = word_data.get("han_viet", "")
            examples = word_data.get("examples", word_data.get("example", ""))
            notes = word_data.get("user_note", "")
        else:
            word = getattr(word_data, "word", "")
            reading = getattr(word_data, "reading", "")
            meaning = getattr(word_data, "meaning", "")
            han_viet = getattr(word_data, "han_viet", "")
            examples = getattr(word_data, "examples", getattr(word_data, "example", ""))
            notes = getattr(word_data, "user_note", "")
        
        self.detail_word_lbl.setText(word)
        self.detail_reading_lbl.setText(reading)
        self.detail_hanviet_lbl.setText(f"Hán Việt: {han_viet}" if han_viet else "")
        self.detail_meaning_lbl.setText(meaning)
        self.detail_examples_txt.setText(examples or "Chưa có ví dụ")
        self.detail_notes_txt.setText(notes or "Chưa có ghi chú")
        self.detail_audio_btn.show()


    def get_current_word_context(self) -> str:
        """Get context string for the currently selected word."""
        if not hasattr(self, '_selected_word_data') or not self._selected_word_data:
            return ""
        
        data = self._selected_word_data
        if isinstance(data, dict):
            word = data.get("word", "")
            reading = data.get("reading", "")
            meaning = data.get("meaning", "")
            han_viet = data.get("han_viet", "")
            examples = data.get("examples", "")
            notes = data.get("user_note", "")
        else:
            word = getattr(data, "word", "")
            reading = getattr(data, "reading", "")
            meaning = getattr(data, "meaning", "")
            han_viet = getattr(data, "han_viet", "")
            examples = getattr(data, "examples", "")
            notes = getattr(data, "user_note", "")
            
        context = f"Từ vựng: {word}"
        if reading: context += f" ({reading})"
        if han_viet: context += f" - Hán Việt: {han_viet}"
        context += f"\nNghĩa: {meaning}"
        if examples: context += f"\nVí dụ: {examples}"
        if notes: context += f"\nGhi chú: {notes}"
        
        return context
    
    def _play_detail_audio(self):
        """Play TTS for the selected word."""
        if hasattr(self, '_selected_word_data') and self._selected_word_data:
            word = self._selected_word_data.get("word") if isinstance(self._selected_word_data, dict) else getattr(self._selected_word_data, "word", "")
            if word:
                self._play_word_audio(word)
    
    def _play_word_audio(self, word: str):
        """Play TTS for a word using the mixin's playback logic."""
        if not word:
            return
        self._mixin_speak_text(word)
    
    def _open_dictionary_url(self, dict_type: str):
        """Open dictionary URL for the selected word."""
        if not hasattr(self, '_selected_word_data') or not self._selected_word_data:
            QMessageBox.warning(self, "Chưa chọn từ", "Vui lòng chọn một từ trước")
            return
        
        word = self._selected_word_data.get("word") if isinstance(self._selected_word_data, dict) else getattr(self._selected_word_data, "word", "")
        if not word:
            return
        
        from PySide6.QtGui import QDesktopServices
        from urllib.parse import quote
        
        lang = self._get_current_lang()
        encoded_word = quote(word)
        
        # Dictionary URLs
        urls = {
            "jisho": f"https://jisho.org/search/{encoded_word}" if lang == "jp" else f"https://www.oxfordlearnersdictionaries.com/definition/english/{encoded_word}",
            "tatoeba": f"https://tatoeba.org/en/sentences/search?query={encoded_word}&from={lang if lang == 'jp' else 'eng'}&to=vie",
            "google_translate": f"https://translate.google.com/?sl={'ja' if lang == 'jp' else 'en'}&tl=vi&text={encoded_word}",
            "cambridge": f"https://dictionary.cambridge.org/dictionary/{'japanese-english' if lang == 'jp' else 'english-vietnamese'}/{encoded_word}",
            "longman": f"https://www.ldoceonline.com/dictionary/{encoded_word}",
        }
        
        url = urls.get(dict_type)
        if url:
            QDesktopServices.openUrl(QUrl(url))
    
    def _show_word_context_menu(self, pos: QPoint):
        """Show context menu for word list."""
        item = self.vocab_table.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Sửa")
        delete_action = menu.addAction("🗑️ Xóa")
        menu.addSeparator()
        lookup_action = menu.addAction("🔍 Tra từ điển")
        
        action = menu.exec_(self.vocab_table.mapToGlobal(pos))
        if action == edit_action:
            self._edit_word(item)
        elif action == delete_action:
            self._delete_word_item(item)
        elif action == lookup_action:
            self._lookup_dictionary(item)
    
    def _edit_selected_word(self):
        """Edit the currently selected word."""
        current_item = self.vocab_table.currentItem()
        if current_item:
            self._edit_word(current_item)
    
    def _edit_word(self, item: QListWidgetItem):
        """Show dialog to edit a word."""
        from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        word_data = item.data(Qt.UserRole)
        if not word_data:
            return
        
        # Extract current values
        if isinstance(word_data, dict):
            word_id = word_data.get("id")
            word = word_data.get("word", "")
            reading = word_data.get("reading", "")
            meaning = word_data.get("meaning", "")
            examples = word_data.get("examples", word_data.get("example", ""))
            notes = word_data.get("user_note", "")
            level = word_data.get("level", "N5")
        else:
            word_id = getattr(word_data, "id", None)
            word = getattr(word_data, "word", "")
            reading = getattr(word_data, "reading", "")
            meaning = getattr(word_data, "meaning", "")
            examples = getattr(word_data, "examples", getattr(word_data, "example", ""))
            notes = getattr(word_data, "user_note", "")
            level = getattr(word_data, "level", "N5")
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sửa từ: {word}")
        dialog.setMinimumWidth(450)
        
        layout = QFormLayout(dialog)
        
        word_input = QLineEdit(word)
        reading_input = QLineEdit(reading or "")
        meaning_input = QTextEdit()
        meaning_input.setText(meaning or "")
        meaning_input.setMaximumHeight(80)
        examples_input = QTextEdit()
        examples_input.setText(examples or "")
        examples_input.setMaximumHeight(80)
        notes_input = QTextEdit()
        notes_input.setText(notes or "")
        notes_input.setMaximumHeight(60)
        level_combo = QComboBox()
        level_combo.addItems(["N5", "N4", "N3", "N2", "N1"])
        idx = level_combo.findText(level or "N5")
        if idx >= 0:
            level_combo.setCurrentIndex(idx)
        
        layout.addRow("Từ vựng:", word_input)
        layout.addRow("Phiên âm:", reading_input)
        layout.addRow("Nghĩa:", meaning_input)
        layout.addRow("Cấp độ:", level_combo)
        layout.addRow("Ví dụ:", examples_input)
        layout.addRow("Ghi chú:", notes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            lang = self._get_current_lang()
            updated_data = {
                "word": word_input.text().strip(),
                "reading": reading_input.text().strip(),
                "meaning": meaning_input.toPlainText().strip(),
                "level": level_combo.currentText(),
                "example": examples_input.toPlainText().strip(),
                "user_note": notes_input.toPlainText().strip(),
            }
            
            if updated_data["word"] and updated_data["meaning"]:
                async def update():
                    return self.vocab_service.update_vocab(word_id, updated_data, lang)
                
                def on_updated(result):
                    if result.get("success"):
                        toast_success(f"Đã cập nhật từ '{updated_data['word']}'")
                        self._load_vocab_list(self.current_filter)
                    else:
                        toast_error(result.get("error", "Không thể cập nhật từ"))
                
                run_async(update, on_updated)
            else:
                toast_warning("Vui lòng nhập từ vựng và nghĩa")
    
    def _delete_selected_word(self):
        """Delete the currently selected word."""
        current_item = self.vocab_table.currentItem()
        if current_item:
            self._delete_word_item(current_item)
    
    def _delete_word_item(self, item: QListWidgetItem):
        """Delete a word from the database."""
        word_data = item.data(Qt.UserRole)
        if not word_data:
            return
        
        word_id = word_data.get("id") if isinstance(word_data, dict) else getattr(word_data, "id", None)
        word_text = word_data.get("word") if isinstance(word_data, dict) else getattr(word_data, "word", "")
        
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc muốn xóa từ '{word_text}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes and word_id:
            lang = self._get_current_lang()
            async def delete():
                return self.vocab_service.delete_vocab(word_id, lang)
            
            def on_deleted(result):
                if result.get("success"):
                    self._load_vocab_list(self.current_filter)
                else:
                    QMessageBox.warning(self, "Lỗi", "Không thể xóa từ này")
            
            run_async(delete, on_deleted)
    
    def _lookup_dictionary(self, item: QListWidgetItem):
        """Lookup word in online dictionary."""
        word_data = item.data(Qt.UserRole)
        if not word_data:
            return
        
        word = word_data.get("word") if isinstance(word_data, dict) else getattr(word_data, "word", "")
        lang = self._get_current_lang()
        
        # Open in browser
        from PySide6.QtGui import QDesktopServices
        if lang == "jp":
            url = QUrl(f"https://jisho.org/search/{word}")
        else:
            url = QUrl(f"https://www.oxfordlearnersdictionaries.com/definition/english/{word}")
        
        QDesktopServices.openUrl(url)
    
    def _show_add_word_dialog(self):
        """Show dialog to add a new word with dictionary lookup."""
        from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QHBoxLayout
        from frontend.services.dictionary_service import DictionaryService
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm từ mới")
        dialog.setMinimumWidth(450)
        
        layout = QFormLayout(dialog)
        
        # Word input with lookup button
        word_row = QHBoxLayout()
        word_input = QLineEdit()
        word_input.setPlaceholderText("Nhập từ cần tra...")
        word_row.addWidget(word_input)
        
        lookup_btn = QPushButton("🔍 Tra từ điển")
        lookup_btn.setStyleSheet("background-color: #2196F3; color: white;")
        word_row.addWidget(lookup_btn)
        
        layout.addRow("Từ vựng:", word_row)
        
        reading_input = QLineEdit()
        meaning_input = QTextEdit()
        meaning_input.setMaximumHeight(80)
        examples_input = QTextEdit()
        examples_input.setMaximumHeight(80)
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        
        # Level dropdown
        lang = self._get_current_lang()
        level_combo = QComboBox()
        from frontend.models.vocab import JAPANESE_LEVELS, ENGLISH_LEVELS
        level_combo.addItems(JAPANESE_LEVELS if lang == "jp" else ENGLISH_LEVELS)
        
        # Source/Curriculum dropdown
        source_combo = QComboBox()
        source_combo.setEditable(True)  # Allow custom entry
        from frontend.models.vocab import JAPANESE_SOURCES, ENGLISH_SOURCES
        source_combo.addItem("(Không chọn)")
        source_combo.addItems(JAPANESE_SOURCES if lang == "jp" else ENGLISH_SOURCES)
        
        status_label = QLabel("")
        status_label.setStyleSheet("color: #666; font-style: italic;")
        
        layout.addRow("Phiên âm:", reading_input)
        layout.addRow("Nghĩa:", meaning_input)
        layout.addRow("📊 Cấp độ:", level_combo)
        layout.addRow("📖 Giáo trình:", source_combo)
        layout.addRow("Ví dụ:", examples_input)
        layout.addRow("Ghi chú:", notes_input)
        layout.addRow(status_label)
        
        # Lookup function
        def do_lookup():
            word = word_input.text().strip()
            if not word:
                status_label.setText("⚠️ Vui lòng nhập từ cần tra")
                return
            
            status_label.setText("⏳ Đang tra cứu từ điển...")
            lookup_btn.setEnabled(False)
            
            lang = self._get_current_lang()
            
            def fetch():
                return DictionaryService.lookup(word, lang)
            
            def on_result(result):
                lookup_btn.setEnabled(True)
                if result.get("error"):
                    status_label.setText(f"❌ {result['error']}")
                else:
                    status_label.setText("✅ Đã tìm thấy! Tự động điền thông tin.")
                    if result.get("reading"):
                        reading_input.setText(result["reading"])
                    if result.get("meaning"):
                        meaning_input.setText(result["meaning"])
                    if result.get("examples"):
                        examples_input.setText(result["examples"])
                    # Auto-detect JLPT level for Japanese
                    jlpt = result.get("jlpt", [])
                    if jlpt:
                        level_text = jlpt[0].replace("jlpt-", "").upper()
                        idx = level_combo.findText(level_text)
                        if idx >= 0:
                            level_combo.setCurrentIndex(idx)
            
            run_async(fetch, on_result)
        
        lookup_btn.clicked.connect(do_lookup)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            lang = self._get_current_lang()
            
            # Get source value (skip if "(Không chọn)")
            source_value = source_combo.currentText().strip()
            if source_value == "(Không chọn)":
                source_value = ""
            
            new_word = {
                "word": word_input.text().strip(),
                "reading": reading_input.text().strip(),
                "meaning": meaning_input.toPlainText().strip(),
                "level": level_combo.currentText(),
                "source_material": source_value,
                "examples": examples_input.toPlainText().strip(),
                "user_note": notes_input.toPlainText().strip(),
            }

            
            if new_word["word"] and new_word["meaning"]:
                async def add():
                    return self.vocab_service.add_vocab(new_word, lang)
                
                def on_added(result):
                    if result.get("success"):
                        toast_success(f"Đã thêm từ '{new_word['word']}'")
                        self._load_vocab_list(self.current_filter)
                    else:
                        toast_error(result.get("error", "Không thể thêm từ"))
                
                run_async(add, on_added)
            else:
                toast_warning("Vui lòng nhập từ vựng và nghĩa")
    
    def _show_import_csv_dialog(self):
        """Show dialog to import vocabulary from CSV file."""
        from frontend.ui.widgets.import_csv_dialog import ImportCSVDialog
        
        lang = self._get_current_lang()
        topics = self.vocab_service.list_topics(lang)
        
        dialog = ImportCSVDialog(
            parent=self,
            lang=lang,
            topics=topics
        )
        
        # Refresh list when import completes
        dialog.import_completed.connect(lambda result: self._load_vocab_list(self.current_filter))
        
        dialog.exec_()
    

    def _batch_lookup(self):
        """Batch lookup to auto-fill missing data for vocabulary items."""
        from frontend.services.dictionary_service import DictionaryService
        
        # Get items that are missing meaning or reading
        lang = self._get_current_lang()
        items = self.vocab_service.list_all(lang)
        
        # Find items missing data
        missing_items = []
        for item in items:
            word = item.get("word", "")
            meaning = item.get("meaning", "")
            reading = item.get("reading", "")
            
            # If missing meaning or reading, add to batch
            if word and (not meaning or not reading):
                missing_items.append(item)
        
        if not missing_items:
            toast_success("Tất cả từ vựng đã có đầy đủ thông tin!")
            return
        
        reply = QMessageBox.question(
            self, "Tra hàng loạt",
            f"Tìm thấy {len(missing_items)} từ thiếu thông tin.\n"
            f"Bạn có muốn tra cứu và tự động điền không?\n\n"
            f"(Quá trình này có thể mất một vài phút)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        progress = QProgressDialog("Đang tra cứu từ điển...", "Hủy", 0, len(missing_items), self)
        progress.setWindowModality(Qt.WindowModal)
        
        updated_count = 0
        error_count = 0
        
        for i, item in enumerate(missing_items):
            if progress.wasCanceled():
                break
            
            progress.setValue(i)
            progress.setLabelText(f"Đang tra: {item.get('word', '')} ({i+1}/{len(missing_items)})")
            
            # Lookup from API
            result = DictionaryService.lookup(item.get("word", ""), lang)
            
            if result.get("success"):
                # Update item
                update_data = {}
                if not item.get("reading") and result.get("reading"):
                    update_data["reading"] = result["reading"]
                if not item.get("meaning") and result.get("meaning"):
                    update_data["meaning"] = result["meaning"]
                if result.get("examples") and not item.get("example"):
                    update_data["example"] = result["examples"]
                
                if update_data:
                    self.vocab_service.update_vocab(item["id"], update_data, lang)
                    updated_count += 1
            else:
                error_count += 1
        
        progress.setValue(len(missing_items))
        
        toast_success(
            f"Tra cứu hàng loạt hoàn tất! ✅ Cập nhật: {updated_count}, ❌ Không tìm thấy: {error_count}"
        )
        
        # Refresh list
        self._load_vocab_list(self.current_filter)
    
    def _enrich_selected_word(self):
        """Enrich the selected word with AI-generated data."""
        if not hasattr(self, '_selected_word_data') or not self._selected_word_data:
            QMessageBox.warning(self, "Chưa chọn từ", "Vui lòng chọn một từ để làm giàu")
            return
        
        word_data = self._selected_word_data
        word_id = word_data.get("id") if isinstance(word_data, dict) else getattr(word_data, "id", None)
        word = word_data.get("word") if isinstance(word_data, dict) else getattr(word_data, "word", "")
        
        if not word_id or not word:
            return
        
        # Disable button during process
        self.ai_enrich_btn.setEnabled(False)
        self.ai_enrich_btn.setText("⏳ Đang xử lý...")
        
        lang = self._get_current_lang()
        
        from frontend.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        
        async def enrich():
            return await ai_service.enrich_vocabulary(word, lang)
        
        def on_enriched(result):
            self.ai_enrich_btn.setEnabled(True)
            self.ai_enrich_btn.setText("✨ AI Làm giàu")
            
            if result.get("success"):
                enriched_data = result.get("data", {})
                
                # Build update data
                update_data = {"is_ai_enriched": True}
                if enriched_data.get("meaning"):
                    update_data["meaning"] = enriched_data["meaning"]
                if enriched_data.get("reading"):
                    update_data["reading"] = enriched_data["reading"]
                if enriched_data.get("examples"):
                    update_data["examples"] = enriched_data["examples"]
                if enriched_data.get("han_viet"):
                    update_data["han_viet"] = enriched_data["han_viet"]
                if enriched_data.get("user_note"):
                    # Append to existing note instead of overwriting
                    existing_note = word_data.get("user_note", "") or ""
                    new_note = enriched_data["user_note"]
                    if new_note not in existing_note:
                        update_data["user_note"] = f"{existing_note}\n{new_note}" if existing_note else new_note
                
                if update_data:
                    # Update in database
                    async def update():
                        return self.vocab_service.update_vocab(word_id, update_data, lang)
                    
                    def on_updated(update_result):
                        if update_result.get("success"):
                            # Update local data and UI immediately
                            if isinstance(self._selected_word_data, dict):
                                self._selected_word_data.update(update_data)
                            else:
                                for key, value in update_data.items():
                                    setattr(self._selected_word_data, key, value)
                            
                            self._display_word_details(self._selected_word_data)
                            
                            toast_success(
                                f"Đã làm giàu từ '{word}'! ✅ Cập nhật: {', '.join(update_data.keys())}"
                            )

                    
                    run_async(update, on_updated)
                else:
                    toast_success("AI không trả về dữ liệu mới cho từ này")
            else:
                error_msg = result.get("error", "Không xác định")
                QMessageBox.warning(self, "Lỗi AI", f"Không thể làm giàu từ vựng:\n{error_msg}")
        
        run_async(enrich, on_enriched)
    
    
    def _batch_enrich_vocab(self):
        """Batch enrich all words in current filtered list with AI."""
        if not hasattr(self, 'all_current_words') or not self.all_current_words:
            QMessageBox.warning(self, "Không có dữ liệu", "Vui lòng chọn giáo trình hoặc bộ lọc có từ vựng")
            return

        # Filter out already enriched words to save tokens
        words_to_enrich_filtered = []
        for word_data in self.all_current_words:
            # Enrich if not marked yet OR if marked but missing the detailed note
            is_enriched = word_data.get("is_ai_enriched")
            has_note = bool(word_data.get("user_note") and word_data.get("user_note").strip())
            
            if not is_enriched or not has_note:
                words_to_enrich_filtered.append(word_data)
        
        skipped_count = len(self.all_current_words) - len(words_to_enrich_filtered)
        
        if not words_to_enrich_filtered:
            toast_success("Tất cả từ vựng trong danh sách đã được làm giàu bởi AI!")
            return

        # Limit total batch size for safety, but allow user to process more
        max_total_batch = 500
        words_to_process = words_to_enrich_filtered[:max_total_batch]
        
        reply = QMessageBox.question(
            self, "Làm giàu hàng loạt với AI",
            f"Tìm thấy {len(words_to_enrich_filtered)} từ chưa được làm giàu.\n"
            f"(Đã bỏ qua {skipped_count} từ đã xử lý)\n\n"
            f"Bạn có muốn xử lý {len(words_to_process)} từ tiếp theo không?\n"
            f"⚠️ Quá trình này sẽ gửi yêu cầu theo nhóm (50 từ/lần) để tiết kiệm RPD tối đa.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.ai_batch_btn.setEnabled(False)
        self.ai_batch_btn.setText("⏳ Đang xử lý...")
        
        from frontend.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        lang = self._get_current_lang()
        
        # Chunk size for batch requests
        CHUNK_SIZE = 50
        
        # Prepare progress dialog
        progress = QProgressDialog("Đang làm giàu từ vựng với AI (Batch)...", "Hủy", 0, len(words_to_process), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        # Define signals for thread-safe updates
        self.worker_signals = WorkerSignals()
        
        def update_progress_ui(val, text):
            progress.setValue(val)
            progress.setLabelText(text)
            
        self.worker_signals.progress.connect(update_progress_ui)
        
        enriched_count = 0
        error_count = 0
        
        async def process_chunks():
            nonlocal enriched_count, error_count
            
            # Create chunks
            chunks = [words_to_process[i:i + CHUNK_SIZE] for i in range(0, len(words_to_process), CHUNK_SIZE)]
            
            for i, chunk in enumerate(chunks):
                if progress.wasCanceled():
                    break
                
                # Emit progress update safely
                processed_so_far = i * CHUNK_SIZE
                self.worker_signals.progress.emit(processed_so_far, f"Đang xử lý nhóm {i+1}/{len(chunks)} ({len(chunk)} từ)...")
                
                # Prepare words for prompt
                words = [item.get("word", "") for item in chunk]
                
                try:
                    # Call AI with batch
                    result = await ai_service.enrich_vocabulary_batch(words, lang)
                    
                    if result.get("success"):
                        batch_results = result.get("results", {})
                        
                        # Process results for each word in the chunk
                        import re
                        def normalize_key(k):
                            return re.sub(r'[()（）\s]', '', str(k)).lower()

                        for item in chunk:
                            word = item.get("word", "")
                            word_id = item.get("id")
                            
                            # Try exact match first, then fuzzy match
                            matched_data = None
                            if word in batch_results:
                                matched_data = batch_results[word]
                            else:
                                # Fuzzy lookup: check if normalized keys match
                                norm_word = normalize_key(word)
                                for res_key, res_data in batch_results.items():
                                    if normalize_key(res_key) == norm_word:
                                        matched_data = res_data
                                        break
                            
                            if matched_data:
                                data = matched_data
                                update_data = {}
                                
                                # Always update if data exists
                                if data.get("meaning"): update_data["meaning"] = data["meaning"]
                                if data.get("examples"): update_data["examples"] = data["examples"]
                                if data.get("reading"): update_data["reading"] = data["reading"]
                                if data.get("han_viet"): update_data["han_viet"] = data["han_viet"]
                                if data.get("user_note"):
                                    # Append to existing note for consistency with single enrich
                                    existing_note = item.get("user_note", "") or ""
                                    new_note = data["user_note"]
                                    if new_note and new_note not in existing_note:
                                        update_data["user_note"] = f"{existing_note}\n{new_note}" if existing_note else new_note
                                
                                # Use the new boolean flag
                                update_data["is_ai_enriched"] = True
                                
                                if update_data:
                                    self.vocab_service.update_vocab(word_id, update_data, lang)
                                    enriched_count += 1
                            else:
                                print(f"Warning: AI didn't return data for {word}")
                                error_count += 1
                    else:
                        print(f"Batch failed: {result.get('error')}")
                        error_count += len(chunk)
                        
                except Exception as e:
                    print(f"Chunk error: {e}")
                    error_count += len(chunk)
                
                # Small delay to respect rate limits if needed
                import asyncio
                await asyncio.sleep(0.5)

            return {"enriched": enriched_count, "errors": error_count}

        def on_batch_complete(result):
            self.ai_batch_btn.setEnabled(True)
            self.ai_batch_btn.setText("✨ AI Làm giàu")
            # Ensure 100% progress
            progress.setValue(len(words_to_process))
            
            # Cleanup signals
            if hasattr(self, 'worker_signals'):
                del self.worker_signals
            
            toast_success(
                f"Làm giàu hàng loạt hoàn tất! ✅ Thành công: {enriched_count}, ❌ Thất bại/Bỏ qua: {error_count}"
            )
            
            self._load_vocab_list(self.current_filter)
        
        run_async(process_chunks, on_batch_complete)
    
    def _on_auto_pronounce_toggled(self, enabled: bool):
        """Handle auto-pronounce toggle."""
        self.auto_pronounce_enabled = enabled
    
    def _create_study_view_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Top bar
        top_bar = QHBoxLayout()
        self.exit_study_btn = QPushButton("🔙 Thoát")
        self.exit_study_btn.clicked.connect(self._exit_study_session)
        self.progress_lbl = QLabel("0/0")
        top_bar.addWidget(self.exit_study_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.progress_lbl)
        layout.addLayout(top_bar)
        
        # Flashcard Area
        self.flashcard = VocabFlashcardView()
        layout.addWidget(self.flashcard, 1) # Expand
        
        # Controls Area
        self.controls_area = QWidget()
        controls_layout = QVBoxLayout(self.controls_area)
        
        # Step 1: Show Answer Button
        self.show_answer_btn = QPushButton("Hiện đáp án (Space)")
        self.show_answer_btn.setFixedHeight(50)
        self.show_answer_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-size: 16px; font-weight: bold; border-radius: 5px;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.show_answer_btn.clicked.connect(self._on_show_answer)
        self.show_answer_btn.setShortcut("Space")
        controls_layout.addWidget(self.show_answer_btn)
        
        # Step 2: Rating Buttons (Hidden initially)
        self.rating_container = QWidget()
        rating_layout = QHBoxLayout(self.rating_container)
        rating_layout.setContentsMargins(0,0,0,0)
        
        # Again (1m)
        self.btn_again = QPushButton("Học lại\n(< 1p)")
        self.btn_again.setStyleSheet("background-color: #FF5252; color: white;")
        self.btn_again.clicked.connect(lambda: self._submit_review(1))
        
        # Hard (5m)
        self.btn_hard = QPushButton("Khó\n(5p)")
        self.btn_hard.setStyleSheet("background-color: #FF9800; color: white;")
        self.btn_hard.clicked.connect(lambda: self._submit_review(2))
        
        # Good (10m)
        self.btn_good = QPushButton("Tốt\n(10p)")
        self.btn_good.setStyleSheet("background-color: #4CAF50; color: white;")
        self.btn_good.clicked.connect(lambda: self._submit_review(3))
        
        # Easy (4d)
        self.btn_easy = QPushButton("Dễ\n(4n)")
        self.btn_easy.setStyleSheet("background-color: #2196F3; color: white;")
        self.btn_easy.clicked.connect(lambda: self._submit_review(4)) # 4 is Easy loop index
        
        rating_layout.addWidget(self.btn_again)
        rating_layout.addWidget(self.btn_hard)
        rating_layout.addWidget(self.btn_good)
        rating_layout.addWidget(self.btn_easy)
        
        controls_layout.addWidget(self.rating_container)
        self.rating_container.hide()
        
        layout.addWidget(self.controls_area)
        
        return widget

    # ================= LOGIC TO LOAD DATA =================
    
    def _get_current_lang(self):
        return self.lang_combo.currentData() or "jp"

    def _on_lang_changed(self):
        self._load_topics()
        self._load_filter_options()

    def _load_topics(self):
        """Load topics into sidebar ListWidget."""
        self.topic_list.clear() # Reset
        lang = self._get_current_lang()
        
        # 1. Special "All" topic
        all_item = QListWidgetItem("Tất cả từ vựng")
        all_item.setData(Qt.UserRole, "ALL") 
        self.topic_list.addItem(all_item)
        
        # 1.5. Unclassified (NULL topic)
        unclassified_item = QListWidgetItem("📂 Chưa phân loại")
        unclassified_item.setData(Qt.UserRole, {"type": "topic", "value": -1})
        self.topic_list.addItem(unclassified_item)
        
        # 2. Levels (Hardcoded per lang)
        levels = JAPANESE_LEVELS if lang == "jp" else ENGLISH_LEVELS
        
        level_header = QListWidgetItem("--- Cấp độ ---")
        level_header.setFlags(Qt.NoItemFlags) # Disabled
        self.topic_list.addItem(level_header)
        
        for level in levels:
            item = QListWidgetItem(f"Trình độ {level}")
            item.setData(Qt.UserRole, {"type": "level", "value": level})
            self.topic_list.addItem(item)

        # 3. Custom Topics from DB
        async def fetch_topics():
            return self.vocab_service.list_topics(lang)
            
        def display_topics(topics):
            if topics:
                 self.topic_list.addItem(QListWidgetItem("--- Custom ---"))
                 for t in topics:
                     item = QListWidgetItem(t["name"])
                     item.setData(Qt.UserRole, {"type": "topic", "value": t["id"]})
                     self.topic_list.addItem(item)
            
            # Select first item
            self.topic_list.setCurrentRow(0)
            self._on_topic_selected(self.topic_list.item(0))
            
        run_async(fetch_topics, display_topics)

    def _on_topic_selected(self, item):
        if not item: return
        data = item.data(Qt.UserRole)
        self._load_vocab_list(data)
        # Refresh filters to catch any new sources/levels added
        self._load_filter_options()
        
    def _create_topic_dialog(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Tạo chủ đề mới", "Tên chủ đề:")
        if ok and name:
            lang = self._get_current_lang()
            async def create():
                return self.vocab_service.create_topic(name, lang)
            
            def created(result):
                if result.get("success"):
                     self._load_topics()
                else:
                     QMessageBox.warning(self, "Lỗi", "Không thể tạo chủ đề")
            
            run_async(create, created)

    def _load_vocab_list(self, filter_data=None):
        """Load vocabulary list based on selected filter."""
        self.current_filter = filter_data
        lang = self._get_current_lang()
        
        # 1. Parse filter_data from sidebar
        topic_id = None
        base_level_filter = None
        
        if filter_data == "ALL":
            topic_id = None
        elif isinstance(filter_data, dict):
            if filter_data.get("type") == "topic":
                topic_id = filter_data.get("value")
            elif filter_data.get("type") == "level":
                base_level_filter = filter_data.get("value")
        
        self.current_topic_id = topic_id # Update state
        
        # 2. Get filter values from Toolbar UI
        source_filter = self.source_filter_combo.currentData() if hasattr(self, 'source_filter_combo') else None
        level_filter = self.level_filter_combo.currentData() if hasattr(self, 'level_filter_combo') else None
        status_filter = self.status_filter_combo.currentData() if hasattr(self, 'status_filter_combo') else None
        
        # Level filter can come from sidebar OR toolbar dropdown
        # If toolbar dropdown has a value, it overrides the sidebar level selection
        final_level = level_filter if level_filter else base_level_filter
        
        # Build mastery_statuses list
        mastery_statuses = [status_filter] if status_filter else None
        
        async def fetch():
            # Use new list_by_filters for advanced filtering
            return self.vocab_service.list_by_filters(
                lang=lang,
                topic_id=topic_id,
                source_material=source_filter,
                level=final_level,
                mastery_statuses=mastery_statuses,
                limit=1000
            )

        def display(words):
            self.all_current_words = words  # Store for search filter
            self._filter_vocab_list()
            
            # Fire separate call for exact Due / New Statistics
            self._update_due_count()

        run_async(fetch, display)
        
    def _update_due_count(self):
        lang = self._get_current_lang()
        async def fetch_stats():
            source = self.source_filter_combo.currentData() if hasattr(self, 'source_filter_combo') else None
            level = self.level_filter_combo.currentData() if hasattr(self, 'level_filter_combo') else None
            topic_id = self.current_topic_id if hasattr(self, 'current_topic_id') else None
            
            # Use get_stats to get multiple metrics at once
            return self.vocab_service.get_stats(
                lang=lang,
                topic_id=topic_id,
                source_material=source,
                level=level
            )
        
        def update(stats):
            due_count = stats.get("due", 0)
            new_count = stats.get("new", 0)
            
            self.due_count_lbl.setText(f"{due_count}")
            self.new_count_lbl.setText(f"{new_count}")
            
            # Highlight Study buttons if items are due
            study_btn_style = """
                QPushButton {{
                    background-color: {color}; color: white; font-weight: bold;
                    padding: 6px 8px; border-radius: 4px; font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {hover_color}; }}
            """
            sidebar_study_style = """
                QPushButton {{
                    background-color: {color}; color: white;
                    padding: 10px; font-size: 15px; font-weight: bold; border-radius: 10px;
                }}
                QPushButton:hover {{ background-color: {hover_color}; }}
            """
            
            if due_count > 0:
                self.study_now_btn.setStyleSheet(study_btn_style.format(color="#f44336", hover_color="#d32f2f"))
                self.study_now_btn_large.setStyleSheet(sidebar_study_style.format(color="#f44336", hover_color="#d32f2f"))
            else:
                self.study_now_btn.setStyleSheet(study_btn_style.format(color="#2196F3", hover_color="#1976D2"))
                self.study_now_btn_large.setStyleSheet(sidebar_study_style.format(color="#2ecc71", hover_color="#27ae60"))
            
            # --- Update Dashboard specific stats ---
            if hasattr(self, 'dash_due_lbl'):
                self.dash_due_lbl.setText(f"{due_count} từ cần ôn")
            
            if hasattr(self, 'dash_new_lbl'):
                 self.dash_new_lbl.setText(f"{new_count} từ mới")
                 
            # Retrieve detailed stats if available (requires modifying service to return more info, 
            # or we can do a separate lightweight query here for levels)
            # For now, we will just use dummy or simple stat aggregation if possible.
            # Ideally we fetch level breakdown.
            self._update_level_progress_ui()
    
    def _update_level_progress_ui(self):
        """Fetch and update the level progress bars in Dashboard."""
        if not hasattr(self, 'dash_progress_layout'):
            return
            
        lang = self._get_current_lang()
        levels = JAPANESE_LEVELS if lang == 'jp' else ENGLISH_LEVELS
        
        async def fetch_level_stats():
            # We need a new service method or just loop for now (inefficient but works for small DB)
            # Better: vocab_service.get_stats(group_by='level')
            # For now, let's assume we can get counts per level.
            # To avoid API changes, we might skip this or do rough count from local 'all_current_words' if loaded?
            # No, 'all_current_words' is filtered.
            
            # Let's try to query stats for each level parallelly
            res = {}
            for lvl in levels:
                stats = await self.vocab_service.get_stats(lang=lang, level=lvl)
                res[lvl] = stats
            return res

        def update(results):
            # Clear old
            while self.dash_progress_layout.count():
                item = self.dash_progress_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            
            for lvl in levels:
                if lvl not in results: continue
                s = results[lvl]
                total = s.get('total', 0)
                mastered = s.get('mastered', 0)
                
                if total == 0: continue # Skip empty levels
                
                percent = int((mastered / total) * 100)
                
                # Create Progress Row
                row = QWidget()
                r_layout = QHBoxLayout(row)
                r_layout.setContentsMargins(0, 5, 0, 5)
                
                lbl = QLabel(f"{lvl}")
                lbl.setFixedWidth(40)
                lbl.setStyleSheet("font-weight: bold;")
                
                pbar = QProgressBar()
                pbar.setRange(0, 100)
                pbar.setValue(percent)
                pbar.setTextVisible(False)
                pbar.setFixedHeight(8)
                pbar.setStyleSheet(f"""
                    QProgressBar {{
                        border-radius: 4px;
                        background: {ThemeColors.BG_TERTIARY};
                        border: none;
                    }}
                    QProgressBar::chunk {{
                        background-color: {ThemeColors.PRIMARY};
                        border-radius: 4px;
                    }}
                """)
                
                count_lbl = QLabel(f"{mastered}/{total}")
                count_lbl.setStyleSheet("color: #777; font-size: 12px;")
                
                r_layout.addWidget(lbl)
                r_layout.addWidget(pbar)
                r_layout.addWidget(count_lbl)
                
                self.dash_progress_layout.addWidget(row)
                
        run_async(fetch_level_stats, update)

            
        run_async(fetch_stats, update)

    def _is_due(self, word):
        # Deprecated: Using service.get_due now
        return False

    def _filter_vocab_list(self):
        """Filter displayed vocab list by search text."""
        query = self.search_input.text().lower()
        self.vocab_table.clear()
        
        visible_words = []
        if hasattr(self, 'all_current_words'):
            for word in self.all_current_words:
                # Apply Text Search
                word_text = word.get('word', '').lower()
                meaning_text = word.get('meaning', '').lower()
                reading_text = word.get('reading', '').lower() if word.get('reading') else ''
                
                if query in word_text or query in meaning_text or query in reading_text:
                    visible_words.append(word)
        
        for w in visible_words:
            status = w.get('mastery_status', 'new').upper()
            level = w.get('level', '')
            source = w.get('source_material', '')
            
            # Format display text
            level_str = f" [{level}]" if level else ""
            text = f"{w.get('word')} - {w.get('meaning')}{level_str} ({status})"
            
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, w)
            
            # Color code by status
            if status == "MASTERED":
                item.setForeground(QColor("#4CAF50"))
            elif status == "HARD":
                item.setForeground(QColor("#F44336"))
            elif status == "LEARNING":
                item.setForeground(QColor("#2196F3"))
                
            self.vocab_table.addItem(item)
            
        # Update count in footer
        if hasattr(self, 'total_words_lbl'):
            self.total_words_lbl.setText(f"Tổng số từ: {self.vocab_table.count()}")
    
    def _apply_filters(self):
        """Apply all filters and reload vocab list."""
        self._load_vocab_list(self.current_filter)
    
    def _clear_filters(self):
        """Clear all filters and reload vocab list."""
        # Block signals to prevent multiple reloads
        self.source_filter_combo.blockSignals(True)
        self.level_filter_combo.blockSignals(True)
        self.status_filter_combo.blockSignals(True)
        
        self.source_filter_combo.setCurrentIndex(0)
        self.level_filter_combo.setCurrentIndex(0)
        self.status_filter_combo.setCurrentIndex(0)
        self.search_input.clear()
        
        self.source_filter_combo.blockSignals(False)
        self.level_filter_combo.blockSignals(False)
        self.status_filter_combo.blockSignals(False)
        
        # Reload
        self._load_vocab_list(None)
    
    def _load_filter_options(self):
        """Load filter options from database for Source and Level combos."""
        lang = self._get_current_lang()
        
        async def fetch_options():
            sources = self.vocab_service.get_distinct_sources(lang)
            levels = self.vocab_service.get_distinct_levels(lang)
            return {"sources": sources, "levels": levels}
        
        def populate(data):
            # Populate Source combo
            sources = data.get("sources", [])
            self.source_filter_combo.blockSignals(True)
            current_source = self.source_filter_combo.currentData()
            self.source_filter_combo.clear()
            self.source_filter_combo.addItem("📖 Tất cả", None)
            
            # Use ONLY sources from DB as requested
            all_sources = [s for s in sources if s and s.strip()]
            all_sources.sort()
            
            print(f"[DEBUG UI] Populating Source Filter (Dynamic) - lang: {lang}")
            print(f"[DEBUG UI] Sources from DB: {all_sources}")
            
            for s in all_sources:
                self.source_filter_combo.addItem(s, s)
            
            # Restore selection if still valid
            if current_source:
                idx = self.source_filter_combo.findData(current_source)
                if idx >= 0:
                    self.source_filter_combo.setCurrentIndex(idx)
            self.source_filter_combo.blockSignals(False)
            
            # Populate Level combo
            levels = data.get("levels", [])
            self.level_filter_combo.blockSignals(True)
            current_level = self.level_filter_combo.currentData()
            self.level_filter_combo.clear()
            self.level_filter_combo.addItem("📊 Tất cả", None)
            
            # Use ONLY levels from DB for consistency
            all_levels = [l for l in levels if l and l.strip()]
            all_levels.sort() # Simple sort (N1, N2.. or alphabetical)
            
            for l in all_levels:
                self.level_filter_combo.addItem(l, l)
            
            # Restore selection
            if current_level:
                idx = self.level_filter_combo.findData(current_level)
                if idx >= 0:
                    self.level_filter_combo.setCurrentIndex(idx)
            self.level_filter_combo.blockSignals(False)
        
        run_async(fetch_options, populate)


    # ================= STUDY MODE =================

    def _start_study_session(self):
        """Switch to Flashcard view with Due cards."""
        lang = self.lang_combo.currentData()
        async def fetch_session():
            # CAPTURE CURRENT FILTERS
            source = self.source_filter_combo.currentData() if hasattr(self, 'source_filter_combo') else None
            level = self.level_filter_combo.currentData() if hasattr(self, 'level_filter_combo') else None
            topic_id = self.current_topic_id if hasattr(self, 'current_topic_id') else None
            
            print(f"[DEBUG Study] Starting session with filters - Source: {source}, Level: {level}, Topic: {topic_id}")
            
            return await self.vocab_service.get_due(
                lang=lang, 
                limit=20, 
                topic_id=topic_id,
                source_material=source,
                level=level
            ) 
            
        def start_session(cards):
            if isinstance(cards, dict) and "error" in cards:
                QMessageBox.warning(self, "Lỗi", f"Không thể tải bài học: {cards['error']}")
                return
                
            if not cards:
                toast_success("Bạn đã hoàn thành bài học hôm nay!\nKhông còn thẻ nào cần ôn tập.")
                return
                
            self.srs_session_queue = cards
            self.current_review_index = 0
            self.stacked_widget.setCurrentWidget(self.study_view_widget)
            self._load_current_card()
            
        run_async(fetch_session, start_session)

    def _load_current_card(self):
        if self.current_review_index >= len(self.srs_session_queue):
            self._finish_study_session()
            return
            
        card_data = self.srs_session_queue[self.current_review_index]
        self.flashcard.set_card(card_data)
        
        # Reset controls
        self.show_answer_btn.show()
        self.show_answer_btn.setFocus()
        self.rating_container.hide()
        
        # Update progress
        self.progress_lbl.setText(f"{self.current_review_index + 1}/{len(self.srs_session_queue)}")

    def _on_show_answer(self):
        self.flashcard.flip()
        self.show_answer_btn.hide()
        self.rating_container.show()
        self.btn_good.setFocus() # Default focus to Good

    def _submit_review(self, quality: int):
        """
        Quality: 
        1=Again (Reset)
        2=Hard (Short interval)
        3=Good (Normal interval)
        4=Easy (Long interval)
        """
        if self.current_review_index >= len(self.srs_session_queue):
            return

        current_card = self.srs_session_queue[self.current_review_index]
        vocab_id = current_card.get('id')
        lang = self.lang_combo.currentData()
        
        async def update_srs():
            return self.vocab_service.submit_review(vocab_id, quality, lang=lang)
            
        def on_updated(result):
            if result.get("error"):
                print(f"Error updating SRS: {result.get('error')}")
            
        run_async(update_srs, on_updated)
        
        # Move to next
        self.current_review_index += 1
        self._load_current_card()

    def _finish_study_session(self):
        toast_success("Bạn đã hoàn thành phiên học!")
        self._exit_study_session()

    def _exit_study_session(self):
        self.stacked_widget.setCurrentWidget(self.list_view_widget)
        self._load_vocab_list(self.current_filter) # Refresh

    # ================= MANAGEMENT =================

    def _show_topic_manager(self):
        toast_info("Quản lý chủ đề sẽ được cập nhật sau.")

    def _scan_image(self):
        # Re-implement Scan Image using existing logic but simplified
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if not file_path:
            return
            
        if not self._gemini_api_key:
             QMessageBox.warning(self, "Lỗi", "Cần cấu hình API Key trong Cài đặt trước.")
             return
             
        progress = QProgressDialog("Đang quét ảnh bằng AI...", "Hủy", 0, 0, self)
        progress.show()
        
        # Use existing worker logic... simplified for rewrite
        # (Assuming GeminiScanWorker import exists and works)
        # ... logic similar to previous implementation ...
        pass

    def _start_tinder_session(self):
        """Start Tinder-style rapid review session."""
        lang = self.lang_combo.currentData() if hasattr(self, 'lang_combo') else "jp"
        
        # Get current filters
        topic_id = self.current_topic_id if hasattr(self, 'current_topic_id') else None
        source_filter = self.source_filter_combo.currentData() if hasattr(self, 'source_filter_combo') else None
        level_filter = self.level_filter_combo.currentData() if hasattr(self, 'level_filter_combo') else None
        
        # Fetch words: Priority Review > New > Random using filters
        async def fetch_tinder_data():
            # Get 20 random items for quick review respecting filters
            return await self.vocab_service.get_random_review_items(
                lang=lang, 
                limit=20,
                topic_id=topic_id,
                source_material=source_filter,
                level=level_filter
            )
            
        run_async(fetch_tinder_data, self._on_tinder_data_ready)
        
    def _on_tinder_data_ready(self, items):
        if not items:
            QMessageBox.information(self, "Thông báo", "Không tìm thấy từ vựng nào để ôn tập! Hãy thêm từ mới trước.")
            return
            
        lang = self.lang_combo.currentData() if hasattr(self, 'lang_combo') else "jp"
        self.tinder_view.start_session(items, lang=lang)
        self.stacked_widget.setCurrentWidget(self.tinder_view)
    
    def _update_stats_ui(self):
        """Update dashboard statistics (due counts, etc)."""
        # Re-fetch stats from service
        lang = self.lang_combo.currentData()
        stats = self.vocab_service.get_stats(lang)
        
        # Update labels in sidebar
        self.due_count_lbl.setText(str(stats.get("due", 0)))
        self.new_count_lbl.setText(str(stats.get("new", 0)))
        
        # Update dashboard cards if they exist
        if hasattr(self, 'dash_due_lbl'):
            self.dash_due_lbl.setText(f"{stats.get('due', 0)} từ cần ôn")
            
        if hasattr(self, 'dash_new_lbl'):
            # Simple logic: if new > 0, Ready, else All Done
            count = stats.get("new", 0)
            if count > 0:
                self.dash_new_lbl.setText("Sẵn sàng")
                self.dash_new_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeColors.PRIMARY}; font-weight: bold;")
            else:
                self.dash_new_lbl.setText("Đã học hết")
                self.dash_new_lbl.setStyleSheet(f"font-size: 14px; color: grey; font-weight: bold;")

    def _reset_all_visible_ai(self):
        """Reset AI enrichment status for all currently visible vocab."""
        if not hasattr(self, 'all_current_words') or not self.all_current_words:
            return
            
        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Bạn có muốn reset trạng thái AI cho {len(self.all_current_words)} từ vựng đang hiển thị không?\n"
            "(Thẻ sẽ được AI làm giàu lại vào lần tới)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        lang = self._get_current_lang()
        count = 0
        for word in self.all_current_words:
            word_id = word.get("id")
            self.vocab_service.update_vocab(word_id, {"is_ai_enriched": False}, lang)
            count += 1
            
        toast_success(f"Đã reset trạng thái AI cho {count} từ vựng.")
        self._apply_filters()
