"""Kanji (Hán tự) Tab - Anki-inspired Japanese kanji learning.

Features inspired by Anki:
- Spaced Repetition System (SRS) with customizable intervals
- Multiple study modes: Recognition, Production, Reading
- Radical/component breakdown with mnemonics
- Stroke order visualization
- JLPT/Grade level organization with decks
- Leech detection (cards repeatedly forgotten)
- Daily review count and statistics
"""
from typing import Optional, List, Dict, Any
from PySide6.QtCore import Qt, QPoint, Signal, QTimer, QThread, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QAction, QFont, QColor, QPalette
# Services
from frontend.utils.async_helpers import run_async
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QListWidget, QLabel, QSplitter, QMenu, QMessageBox,
    QListWidgetItem, QTreeWidget, QTreeWidgetItem, QGroupBox, QFrame,
    QProgressBar, QSpinBox, QCheckBox, QStackedWidget, QTextBrowser,
    QGridLayout, QScrollArea, QFileDialog, QProgressDialog, QGraphicsOpacityEffect,
    QSizePolicy, QTabWidget, QButtonGroup
)

# UI Components
from frontend.ui.widgets.practice_settings_dialog import PracticeSettingsDialog
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin

# Models
from sqlmodel import Session, select, or_, func
from frontend.models.kanji import (
    KanjiMasteryStatus, KanjiStudyMode, KanjiItem, KanjiDeck, KanjiVocab,
    DEFAULT_KANJI_DECKS, SRS_INTERVALS, SRS_RATINGS,
    JLPT_KANJI_COUNTS, GRADE_LEVELS
)

# Custom Imports
from scripts.import_kanji import import_docx_to_db
from frontend.core.database import engine
from frontend.services.ai_service import get_ai_service
from frontend.services.tts import get_tts_service
from frontend.ui.styles.theme import ThemeColors
from frontend.ui.styles.animations import AnimationService
from frontend.ui.tabs.kanji_practice_tab import KanjiPracticeTab
from frontend.ui.widgets.kanji_flashcard import KanjiFlashcardView
from frontend.services.kanji_service import get_kanji_service
from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning





class ImportWorker(QThread):
    """Background worker for importing Kanji from Word document."""
    finished = Signal(int, int) # kanji_count, vocab_count
    error = Signal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            k, v = import_docx_to_db(self.file_path, engine)
            self.finished.emit(k, v)
        except Exception as e:
            self.error.emit(str(e))


class KanjiEnrichWorker(QThread):
    """Background worker for enriching Kanji data using AI."""
    finished = Signal(int) # total_enriched
    error = Signal(str)
    progress = Signal(int, int) # current, total

    def __init__(self, kanji_list: List[str]):
        super().__init__()
        self.kanji_list = kanji_list

    def run(self):
        try:
            ai_service = get_ai_service()
            total = len(self.kanji_list)
            chunk_size = 50 # Process in larger batches to save RPD
            enriched_count = 0
            
            for i in range(0, total, chunk_size):
                chunk = self.kanji_list[i:i + chunk_size]
                self.progress.emit(i, total)
                
                import asyncio
                # Run the async enrichment in a thread-safe way
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(ai_service.enrich_kanji_batch(chunk))
                loop.close()
                
                if result.get("success"):
                    ai_data = result.get("results", {})
                    with Session(engine) as session:
                        for char, data in ai_data.items():
                            item = session.exec(select(KanjiItem).where(KanjiItem.kanji == char)).first()
                            if item:
                                if data.get("meaning_vi"): item.meaning_vi = data["meaning_vi"]
                                if data.get("han_viet"): item.han_viet = data["han_viet"].upper()
                                if data.get("onyomi"): item.onyomi = data["onyomi"]
                                if data.get("kunyomi"): item.kunyomi = data["kunyomi"]
                                if data.get("radicals"): item.radicals = data["radicals"]
                                if data.get("components"): item.components = data["components"]
                                if data.get("mnemonic"): item.mnemonic = data["mnemonic"]
                                
                                # Set AI Enriched flag
                                item.is_ai_enriched = True
                                
                                session.add(item)
                                enriched_count += 1
                        session.commit()
                else:
                    # Log error but continue
                    print(f"[KanjiEnrichWorker] AI error for chunk {chunk}: {result.get('error')}")
            
            self.finished.emit(enriched_count)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))



