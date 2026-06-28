"""Grammar Tab - Anki-style Flashcard Learning (Vietnamese Interface)."""
from typing import Optional, List, Dict, Any
from sqlmodel import select, func, or_
# Services
from frontend.core.database import get_session
from frontend.core.user_settings import get_user_settings
from frontend.services.grammar_fetcher_service import GrammarFetcherService
from frontend.models.grammar import GrammarTopic, GrammarMasteryStatus, JAPANESE_GRAMMAR_LEVELS, JAPANESE_GRAMMAR_SOURCES
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin
from frontend.utils.async_helpers import run_async
from frontend.services.tts import get_tts_service
from frontend.ui.tabs.grammar_practice_tab import GrammarPracticeTab
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QListWidget, QLabel, QSplitter, QMenu, QMessageBox,
    QListWidgetItem, QGroupBox, QFrame, QStackedWidget, QScrollArea,
    QGraphicsOpacityEffect, QGridLayout, QSizePolicy, QCheckBox, QTabWidget,
    QButtonGroup
)
from PySide6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QAction, QFont, QDesktopServices
from urllib.parse import quote
from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning
from frontend.ui.styles.theme import ThemeColors
from frontend.ui.styles.animations import AnimationService
import markdown
from frontend.ui.widgets.grammar_flashcard import GrammarFlashcardView
from frontend.ui.widgets.learning_map import LearningMapWidget
from frontend.services.learning_map_service import LearningMapService
from frontend.models.learning_progress import MapStatus