class KanjiTab(QWidget, TextContextMenuMixin):
    """Kanji learning tab with Anki-inspired SRS system.
    
    Provides:
    - Kanji search and lookup with meanings/readings
    - Deck-based organization (JLPT levels, custom decks)
    - SRS-powered flashcard study sessions
    - Stroke order display
    - Radical/component breakdown
    - Progress tracking and statistics
    """
    
    def __init__(self) -> None:
        """Initialize kanji tab."""
        super().__init__()
        
        # State

        self.current_kanji_id: Optional[int] = None
        self.current_kanji_data: Optional[Dict[str, Any]] = None
        self.current_deck_id: Optional[int] = None
        self.decks: List[Dict[str, Any]] = []
        self.kanji_list: List[Dict[str, Any]] = []
        
        # Pagination state
        self.current_offset: int = 0
        self.page_size: int = 100
        self.total_count: int = 0
        
        # Study session state
        self.study_queue: List[Dict[str, Any]] = []
        self.current_study_index: int = 0
        self.is_answer_shown: bool = False
        
        # Services
        self.kanji_service = get_kanji_service()
        
        self._init_ui()
        self._load_initial_data()
    
    def _init_ui(self):
        """Initialize UI layout with tabs (Browse and Practice)."""
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

        # --- TAB 1: Kanji Browser/Study ---
        self.browse_page = QWidget()
        browse_layout = QHBoxLayout(self.browse_page)
        browse_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = self._create_sidebar()
        browse_layout.addWidget(self.sidebar)
        
        # Main content stacked widget (Smart Dashboard / Dictionary / Study)
        self.main_content_area = QWidget()
        main_content_layout = QVBoxLayout(self.main_content_area)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toggle Bar (Smart vs Dictionary)
        toggle_container = QWidget()
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.addStretch()
        
        self.view_toggle_group = QButtonGroup(self)
        self.view_toggle_group.setExclusive(True)
        
        # Smart Mode Button
        self.btn_view_smart = QPushButton("🏰 Xây dựng")
        self.btn_view_smart.setCheckable(True)
        self.btn_view_smart.setChecked(True)
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
        
        main_content_layout.addWidget(toggle_container)

        # Content Stack
        self.view_stack = QStackedWidget()
        
        # View 0: Smart Dashboard (Construction Site mode)
        self.smart_dashboard = self._create_smart_dashboard()
        self.view_stack.addWidget(self.smart_dashboard)
        
        # View 1: Dictionary / Browser
        self.browse_widget = self._create_browse_content()
        self.view_stack.addWidget(self.browse_widget) # This contains its own stack for list/study
        
        # When study starts, we might need to override this logic or ensure browse_widget handles it
        # Actually browse_widget has a stack for Browse/Study.
        # So View 1 is Browse Widget.
        
        main_content_layout.addWidget(self.view_stack)
        
        browse_layout.addWidget(self.main_content_area)
        
        self.main_tabs.addTab(self.browse_page, "🈴 Hán tự")
        
        # --- TAB 2: Luyện tập (KanjiPracticeTab) ---
        self.practice_tab = KanjiPracticeTab()
        self.main_tabs.addTab(self.practice_tab, "🎯 Luyện tập")
        
        # Main Layout
        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(self.main_tabs)

        # Connect tab change to refresh practice data
        self.main_tabs.currentChanged.connect(self._on_subtab_changed)

    def _create_smart_dashboard(self) -> QWidget:
        """Create the Gamified 'Construction' Dashboard."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(20)
        
        # -- Welcome --
        welcome_lbl = QLabel("🏗️ Kiến trúc sư! Hôm nay ta xây tầng nào?")
        welcome_lbl.setStyleSheet(f"font-size: 16px; color: {ThemeColors.TEXT_SECONDARY}; font-style: italic;")
        welcome_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_lbl)
        
        # -- Main Action Cards --
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Card 1: Review (Repair)
        self.card_repair = QFrame()
        self.card_repair.setStyleSheet(f"""
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
        c1_layout = QVBoxLayout(self.card_repair)
        c1_icon = QLabel("🛠️")
        c1_icon.setStyleSheet("font-size: 32px;")
        c1_icon.setAlignment(Qt.AlignCenter)
        c1_title = QLabel("Gia cố kiến thức")
        c1_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        c1_title.setAlignment(Qt.AlignCenter)
        
        self.dash_repair_lbl = QLabel("0 viên gạch lỏng lẻo")
        self.dash_repair_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeColors.DANGER}; font-weight: bold;")
        self.dash_repair_lbl.setAlignment(Qt.AlignCenter)
        
        c1_btn = QPushButton("Sửa chữa ngay")
        c1_btn.setCursor(Qt.PointingHandCursor)
        c1_btn.setStyleSheet(f"""
            background-color: {ThemeColors.DANGER}; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;
        """)
        c1_btn.clicked.connect(self._start_smart_review)
        
        c1_layout.addWidget(c1_icon)
        c1_layout.addWidget(c1_title)
        c1_layout.addWidget(self.dash_repair_lbl)
        c1_layout.addWidget(c1_btn)
        
        cards_layout.addWidget(self.card_repair)
        
        # Card 2: Build New (Learn)
        self.card_build = QFrame()
        self.card_build.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 12px;
                border: 1px solid {ThemeColors.BORDER};
            }}
            QFrame:hover {{
                border: 2px solid {ThemeColors.SUCCESS};
                background-color: {ThemeColors.BG_TERTIARY};
                margin-top: -5px; /* Lift effect */
                margin-bottom: 5px;
            }}
        """)
        c2_layout = QVBoxLayout(self.card_build)
        c2_icon = QLabel("🧱")
        c2_icon.setStyleSheet("font-size: 32px;")
        c2_icon.setAlignment(Qt.AlignCenter)
        c2_title = QLabel("Xây tầng mới")
        c2_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        c2_title.setAlignment(Qt.AlignCenter)
        
        self.dash_build_lbl = QLabel("Vật liệu sẵn sàng")
        self.dash_build_lbl.setStyleSheet(f"font-size: 14px; color: {ThemeColors.SUCCESS}; font-weight: bold;")
        self.dash_build_lbl.setAlignment(Qt.AlignCenter)
        
        c2_btn = QPushButton("Đặt 5 viên gạch")
        c2_btn.setCursor(Qt.PointingHandCursor)
        c2_btn.setStyleSheet(f"""
            background-color: {ThemeColors.SUCCESS}; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;
        """)
        c2_btn.clicked.connect(self._start_smart_learn)
        
        c2_layout.addWidget(c2_icon)
        c2_layout.addWidget(c2_title)
        c2_layout.addWidget(self.dash_build_lbl)
        c2_layout.addWidget(c2_btn)
        
        cards_layout.addWidget(self.card_build)
        
        layout.addLayout(cards_layout)
        
        # -- Construction Map (Levels) --
        layout.addSpacing(20)
        map_header = QLabel("🗺️ Bản đồ công trình")
        map_header.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY}; border-bottom: 2px solid {ThemeColors.BORDER}; padding-bottom: 5px;")
        layout.addWidget(map_header)
        
        # Visual Wall Progress
        self.map_container = QWidget()
        self.map_layout = QHBoxLayout(self.map_container)
        self.map_layout.setSpacing(10)
        self.map_layout.setAlignment(Qt.AlignLeft)
        
        # We will populate this map in _update_dashboard with "bricks"
        # Each level is a "Column" of bricks
        
        layout.addWidget(self.map_container)
        layout.addStretch()

        # Add hover animations
        self._add_hover_animations(self.card_repair)
        self._add_hover_animations(self.card_build)
        
        return widget

    def _add_hover_animations(self, widget):
        """Add raise/shadow effect on hover."""
        shadow = QGraphicsOpacityEffect(widget)
        shadow.setOpacity(0) # Initially no shadow processing, handled by stylesheet mostly, but we use GraphicsEffect for elevation if needed
        # Actually simplify: just stylesheet is enough for shadow/border.
        # Let's add simple "Rise" animation by moving it up slightly?
        # QWidget doesn't support easy 'transform' without GraphicsView.
        # We stick to Stylesheet hover which is already good.
        # But we can add a 'Glow' effect via Shadow.
        
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        eff = QGraphicsDropShadowEffect(widget)
        eff.setBlurRadius(20)
        eff.setColor(QColor(0, 0, 0, 50))
        eff.setOffset(0, 4)
        widget.setGraphicsEffect(eff)
        
        # We can animate blur radius on enter/leave if we subclass, but for now specific stylesheet hover is fine.
        # The user requested "Hover" & "Click" effects.
        # The existing stylesheet handles border/bg change.
        # Let's trust the stylesheet updates in _create_smart_dashboard to be sufficient for visual 'pop'.
        pass

    def _update_dashboard_wall(self):
        """Draw the 'Brick Wall' progress."""
        # Clear existing
        item = self.map_layout.takeAt(0)
        while item:
            w = item.widget()
            if w: w.deleteLater()
            item = self.map_layout.takeAt(0)
            
        # Draw columns for N5, N4, N3, N2, N1
        levels = ["N5", "N4", "N3", "N2", "N1"]
        
        with Session(engine) as session:
             # Calculate completion for each level
             # This assumes deck names contain N5, N4 etc or using tags?
             # For simplicity, we just look at decks.
             decks = session.exec(select(KanjiDeck)).all()
             
             for level in levels:
                 # Find relevant decks - also count direct items if no decks found
                 level_decks = [d.id for d in decks if level in d.name]
                 
                 learned_score = 0
                 total = 0
                 
                 if level_decks:
                     for did in level_decks:
                         total += session.exec(select(func.count()).where(KanjiItem.deck_id == did)).one()
                         # Mastered = 1.0 point
                         m_count = session.exec(select(func.count()).where(KanjiItem.deck_id == did, KanjiItem.mastery_status == KanjiMasteryStatus.MASTERED.value)).one()
                         # Reviewing = 0.5 point (Learning progress)
                         r_count = session.exec(select(func.count()).where(KanjiItem.deck_id == did, KanjiItem.mastery_status == KanjiMasteryStatus.REVIEWING.value)).one()
                         
                         learned_score += m_count + (r_count * 0.5)
                 
                 # Always show column even if total is 0
                 if total == 0: 
                     total = 1  # avoid div zero, will show empty pillar
                 
                 # Draw a "Pillar"
                 pillar = QFrame()
                 pillar.setFixedSize(60, 200) # Fixed size pillar
                 pillar.setStyleSheet(f"background: {ThemeColors.BG_TERTIARY}; border-radius: 4px; border: 1px solid {ThemeColors.BORDER};")
                 
                 p_layout = QVBoxLayout(pillar)
                 p_layout.setContentsMargins(2,2,2,2)
                 p_layout.setSpacing(1)
                 p_layout.setAlignment(Qt.AlignBottom)
                 
                 # Calculate number of "bricks" to show (max 10 bricks high)
                 # Calculate number of "bricks" to show (max 10 bricks high)
                 percent = learned_score / total
                 bricks_to_fill = int(percent * 10)
                 
                 # Add bricks (bottom up)
                 for i in range(10):
                     brick = QLabel()
                     brick.setFixedHeight(16)
                     
                     # Check if this brick should be filled
                     # Indexes 0-9 top-to-bottom. Bottom is 9.
                     # If we have 3 bricks, we fill indices 7, 8, 9.
                     # Logic: is_filled if (9-i) < bricks_to_fill
                     
                     is_filled = (9-i) < bricks_to_fill
                     if is_filled:
                         # Gradient color based on progress? Or just simple Green for now.
                         # Maybe Orange for partial? Let's stick to Green for visible progress.
                         brick.setStyleSheet(f"background: {ThemeColors.SUCCESS}; border-radius: 2px;")
                     else:
                         brick.setStyleSheet(f"background: {ThemeColors.BG_SECONDARY}; border-radius: 2px; border: 1px dashed {ThemeColors.BORDER};")
                         
                     p_layout.addWidget(brick)
                 
                 # Label
                 lbl = QLabel(level)
                 lbl.setAlignment(Qt.AlignCenter)
                 
                 col_container = QWidget()
                 col_layout = QVBoxLayout(col_container)
                 col_layout.addWidget(pillar)
                 col_layout.addWidget(lbl, alignment=Qt.AlignCenter)
                 
                 self.map_layout.addWidget(col_container)

    def _on_subtab_changed(self, index):
        if index == 1:  # Luyện tập tab
            if hasattr(self, 'practice_tab'):
                self.practice_tab._load_items()
    
    def _create_sidebar(self) -> QWidget:
        """Create the left sidebar with deck tree and stats.
        
        Returns:
            Sidebar widget
        """
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 8px;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QTreeWidget {{
                background: transparent;
                border: none;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background-color: {ThemeColors.BG_TERTIARY};
            }}
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(10)
        
        # Header with kanji icon
        header = QLabel("🈴 漢字 - Hán tự")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.ACCENT};")
        layout.addWidget(header)
        
        # Today's stats panel (Anki-style)
        stats_group = QFrame()
        stats_group.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        stats_layout = QGridLayout(stats_group)
        
        # Review cards (Cần ôn) - Consistent with VocabTab/GrammarTab
        review_icon = QLabel("🔄")
        review_lbl = QLabel("Cần ôn")
        review_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; font-size: 13px;")
        self.review_count_label = QLabel("0")
        self.review_count_label.setStyleSheet(f"color: {ThemeColors.SUCCESS}; font-size: 18px; font-weight: bold;")
        self.review_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        stats_layout.addWidget(review_icon, 0, 0)
        stats_layout.addWidget(review_lbl, 0, 1)
        stats_layout.addWidget(self.review_count_label, 0, 2)
        
        # New cards (Mới)
        new_icon = QLabel("🆕")
        new_lbl = QLabel("Mới")
        new_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; font-size: 13px;")
        self.new_count_label = QLabel("0")
        self.new_count_label.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-size: 18px; font-weight: bold;")
        self.new_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        stats_layout.addWidget(new_icon, 1, 0)
        stats_layout.addWidget(new_lbl, 1, 1)
        stats_layout.addWidget(self.new_count_label, 1, 2)
        
        # Learning cards (Đang học)
        learning_icon = QLabel("📖")
        learning_lbl = QLabel("Đang học")
        learning_lbl.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; font-size: 13px;")
        self.learning_count_label = QLabel("0")
        self.learning_count_label.setStyleSheet(f"color: {ThemeColors.DANGER}; font-size: 18px; font-weight: bold;")
        self.learning_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        stats_layout.addWidget(learning_icon, 2, 0)
        stats_layout.addWidget(learning_lbl, 2, 1)
        stats_layout.addWidget(self.learning_count_label, 2, 2)
        
        stats_layout.setColumnStretch(1, 1)
        
        layout.addWidget(stats_group)
        
        # Big Study button (Anki-style)
        self.study_btn = QPushButton("🚀 Bắt đầu học!")
        self.study_btn.setToolTip("Bắt đầu ôn tập các thẻ đến hạn")
        self.study_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SUCCESS};
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """)
        self.study_btn.clicked.connect(self._start_study_session)
        layout.addWidget(self.study_btn)

        # Auto-pronounce checkbox
        self.auto_pronounce_cb = QCheckBox("🔊 Tự động phát âm")
        self.auto_pronounce_cb.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; margin-top: 5px;")
        self.auto_pronounce_cb.setChecked(True)
        layout.addWidget(self.auto_pronounce_cb)
        
        # Deck tree
        deck_label = QLabel("📚 Bộ thẻ (Decks)")
        deck_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(deck_label)
        
        self.deck_tree = QTreeWidget()
        self.deck_tree.setHeaderHidden(True)
        self.deck_tree.itemClicked.connect(self._on_deck_selected)
        layout.addWidget(self.deck_tree, 1)
        
        # Deck management buttons
        deck_btn_layout = QHBoxLayout()
        
        self.add_deck_btn = QPushButton("➕ Thêm")
        self.add_deck_btn.setToolTip("Thêm bộ thẻ mới")
        # Remove setFixedWidth to allow text to fit
        self.add_deck_btn.clicked.connect(self._add_deck)
        
        self.import_btn = QPushButton("📥 Nhập")
        self.import_btn.setToolTip("Import từ file")
        # Remove setFixedWidth
        self.import_btn.clicked.connect(self._import_deck)
        
        deck_btn_layout.addWidget(self.add_deck_btn)
        deck_btn_layout.addWidget(self.import_btn)
        deck_btn_layout.addStretch()
        layout.addLayout(deck_btn_layout)
        
        # Filter by status
        filter_label = QLabel("🎯 Lọc:")
        layout.addWidget(filter_label)
        
        self.status_filter = QComboBox()
        self.status_filter.setStyleSheet(f"background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY};")
        self.status_filter.addItem("📋 Tất cả", None)
        self.status_filter.addItem("🆕 Chưa học", KanjiMasteryStatus.NEW.value)
        self.status_filter.addItem("📖 Đang học", KanjiMasteryStatus.LEARNING.value)
        self.status_filter.addItem("🔄 Ôn tập", KanjiMasteryStatus.REVIEWING.value)
        self.status_filter.addItem("✅ Đã thuộc", KanjiMasteryStatus.MASTERED.value)
        self.status_filter.addItem("⚠️ Leech", KanjiMasteryStatus.LEECH.value)
        self.status_filter.currentIndexChanged.connect(lambda: self._apply_filters(reset_pagination=True))
        layout.addWidget(self.status_filter)
        
        return sidebar
    
    def _create_browse_content(self) -> QWidget:
        """Create the browse mode content.
        
        Returns:
            Browse widget (Stacked)
        """
        self.content_stack = QStackedWidget()
        
        # --- Page 0: Browser ---
        browse_container = QWidget()
        layout = QVBoxLayout(browse_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kanji (ví dụ: 食, たべる, ăn, eat...)")
        self.search_input.textChanged.connect(lambda: self._search_kanji(reset_pagination=True))
        
        search_layout.addWidget(self.search_input, 1)
        
        # Add New Kanji Button
        self.add_kanji_btn = QPushButton(" Thêm")
        self.add_kanji_btn.setToolTip("Thêm Kanji mới")
        self.add_kanji_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SUCCESS}; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #388E3C; }}
        """)
        self.add_kanji_btn.clicked.connect(self._add_new_kanji)
        search_layout.addWidget(self.add_kanji_btn)

        # Import Button
        self.import_btn_toolbar = QPushButton(" Import")
        self.import_btn_toolbar.setToolTip("Nhập Kanji từ tệp Word/Excel/CSV")
        self.import_btn_toolbar.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.ACCENT}; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #F57C00; }}
        """)
        self.import_btn_toolbar.clicked.connect(self._import_deck)
        search_layout.addWidget(self.import_btn_toolbar)

        # Study Button (Small)
        self.study_now_btn_small = QPushButton(" Học")
        self.study_now_btn_small.setToolTip("Bắt đầu phiên học Flashcard")
        self.study_now_btn_small.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY}; color: white; font-weight: bold; 
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.PRIMARY_HOVER}; }}
        """)
        self.study_now_btn_small.clicked.connect(self._start_study_session)
        search_layout.addWidget(self.study_now_btn_small)

        # Batch Lookup Button
        self.batch_lookup_btn = QPushButton(" Tra loạt")
        self.batch_lookup_btn.setToolTip("Tra cứu hàng loạt Kanji")
        self.batch_lookup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_PRESSED}; color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.PRIMARY}; }}
        """)
        self.batch_lookup_btn.clicked.connect(lambda: toast_info("Tính năng tra cứu hàng loạt Kanji sẽ giúp tự động điền các thông tin còn thiếu."))
        search_layout.addWidget(self.batch_lookup_btn)
        
        # AI Batch Enrich Button
        self.enrich_ai_btn = QPushButton(" AI Làm giàu")
        self.enrich_ai_btn.setToolTip("Dùng AI làm giàu hàng loạt chữ Hán (âm On/Kun, bộ thủ, mẹo nhớ)")
        self.enrich_ai_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ThemeColors.PRIMARY}, stop:1 {ThemeColors.ACCENT}); 
                color: white; font-weight: bold;
                padding: 6px 8px; border-radius: 4px; font-size: 12px;
            }}
            QPushButton:hover {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ThemeColors.PRIMARY_HOVER}, stop:1 {ThemeColors.ACCENT});
            }}
        """)
        self.enrich_ai_btn.clicked.connect(self._enrich_kanji_ai)
        search_layout.addWidget(self.enrich_ai_btn)
        
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
        search_layout.addWidget(self.reset_ai_btn)
        
        layout.addLayout(search_layout)
        
        # Splitter: Kanji list | Kanji details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Kanji grid/list
        list_panel = self._create_kanji_list_panel()
        splitter.addWidget(list_panel)
        
        # Right: Kanji details
        detail_panel = self._create_kanji_detail_panel()
        splitter.addWidget(detail_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)
        
        self.content_stack.addWidget(browse_container)
        
        # --- Page 1: Study Mode ---
        self.study_widget = self._create_study_content()
        self.content_stack.addWidget(self.study_widget)
        
        return self.content_stack
    
    def _create_kanji_list_panel(self) -> QWidget:
        """Create the kanji list/grid panel.
        
        Returns:
            List panel widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Kanji grid display
        self.kanji_grid = QListWidget()
        self.kanji_grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.kanji_grid.setIconSize(self.kanji_grid.iconSize())
        self.kanji_grid.setSpacing(5)
        self.kanji_grid.setStyleSheet(f"""
            QListWidget {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 5px;
            }}
            QListWidget::item {{
                background-color: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 5px;
                padding: 10px;
                margin: 3px;
                font-size: 24px;
                min-width: 50px;
                min-height: 50px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.PRIMARY_LIGHT};
                border: 2px solid {ThemeColors.PRIMARY};
                color: {ThemeColors.PRIMARY};
            }}
        """)
        self.kanji_grid.itemClicked.connect(self._load_kanji)
        self.kanji_grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.kanji_grid.customContextMenuRequested.connect(self._show_kanji_context_menu)
        layout.addWidget(self.kanji_grid, 1)
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("⬅️")
        self.prev_btn.setToolTip("Trang trước")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.clicked.connect(self._prev_page)
        self.prev_btn.setEnabled(False)
        
        self.next_btn = QPushButton("➡️")
        self.next_btn.setToolTip("Trang sau")
        self.next_btn.setFixedWidth(40)
        self.next_btn.clicked.connect(self._next_page)
        self.next_btn.setEnabled(False)
        
        self.page_label = QLabel("Hiển thị 0 kanji")
        self.page_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY};")
        
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label, 1, Qt.AlignmentFlag.AlignCenter)
        pagination_layout.addWidget(self.next_btn)
        
        layout.addLayout(pagination_layout)
        
        return widget
    
    def _create_kanji_detail_panel(self) -> QWidget:
        """Create the kanji detail panel.
        
        Returns:
            Detail panel widget
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Big kanji display
        self.kanji_display = QLabel("漢")
        self.kanji_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.kanji_display.setStyleSheet(f"""
            QLabel {{
                font-size: 120px;
                font-family: 'Noto Sans JP', 'Yu Gothic', sans-serif;
                background-color: {ThemeColors.BG_SECONDARY};
                border: 2px solid {ThemeColors.BORDER};
                border-radius: 10px;
                padding: 20px;
                min-height: 150px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.kanji_display)
        
        # Readings section
        readings_group = QGroupBox("📖 Cách đọc")
        readings_layout = QGridLayout(readings_group)
        
        readings_layout.addWidget(QLabel("音読み (Onyomi):"), 0, 0)
        self.onyomi_label = QLabel("-")
        self.onyomi_label.setStyleSheet(f"font-size: 18px; color: {ThemeColors.DANGER};")
        readings_layout.addWidget(self.onyomi_label, 0, 1)
        
        readings_layout.addWidget(QLabel("訓読み (Kunyomi):"), 1, 0)
        self.kunyomi_label = QLabel("-")
        self.kunyomi_label.setStyleSheet(f"font-size: 18px; color: {ThemeColors.PRIMARY};")
        readings_layout.addWidget(self.kunyomi_label, 1, 1)
        
        readings_layout.addWidget(QLabel("Hán Việt:"), 2, 0)
        self.hanviet_label = QLabel("-")
        self.hanviet_label.setStyleSheet(f"font-size: 18px; color: {ThemeColors.SUCCESS}; font-weight: bold;")
        readings_layout.addWidget(self.hanviet_label, 2, 1)
        
        layout.addWidget(readings_group)
        
        # Meaning section
        meaning_group = QGroupBox("💡 Nghĩa")
        meaning_layout = QVBoxLayout(meaning_group)
        
        self.meaning_label = QLabel("-")
        self.meaning_label.setWordWrap(True)
        self.meaning_label.setStyleSheet("font-size: 16px;")
        meaning_layout.addWidget(self.meaning_label)
        
        layout.addWidget(meaning_group)
        
        # Components/Radicals section
        components_group = QGroupBox("🧩 Bộ thủ / Thành phần")
        components_layout = QVBoxLayout(components_group)
        
        self.components_label = QLabel("-")
        self.components_label.setWordWrap(True)
        components_layout.addWidget(self.components_label)
        
        self.mnemonic_label = QLabel("")
        self.mnemonic_label.setWordWrap(True)
        self.mnemonic_label.setStyleSheet("color: #666; font-style: italic;")
        components_layout.addWidget(self.mnemonic_label)
        
        layout.addWidget(components_group)
        
        # Example words section
        vocab_group = QGroupBox("📝 Từ vựng mẫu")
        vocab_layout = QVBoxLayout(vocab_group)
        
        self.vocab_list = QTextBrowser()
        self.vocab_list.setMaximumHeight(150)
        self.vocab_list.setStyleSheet("background: #f9f9f9;")
        vocab_layout.addWidget(self.vocab_list)
        
        layout.addWidget(vocab_group)
        
        # SRS info
        srs_group = QGroupBox("📊 Tiến độ học (SRS)")
        srs_layout = QGridLayout(srs_group)
        
        srs_layout.addWidget(QLabel("Trạng thái:"), 0, 0)
        self.status_label = QLabel("🆕 Mới")
        srs_layout.addWidget(self.status_label, 0, 1)
        
        srs_layout.addWidget(QLabel("SRS Level:"), 1, 0)
        self.srs_level_label = QLabel("0")
        srs_layout.addWidget(self.srs_level_label, 1, 1)
        
        srs_layout.addWidget(QLabel("Ôn tập tiếp:"), 2, 0)
        self.next_review_label = QLabel("-")
        srs_layout.addWidget(self.next_review_label, 2, 1)
        
        layout.addWidget(srs_group)
        
        # ===== AI Enrichment Section =====
        ai_layout = QHBoxLayout()
        self.kanji_ai_enrich_btn = QPushButton("✨ AI Làm giàu")
        self.kanji_ai_enrich_btn.setToolTip("Dùng AI cải thiện nghĩa, âm On/Kun và thêm mẹo nhớ")
        self.kanji_ai_enrich_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #DB2777);
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6D28D9, stop:1 #BE185D);
            }
            QPushButton:disabled {
                background: #ccc;
                color: #888;
            }
        """)
        self.kanji_ai_enrich_btn.clicked.connect(self._enrich_selected_kanji)
        ai_layout.addWidget(self.kanji_ai_enrich_btn)
        
        layout.addLayout(ai_layout)
        
        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def _create_study_content(self) -> QWidget:
        """Create the study mode content (Anki-style flashcard).
        
        Returns:
            Study widget
        """
        widget = QWidget()
        widget.setStyleSheet("background-color: #2c3e50;")
        layout = QVBoxLayout(widget)
        
        # Progress bar
        progress_layout = QHBoxLayout()
        
        self.study_progress = QProgressBar()
        self.study_progress.setStyleSheet("""
            QProgressBar {
                background-color: #34495e;
                border-radius: 5px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.study_progress, 1)
        
        self.study_counter = QLabel("0 / 0")
        self.study_counter.setStyleSheet("color: white; font-size: 14px;")
        progress_layout.addWidget(self.study_counter)
        
        self.exit_study_btn = QPushButton("✕ Thoát")
        self.exit_study_btn.setStyleSheet("background: #e74c3c; color: white; padding: 5px 10px;")
        self.exit_study_btn.clicked.connect(self._exit_study_mode)
        progress_layout.addWidget(self.exit_study_btn)
        
        layout.addLayout(progress_layout)
        
        # Flashcard area
        self.flashcard = KanjiFlashcardView()
        layout.addWidget(self.flashcard, 1)
        
        # Action buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)
        
        # Show Answer button
        self.show_answer_btn = QPushButton("Hiện đáp án")
        self.show_answer_btn.setShortcut("Space")
        self.show_answer_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 20px 60px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.show_answer_btn.clicked.connect(self._show_answer)
        button_layout.addWidget(self.show_answer_btn)
        
        # Rating buttons (hidden initially)
        self.rating_widget = QWidget()
        rating_layout = QHBoxLayout(self.rating_widget)
        rating_layout.setSpacing(10)
        
        # Again (1)
        self.again_btn = QPushButton("❌ Lại\n<1m")
        self.again_btn.setShortcut("1")
        self.again_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 15px 25px;
                font-size: 14px;
                border-radius: 8px;
            }
        """)
        self.again_btn.clicked.connect(lambda: self._rate_card(1))
        rating_layout.addWidget(self.again_btn)
        
        # Hard (2)
        self.hard_btn = QPushButton("🟠 Khó\n<10m")
        self.hard_btn.setShortcut("2")
        self.hard_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 15px 25px;
                font-size: 14px;
                border-radius: 8px;
            }
        """)
        self.hard_btn.clicked.connect(lambda: self._rate_card(2))
        rating_layout.addWidget(self.hard_btn)
        
        # Good (3)
        self.good_btn = QPushButton("🟢 Tốt\n1d")
        self.good_btn.setShortcut("3")
        self.good_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 15px 25px;
                font-size: 14px;
                border-radius: 8px;
            }
        """)
        self.good_btn.clicked.connect(lambda: self._rate_card(3))
        rating_layout.addWidget(self.good_btn)
        
        # Easy (4)
        self.easy_btn = QPushButton("⭐ Dễ\n4d")
        self.easy_btn.setShortcut("4")
        self.easy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 15px 25px;
                font-size: 14px;
                border-radius: 8px;
            }
        """)
        self.easy_btn.clicked.connect(lambda: self._rate_card(4))
        rating_layout.addWidget(self.easy_btn)
        
        self.rating_widget.hide()
        button_layout.addWidget(self.rating_widget)
        
        layout.addWidget(button_container)
        
        return widget
    
    # ============ DATA LOADING ============
    
    def _load_initial_data(self) -> None:
        """Load initial data on tab startup."""
        self._refresh_decks()
        self._update_stats()
        self._search_kanji()
        if hasattr(self, '_update_dashboard_wall'):
            self._update_dashboard_wall()
    
    def _refresh_decks(self) -> None:
        """Refresh deck list from database."""
        with Session(engine) as session:
            db_decks = session.exec(select(KanjiDeck)).all()
            self.decks = [deck.model_dump() for deck in db_decks]
        self._populate_deck_tree()
    
    def _populate_deck_tree(self) -> None:
        """Populate the deck tree widget."""
        self.deck_tree.clear()
        
        # All kanji item
        all_item = QTreeWidgetItem(["📋 Tất cả Kanji"])
        all_item.setData(0, Qt.ItemDataRole.UserRole, None)
        self.deck_tree.addTopLevelItem(all_item)
        
        # Add decks
        for deck in self.decks:
            icon = deck.get('icon', '📁')
            name = deck.get('name', 'Unknown')
            
            item = QTreeWidgetItem([f"{icon} {name}"])
            item.setData(0, Qt.ItemDataRole.UserRole, deck.get('id'))
            self.deck_tree.addTopLevelItem(item)
    
    def _update_stats(self) -> None:
        """Update today's study statistics."""
        with Session(engine) as session:
            new_count = len(session.exec(select(KanjiItem).where(KanjiItem.mastery_status == "new")).all())
            learning_count = len(session.exec(select(KanjiItem).where(KanjiItem.mastery_status == "learning")).all())
            review_count = len(session.exec(select(KanjiItem).where(KanjiItem.mastery_status == "reviewing")).all())
            
            self.new_count_label.setText(str(new_count))
            self.learning_count_label.setText(str(learning_count))
            self.review_count_label.setText(str(review_count))
            
            # Update Study Button Style (Dynamic)
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
                    padding: 15px; font-size: 16px; font-weight: bold; border-radius: 8px;
                }}
                QPushButton:hover {{ background-color: {hover_color}; }}
            """
            
            # In KanjiTab, 'review_count' are the cards due for SRS
            if review_count > 0:
                # Red highlight if cards are due
                self.study_now_btn_small.setStyleSheet(study_btn_style.format(color="#f44336", hover_color="#d32f2f"))
                self.study_btn.setStyleSheet(sidebar_study_style.format(color="#f44336", hover_color="#d32f2f"))
            else:
                # Blue/Green if no cards due
                self.study_now_btn_small.setStyleSheet(study_btn_style.format(color="#2196F3", hover_color="#1976D2"))
                self.study_btn.setStyleSheet(sidebar_study_style.format(color="#2ecc71", hover_color="#27ae60"))
    
    def _on_deck_selected(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle deck selection."""
        self.current_deck_id = item.data(0, Qt.ItemDataRole.UserRole)
        self._apply_filters(reset_pagination=True)
    
    def _apply_filters(self, reset_pagination: bool = True) -> None:
        """Apply current filters."""
        self._search_kanji(reset_pagination=reset_pagination)
    
    def _next_page(self) -> None:
        """Go to next page."""
        if self.current_offset + self.page_size < self.total_count:
            self.current_offset += self.page_size
            self._search_kanji(reset_pagination=False)
            
    def _prev_page(self) -> None:
        """Go to previous page."""
        if self.current_offset >= self.page_size:
            self.current_offset -= self.page_size
            self._search_kanji(reset_pagination=False)
    
    # ============ KANJI OPERATIONS ============
    
    def _search_kanji(self, reset_pagination: bool = False) -> None:
        """Search kanji from database."""
        if reset_pagination:
            self.current_offset = 0
            
        query_text = self.search_input.text().strip()
        status_filter = self.status_filter.currentData()
        
        # Use Service instead of direct SQL
        results, total = self.kanji_service.search_kanji(
            deck_id=self.current_deck_id,
            status=status_filter,
            query=query_text,
            offset=self.current_offset,
            limit=self.page_size
        )
        
        self.total_count = total
        self.kanji_list = results
        
        self._populate_kanji_grid(self.kanji_list)
        self._update_pagination_controls()

    def _update_pagination_controls(self) -> None:
        """Update pagination buttons and label."""
        self.prev_btn.setEnabled(self.current_offset > 0)
        self.next_btn.setEnabled(self.current_offset + self.page_size < self.total_count)
        
        start_idx = self.current_offset + 1 if self.total_count > 0 else 0
        end_idx = min(self.current_offset + self.page_size, self.total_count)
        
        current_page = (self.current_offset // self.page_size) + 1
        total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
        
        self.page_label.setText(
            f"Trang {current_page}/{total_pages} (Hiển thị {start_idx}-{end_idx} / {self.total_count})"
        )
    
    def _populate_kanji_grid(self, kanji_list: List[Dict[str, Any]]) -> None:
        """Populate kanji grid."""
        self.kanji_grid.clear()
        
        for kanji in kanji_list:
            char = kanji.get('kanji', '?')
            
            item = QListWidgetItem(char)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setData(Qt.ItemDataRole.UserRole, kanji.get('id'))
            item.setData(Qt.ItemDataRole.UserRole + 1, kanji)
            
            # Set tooltip
            tooltip = f"{char}\n{kanji.get('han_viet', '')}\n{kanji.get('meaning_vi', '')}"
            item.setToolTip(tooltip)
            
            self.kanji_grid.addItem(item)
        
        self.page_label.setText(f"Hiển thị {len(kanji_list)} kanji")
    
    def _load_kanji(self, item: QListWidgetItem) -> None:
        """Load kanji details."""
        kanji_data = item.data(Qt.ItemDataRole.UserRole + 1)
        if not kanji_data:
            return
        
        self.current_kanji_id = kanji_data.get('id')
        self.current_kanji_data = kanji_data
        self._display_kanji(kanji_data)
    
    def _display_kanji(self, kanji: Dict[str, Any]) -> None:
        """Display kanji details."""
        self.kanji_display.setText(kanji.get('kanji', '?'))
        AnimationService.fade_in(self.kanji_display)
        self.onyomi_label.setText(kanji.get('onyomi', '-'))
        self.kunyomi_label.setText(kanji.get('kunyomi', '-'))
        self.hanviet_label.setText(kanji.get('han_viet', '-'))
        self.meaning_label.setText(kanji.get('meaning_vi', '-'))
        
        # Components
        self.components_label.setText(kanji.get('components', 'Đang cập nhật...'))
        self.mnemonic_label.setText(kanji.get('mnemonic', ''))
        
        # Vocab examples
        vocab_html = ""
        with Session(engine) as session:
            vocabs = session.exec(select(KanjiVocab).where(KanjiVocab.kanji_id == kanji.get('id'))).all()
            if vocabs:
                vocab_html = "<ul>"
                for v in vocabs:
                    # Use getattr for safety in case of model/DB mismatches
                    word = getattr(v, 'word', '-')
                    reading = getattr(v, 'reading', '-')
                    han_viet = getattr(v, 'han_viet', '-')
                    meaning = getattr(v, 'meaning_vi', '-')
                    vocab_html += f"<li><b>{word}</b> ({reading}) - <i>{han_viet}</i>: {meaning}</li>"
                vocab_html += "</ul>"
            else:
                vocab_html = "<i>Không có từ vựng mẫu</i>"
        
        self.vocab_list.setHtml(vocab_html)
        
        # SRS status
        status = kanji.get('mastery_status', 'new')
        status_display = {
            'new': '🆕 Mới',
            'learning': '📖 Đang học',
            'reviewing': '🔄 Ôn tập',
            'mastered': '✅ Đã thuộc',
            'leech': '⚠️ Leech'
        }
        self.status_label.setText(status_display.get(status, status))
        self.srs_level_label.setText(str(kanji.get('srs_level', 0)))
        self.next_review_label.setText(kanji.get('next_review', 'Hôm nay'))
    
    def _add_new_kanji(self) -> None:
        """Add new kanji."""
        toast_info("Chức năng thêm kanji đang được phát triển!")
    
    def _add_deck(self) -> None:
        """Add new deck."""
        toast_info("Chức năng thêm bộ thẻ đang được phát triển!")
    
    def _import_deck(self) -> None:
        """Import deck from Word file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Chọn file Từ điển Kanji", "", "Word Files (*.docx)"
        )
        if not file_name:
            return
            
        # Show progress dialog
        self.progress_dialog = QProgressDialog("Đang nhập dữ liệu Kanji... (Có thể mất 1-2 phút)", "Hủy", 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        # Run in thread
        self.import_worker = ImportWorker(file_name)
        self.import_worker.finished.connect(self._on_import_success)
        self.import_worker.error.connect(self._on_import_error)
        self.import_worker.start()

    def _on_import_success(self, k: int, v: int) -> None:
        """Handle successful import."""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        toast_success(f"✅ Đã nhập {k} Kanji và {v} từ vựng mới!")
        self._load_initial_data() # Refresh UI

    def _on_import_error(self, err_msg: str) -> None:
        """Handle import error."""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        QMessageBox.critical(self, "Lỗi", f"❌ Có lỗi xảy ra khi nhập dữ liệu: {err_msg}")
    
    # ============ AI ENRICHMENT ============
    
    def _enrich_kanji_ai(self) -> None:
        """Enrich visible kanji list using AI."""
        if not self.kanji_list:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn hoặc tìm kiếm Kanji để làm giàu dữ liệu!")
            return
            
        # Filter out already enriched kanji unless they are missing the mnemonic
        kanjis_to_enrich = []
        for k in self.kanji_list:
            is_enriched = k.get('is_ai_enriched')
            has_mnemonic = bool(k.get('mnemonic') and k.get('mnemonic').strip())
            if not is_enriched or not has_mnemonic:
                kanjis_to_enrich.append(k.get('kanji'))
        
        skipped_count = len(self.kanji_list) - len(kanjis_to_enrich)
        
        if not kanjis_to_enrich:
            toast_info("Tất cả chữ Hán trong danh sách hiện tại đã được làm giàu bởi AI!")
            return
            
        msg = f"Bạn có muốn dùng AI để làm giàu dữ liệu cho {len(kanjis_to_enrich)} chữ Hán chưa được xử lý không?\n"
        if skipped_count > 0:
            msg += f"(Đã tự động bỏ qua {skipped_count} chữ đã làm giàu rồi)\n"
        msg += "⚠️ Quá trình này sẽ gửi yêu cầu theo nhóm (50 chữ Hán/lần) để tiết kiệm RPD tối đa."
            
        reply = QMessageBox.question(
            self, "Xác nhận", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
            
        # Show progress
        self.progress_dialog = QProgressDialog("Đang kết nối AI...", "Hủy", 0, len(kanjis_to_enrich), self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        # Start worker
        self.enrich_worker = KanjiEnrichWorker(kanjis_to_enrich)
        self.enrich_worker.progress.connect(lambda cur, tot: self.progress_dialog.setValue(cur))
        self.enrich_worker.finished.connect(self._on_enrich_success)
        self.enrich_worker.error.connect(self._on_enrich_error)
        self.enrich_worker.start()

    def _on_enrich_success(self, count: int) -> None:
        """Handle successful AI enrichment."""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        toast_success(f"✅ Đã làm giàu dữ liệu AI cho {count} chữ Hán!")
        self._search_kanji() # Refresh current view

    def _on_enrich_error(self, err_msg: str) -> None:
        """Handle enrichment error."""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        QMessageBox.critical(self, "Lỗi AI", f"❌ Lỗi khi làm giàu dữ liệu: {err_msg}")

    # ============ STUDY SESSION (Anki-style) ============
    
    def _start_study_session(self) -> None:
        """Start a study session with currently loaded list."""
        self._launch_study_with_items(self.kanji_list if hasattr(self, 'kanji_list') else [])

    def _start_smart_review(self) -> None:
        """Smart Mode: Review items (Review, Learning, Leech)."""
        with Session(engine) as session:
            # Prioritize: Reviewing > Learning > Leech
            # TODO: Use next_review_at logic properly. For now, just status.
            statement = select(KanjiItem).where(
                or_(
                    KanjiItem.mastery_status == KanjiMasteryStatus.REVIEWING.value,
                    KanjiItem.mastery_status == KanjiMasteryStatus.LEARNING.value,
                    KanjiItem.mastery_status == KanjiMasteryStatus.LEECH.value
                )
            ).limit(20) # Limit review batch size to 20 for focus
            items = session.exec(statement).all()
            
            if not items:
                # If no review, try getting some 'Mastered' ones that haven't been seen in a while?
                # For now just toast
                toast_info("Bạn đã hoàn thành bài ôn tập! Hãy thử học từ mới.")
                return
            
            kanji_list = [item.model_dump() for item in items]
            self._launch_study_with_items(kanji_list)

    def _start_smart_learn(self) -> None:
        """Smart Mode: Learn 5 new items."""
        with Session(engine) as session:
            statement = select(KanjiItem).where(
                KanjiItem.mastery_status == KanjiMasteryStatus.NEW.value
            ).limit(5)
            items = session.exec(statement).all()
            
            if not items:
                toast_info("Bạn đã học hết Kanji mới! Tuyệt vời.")
                return
            
            kanji_list = [item.model_dump() for item in items]
            self._launch_study_with_items(kanji_list)

    def _launch_study_with_items(self, items: List[Dict[str, Any]]) -> None:
        """Launch the study interface with a specific list of items."""
        if not items:
            toast_info("Không có kanji nào để học!")
            return
        
        # Prepare study queue
        self.study_queue = items
        self.current_study_index = 0
        self.is_answer_shown = False
        
        # Switch to study mode
        # If we are in Dashboard mode (index 0), switch to Browse/Study Stack (index 1)
        # And ensure Browse/Study Stack is on Study Page (index 1)
        self.view_stack.setCurrentIndex(1)
        
        # Access the study widget inside the browse_widget (which might be complicated if browse_widget is just a wrapper)
        # Wait, in _init_ui:
        # self.content_stack = QStackedWidget() inside browse_page???
        # No, in previous refactor:
        # self.view_stack includes:
        # 0: Smart Dashboard
        # 1: Browse Widget (which contains self.content_stack)
        
        # Browse Widget creation:
        # self.content_stack = QStackedWidget()
        # self.content_stack.addWidget(self.browse_widget) # View Mode
        # self.content_stack.addWidget(self.study_widget) # Study Mode
        
        # So we need to:
        # 1. Show View 1 (Browse Widget Container)
        # 2. Inside Browse Widget Container, Show Index 1 (Study Widget)
        
        self.view_stack.setCurrentIndex(1)
        if hasattr(self, 'content_stack'):
            self.content_stack.setCurrentIndex(1)
        
        # Update progress
        self._update_study_progress()
        
        # Show first card
        self._show_current_card()
    
    def _show_current_card(self) -> None:
        """Show current study card."""
        if self.current_study_index >= len(self.study_queue):
            self._finish_study_session()
            return
        
        kanji = self.study_queue[self.current_study_index]
        self.flashcard.set_card(kanji)
        
        # Hide ratings, show "Show Answer" button
        self.rating_widget.hide()
        self.show_answer_btn.show()
        
        self.is_answer_shown = False
    
    def _show_answer(self) -> None:
        """Show card answer."""
        if not self.is_answer_shown:
            self.flashcard.flip()
            self.show_answer_btn.hide()
            self.rating_widget.show()
            self.is_answer_shown = True
    
    def _rate_card(self, rating: int) -> None:
        """Rate the current card.
        
        Args:
            rating: 1=Again, 2=Hard, 3=Good, 4=Easy
        """
        kanji = self.study_queue[self.current_study_index]
        kanji_id = kanji.get('id')
        
        # Submit rating to backend service
        async def submit():
            return self.kanji_service.submit_review(kanji_id, rating)
        
        run_async(submit, lambda _: None)
        
        # Move to next card
        self.current_study_index += 1
        self._update_study_progress()
        self._show_current_card()
    
    def _update_study_progress(self) -> None:
        """Update study progress bar."""
        total = len(self.study_queue)
        current = self.current_study_index
        
        self.study_progress.setMaximum(total)
        self.study_progress.setValue(current)
        self.study_counter.setText(f"{current} / {total}")
    
    def _finish_study_session(self) -> None:
        """Finish study session."""
        toast_success(
            f"🎉 Hoàn thành! Bạn đã hoàn thành {len(self.study_queue)} thẻ! Tiếp tục luyện tập mỗi ngày."
        )
        self._exit_study_mode()
    
    def _exit_study_mode(self) -> None:
        """Exit study mode and return to dashboard."""
        # Return to Dashboard view
        if hasattr(self, 'view_stack'):
            self.view_stack.setCurrentIndex(0)
            
        self._update_stats()
        # Refresh gamification wall
        if hasattr(self, '_update_dashboard_wall'):
            self._update_dashboard_wall()
    
    # ============ CONTEXT MENUS ============
    
    def _show_kanji_context_menu(self, position: QPoint) -> None:
        """Show context menu for kanji grid."""
        item = self.kanji_grid.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Status change
        status_menu = menu.addMenu("🎯 Đổi trạng thái")
        for status in KanjiMasteryStatus:
            icons = {'new': '🆕', 'learning': '📖', 'reviewing': '🔄', 'mastered': '✅', 'leech': '⚠️'}
            action = QAction(f"{icons.get(status.value, '')} {status.value.title()}", self)
            action.triggered.connect(lambda _, s=status: self._change_kanji_status(item, s))
            status_menu.addAction(action)
        
        menu.addSeparator()
        
        # Move to deck
        move_menu = menu.addMenu("📚 Chuyển sang bộ thẻ")
        for deck in self.decks:
            action = QAction(f"{deck.get('icon', '')} {deck.get('name', '')}", self)
            action.triggered.connect(lambda _, d=deck: self._move_to_deck(item, d))
            move_menu.addAction(action)
        
        menu.addSeparator()
        
        # Delete
        delete_action = QAction("❌ Xóa", self)
        delete_action.triggered.connect(lambda: self._delete_kanji(item))
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Reset AI
        reset_ai_action = QAction("🔄 Reset AI Enrichment", self)
        reset_ai_action.triggered.connect(lambda: self._reset_kanji_ai(item))
        menu.addAction(reset_ai_action)
        
        menu.exec(self.kanji_grid.mapToGlobal(position))
    
    def _change_kanji_status(self, item: QListWidgetItem, status: KanjiMasteryStatus) -> None:
        """Change kanji status."""
        kanji_id = item.data(Qt.ItemDataRole.UserRole)
        
        async def update():
            return self.kanji_service.change_status(kanji_id, status.value)
        
        run_async(update, lambda success: self._search_kanji() if success else None)
    
    def _move_to_deck(self, item: QListWidgetItem, deck: Dict[str, Any]) -> None:
        """Move kanji to another deck."""
        kanji_id = item.data(Qt.ItemDataRole.UserRole)
        print(f"[TODO] Move kanji {kanji_id} to deck {deck.get('name')}")

    def _reset_kanji_ai(self, item: QListWidgetItem) -> None:
        """Reset AI enrichment status for a single kanji."""
        kanji_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            with Session(engine) as session:
                db_item = session.get(KanjiItem, kanji_id)
                if db_item:
                    db_item.is_ai_enriched = False
                    session.add(db_item)
                    session.commit()
                    toast_success(f"Đã reset trạng thái AI cho: {db_item.kanji}")
                    self._apply_filters(reset_pagination=False)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể reset AI: {e}")

    def _reset_all_visible_ai(self) -> None:
        """Reset AI enrichment status for all currently visible kanji."""
        if not self.kanji_list:
            return
            
        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Bạn có muốn reset trạng thái AI cho {len(self.kanji_list)} chữ Hán đang hiển thị không?\n"
            "(Thẻ sẽ được AI làm giàu lại vào lần tới)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
            
        try:
            with Session(engine) as session:
                for k in self.kanji_list:
                    kanji_id = k.get('id')
                    db_item = session.get(KanjiItem, kanji_id)
                    if db_item:
                        db_item.is_ai_enriched = False
                        session.add(db_item)
                session.commit()
                toast_success(f"Đã reset trạng thái AI cho {len(self.kanji_list)} chữ Hán.")
                self._apply_filters(reset_pagination=False)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể reset AI: {e}")
    
    def _delete_kanji(self, item: QListWidgetItem) -> None:
        """Delete kanji."""
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            "Bạn có chắc muốn xóa kanji này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            row = self.kanji_grid.row(item)
            self.kanji_grid.takeItem(row)
    def _enrich_selected_kanji(self):
        """Enrich the selected Kanji with AI."""
        if not self.current_kanji_id or not self.current_kanji_data:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một chữ Hán để làm giàu")
            return
            
        kanji_char = self.current_kanji_data.get("kanji")
        if not kanji_char:
            return
            
        self.kanji_ai_enrich_btn.setEnabled(False)
        self.kanji_ai_enrich_btn.setText("⏳ Đang xử lý...")
        
        from frontend.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        
        async def enrich():
            # Use the batch method but with single kanji for now, 
            # or I'll add a specific method to ai_service shortly
            return await ai_service.enrich_kanji_batch([kanji_char])
            
        def on_enriched(result):
            self.kanji_ai_enrich_btn.setEnabled(True)
            self.kanji_ai_enrich_btn.setText("✨ AI Làm giàu")
            
            if result.get("success"):
                results = result.get("results", {})
                if kanji_char in results:
                    data = results[kanji_char]
                    with Session(engine) as session:
                        item = session.get(KanjiItem, self.current_kanji_id)
                        if item:
                            if data.get("meaning_vi"): item.meaning_vi = data["meaning_vi"]
                            if data.get("han_viet"): item.han_viet = data["han_viet"].upper()
                            if data.get("onyomi"): item.onyomi = data["onyomi"]
                            if data.get("kunyomi"): item.kunyomi = data["kunyomi"]
                            if data.get("radicals"): item.radicals = data["radicals"]
                            if data.get("components"): item.components = data["components"]
                            if data.get("mnemonic"): item.mnemonic = data["mnemonic"]
                            item.is_ai_enriched = True
                            
                            # Handle vocabulary enrichment
                            ai_vocab = data.get("vocabulary", [])
                            if ai_vocab:
                                # Optional: Clear existing vocabs for this kanji before adding new AI ones
                                from sqlmodel import delete
                                session.exec(delete(KanjiVocab).where(KanjiVocab.kanji_id == item.id))
                                
                                for v in ai_vocab:
                                    new_vocab = KanjiVocab(
                                        kanji_id=item.id,
                                        word=v.get("word", ""),
                                        reading=v.get("reading", ""),
                                        han_viet=v.get("han_viet", ""),
                                        meaning_vi=v.get("meaning", ""),
                                        is_common=True
                                    )
                                    session.add(new_vocab)
                            
                            session.add(item)
                            session.commit()
                            
                            # Refresh item from DB with relationships
                            session.refresh(item)
                            
                            toast_success(f"Đã làm giàu chữ Hán '{kanji_char}' cùng {len(ai_vocab)} từ vựng mẫu!")
                            
                            # Reload entry to update UI
                            self.current_kanji_data = item.model_dump()
                            self._display_kanji(self.current_kanji_data)
                            
                            # Also update the list item in the grid for tooltips and consistency
                            curr_item = self.kanji_grid.currentItem()
                            if curr_item and curr_item.data(Qt.ItemDataRole.UserRole) == self.current_kanji_id:
                                curr_item.setData(Qt.ItemDataRole.UserRole + 1, self.current_kanji_data)
                                tooltip = f"{kanji_char}\n{item.han_viet}\n{item.meaning_vi}"
                                curr_item.setToolTip(tooltip)
                        else:
                            QMessageBox.warning(self, "Lỗi", "Không tìm thấy Kanji trong CSDL")

                else:
                    QMessageBox.warning(self, "Lỗi AI", "AI không trả về dữ liệu cho chữ Hán này")
            else:
                QMessageBox.warning(self, "Lỗi AI", result.get("error", "Lỗi không xác định"))
                
        run_async(enrich, on_enriched)