class GrammarTab(QWidget, TextContextMenuMixin):
    """Grammar Study Tab with Anki Interface."""
    
    def __init__(self):
        super().__init__()
        self.fetcher_service = GrammarFetcherService()
        self.map_service = LearningMapService()
        self.srs_session_queue = []
        self.current_review_index = 0
        
        self._init_ui()
        self._load_levels()
        self._load_filter_options()
        self.map_service.ensure_progress_exists()
        
    def showEvent(self, event):
        """Sync language when tab is shown."""
        super().showEvent(event)
        settings = get_user_settings()
        lang = settings.get_language()
        
        # Sync ComboBox
        index = self.lang_combo.findData(lang)
        if index != -1 and index != self.lang_combo.currentIndex():
            self.lang_combo.setCurrentIndex(index)
    
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

        # --- TAB 1: Ngữ pháp & Học tập ---
        self.study_page = QWidget()
        study_layout = QHBoxLayout(self.study_page)
        study_layout.setContentsMargins(0,0,0,0)
        
        # --- SIDEBAR ---
        self.sidebar = self._create_sidebar()
        study_layout.addWidget(self.sidebar)

        # ===== MAIN CONTENT =====
        self.main_content_area = QWidget()
        main_content_layout = QVBoxLayout(self.main_content_area)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toggle Bar
        toggle_container = QWidget()
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.addStretch()
        
        self.view_toggle_group = QButtonGroup(self)
        self.view_toggle_group.setExclusive(True)
        
        self.btn_view_smart = QPushButton("🧩 Lắp ghép")
        self.btn_view_smart.setCheckable(True)
        self.btn_view_smart.setChecked(True)
        self.btn_view_smart.setFixedSize(140, 36)
        self.btn_view_smart.setCursor(Qt.PointingHandCursor)
        self.btn_view_smart.clicked.connect(lambda: self.view_stack.setCurrentIndex(0))
        
        self.btn_view_dict = QPushButton("📖 Tra cứu / List")
        self.btn_view_dict.setCheckable(True)
        self.btn_view_dict.setFixedSize(140, 36)
        self.btn_view_dict.setCursor(Qt.PointingHandCursor)
        self.btn_view_dict.clicked.connect(lambda: self.view_stack.setCurrentIndex(1))
        
        self.view_toggle_group.addButton(self.btn_view_smart)
        self.view_toggle_group.addButton(self.btn_view_dict)
        
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
        
        # Map View toggle button
        self.btn_view_map = QPushButton("🗺️ Bản đồ")
        self.btn_view_map.setCheckable(True)
        self.btn_view_map.setFixedSize(140, 36)
        self.btn_view_map.setCursor(Qt.PointingHandCursor)
        self.btn_view_map.clicked.connect(lambda: self.view_stack.setCurrentIndex(3))
        self.btn_view_map.setStyleSheet(toggle_style)
        self.view_toggle_group.addButton(self.btn_view_map)
        toggle_layout.addWidget(self.btn_view_map)
        
        toggle_layout.addStretch()
        
        main_content_layout.addWidget(toggle_container)
        
        self.view_stack = QStackedWidget()
        
        # View 0: Smart Dashboard (Puzzle)
        self.smart_dashboard = self._create_smart_dashboard()
        self.view_stack.addWidget(self.smart_dashboard)
        
        # View 1: List View (Manage/Browsing)
        self.list_view = self._create_list_view()
        self.view_stack.addWidget(self.list_view)
        
        # Note: Study View is part of list_view stack OR handled separately.
        # In GrammarTab, study view was part of stacked widget.
        # We need to make sure _start_session switches correctly.
        # Let's add study view as View 2 in main stack for simplicity.
        self.study_view = self._create_study_view()
        self.view_stack.addWidget(self.study_view)
        
        # View 3: Learning Map View (filtered by current language)
        current_lang = self.lang_combo.currentData() or "en"
        self.map_view = LearningMapWidget(lang=current_lang)
        self.map_view.node_selected.connect(self._on_map_node_selected)
        self.view_stack.addWidget(self.map_view)
        
        main_content_layout.addWidget(self.view_stack)
        study_layout.addWidget(self.main_content_area)

        self.main_tabs.addTab(self.study_page, "📖 Ngữ pháp")

        # --- TAB 2: Luyện tập (GrammarPracticeTab) ---
        self.practice_tab = GrammarPracticeTab()
        self.main_tabs.addTab(self.practice_tab, "🎯 Luyện tập")

        # Main layout for GrammarTab
        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(self.main_tabs)

        # Connect tab change to refresh practice data
        self.main_tabs.currentChanged.connect(self._on_subtab_changed)

    def _create_sidebar(self) -> QWidget:
        # Extracted existing sidebar creation logic
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 8px;
                border-right: none;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        # Header
        header_lbl = QLabel("📖 Ngữ pháp (Grammar)")
        header_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.ACCENT};")
        sidebar_layout.addWidget(header_lbl)
        
        # Lang Toggle
        lang_layout = QHBoxLayout()
        lang_lbl = QLabel("Ngôn ngữ:")
        lang_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-weight: normal;")
        lang_layout.addWidget(lang_lbl)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("🇯🇵 Tiếng Nhật", "jp")
        self.lang_combo.addItem("🇬🇧 Tiếng Anh", "en")
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        self.lang_combo.setStyleSheet(f"""
            QComboBox {{
                background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; border-radius: 4px;
                padding: 4px; border: 1px solid {ThemeColors.BORDER};
            }}
        """)
        lang_layout.addWidget(self.lang_combo)
        sidebar_layout.addLayout(lang_layout)
        
        # Stats Panel
        self.stats_group = QFrame()
        self.stats_group.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        stats_layout = QGridLayout(self.stats_group)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setHorizontalSpacing(10)
        stats_layout.setVerticalSpacing(8)
        
        due_icon = QLabel("🔄")
        self.due_title_lbl = QLabel("Cần ôn")
        self.due_title_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 13px;")
        
        self.due_count_lbl = QLabel("0")
        self.due_count_lbl.setStyleSheet(f"color: {ThemeColors.SUCCESS}; font-size: 18px; font-weight: bold;")
        self.due_count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        stats_layout.addWidget(due_icon, 0, 0)
        stats_layout.addWidget(self.due_title_lbl, 0, 1)
        stats_layout.addWidget(self.due_count_lbl, 0, 2)
        stats_layout.setColumnStretch(1, 1)
        
        sidebar_layout.addWidget(self.stats_group)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.add_cat_btn = QPushButton("➕ Topic mới")
        self.add_cat_btn.setFixedHeight(32)
        self.add_cat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; border-radius: 6px;
                font-weight: bold; padding: 0 10px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.SECONDARY}; }}
        """)
        self.add_cat_btn.clicked.connect(self._create_category_dialog)
        btn_layout.addWidget(self.add_cat_btn)
        sidebar_layout.addLayout(btn_layout)

        # Study Now Large Button (Sidebar)
        self.study_now_btn_large = QPushButton("🚀 Bắt đầu học!")
        self.study_now_btn_large.setFixedHeight(45)
        self.study_now_btn_large.setCursor(Qt.PointingHandCursor)
        self.study_now_btn_large.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SUCCESS}; color: white;
                font-size: 15px; font-weight: bold; border-radius: 10px;
            }}
            QPushButton:hover {{ background-color: #27ae60; }}
        """)
        self.study_now_btn_large.clicked.connect(self._start_session)
        sidebar_layout.addWidget(self.study_now_btn_large)

        # Level/Category List
        sidebar_layout.addWidget(QLabel("📚 Trình độ / Chủ đề:"))
        self.level_list = QListWidget()
        self.level_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent; border: none; color: {ThemeColors.TEXT_SECONDARY};
            }}
            QListWidget::item {{
                padding: 8px 12px; border-radius: 6px; margin-bottom: 2px;
            }}
            QListWidget::item:hover {{ background-color: {ThemeColors.BG_TERTIARY}; }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.PRIMARY}; font-weight: bold;
            }}
        """)
        self.level_list.itemClicked.connect(self._on_level_selected)
        sidebar_layout.addWidget(self.level_list, 1)
        
        return sidebar

    def _create_smart_dashboard(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 10, 20, 20)
        
        # Welcome
        wl = QLabel("🧩 Chào mừng đến với xưởng lắp ghép câu!")
        wl.setStyleSheet(f"font-size: 16px; color: {ThemeColors.TEXT_SECONDARY}; font-style: italic;")
        wl.setAlignment(Qt.AlignCenter)
        layout.addWidget(wl)
        layout.addSpacing(20)
        
        # Cards
        card_layout = QHBoxLayout()
        
        # Review Card
        r_card = QFrame()
        r_card.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SECONDARY}; border-radius: 12px; border: 1px solid {ThemeColors.BORDER};
            }}
            QFrame:hover {{
                border: 2px solid {ThemeColors.ACCENT};
                margin-top: -5px;
                margin-bottom: 5px;
                background: {ThemeColors.BG_TERTIARY};
            }}
        """)
        r_l = QVBoxLayout(r_card)
        r_icon = QLabel("🧠")
        r_icon.setStyleSheet("font-size: 30px;")
        r_icon.setAlignment(Qt.AlignCenter)
        r_btn = QPushButton("Ôn tập mẫu câu")
        r_btn.setStyleSheet(f"background: {ThemeColors.ACCENT}; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        r_btn.clicked.connect(self._start_smart_review)
        
        r_l.addWidget(r_icon)
        r_l.addWidget(QLabel("Củng cố trí nhớ", alignment=Qt.AlignCenter))
        r_l.addWidget(r_btn)
        card_layout.addWidget(r_card)

        # New Card
        n_card = QFrame()
        n_card.setStyleSheet(f"""
            QFrame {{
                background: {ThemeColors.BG_SECONDARY}; border-radius: 12px; border: 1px solid {ThemeColors.BORDER};
            }}
            QFrame:hover {{
                border: 2px solid {ThemeColors.PRIMARY};
                margin-top: -5px;
                margin-bottom: 5px;
                background: {ThemeColors.BG_TERTIARY};
            }}
        """)
        n_l = QVBoxLayout(n_card)
        n_icon = QLabel("🧩")
        n_icon.setStyleSheet("font-size: 30px;")
        n_icon.setAlignment(Qt.AlignCenter)
        n_btn = QPushButton("Ghép 5 câu mới")
        n_btn.setStyleSheet(f"background: {ThemeColors.PRIMARY}; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        n_btn.clicked.connect(self._start_smart_learn)
        
        n_l.addWidget(n_icon)
        n_l.addWidget(QLabel("Học mẫu mới", alignment=Qt.AlignCenter))
        n_l.addWidget(n_btn)
        card_layout.addWidget(n_card)
        
        layout.addLayout(card_layout)
        
        # -- Puzzle Progress (Levels) --
        layout.addSpacing(20)
        map_header = QLabel("🧩 Tiến độ lắp ghép")
        map_header.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY}; border-bottom: 2px solid {ThemeColors.BORDER}; padding-bottom: 5px;")
        layout.addWidget(map_header)
        
        self.puzzle_container = QWidget()
        self.puzzle_layout = QHBoxLayout(self.puzzle_container)
        self.puzzle_layout.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.puzzle_container)
        
        layout.addStretch()
        
        self._update_dashboard_puzzle()
        
        return widget

    def _update_dashboard_puzzle(self):
        """Draw 'Puzzle' progress."""
        # Clear existing
        item = self.puzzle_layout.takeAt(0)
        while item:
            w = item.widget()
            if w: w.deleteLater()
            item = self.puzzle_layout.takeAt(0)
            
        # Draw puzzle clusters for N5, N4, N3, N2, N1
        levels = ["N5", "N4", "N3", "N2", "N1"]
        lang = self._get_current_lang()
        if lang != 'jp':
             levels = ["A1", "A2", "B1", "B2", "C1"]
        
        with get_session() as session:
             for level in levels:
                 # Count items
                 total_q = select(func.count()).where(GrammarTopic.lang == lang, GrammarTopic.level == level)
                 total = session.exec(total_q).one()
                 
                 mastered_q = select(func.count()).where(GrammarTopic.lang == lang, GrammarTopic.level == level, GrammarTopic.mastery_status == GrammarMasteryStatus.MASTERED.value)
                 mastered = session.exec(mastered_q).one()
                 
                 if total == 0: total = 1
                 percent = mastered / total
                 
                 # Draw "Puzzle Box"
                 box = QFrame()
                 box.setFixedSize(100, 100)
                 box.setStyleSheet(f"background: {ThemeColors.BG_TERTIARY}; border-radius: 8px; border: 1px solid {ThemeColors.BORDER};")
                 
                 b_layout = QVBoxLayout(box)
                 b_layout.setAlignment(Qt.AlignCenter)
                 
                 # Icon/Shape
                 shape = QLabel("🧩")
                 shape.setStyleSheet("font-size: 30px;")
                 shape.setAlignment(Qt.AlignCenter)
                 
                 # Progress Ring/Bar (Simplified as label for now)
                 prog_lbl = QLabel(f"{int(percent*100)}%")
                 prog_lbl.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-weight: bold; font-size: 16px;")
                 prog_lbl.setAlignment(Qt.AlignCenter)
                 
                 lvl_lbl = QLabel(level)
                 lvl_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 12px;")
                 lvl_lbl.setAlignment(Qt.AlignCenter)
                 
                 b_layout.addWidget(shape)
                 b_layout.addWidget(prog_lbl)
                 b_layout.addWidget(lvl_lbl)
                 
                 self.puzzle_layout.addWidget(box)

    def _on_subtab_changed(self, index):
        if index == 1:  # Luyện tập tab
            if hasattr(self, 'practice_tab'):
                self.practice_tab._load_items()
        
    def _create_list_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm cấu trúc...")
        self.search_input.textChanged.connect(self._filter_list)
        toolbar.addWidget(self.search_input)
        
        # Add New Grammar Button
        self.add_grammar_btn = QPushButton(" Thêm")
        self.add_grammar_btn.setToolTip("Thêm cấu trúc ngữ pháp mới")
        self.add_grammar_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.add_grammar_btn.clicked.connect(self._show_add_grammar_dialog)
        toolbar.addWidget(self.add_grammar_btn)
        
        # Import CSV Button
        self.import_csv_btn = QPushButton(" Import")
        self.import_csv_btn.setToolTip("Nhập ngữ pháp từ tệp CSV/Excel")
        self.import_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.import_csv_btn.clicked.connect(self._show_import_csv_dialog)
        toolbar.addWidget(self.import_csv_btn)

        # Study Button
        self.study_btn = QPushButton(" Học")
        self.study_btn.setToolTip("Bắt đầu phiên học Flashcard")
        self.study_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; font-weight: bold; 
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.study_btn.clicked.connect(self._start_session)
        toolbar.addWidget(self.study_btn)

        # Batch Lookup Button
        self.batch_lookup_btn = QPushButton(" Tra loạt")
        self.batch_lookup_btn.setToolTip("Tra cứu hàng loạt cấu trúc ngữ pháp")
        self.batch_lookup_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.batch_lookup_btn.clicked.connect(self._batch_lookup)
        toolbar.addWidget(self.batch_lookup_btn)
        
        # AI Batch Enrich Button
        self.ai_batch_btn = QPushButton(" AI Làm giàu")
        self.ai_batch_btn.setToolTip("Dùng AI làm giàu hàng loạt cấu trúc (nghĩa, ví dụ, lỗi sai)")
        self.ai_batch_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #DB2777); 
                color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6D28D9, stop:1 #BE185D);
            }
        """)
        self.ai_batch_btn.clicked.connect(self._batch_enrich_grammar)
        toolbar.addWidget(self.ai_batch_btn)
        
        # Reset AI Button
        self.reset_ai_btn = QPushButton("🔄 Reset AI")
        self.reset_ai_btn.setToolTip("Reset trạng thái làm giàu AI cho danh sách này")
        self.reset_ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.reset_ai_btn.clicked.connect(self._reset_all_visible_ai)
        toolbar.addWidget(self.reset_ai_btn)
        
        layout.addLayout(toolbar)
        
        # ===== FILTER BAR (Curriculum/Level) =====
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)
        
        # Source/Curriculum Filter
        filter_bar.addWidget(QLabel("📖 Giáo trình:"))
        self.source_filter_combo = QComboBox()
        self.source_filter_combo.setMinimumWidth(150)
        self.source_filter_combo.addItem("Tất cả", None)
        self.source_filter_combo.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.source_filter_combo)
        
        # Level Filter
        filter_bar.addWidget(QLabel("📊 Cấp độ:"))
        self.level_filter_combo = QComboBox()
        self.level_filter_combo.setMinimumWidth(100)
        self.level_filter_combo.addItem("Tất cả", None)
        self.level_filter_combo.currentIndexChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.level_filter_combo)
        
        # Status Filter
        filter_bar.addWidget(QLabel("🎯 Trạng thái:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.setMinimumWidth(120)
        self.status_filter_combo.addItem("Tất cả", None)
        self.status_filter_combo.addItem("🆕 Mới", "new")
        self.status_filter_combo.addItem("📖 Đang học", "learning")
        self.status_filter_combo.addItem("❗ Khó", "hard")
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
        
        # Left: Grammar List
        self.grammar_list = QListWidget()
        self.grammar_list.setAlternatingRowColors(True)
        self.grammar_list.itemClicked.connect(self._on_grammar_selected)
        self.grammar_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grammar_list.customContextMenuRequested.connect(self._show_grammar_context_menu)
        self.list_splitter.addWidget(self.grammar_list)
        
        # Right: Detail Panel (Wrapped in Scroll Area)
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setFrameShape(QFrame.NoFrame)
        self.grammar_detail_panel = self._create_grammar_detail_panel()
        self.detail_scroll.setWidget(self.grammar_detail_panel)
        self.list_splitter.addWidget(self.detail_scroll)
        
        self.list_splitter.setSizes([400, 600])
        self.list_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.list_splitter, 1)
        
        # Status Bar (Footer)
        footer = QFrame()
        footer.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #ddd; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 5, 15, 5)
        
        self.grammar_count_lbl = QLabel("Tổng số cấu trúc: 0")
        self.grammar_count_lbl.setStyleSheet("color: #666; font-size: 11px; font-weight: bold;")
        footer_layout.addWidget(self.grammar_count_lbl)
        footer_layout.addStretch()
        
        layout.addWidget(footer)
        
        return widget
    
    def _create_grammar_detail_panel(self) -> QFrame:
        """Create the grammar detail panel."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 8px;
            }}
            QLabel#DetailPattern {{
                font-size: 26px;
                font-weight: bold;
                color: {ThemeColors.PRIMARY};
            }}
            QLabel#DetailTitle {{
                font-size: 18px;
                color: {ThemeColors.TEXT_SECONDARY};
            }}
            QLabel#DetailMeaning {{
                font-size: 18px;
                color: {ThemeColors.SUCCESS};
                font-weight: bold;
            }}
            QLabel#SectionHeader {{
                font-size: 14px;
                font-weight: bold;
                color: {ThemeColors.TEXT_PRIMARY};
                margin-top: 8px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Pattern
        self.grammar_pattern_lbl = QLabel("Chọn một cấu trúc để xem chi tiết")
        self.grammar_pattern_lbl.setObjectName("DetailPattern")
        self.grammar_pattern_lbl.setAlignment(Qt.AlignCenter)
        self.grammar_pattern_lbl.setWordWrap(True)
        layout.addWidget(self.grammar_pattern_lbl)
        
        # Title
        self.grammar_title_lbl = QLabel("")
        self.grammar_title_lbl.setObjectName("DetailTitle")
        self.grammar_title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.grammar_title_lbl)
        
        # Meaning
        meaning_header = QLabel("📖 Ý nghĩa:")
        meaning_header.setObjectName("SectionHeader")
        layout.addWidget(meaning_header)
        
        self.grammar_meaning_lbl = QLabel("")
        self.grammar_meaning_lbl.setObjectName("DetailMeaning")
        self.grammar_meaning_lbl.setWordWrap(True)
        layout.addWidget(self.grammar_meaning_lbl)
        
        # Usage
        usage_header = QLabel("📝 Cách dùng:")
        usage_header.setObjectName("SectionHeader")
        layout.addWidget(usage_header)
        
        self.grammar_usage_txt = QTextEdit()
        self.grammar_usage_txt.setReadOnly(True)
        self.grammar_usage_txt.setMinimumHeight(250)
        self.grammar_usage_txt.setStyleSheet(f"background: {ThemeColors.BG_PRIMARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 4px; padding: 10px; color: {ThemeColors.TEXT_PRIMARY};")
        layout.addWidget(self.grammar_usage_txt)
        
        # Common Mistakes
        mistakes_header = QLabel("⚠️ Lỗi thường gặp:")
        mistakes_header.setObjectName("SectionHeader")
        layout.addWidget(mistakes_header)
        
        self.grammar_mistakes_txt = QTextEdit()
        self.grammar_mistakes_txt.setReadOnly(True)
        self.grammar_mistakes_txt.setMinimumHeight(150)
        self.grammar_mistakes_txt.setStyleSheet(f"background: {ThemeColors.BG_PRIMARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 4px; padding: 10px; color: {ThemeColors.TEXT_PRIMARY};")
        layout.addWidget(self.grammar_mistakes_txt)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        self.grammar_edit_btn = QPushButton("✏️ Sửa")
        self.grammar_edit_btn.clicked.connect(self._edit_selected_grammar)
        self.grammar_delete_btn = QPushButton("🗑️ Xóa")
        self.grammar_delete_btn.setStyleSheet("color: #d32f2f;")
        self.grammar_delete_btn.clicked.connect(self._delete_selected_grammar)
        action_layout.addWidget(self.grammar_edit_btn)
        action_layout.addWidget(self.grammar_delete_btn)
        layout.addLayout(action_layout)
        
        # ===== Grammar Lookup Sources Section =====
        lookup_header = QLabel("🔍 Tra thêm ngữ pháp:")
        lookup_header.setObjectName("SectionHeader")
        layout.addWidget(lookup_header)
        
        lookup_layout = QHBoxLayout()
        
        # Bunpro / JLPT Sensei
        self.grammar_bunpro_btn = QPushButton("📚 Bunpro")
        self.grammar_bunpro_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        self.grammar_bunpro_btn.clicked.connect(lambda: self._open_grammar_url("bunpro"))
        lookup_layout.addWidget(self.grammar_bunpro_btn)
        
        # Takoboto Grammar
        self.grammar_takoboto_btn = QPushButton("🐙 Takoboto")
        self.grammar_takoboto_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        self.grammar_takoboto_btn.clicked.connect(lambda: self._open_grammar_url("takoboto"))
        lookup_layout.addWidget(self.grammar_takoboto_btn)
        
        # Google Search
        self.grammar_google_btn = QPushButton("🌐 Google")
        self.grammar_google_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 5px;")
        self.grammar_google_btn.clicked.connect(lambda: self._open_grammar_url("google"))
        lookup_layout.addWidget(self.grammar_google_btn)
        
        # ===== AI Enrichment Section =====
        ai_layout = QHBoxLayout()
        self.grammar_ai_enrich_btn = QPushButton("✨ AI Làm giàu")
        self.grammar_ai_enrich_btn.setToolTip("Dùng AI cải thiện ý nghĩa và thêm hướng dẫn chi tiết")
        self.grammar_ai_enrich_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #DB2777);
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6D28D9, stop:1 #BE185D);
            }
            QPushButton:disabled {
                background: #ccc;
                color: #888;
            }
        """)
        self.grammar_ai_enrich_btn.clicked.connect(self._enrich_selected_grammar)
        ai_layout.addWidget(self.grammar_ai_enrich_btn)
        
        layout.addLayout(ai_layout)
        
        layout.addStretch()
        
        return panel
    
    def _open_grammar_url(self, source: str):
        """Open grammar resource URL for the selected grammar."""
        if not hasattr(self, '_selected_grammar_data') or not self._selected_grammar_data:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một ngữ pháp trước")
            return
        
        data = self._selected_grammar_data
        pattern = data.get("pattern") if isinstance(data, dict) else getattr(data, "pattern", "")
        title = data.get("title") if isinstance(data, dict) else getattr(data, "title", "")
        
        query = title or pattern
        if not query:
            return
        
        encoded = quote(query)
        
        urls = {
            "bunpro": f"https://bunpro.jp/grammar_points?search={encoded}",
            "takoboto": f"https://takoboto.jp/?q={encoded}",
            "google": f"https://www.google.com/search?q={encoded}+grammar+Japanese+JLPT",
            "jlptsensei": f"https://jlptsensei.com/?s={encoded}",
        }
        
        url = urls.get(source)
        if url:
            QDesktopServices.openUrl(QUrl(url))
    
    def _load_filter_options(self):
        """Load filter options from database for Source and Level combos."""
        lang = self._get_current_lang()
        from frontend.models.grammar import JAPANESE_GRAMMAR_SOURCES, ENGLISH_GRAMMAR_SOURCES, JAPANESE_GRAMMAR_LEVELS, ENGLISH_GRAMMAR_LEVELS
        
        async def fetch_options():
            with get_session() as session:
                sources = self.fetcher_service.get_distinct_sources(lang, session)
                levels = self.fetcher_service.get_distinct_levels(lang, session)
                return {"sources": sources, "levels": levels}
        
        def populate(data):
            if not data: return
            
            # --- Source Filter ---
            self.source_filter_combo.blockSignals(True)
            curr_source = self.source_filter_combo.currentData()
            self.source_filter_combo.clear()
            self.source_filter_combo.addItem("Tất cả", None)
            
            # Use only sources from DB as requested
            all_sources = sorted([s for s in data["sources"] if s and s.strip()])
            
            for s in all_sources:
                self.source_filter_combo.addItem(s, s)
            
            idx = self.source_filter_combo.findData(curr_source)
            if idx >= 0: 
                self.source_filter_combo.setCurrentIndex(idx)
            self.source_filter_combo.blockSignals(False)
            
            # --- Level Filter ---
            self.level_filter_combo.blockSignals(True)
            curr_level = self.level_filter_combo.currentData()
            self.level_filter_combo.clear()
            self.level_filter_combo.addItem("Tất cả", None)
            
            # Use only levels from DB as requested
            all_levels = sorted([l for l in data["levels"] if l and l.strip()])
            
            for l in all_levels:
                self.level_filter_combo.addItem(l, l)
            
            idx = self.level_filter_combo.findData(curr_level)
            if idx >= 0: 
                self.level_filter_combo.setCurrentIndex(idx)
            self.level_filter_combo.blockSignals(False)
            
        run_async(fetch_options, populate)

    def _on_grammar_selected(self, item: QListWidgetItem):
        """Display grammar details in the detail panel."""
        data = item.data(Qt.UserRole)
        if not data:
            return
        
        self._selected_grammar_data = data
        self._display_grammar_details(data)

    def _display_grammar_details(self, data: Any):
        """Update the detail panel with grammar data."""
        if not data:
            return

        # Handle both dict and object
        if isinstance(data, dict):
            pattern = data.get("pattern", "")
            title = data.get("title", "")
            desc = data.get("description", "")
            usage = data.get("usage_notes", "")
            mistakes = data.get("common_mistakes", "")
        else:
            pattern = getattr(data, "pattern", "")
            title = getattr(data, "title", "")
            desc = getattr(data, "description", "")
            usage = getattr(data, "usage_notes", "")
            mistakes = getattr(data, "common_mistakes", "")
        
        self.grammar_pattern_lbl.setText(title or pattern)
        self.grammar_title_lbl.setText(pattern if title else "")
        
        # Render markdown for description
        desc_html = markdown.markdown(desc or "") if desc else "<i>Chưa có mô tả</i>"
        self.grammar_meaning_lbl.setText(desc_html)
        
        usage_html = markdown.markdown(usage or "") if usage else "<i>Chưa có hướng dẫn</i>"
        self.grammar_usage_txt.setHtml(usage_html)
        self.grammar_mistakes_txt.setText(mistakes or "Chưa có thông tin")

    
    def _show_grammar_context_menu(self, pos):
        """Show context menu for grammar list."""
        item = self.grammar_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Sửa")
        delete_action = menu.addAction("🗑️ Xóa")
        
        action = menu.exec_(self.grammar_list.mapToGlobal(pos))
        if action == edit_action:
            self._edit_grammar_item(item)
        elif action == delete_action:
            self._delete_grammar_item(item)
    
    def _edit_selected_grammar(self):
        """Edit the currently selected grammar."""
        current_item = self.grammar_list.currentItem()
        if current_item:
            self._edit_grammar_item(current_item)
    
    def _delete_selected_grammar(self):
        """Delete the currently selected grammar."""
        current_item = self.grammar_list.currentItem()
        if current_item:
            self._delete_grammar_item(current_item)
    
    def _edit_grammar_item(self, item: QListWidgetItem):
        """Edit a grammar point with dialog."""
        from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        data = item.data(Qt.UserRole)
        if not data:
            return
        
        # Extract current values
        if isinstance(data, dict):
            grammar_id = data.get("id")
            title = data.get("title", "")
            pattern = data.get("pattern", "")
            desc = data.get("description", "")
            usage = data.get("usage_notes", "")
            mistakes = data.get("common_mistakes", "")
            level = data.get("level", "N5")
        else:
            grammar_id = getattr(data, "id", None)
            title = getattr(data, "title", "")
            pattern = getattr(data, "pattern", "")
            desc = getattr(data, "description", "")
            usage = getattr(data, "usage_notes", "")
            mistakes = getattr(data, "common_mistakes", "")
            level = getattr(data, "level", "N5")
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Sửa ngữ pháp: {title}")
        dialog.setMinimumWidth(450)
        
        layout = QFormLayout(dialog)
        
        title_input = QLineEdit(title)
        pattern_input = QLineEdit(pattern or "")
        desc_input = QTextEdit()
        desc_input.setText(desc or "")
        desc_input.setMaximumHeight(80)
        usage_input = QTextEdit()
        usage_input.setText(usage or "")
        usage_input.setMaximumHeight(80)
        mistakes_input = QLineEdit(mistakes or "")
        level_combo = QComboBox()
        level_combo.addItems(["N5", "N4", "N3", "N2", "N1"])
        idx = level_combo.findText(level or "N5")
        if idx >= 0:
            level_combo.setCurrentIndex(idx)
        
        layout.addRow("Tiêu đề:", title_input)
        layout.addRow("Pattern:", pattern_input)
        layout.addRow("Cấp độ:", level_combo)
        layout.addRow("Ý nghĩa:", desc_input)
        layout.addRow("Cách dùng:", usage_input)
        layout.addRow("Lỗi thường gặp:", mistakes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            lang = self._get_current_lang()
            updated_data = {
                "title": title_input.text().strip(),
                "pattern": pattern_input.text().strip(),
                "description": desc_input.toPlainText().strip(),
                "usage_notes": usage_input.toPlainText().strip(),
                "common_mistakes": mistakes_input.text().strip(),
                "level": level_combo.currentText(),
            }
            
            if updated_data["title"]:
                async def update():
                    with get_session() as session:
                        return self.fetcher_service.update_grammar(grammar_id, updated_data, session)
                
                def on_updated(result):
                    if result and result.get("success"):
                        toast_success(f"Đã cập nhật ngữ pháp '{updated_data['title']}'")
                        self._refresh_list()
                    else:
                        toast_error(result.get("error", "Không thể cập nhật ngữ pháp") if result else "Lỗi không xác định")
                
                run_async(update, on_updated)
            else:
                toast_warning("Vui lòng nhập tiêu đề")
    
    def _delete_grammar_item(self, item: QListWidgetItem):
        """Delete a grammar point."""
        data = item.data(Qt.UserRole)
        if not data:
            return
        
        grammar_id = data.get("id") if isinstance(data, dict) else getattr(data, "id", None)
        title = data.get("title") if isinstance(data, dict) else getattr(data, "title", "")
        
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc muốn xóa ngữ pháp '{title}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes and grammar_id:
            async def delete():
                with get_session() as session:
                    return self.fetcher_service.delete_grammar(grammar_id, session)
            
            def on_deleted(result):
                if result and result.get("success"):
                    self._refresh_list()
                else:
                    QMessageBox.warning(self, "Lỗi", "Không thể xóa ngữ pháp này")
            
            run_async(delete, on_deleted)
    
    def _show_add_grammar_dialog(self):
        """Show dialog to add new grammar."""
        from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Thêm ngữ pháp mới")
        dialog.setMinimumWidth(450)
        
        layout = QFormLayout(dialog)
        
        lang = self._get_current_lang()
        
        title_input = QLineEdit()
        pattern_input = QLineEdit()
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(80)
        usage_input = QTextEdit()
        usage_input.setMaximumHeight(80)
        mistakes_input = QLineEdit()
        
        # Level dropdown
        level_combo = QComboBox()
        from frontend.models.grammar import JAPANESE_GRAMMAR_LEVELS, ENGLISH_GRAMMAR_LEVELS
        level_combo.addItems(JAPANESE_GRAMMAR_LEVELS if lang == "jp" else ENGLISH_GRAMMAR_LEVELS)
        
        # Source/Curriculum dropdown
        source_combo = QComboBox()
        source_combo.setEditable(True)  # Allow custom entry
        from frontend.models.grammar import JAPANESE_GRAMMAR_SOURCES, ENGLISH_GRAMMAR_SOURCES
        source_combo.addItem("(Không chọn)")
        source_combo.addItems(JAPANESE_GRAMMAR_SOURCES if lang == "jp" else ENGLISH_GRAMMAR_SOURCES)
        
        layout.addRow("Tiêu đề:", title_input)
        layout.addRow("Pattern:", pattern_input)
        layout.addRow("📊 Cấp độ:", level_combo)
        layout.addRow("📖 Giáo trình:", source_combo)
        layout.addRow("Ý nghĩa:", desc_input)
        layout.addRow("Cách dùng:", usage_input)
        layout.addRow("Lỗi thường gặp:", mistakes_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            # Get source value
            source_value = source_combo.currentText().strip()
            if source_value == "(Không chọn)":
                source_value = ""
            
            new_grammar = {
                "title": title_input.text().strip(),
                "pattern": pattern_input.text().strip(),
                "description": desc_input.toPlainText().strip(),
                "usage_notes": usage_input.toPlainText().strip(),
                "common_mistakes": mistakes_input.text().strip(),
                "level": level_combo.currentText(),
                "source_material": source_value,
            }
            
            if new_grammar["title"]:
                async def add():
                    with get_session() as session:
                        return self.fetcher_service.add_grammar(new_grammar, lang, session)
                
                def on_added(result):
                    if result and result.get("success"):
                        toast_success(f"Đã thêm ngữ pháp '{new_grammar['title']}'")
                        self._refresh_list()
                    else:
                        toast_error(result.get("error", "Không thể thêm ngữ pháp"))
                
                run_async(add, on_added)
            else:
                toast_warning("Vui lòng nhập tiêu đề")
    
    def _show_import_csv_dialog(self):
        """Show dialog to import grammar from CSV file."""
        from frontend.ui.widgets.import_grammar_csv_dialog import ImportGrammarCSVDialog
        
        lang = self._get_current_lang()
        
        # Get categories for dialog
        async def fetch_cats():
            with get_session() as session:
                return self.fetcher_service.list_categories(lang, session)
        
        def show_dialog(categories):
            cats_list = [{"id": c.id, "name": c.name, "icon": c.icon or "📁"} for c in categories] if categories else []
            
            dialog = ImportGrammarCSVDialog(
                parent=self,
                lang=lang,
                categories=cats_list
            )
            
            # Refresh list when import completes
            dialog.import_completed.connect(lambda result: self._refresh_list())
            
            dialog.exec_()
        
        run_async(fetch_cats, show_dialog)


    def _create_study_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Top Bar
        top_bar = QHBoxLayout()
        exit_btn = QPushButton(" 🔙 Thoát ")
        exit_btn.setFixedHeight(35)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5; border: 1px solid #ddd;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #eeeeee; }
        """)
        exit_btn.clicked.connect(self._exit_session)
        
        self.progress_lbl = QLabel("0/0")
        self.progress_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #666;")
        
        top_bar.addWidget(exit_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.progress_lbl)
        layout.addLayout(top_bar)
        
        # Flashcard
        self.flashcard = GrammarFlashcardView()
        layout.addWidget(self.flashcard, 1)
        
        # Controls Area
        self.controls_area = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_area)
        self.controls_layout.setContentsMargins(0, 10, 0, 0)
        
        # Show Answer Button
        self.show_answer_btn = QPushButton(" HIỆN ĐÁP ÁN (Space) ")
        self.show_answer_btn.setShortcut("Space")
        self.show_answer_btn.setFixedHeight(55)
        self.show_answer_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white;
                font-weight: bold; font-size: 18px;
                border-radius: 10px; border: none;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.show_answer_btn.clicked.connect(self._on_show_answer)
        self.controls_layout.addWidget(self.show_answer_btn)
        
        # Rating Buttons Container
        self.rating_container = QWidget()
        rating_layout = QHBoxLayout(self.rating_container)
        rating_layout.setContentsMargins(0, 0, 0, 0)
        rating_layout.setSpacing(15)
        
        button_style = """
            QPushButton {{
                background-color: {color}; color: white;
                font-weight: bold; font-size: 15px;
                border-radius: 10px; padding: 15px; border: none;
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
        """
        
        # Again (1)
        btn_again = QPushButton("LẶP LẠI\n(1)")
        btn_again.setStyleSheet(button_style.format(color="#f44336", hover_color="#d32f2f"))
        btn_again.setToolTip("Chưa nhớ → Sẽ hỏi lại ngay lập tức")
        btn_again.clicked.connect(lambda: self._submit_review(1))
        
        # Hard (2)
        btn_hard = QPushButton("KHÓ\n(2)")
        btn_hard.setStyleSheet(button_style.format(color="#FF9800", hover_color="#F57C00"))
        btn_hard.setToolTip("Khó nhớ → Sẽ hỏi lại sớm hơn bình thường")
        btn_hard.clicked.connect(lambda: self._submit_review(2))
        
        # Good (3)
        btn_good = QPushButton("TỐT\n(3)")
        btn_good.setStyleSheet(button_style.format(color="#4CAF50", hover_color="#388E3C"))
        btn_good.setToolTip("Nhớ được → Sẽ hỏi lại sau vài ngày")
        btn_good.clicked.connect(lambda: self._submit_review(3))
        
        # Easy (4)
        btn_easy = QPushButton("DỄ\n(4)")
        btn_easy.setStyleSheet(button_style.format(color="#00BCD4", hover_color="#0097A7"))
        btn_easy.setToolTip("Dễ quá → Sẽ hỏi lại sau lâu hơn (1-2 tuần)")
        btn_easy.clicked.connect(lambda: self._submit_review(4))
        
        rating_layout.addWidget(btn_again)
        rating_layout.addWidget(btn_hard)
        rating_layout.addWidget(btn_good)
        rating_layout.addWidget(btn_easy)
        
        self.controls_layout.addWidget(self.rating_container)
        self.rating_container.hide()
        
        # ===== COMPLETION BUTTON =====
        self.completion_container = QFrame()
        self.completion_container.setStyleSheet("""
            QFrame { background-color: transparent; }
        """)
        completion_layout = QHBoxLayout(self.completion_container)
        completion_layout.setContentsMargins(0, 10, 0, 0)
        
        self.btn_completed = QPushButton("✅ Đã hiểu! (Mở khóa node tiếp theo)")
        self.btn_completed.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1B5E20;
            }
        """)
        self.btn_completed.setToolTip("Đánh dấu hoàn thành và mở khóa các node tiếp theo trên bản đồ")
        self.btn_completed.clicked.connect(self._on_mark_completed)
        completion_layout.addWidget(self.btn_completed)
        
        # AI Enrich Button (for map view)
        self.btn_ai_enrich_study = QPushButton("✨ AI Làm giàu")
        self.btn_ai_enrich_study.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #DB2777);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6D28D9, stop:1 #BE185D);
            }
            QPushButton:disabled {
                background: #ccc;
                color: #888;
            }
        """)
        self.btn_ai_enrich_study.setToolTip("Dùng AI làm giàu ngữ pháp này (thêm giải thích, ví dụ, lỗi sai)")
        self.btn_ai_enrich_study.clicked.connect(self._enrich_selected_grammar)
        completion_layout.addWidget(self.btn_ai_enrich_study)
        
        self.controls_layout.addWidget(self.completion_container)
        self.completion_container.hide()


        
        layout.addWidget(self.controls_area)
        
        return widget

    # ============ LOGIC ============
    
    def _get_current_lang(self):
        return self.lang_combo.currentData() or "jp"
        
    def _on_lang_changed(self):
        self._load_levels()
        self._load_filter_options()
        # Update Learning Map filter when language changes
        new_lang = self.lang_combo.currentData() or "en"
        self.map_view.set_language(new_lang)
    
    def _on_map_node_selected(self, grammar_id: int):
        """Handle grammar node click from Learning Map.
        
        Loads the grammar data and opens the flashcard view.
        """
        print(f"[GrammarTab] _on_map_node_selected called with grammar_id: {grammar_id}")
        from sqlmodel import select
        from frontend.core.database import get_session
        from frontend.models.grammar import GrammarTopic
        
        # Synchronous fetch (SQLite is fast enough)
        try:
            with get_session() as session:
                stmt = select(GrammarTopic).where(GrammarTopic.id == grammar_id)
                grammar = session.exec(stmt).first()
                
                if grammar:
                    # Force load all attributes before detaching
                    _ = grammar.title  # Access to load
                    _ = grammar.pattern
                    _ = grammar.description  # NOT 'explanation'
                    _ = grammar.level
                    _ = grammar.lang
                    
                    # Detach from session to use outside context
                    session.expunge(grammar)
            
            if grammar:
                # Store selected grammar
                self._selected_grammar_data = grammar
                
                # Create a study session queue with just this item
                self.srs_session_queue = [grammar]
                self.current_review_index = 0
                
                # Update flashcard content
                self.flashcard.set_grammar(grammar)
                
                # Switch to study view
                self.view_stack.setCurrentIndex(2)
                
                # Show completion container (with AI Enrich button) and hide SRS rating
                self.show_answer_btn.hide()
                self.rating_container.hide()
                self.completion_container.show()
                
                # Update toggle buttons
                self.btn_view_smart.setChecked(False)
                self.btn_view_dict.setChecked(False)
                self.btn_view_map.setChecked(False)
                
                print(f"[GrammarTab] Loaded grammar '{grammar.title}', switched to study view")
            else:
                print(f"[GrammarTab] Grammar ID {grammar_id} not found!")
        except Exception as e:
            print(f"[GrammarTab] Error loading grammar: {e}")
            import traceback
            traceback.print_exc()


    def _create_category_dialog(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Tạo chủ đề", "Tên chủ đề ngữ pháp:")
        if ok and name:
            lang = self._get_current_lang()
            async def create():
                with get_session() as session:
                    return self.fetcher_service.create_category(name, lang)
            
            def done(res):
                if res.get("success"):
                    self._load_levels()
                else:
                    QMessageBox.warning(self, "Lỗi", "Không thể tạo chủ đề")
            
            run_async(create, done)
    
    def _load_levels(self):
        self.level_list.clear() # Reset
        lang = self._get_current_lang()
        
        # 1. All
        all_item = QListWidgetItem("Tất cả")
        all_item.setData(Qt.UserRole, "ALL")
        self.level_list.addItem(all_item)
        
        # 2. Hardcoded Levels (JP only commonly)
        if lang == "jp":
            levels = ["N5", "N4", "N3", "N2", "N1"]
            self.level_list.addItem(QListWidgetItem("--- JLPT ---"))
            for level in levels:
                item = QListWidgetItem(level)
                item.setData(Qt.UserRole, {"type": "level", "value": level})
                self.level_list.addItem(item)
        
        # 3. Custom Categories
        async def fetch_cats():
            with get_session() as session:
                cats = self.fetcher_service.list_categories(lang, session)
                # Convert to plain data to avoid DetachedInstanceError in callback
                return [{"id": c.id, "name": c.name} for c in cats]
                
        def update_cats(cats_data):
            if cats_data:
                self.level_list.addItem(QListWidgetItem("--- Custom ---"))
                for c in cats_data:
                    item = QListWidgetItem(c["name"])
                    item.setData(Qt.UserRole, {"type": "category", "value": c["id"]})
                    self.level_list.addItem(item)
            
            self.level_list.setCurrentRow(0)
            self._on_level_selected(self.level_list.item(0))
            
        run_async(fetch_cats, update_cats)

    def _on_level_selected(self, item):
        if not item: return
        self.current_display_filter = item.data(Qt.UserRole)
        self.current_filter_label = item.text()
        self._refresh_list()
        
    def _refresh_list(self):
        """Load grammar list with filters applied."""
        lang = self._get_current_lang()
        
        # 1. Parse filter from sidebar
        category_id = None
        base_level_filter = None
        
        current_data = getattr(self, 'current_display_filter', None)
        if current_data == "ALL":
            pass
        elif isinstance(current_data, dict):
            if current_data.get("type") == "category":
                category_id = current_data.get("value")
            elif current_data.get("type") == "level":
                base_level_filter = current_data.get("value")
        
        # 2. Get filter values from Toolbar UI
        source_filter = self.source_filter_combo.currentData() if hasattr(self, 'source_filter_combo') else None
        level_filter = self.level_filter_combo.currentData() if hasattr(self, 'level_filter_combo') else None
        status_filter = self.status_filter_combo.currentData() if hasattr(self, 'status_filter_combo') else None
        
        # Level filter can come from sidebar OR toolbar dropdown
        final_level = level_filter if level_filter else base_level_filter
        
        # Build mastery_statuses list
        mastery_statuses = [status_filter] if status_filter else None
        
        async def fetch():
            with get_session() as session:
                # 1. Fetch filtered items for the list
                items = self.fetcher_service.list_by_filters(
                    lang=lang,
                    session=session,
                    category_id=category_id,
                    source_material=source_filter,
                    level=final_level,
                    mastery_statuses=mastery_statuses,
                    limit=1000
                )
                
                # 2. Fetch due count for the SPECIFIC filter
                due_items = self.fetcher_service.get_due(
                    lang=lang,
                    session=session,
                    limit=9999,
                    category_id=category_id,
                    source_material=source_filter,
                    level=final_level
                )
                return items, len(due_items)
                
        def update(result):
            items, due_count = result
            self.all_items = items
            self._filter_list()
            
            # Display human-readable name for current filter
            filter_name = getattr(self, 'current_filter_label', "Tất cả")
            if filter_name.startswith("---"):
                 filter_name = "Tất cả"
            
            self.due_title_lbl.setText(f"Cần ôn ({filter_name})")
            self.due_count_lbl.setText(f"{due_count}")
            
            # Highlighting and buttons in top bar
            study_btn_style = """
                QPushButton {{
                    background-color: {color}; color: white; font-weight: bold;
                    border-radius: 4px; padding: 6px 8px; border: none; font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {hover_color}; }}
            """
            sidebar_study_style = """
                QPushButton {{
                    background-color: {color}; color: white;
                    font-size: 15px; font-weight: bold; border-radius: 10px;
                }}
                QPushButton:hover {{ background-color: {hover_color}; }}
            """
            
            if due_count > 0:
                if hasattr(self, 'study_btn'):
                    self.study_btn.setStyleSheet(study_btn_style.format(color="#f44336", hover_color="#d32f2f"))
                if hasattr(self, 'study_now_btn_large'):
                    self.study_now_btn_large.setStyleSheet(sidebar_study_style.format(color="#f44336", hover_color="#d32f2f"))
                    self.study_now_btn_large.setText("🚀 Bắt đầu học!")
            else:
                if hasattr(self, 'study_btn'):
                    self.study_btn.setStyleSheet(study_btn_style.format(color="#2196F3", hover_color="#1976D2"))
                if hasattr(self, 'study_now_btn_large'):
                    self.study_now_btn_large.setStyleSheet(sidebar_study_style.format(color="#2ecc71", hover_color="#27ae60"))
                    self.study_now_btn_large.setText("🚀 Bắt đầu học!")
            
        run_async(fetch, update)

    def _filter_list(self):
        """Filter displayed grammar list by search text."""
        from PySide6.QtGui import QColor
        
        query = self.search_input.text().lower()
        self.grammar_list.clear()
        
        for item in getattr(self, 'all_items', []):
            item_level = item.get('level', '') if isinstance(item, dict) else getattr(item, 'level', '')
            item_title = item.get('title', '') if isinstance(item, dict) else getattr(item, 'title', '')
            item_pattern = item.get('pattern', '') if isinstance(item, dict) else getattr(item, 'pattern', '')
            item_status = item.get('mastery_status', 'new') if isinstance(item, dict) else getattr(item, 'mastery_status', 'new')
            
            # Check Query
            if query and query not in item_title.lower() and query not in (item_pattern or "").lower():
                continue
            
            # Format display text
            status_upper = (item_status or 'new').upper()
            level_str = f" [{item_level}]" if item_level else ""
            display = f"{item_title} - {item_pattern}{level_str} ({status_upper})" if item_pattern else f"{item_title}{level_str} ({status_upper})"
            
            list_item = QListWidgetItem(display)
            list_item.setData(Qt.UserRole, item)
            
            # Color code by status
            if status_upper == "MASTERED":
                list_item.setForeground(QColor("#4CAF50"))
            elif status_upper == "HARD":
                list_item.setForeground(QColor("#F44336"))
            elif status_upper == "LEARNING":
                list_item.setForeground(QColor("#2196F3"))
                
            self.grammar_list.addItem(list_item)
            
        # Update count in footer
        if hasattr(self, 'grammar_count_lbl'):
            self.grammar_count_lbl.setText(f"Tổng số cấu trúc: {self.grammar_list.count()}")
    
    def _apply_filters(self):
        """Apply all filters and reload grammar list."""
        self._refresh_list()
    
    def _clear_filters(self):
        """Clear all filters and reload grammar list."""
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
        self._refresh_list()
    


    # ============ STUDY ============
    
    # ================= SMART LEARNING =================
    
    def _start_smart_review(self):
        """Smart Mode: Review items."""
        lang = self._get_current_lang()
        run_async(
            lambda: self._fetch_smart_items(lang, "review"),
            self._on_smart_fetched
        )
        
    def _start_smart_learn(self):
        """Smart Mode: Learn 5 new items."""
        lang = self._get_current_lang()
        run_async(
            lambda: self._fetch_smart_items(lang, "new"),
            self._on_smart_fetched
        )
        
    async def _fetch_smart_items(self, lang, mode):
        """Background fetcher for smart items."""
        with get_session() as session:
            if mode == "review":
                return self.fetcher_service.get_due(lang, session, limit=20)
            elif mode == "new":
                return self.fetcher_service.list_by_filters(
                    lang, session, 
                    mastery_statuses=[GrammarMasteryStatus.NEW.value], 
                    limit=5
                )
            return []
            
    def _on_smart_fetched(self, items):
        if not items:
            toast_info("Dữ liệu trống! Hãy thử thêm dữ liệu mới hoặc đổi chế độ.")
            return
            
        self._launch_session_with_items(items)

    def _launch_session_with_items(self, items):
        """Launch study view with specific items."""
        self.srs_session_queue = items
        self.current_review_index = 0
        
        # Switch to Study View in Stack
        # view_stack index: 0=Smart, 1=List, 2=Study
        if hasattr(self, 'view_stack'):
            self.view_stack.setCurrentIndex(2)
        elif hasattr(self, 'stacked_widget'): # Fallback logic
            self.stacked_widget.setCurrentWidget(self.study_view)
            
        self._load_current_card()

    def _start_session(self):
        """Legacy/Manual Start from List View (uses current filters)."""
        lang = self._get_current_lang()
        
        # Determine filters from UI
        category_id = None
        base_level_filter = None
        
        current_data = getattr(self, 'current_display_filter', None)
        if isinstance(current_data, dict):
            if current_data.get("type") == "category":
                category_id = current_data.get("value")
            elif current_data.get("type") == "level":
                base_level_filter = current_data.get("value")
                
        source_filter = self.source_filter_combo.currentData()
        level_filter = self.level_filter_combo.currentData()
        final_level = level_filter if level_filter else base_level_filter
        
        async def fetch_due():
            with get_session() as session:
                return self.fetcher_service.get_due(
                    lang=lang, 
                    session=session, 
                    limit=20,
                    category_id=category_id,
                    source_material=source_filter,
                    level=final_level
                )
                
        run_async(fetch_due, self._on_smart_fetched)

    def _load_current_card(self):
        if self.current_review_index >= len(self.srs_session_queue):
            toast_success("Đã ôn tập xong!")
            self._exit_session()
            return
            
        card = self.srs_session_queue[self.current_review_index]
        self.flashcard.set_card(card)
        self.progress_lbl.setText(f"{self.current_review_index + 1}/{len(self.srs_session_queue)}")
        
        self.show_answer_btn.show()
        self.show_answer_btn.setFocus()
        self.rating_container.hide()
        if hasattr(self, 'completion_container'):
            self.completion_container.hide()


    def _on_show_answer(self):
        self.flashcard.flip()
        self.show_answer_btn.hide()
        self.rating_container.show()
        if hasattr(self, 'completion_container'):
            self.completion_container.show()

    
    def _submit_review(self, quality):
        if self.current_review_index >= len(self.srs_session_queue):
            return
            
        card = self.srs_session_queue[self.current_review_index]
        card_id = card.get('id') if isinstance(card, dict) else card.id
        
        # Update SRS Progress (Original Logic)
        async def save_srs():
            with get_session() as session:
                self.fetcher_service.submit_review(card_id, quality, session)
        run_async(save_srs, lambda _: None)

        # Update Learning Map Progress
        if quality >= 3: # Good or Easy
            self.map_service.update_progress(card_id, MapStatus.MASTERED)
            self.map_service.unlock_next_nodes(card_id)
        else:
            self.map_service.update_progress(card_id, MapStatus.LEARNING)
        
        # Refresh Map UI if it exists
        if hasattr(self, 'map_view'):
            self.map_view.refresh_data()
            
        self.current_review_index += 1
        self._load_current_card()

    def _exit_session(self):
        """Exit study mode and return to list view."""
        if hasattr(self, 'view_stack'):
            self.view_stack.setCurrentWidget(self.list_view)
        self._refresh_list()
    
    def _on_mark_completed(self):
        """Mark current grammar as completed and unlock next nodes."""
        if not self.srs_session_queue or self.current_review_index >= len(self.srs_session_queue):
            return
        
        card = self.srs_session_queue[self.current_review_index]
        card_id = card.get('id') if isinstance(card, dict) else card.id
        card_title = card.get('title') if isinstance(card, dict) else getattr(card, 'title', 'Unknown')
        
        # Mark as MASTERED (MapStatus is imported at top of file from frontend.models.learning_progress)
        if hasattr(self, 'map_service') and self.map_service:
            self.map_service.update_progress(card_id, MapStatus.MASTERED)
            self.map_service.unlock_next_nodes(card_id)
            print(f"[GrammarTab] Marked '{card_title}' as MASTERED and unlocked next nodes")
        
        # Refresh Map UI
        if hasattr(self, 'map_view'):
            self.map_view.refresh_data()
        
        # Show success message (toast_success is imported at top of file)
        toast_success(f"🎉 Hoàn thành '{card_title}'! Các node tiếp theo đã được mở khóa.")
        
        # Return to map view
        if hasattr(self, 'view_stack'):
            self.view_stack.setCurrentIndex(3)  # Map view index


    def _batch_lookup(self):
        """Batch lookup for grammar items (Placeholder for search multiple)."""
        toast_info("Tính năng tra cứu hàng loạt sẽ giúp tự động điền các thông tin còn thiếu từ các nguồn online.")

    def _batch_enrich_grammar(self):
        """Batch enrich grammar items with AI."""
        if not hasattr(self, 'all_items') or not self.all_items:
            QMessageBox.warning(self, "Không có dữ liệu", "Vui lòng chọn trình độ hoặc bộ lọc có ngữ pháp.")
            return

        # Filter items to enrich
        items_to_enrich = []
        for item in self.all_items:
            # Re-enrich if missing description or usage notes even if marked
            # Handle both dict and object types safely
            if isinstance(item, dict):
                is_enriched = item.get("is_ai_enriched")
                desc = item.get("description")
                usage = item.get("usage_notes")
            else:
                is_enriched = getattr(item, "is_ai_enriched", False)
                desc = getattr(item, "description", None)
                usage = getattr(item, "usage_notes", None)

            if not is_enriched or not desc or not usage:
                items_to_enrich.append(item)
        
        if not items_to_enrich:
            toast_success("Tất cả ngữ pháp trong danh sách đã được làm giàu bởi AI!")
            return

        # Prepare processing
        max_total_batch = 500
        process_list = items_to_enrich[:max_total_batch]
        
        reply = QMessageBox.question(
            self, "Làm giàu hàng loạt với AI",
            f"Tìm thấy {len(items_to_enrich)} cấu trúc chưa được làm giàu.\n"
            f"Bạn có muốn AI xử lý {len(process_list)} cấu trúc tiếp theo không?\n"
            f"⚠️ Vì nội dung ngữ pháp dài, hệ thống sẽ gửi theo nhóm (20 cấu trúc/lần) để đảm bảo chất lượng.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes: return

        self.ai_batch_btn.setEnabled(False)
        self.ai_batch_btn.setText("⏳ Đang xử lý...")
        
        from frontend.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        lang = self._get_current_lang()
        CHUNK_SIZE = 12 

        from PySide6.QtWidgets import QProgressDialog
        progress = QProgressDialog("Đang làm giàu ngữ pháp với AI...", "Hủy", 0, len(process_list), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        enriched_count = 0
        error_count = 0
        
        async def process():
            nonlocal enriched_count, error_count
            chunks = [process_list[i:i + CHUNK_SIZE] for i in range(0, len(process_list), CHUNK_SIZE)]
            
            for i, chunk in enumerate(chunks):
                if progress.wasCanceled(): break
                processed_so_far = i * CHUNK_SIZE
                def update_progress(v=processed_so_far, t=f"Đang xử lý nhóm {i+1}/{len(chunks)} ({len(chunk)} cấu trúc)..."):
                    progress.setValue(v)
                    progress.setLabelText(t)
                QTimer.singleShot(0, update_progress)
                
                patterns = []
                for item in chunk:
                    p_title = item.get("title") if isinstance(item, dict) else getattr(item, "title", None)
                    if p_title:
                        patterns.append(p_title)
                try:
                    result = await ai_service.enrich_grammar_batch(patterns, lang)
                    if result.get("success"):
                        batch_data = result.get("results", {})
                        with get_session() as session:
                            for idx, item_data in enumerate(chunk):
                                title = item_data.get("title") if isinstance(item_data, dict) else getattr(item_data, "title", None)
                                
                                # Use index-based lookup (1-indexed as requested in prompt)
                                ai_data = batch_data.get(str(idx + 1)) or batch_data.get(idx + 1)
                                
                                if not ai_data:
                                    # Fallback to fuzzy match by title if index fails
                                    if title and title in batch_data: 
                                        ai_data = batch_data[title]
                                    else:
                                        import re
                                        def norm(s): return re.sub(r'[～\s\.\,\、\。\?\!\-\(\)（）]', '', str(s)).lower()
                                        target_norm = norm(title)
                                        for k, v in batch_data.items():
                                            if norm(k) == target_norm:
                                                ai_data = v; break
                                
                                if ai_data:
                                    try:
                                        grammar_id = item_data.get("id") if isinstance(item_data, dict) else getattr(item_data, "id", None)
                                        if not grammar_id:
                                            print(f"Warning: Missing ID for item {title}")
                                            error_count += 1
                                            continue
                                            
                                        db_item = session.get(GrammarTopic, grammar_id)
                                        if db_item:
                                            # Combine meaning and description into description field
                                            meaning = ai_data.get("meaning", "")
                                            desc = ai_data.get("description", "")
                                            
                                            if meaning and desc:
                                                db_item.description = f"**{meaning}**\n\n{desc}"
                                            elif meaning:
                                                db_item.description = meaning
                                            elif desc:
                                                db_item.description = desc
                                                
                                            if ai_data.get("usage_notes"): db_item.usage_notes = ai_data["usage_notes"]
                                            if ai_data.get("common_mistakes"): db_item.common_mistakes = ai_data["common_mistakes"]
                                            
                                            # Handle examples list
                                            if ai_data.get("examples"):
                                                exs = ai_data["examples"]
                                                ex_text = "\n".join(exs) if isinstance(exs, list) else exs
                                                if db_item.usage_notes: 
                                                    db_item.usage_notes += f"\n\n--- AI Examples ---\n{ex_text}"
                                                else:
                                                    db_item.usage_notes = ex_text
                                            
                                            # Set AI Enriched flag
                                            db_item.is_ai_enriched = True
                                            
                                            session.add(db_item)
                                            enriched_count += 1
                                        else: 
                                            print(f"Error: Could not find DB item with ID {grammar_id}")
                                            error_count += 1
                                    except Exception as e:
                                        print(f"Error updating item {title}: {e}")
                                        error_count += 1
                                else: 
                                    print(f"Warning: No AI data for {title}")
                                    error_count += 1
                            session.commit()
                    else: 
                        print(f"Grammar Batch {i+1} Failed: {result.get('error')}")
                        error_count += len(chunk)
                except Exception as e:
                    import traceback
                    print(f"Grammar Batch Error (Chunk {i+1}): {e}\n{traceback.format_exc()}")
                    error_count += len(chunk)
                
                import asyncio
                await asyncio.sleep(0.5)
                
            return {"enriched": enriched_count, "errors": error_count}

        def done(result):
            self.ai_batch_btn.setEnabled(True)
            self.ai_batch_btn.setText(" AI Làm giàu")
            QTimer.singleShot(0, lambda: progress.setValue(len(process_list)))
            toast_info(f"Làm giàu ngữ pháp hoàn tất!\n\n✅ Thành công: {enriched_count}\n❌ Thất bại: {error_count}")
            self._refresh_list()

        run_async(process, done)

    def _enrich_selected_grammar(self):
        """Enrich the selected grammar point with AI."""
        if not hasattr(self, '_selected_grammar_data') or not self._selected_grammar_data:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một cấu trúc để làm giàu")
            return
            
        data = self._selected_grammar_data
        grammar_id = data.get("id") if isinstance(data, dict) else getattr(data, "id", None)
        pattern = data.get("pattern") if isinstance(data, dict) else getattr(data, "pattern", "")
        title = data.get("title") if isinstance(data, dict) else getattr(data, "title", "")
        
        if not grammar_id:
            return
            
        self.grammar_ai_enrich_btn.setEnabled(False)
        self.grammar_ai_enrich_btn.setText("⏳ Đang xử lý...")
        
        lang = self._get_current_lang()
        from frontend.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        
        async def enrich():
            # Use title if available, otherwise pattern
            query = title or pattern
            return await ai_service.enrich_grammar(query, lang)
            
        def on_enriched(result):
            self.grammar_ai_enrich_btn.setEnabled(True)
            self.grammar_ai_enrich_btn.setText("✨ AI Làm giàu")
            
            if result.get("success"):
                ai_data = result.get("data", {})
                
                # Check if we got valid data
                if not ai_data or (not ai_data.get("meaning") and not ai_data.get("description")):
                    QMessageBox.warning(self, "AI Trả về rỗng", "AI không trả về nội dung hữu ích nào.")
                    return

                update_data = {"is_ai_enriched": True}
                
                # ... (AI data processing logic remains the same) ...
                if ai_data.get("meaning") or ai_data.get("description"):
                    meaning = ai_data.get("meaning", "")
                    desc = ai_data.get("description", "")
                    if meaning and desc:
                        update_data["description"] = f"**{meaning}**\n\n{desc}"
                    else:
                        update_data["description"] = meaning or desc
                
                if ai_data.get("usage_notes"):
                    usage = ai_data["usage_notes"]
                    if ai_data.get("examples"):
                        ex_text = ai_data["examples"]
                        usage += f"\n\n--- Ví dụ AI ---\n{ex_text}"
                    update_data["usage_notes"] = usage
                
                if ai_data.get("common_mistakes"): 
                    update_data["common_mistakes"] = ai_data["common_mistakes"]
                
                async def save():
                    with get_session() as session:
                        return self.fetcher_service.update_grammar(grammar_id, update_data, session)
                        
                def on_saved(save_result):
                    if save_result and save_result.get("success"):
                        # 1. Update local data object
                        if isinstance(self._selected_grammar_data, dict):
                            self._selected_grammar_data.update(update_data)
                        else:
                            for key, value in update_data.items():
                                setattr(self._selected_grammar_data, key, value)
                        
                        # 2. Update Detail View (if in List mode)
                        self._display_grammar_details(self._selected_grammar_data)
                        
                        # 3. Update Flashcard View (if in Study mode)
                        if hasattr(self, 'flashcard') and self.flashcard.isVisible():
                            print("[GrammarTab] Refreshing flashcard with enriched data")
                            self.flashcard.set_grammar(self._selected_grammar_data)

                        # 4. Show Success Notification
                        toast_success(f"✨ Đã làm giàu xong: {title or pattern}")
                        
                        # 5. Refresh list to show icon
                        self._refresh_list()
                    else:
                        QMessageBox.warning(self, "Lỗi", "Không thể lưu dữ liệu AI vào database")

                run_async(save, on_saved)
            else:
                QMessageBox.warning(self, "Lỗi AI", result.get("error", "Lỗi không xác định"))
                
        run_async(enrich, on_enriched)

    def _reset_all_visible_ai(self):
        """Reset AI enrichment status for all currently visible grammar."""
        if not hasattr(self, 'all_items') or not self.all_items:
            return
            
        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Bạn có muốn reset trạng thái AI cho {len(self.all_items)} cấu trúc ngữ pháp đang hiển thị không?\n"
            "(Thẻ sẽ được AI làm giàu lại vào lần tới)",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        try:
            with get_session() as session:
                for item in self.all_items:
                    grammar_id = item.get("id") if isinstance(item, dict) else getattr(item, "id", None)
                    if grammar_id:
                        db_item = session.get(GrammarTopic, grammar_id)
                    if db_item:
                        db_item.is_ai_enriched = False
                        session.add(db_item)
                session.commit()
                toast_success(f"Đã reset trạng thái AI cho {len(self.all_items)} cấu trúc ngữ pháp.")
                self._refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể reset AI: {e}")
