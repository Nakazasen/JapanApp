"""Reading tab for book reading feature."""
# Standard library
import json
from pathlib import Path
from typing import Optional, Dict, List

# Third-party
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QTextBrowser, QComboBox, QFileDialog, QMessageBox, QSlider,
    QProgressBar, QSplitter, QFrame, QScrollArea, QDialog,
    QLineEdit, QTabWidget, QGroupBox, QCheckBox, QListWidget
)
from PySide6.QtCore import Qt, QTimer, QUrl, QPoint
from PySide6.QtGui import QTextCursor, QAction, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# Local
from frontend.services.reading_service import get_reading_service
from frontend.services.tts import TTSService, get_tts_service
from frontend.services import get_vocab_service
from frontend.services.reading.tts.tts_factory import TTSFactory
from frontend.services.dictionary_service import DictionaryService
from frontend.ui.widgets.dictionary_dialog import DictionaryLookupDialog
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin
from frontend.utils.async_helpers import run_async
from frontend.utils.language_utils import detect_language
from frontend.utils.language_utils import detect_language
from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning
from frontend.ui.styles.theme import ThemeColors



# Default settings
DEFAULT_SETTINGS = {
    "font_size": 14,
    "font_family": "Arial",
    "background_color": "#FFFFFF",
    "text_color": "#000000",
    "night_mode": False,
    "night_bg_color": "#1E1E1E",
    "night_text_color": "#E0E0E0",
    "tts_enabled": True,
    "tts_voice": "female",
    "tts_speed": 150,
    "tts_engine": "pyttsx3",
    "tts_voice_id": None,
    "tts_voice_name": "",
    "remember_position": True,
}


class SettingsDialog(QDialog):
    """Settings dialog for reading tab."""
    
    def __init__(self, parent=None, settings=None, voice_loader=None):
        super().__init__(parent)
        self.settings = settings or DEFAULT_SETTINGS.copy()
        self.voice_loader = voice_loader
        self.current_voice_options: List[Dict[str, str]] = []
        self._pending_voice_id: Optional[str] = None
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        self.setWindowTitle("Cài đặt")
        self.setMinimumWidth(420)
        
        layout = QVBoxLayout()
        
        # Font settings
        font_group = QGroupBox("Font chữ")
        font_layout = QVBoxLayout()
        
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(10)
        self.font_size_slider.setMaximum(30)
        self.font_size_label = QLabel("Cỡ chữ: 14")
        font_layout.addWidget(self.font_size_label)
        font_layout.addWidget(self.font_size_slider)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Night mode
        self.night_mode_checkbox = QCheckBox("Chế độ ban đêm")
        layout.addWidget(self.night_mode_checkbox)
        
        # TTS settings
        tts_group = QGroupBox("Text-to-Speech")
        tts_layout = QVBoxLayout()
        
        tts_info = QLabel("💡 Pyttsx3: dùng giọng cài sẵn trong Windows (offline).\n"
                          "💡 gTTS: giọng Google (cần internet, tối ưu tiếng Việt).")
        tts_info.setWordWrap(True)
        tts_info.setStyleSheet(f"color: {ThemeColors.ACCENT}; font-style: italic;")
        tts_layout.addWidget(tts_info)
        
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItem("pyttsx3 (Offline - Windows voices)", "pyttsx3")
        self.tts_engine_combo.addItem("gTTS (Google TTS - Tiếng Việt)", "gtts")
        self.tts_engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        tts_layout.addWidget(QLabel("TTS Engine:"))
        tts_layout.addWidget(self.tts_engine_combo)
        
        self.tts_voice_combo = QComboBox()
        tts_layout.addWidget(QLabel("Giọng đọc:"))
        tts_layout.addWidget(self.tts_voice_combo)
        
        self.tts_speed_slider = QSlider(Qt.Horizontal)
        self.tts_speed_slider.setMinimum(50)
        self.tts_speed_slider.setMaximum(300)
        self.tts_speed_label = QLabel("Tốc độ: 150")
        tts_layout.addWidget(self.tts_speed_label)
        tts_layout.addWidget(self.tts_speed_slider)
        
        self.font_size_slider.valueChanged.connect(
            lambda v: self.font_size_label.setText(f"Cỡ chữ: {v}")
        )
        self.tts_speed_slider.valueChanged.connect(
            lambda v: self.tts_speed_label.setText(f"Tốc độ: {v}")
        )
        
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Hủy")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _on_engine_changed(self, index):
        engine_type = self.tts_engine_combo.itemData(index)
        self._populate_voice_combo(engine_type, self._pending_voice_id)
        self._pending_voice_id = None
    
    def _populate_voice_combo(self, engine_type: str, selected_voice_id: Optional[str] = None):
        voices = self.voice_loader(engine_type) if self.voice_loader else []
        self.current_voice_options = voices
        self.tts_voice_combo.clear()
        
        if not voices:
            self.tts_voice_combo.addItem("Mặc định hệ thống", "")
            self.tts_voice_combo.setEnabled(False)
            return
        
        self.tts_voice_combo.setEnabled(True)
        for voice in voices:
            label = voice.get("name") or voice.get("id") or "Voice"
            lang = voice.get("lang")
            if lang:
                label = f"{label} ({lang})"
            self.tts_voice_combo.addItem(label, voice.get("id"))
        
        if selected_voice_id:
            idx = self.tts_voice_combo.findData(selected_voice_id)
            if idx >= 0:
                self.tts_voice_combo.setCurrentIndex(idx)
    
    def load_settings(self):
        self.font_size_slider.setValue(self.settings.get("font_size", 14))
        self.night_mode_checkbox.setChecked(self.settings.get("night_mode", False))
        self.tts_speed_slider.setValue(self.settings.get("tts_speed", 150))
        
        engine = self.settings.get("tts_engine", "pyttsx3")
        idx = self.tts_engine_combo.findData(engine)
        self._pending_voice_id = self.settings.get("tts_voice_id")
        if idx >= 0:
            self.tts_engine_combo.setCurrentIndex(idx)
        else:
            self.tts_engine_combo.setCurrentIndex(0)
            self._populate_voice_combo("pyttsx3", self._pending_voice_id)
            self._pending_voice_id = None
        
        if self._pending_voice_id:
            # Engine combo change may not trigger if already at same index
            self._populate_voice_combo(engine, self._pending_voice_id)
            self._pending_voice_id = None
    
    def get_settings(self):
        engine_type = self.tts_engine_combo.currentData()
        voice_id = self.tts_voice_combo.currentData()
        voice_name = self.tts_voice_combo.currentText() if voice_id else ""
        
        return {
            "font_size": self.font_size_slider.value(),
            "night_mode": self.night_mode_checkbox.isChecked(),
            "tts_engine": engine_type or "pyttsx3",
            "tts_voice": "custom" if voice_id else self.settings.get("tts_voice", "female"),
            "tts_voice_id": voice_id if voice_id else None,
            "tts_voice_name": voice_name,
            "tts_speed": self.tts_speed_slider.value(),
        }


class ReadingTab(QWidget, TextContextMenuMixin):
    """Reading tab for book reading - with context menu from mixin."""
    
    def __init__(self):
        super().__init__()
        self.reading_service = get_reading_service()
        self.current_book_id: Optional[int] = None
        self.current_chapter_id: Optional[int] = None
        self.current_chapter_index = 0
        self.book_data: Optional[Dict] = None
        self.tts_engine = None
        self.available_voices: List[Dict[str, str]] = []
        self._voice_cache: Dict[str, List[Dict[str, str]]] = {}
        self.dictionary_dialog: Optional[DictionaryLookupDialog] = None
        self._tts_media_player: Optional[QMediaPlayer] = None
        self._tts_audio_output: Optional[QAudioOutput] = None
        self._tts_temp_file: Optional[str] = None
        
        # Default to gTTS for better Vietnamese support
        if "tts_engine" not in DEFAULT_SETTINGS:
            DEFAULT_SETTINGS["tts_engine"] = "gtts"
        
        self.settings = DEFAULT_SETTINGS.copy()
        self.current_text_length = 0
        self.read_start_position = 0
        self.vocab_service = get_vocab_service()
        
        self._init_ui()
        self._refresh_available_voices(self.settings.get("tts_engine", "pyttsx3"))
        self._init_tts()
    
    def _init_ui(self):
        """Initialize UI - Focused E-Book Reader Edition."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setStyleSheet(f"""
            QWidget#ReadingTab {{ background-color: {ThemeColors.BG_PRIMARY}; }}
            QFrame#Sidebar {{ 
                background-color: {ThemeColors.BG_SECONDARY};
                border-right: 1px solid {ThemeColors.BORDER}; 
            }}
            QLabel#SidebarLabel {{ 
                font-size: 13px; font-weight: 900; color: {ThemeColors.ACCENT}; 
                margin-top: 15px; letter-spacing: 1px;
            }}
            QLabel#WhiteLabels {{ color: {ThemeColors.TEXT_PRIMARY}; }}
            
            QFrame#ControlBar {{ background: {ThemeColors.BG_SECONDARY}; border-bottom: 2px solid {ThemeColors.BORDER}; }}
            
            QPushButton#ActionBtn {{
                background-color: {ThemeColors.PRIMARY};
                color: {ThemeColors.TEXT_INVERSE}; border-radius: 8px; padding: 10px 20px; font-weight: bold;
                border: none;
            }}
            QPushButton#ActionBtn:hover {{ 
                background-color: {ThemeColors.PRIMARY_HOVER};
            }}
            
            QTextBrowser#BookEditor {{
                background: {ThemeColors.BG_SECONDARY}; 
                border: 1px solid {ThemeColors.BORDER}; 
                border-radius: 8px; 
                padding: 60px;
                font-size: 20px; 
                line-height: 1.8; 
                color: {ThemeColors.TEXT_PRIMARY};
                font-family: 'Georgia', 'Times New Roman', serif;
                selection-background-color: {ThemeColors.ACCENT};
                selection-color: white;
            }}
            
            QFrame#MediaCard {{
                background: {ThemeColors.BG_TERTIARY}; 
                border-radius: 12px; 
                padding: 15px; 
                border: 1px solid {ThemeColors.BORDER};
            }}
            
            QComboBox {{ 
                background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; border: 1px solid {ThemeColors.BORDER}; 
                border-radius: 8px; padding: 8px; 
            }}
            
            QListWidget {{ background: transparent; border: none; color: {ThemeColors.TEXT_SECONDARY}; outline: none; }}
            QListWidget::item {{ padding: 12px 15px; border-bottom: 1px solid {ThemeColors.BORDER}; }}
            QListWidget::item:selected {{ 
                background: {ThemeColors.BG_TERTIARY}; 
                color: {ThemeColors.PRIMARY}; 
                border-left: 4px solid {ThemeColors.PRIMARY};
                font-weight: bold;
            }}
            QListWidget::item:hover:!selected {{ background: {ThemeColors.BG_TERTIARY}; }}
            
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar::tab {{ 
                background: transparent; color: {ThemeColors.TEXT_SECONDARY}; padding: 10px 20px; font-weight: bold;
            }}
            QTabBar::tab:selected {{ 
                color: {ThemeColors.PRIMARY}; border-bottom: 2px solid {ThemeColors.PRIMARY}; 
            }}
        """)
        self.setObjectName("ReadingTab")

        # ========== SIDEBAR: Book Library & Nav ==========
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        # Book Selection
        sidebar_layout.addWidget(QLabel("📚 THƯ VIỆN SÁCH", objectName="SidebarLabel"))
        self.book_combo = QComboBox()
        self.book_combo.currentIndexChanged.connect(self._on_book_changed)
        sidebar_layout.addWidget(self.book_combo)
        
        self.upload_button = QPushButton("➕ Tải lên sách")
        self.upload_button.setObjectName("ActionBtn")
        self.upload_button.clicked.connect(self._upload_book)
        sidebar_layout.addWidget(self.upload_button)

        # Tabs for Chapters and Bookmarks
        self.nav_tabs = QTabWidget()
        
        # Chapter Tab
        chapter_tab = QWidget()
        chap_lay = QVBoxLayout(chapter_tab)
        chap_lay.setContentsMargins(0, 5, 0, 0)
        self.chapter_list = QListWidget()
        self.chapter_list.itemClicked.connect(self._on_chapter_selected)
        self.chapter_list.itemDoubleClicked.connect(self._on_chapter_double_clicked)
        chap_lay.addWidget(self.chapter_list)
        self.nav_tabs.addTab(chapter_tab, "Mục lục")
        
        # Bookmark Tab
        bookmark_tab = QWidget()
        bm_lay = QVBoxLayout(bookmark_tab)
        bm_lay.setContentsMargins(0, 5, 0, 0)
        self.bookmark_list = QListWidget()
        self.bookmark_list.itemClicked.connect(self._on_bookmark_selected)
        self.bookmark_list.itemDoubleClicked.connect(self._on_bookmark_double_clicked)
        bm_lay.addWidget(self.bookmark_list)
        self.nav_tabs.addTab(bookmark_tab, "Dấu trang")
        
        sidebar_layout.addWidget(self.nav_tabs, 1)
        
        # Audio Control Card
        sidebar_layout.addWidget(QLabel("🎧 TRÌNH ĐỌC (TTS)", objectName="SidebarLabel"))
        media_card = QFrame()
        media_card.setObjectName("MediaCard")
        media_lay = QVBoxLayout(media_card)
        
        ctrl_row = QHBoxLayout()
        self.tts_play_button = QPushButton("▶")  # Initialize button
        self.tts_play_button.setFixedSize(36, 36)
        self.tts_play_button.setStyleSheet(f"background: {ThemeColors.ACCENT}; border-radius: 18px; color: white; font-weight: bold;")
        self.tts_play_button.clicked.connect(self._toggle_tts)
        
        self.tts_pause_button = QPushButton("‖") # Initialize button
        self.tts_pause_button.setFixedSize(36, 36)
        self.tts_pause_button.setStyleSheet(f"background: {ThemeColors.SECONDARY}; border-radius: 18px; color: white;")
        self.tts_pause_button.clicked.connect(self._pause_tts)
        
        self.tts_stop_button = QPushButton("■") # Initialize button
        self.tts_stop_button.setFixedSize(36, 36)
        self.tts_stop_button.setStyleSheet(f"background: {ThemeColors.DANGER}; border-radius: 18px; color: white;")
        self.tts_stop_button.clicked.connect(self._stop_tts)
        
        ctrl_row.addWidget(self.tts_play_button)
        ctrl_row.addWidget(self.tts_pause_button)
        ctrl_row.addWidget(self.tts_stop_button)
        media_lay.addLayout(ctrl_row)
        
        self.tts_play_selection_button = QPushButton("📄 Đọc đoạn đã chọn")
        self.tts_play_selection_button.setStyleSheet(f"background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; border-radius: 6px; padding: 5px;")
        self.tts_play_selection_button.clicked.connect(self._read_selected_text)
        self.tts_play_selection_button.setEnabled(False)
        media_lay.addWidget(self.tts_play_selection_button)
        
        sidebar_layout.addWidget(media_card)
        
        main_layout.addWidget(sidebar)

        # ========== MAIN AREA: Reader ==========
        self.content_area = QWidget()
        content_main_layout = QVBoxLayout(self.content_area)
        content_main_layout.setContentsMargins(0, 0, 0, 0)
        content_main_layout.setSpacing(0)
        
        # Top Toolbar
        toolbar = QFrame()
        toolbar.setObjectName("ControlBar")
        toolbar.setFixedHeight(60)
        toolbar_lay = QHBoxLayout(toolbar)
        toolbar_lay.setContentsMargins(20, 0, 20, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm trong sách...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet(f"border-radius: 15px; padding: 5px 15px; background: {ThemeColors.BG_TERTIARY}; border: 1px solid {ThemeColors.BORDER}; color: {ThemeColors.TEXT_PRIMARY};")
        self.search_input.returnPressed.connect(self._search_text)
        toolbar_lay.addWidget(self.search_input)
        
        toolbar_lay.addStretch()
        
        self.bookmark_button = QPushButton("🔖 Đánh dấu trang")
        self.bookmark_button.setObjectName("ActionBtn")
        self.bookmark_button.clicked.connect(self._add_bookmark)
        toolbar_lay.addWidget(self.bookmark_button)
        
        self.settings_button = QPushButton("⚙️ Cài đặt")
        self.settings_button.setObjectName("ActionBtn")
        self.settings_button.clicked.connect(self._show_settings)
        toolbar_lay.addWidget(self.settings_button)
        
        content_main_layout.addWidget(toolbar)
        
        # Reading Workspace
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {ThemeColors.BG_SECONDARY};")
        
        reader_container = QWidget()
        reader_lay = QVBoxLayout(reader_container)
        reader_lay.setContentsMargins(40, 40, 40, 40)
        reader_lay.setAlignment(Qt.AlignCenter)
        
        # Slider section
        pos_lay = QHBoxLayout()
        pos_lay.addWidget(QLabel("Tiến độ:"))
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.valueChanged.connect(self._on_position_changed)
        self.position_slider.sliderReleased.connect(self._on_position_slider_released)
        pos_lay.addWidget(self.position_slider)
        self.position_label = QLabel("0%")
        pos_lay.addWidget(self.position_label)
        
        self.read_from_position_button = QPushButton("� Đọc từ đây")
        self.read_from_position_button.setFixedWidth(120)
        self.read_from_position_button.clicked.connect(self._read_from_current_position)
        self.read_from_position_button.setEnabled(False)
        pos_lay.addWidget(self.read_from_position_button)
        reader_lay.addLayout(pos_lay)
        
        # The Text
        self.content_text = QTextBrowser()
        self.content_text.setObjectName("BookEditor")
        self.content_text.setReadOnly(True)
        self.content_text.setFixedWidth(850)
        self.content_text.setMinimumHeight(1200)
        self.content_text.cursorPositionChanged.connect(self._on_cursor_position_changed)
        self.content_text.selectionChanged.connect(self._on_selection_changed)
        self.content_text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.content_text.customContextMenuRequested.connect(self._show_context_menu)
        self.content_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        self.content_text.setOpenLinks(False)
        self.content_text.anchorClicked.connect(self._on_anchor_clicked)
        reader_lay.addWidget(self.content_text)
        
        scroll.setWidget(reader_container)
        content_main_layout.addWidget(scroll)
        
        # Chapter Navigation Bottom Bar
        nav_bar = QFrame()
        nav_bar.setFixedHeight(50)
        nav_bar.setStyleSheet(f"background: {ThemeColors.BG_SECONDARY}; border-top: 1px solid {ThemeColors.BORDER};")
        nav_lay = QHBoxLayout(nav_bar)
        
        self.prev_chapter_button = QPushButton("◀ Chương trước")
        self.prev_chapter_button.clicked.connect(self._prev_chapter)
        self.prev_chapter_button.setEnabled(False)
        nav_lay.addWidget(self.prev_chapter_button)
        
        nav_lay.addStretch()
        self.selection_info_label = QLabel("Sẵn sàng")
        self.selection_info_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-style: italic;")
        nav_lay.addWidget(self.selection_info_label)
        nav_lay.addStretch()
        
        self.next_chapter_button = QPushButton("Chương sau ▶")
        self.next_chapter_button.clicked.connect(self._next_chapter)
        self.next_chapter_button.setEnabled(False)
        nav_lay.addWidget(self.next_chapter_button)
        
        content_main_layout.addWidget(nav_bar)
        
        main_layout.addWidget(self.content_area, 1)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        content_main_layout.addWidget(self.progress_bar)

        self._apply_settings()
        QTimer.singleShot(100, self._load_books)
    
    def _init_tts(self):
        """Initialize TTS engine with auto-fallback."""
        engine_type = self.settings.get("tts_engine", "gtts")  # Default to gTTS
        
        print(f"[reading_tab] _init_tts được gọi với engine_type: {engine_type}")
        
        # Try gTTS first (recommended for Vietnamese)
        if engine_type == "gtts":
            try:
                print("[reading_tab] Đang khởi tạo Google TTS (gTTS)...")
                self.tts_engine = TTSFactory.create_engine("gtts", lang="vi")
                print(f"[reading_tab] ✅ Khởi tạo gTTS thành công!")
            except Exception as e:
                print(f"[reading_tab] ⚠️ Không thể khởi tạo gTTS: {e}")
                print(f"[reading_tab] 🔄 Tự động chuyển sang Pyttsx3 (offline)...")
                try:
                    self.tts_engine = TTSFactory.create_engine("pyttsx3")
                    self.settings["tts_engine"] = "pyttsx3"  # Update settings
                    print(f"[reading_tab] ✅ Fallback sang Pyttsx3 thành công")
                except Exception as e2:
                    print(f"[reading_tab] ❌ Không thể khởi tạo Pyttsx3: {e2}")
                    self.tts_engine = None
        else:
            # User explicitly chose Pyttsx3
            try:
                print(f"[reading_tab] Đang khởi tạo Pyttsx3...")
                self.tts_engine = TTSFactory.create_engine("pyttsx3")
                print(f"[reading_tab] ✅ Khởi tạo Pyttsx3 thành công")
            except Exception as e:
                print(f"[reading_tab] ❌ Không thể khởi tạo Pyttsx3: {e}")
                self.tts_engine = None
        
        if self.tts_engine:
            print(f"[reading_tab] TTS engine đã khởi tạo: {type(self.tts_engine).__name__}")
            self.tts_engine.set_rate(self.settings.get("tts_speed", 150))
            voice_id = self.settings.get("tts_voice_id")
            if voice_id and hasattr(self.tts_engine, "set_voice_by_id"):
                self.tts_engine.set_voice_by_id(voice_id)
            else:
                self.tts_engine.set_voice(self.settings.get("tts_voice", "female"))
        else:
            print("[reading_tab] ❌ CẢNH BÁO: TTS engine là None! Không thể đọc văn bản.")

    def _refresh_available_voices(self, engine_type: Optional[str] = None):
        """Lấy và lưu cache danh sách giọng đọc khả dụng."""
        engine_key = (engine_type or self.settings.get("tts_engine", "pyttsx3")).lower()
        voices = self._voice_cache.get(engine_key)
        
        if voices is None:
            try:
                voices = TTSFactory.get_available_voices(engine_key)
            except Exception as e:
                print(f"[reading_tab] Không thể lấy danh sách giọng cho {engine_key}: {e}")
                voices = []
            self._voice_cache[engine_key] = voices
        
        current_engine = (self.settings.get("tts_engine", "pyttsx3") or "pyttsx3").lower()
        if engine_key == current_engine:
            self.available_voices = voices
        
        return voices

    def _get_voice_options(self, engine_type: str):
        """Helper cho SettingsDialog lấy danh sách giọng."""
        return self._refresh_available_voices(engine_type)
    
    def _apply_settings(self):
        """Apply settings to UI."""
        font_size = self.settings.get("font_size", 14)
        font = QFont("Arial", font_size)
        self.content_text.setFont(font)
        
        night_mode = self.settings.get("night_mode", False)
        if night_mode:
            self.content_text.setStyleSheet(
                f"background-color: {self.settings.get('night_bg_color', '#1E1E1E')}; "
                f"color: {self.settings.get('night_text_color', '#E0E0E0')};"
            )
        else:
            self.content_text.setStyleSheet(
                f"background-color: {self.settings.get('background_color', '#FFFFFF')}; "
                f"color: {self.settings.get('text_color', '#000000')};"
            )
    
    def _load_books(self):
        """Load user's books."""
        async def load():
            try:
                # reading_service.get_books is sync (no await)
                return self.reading_service.get_books()
            except Exception as e:
                print(f"Error loading books: {e}")
                return []
        
        def update_ui(books):
            self.book_combo.clear()
            for book in books:
                self.book_combo.addItem(book['title'], book['id'])
        
        run_async(load, update_ui)
    
    def _upload_book(self):
        """Upload book file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Mở file sách",
            "",
            "All Supported (*.epub *.mobi *.prc *.azw3 *.docx *.xlsx *.pptx);;EPUB (*.epub);;MOBI (*.mobi *.prc);;AZW3 (*.azw3);;Word (*.docx);;Excel (*.xlsx);;PowerPoint (*.pptx)"
        )
        
        if file_path:
            async def upload():
                try:
                    # reading_service.upload_book is sync
                    return self.reading_service.upload_book(file_path)
                except Exception as e:
                    return {"error": str(e)}
            
            def update_ui(result):
                if "error" in result:
                    QMessageBox.critical(self, "Lỗi", f"Không thể tải lên sách:\n{result['error']}")
                else:
                    toast_success("Đã tải lên và phân tích sách thành công!")
                    self._load_books()
            
            run_async(upload, update_ui)
    
    def _on_book_changed(self, index):
        """Handle book selection change."""
        if index >= 0:
            book_id = self.book_combo.currentData()
            if book_id:
                self._load_book(book_id)
    
    def _load_book(self, book_id: int):
        """Load book data."""
        async def load():
            try:
                # reading_service.get_book is sync
                return self.reading_service.get_book(book_id)
            except Exception as e:
                return {"error": str(e)}
        
        def update_ui(book_data):
            if "error" in book_data:
                QMessageBox.critical(self, "Lỗi", f"Không thể tải sách:\n{book_data['error']}")
                return
            
            self.current_book_id = book_id
            self.book_data = book_data
            
            # Load chapters
            self.chapter_list.clear()
            for chapter in book_data.get("chapters", []):
                self.chapter_list.addItem(f"{chapter['chapter_index'] + 1}. {chapter['title']}")
            
            # Load reading position
            self._load_reading_position()
            
            # Load bookmarks
            self._load_bookmarks()
            
            # Enable/disable buttons
            total_chapters = len(book_data.get("chapters", []))
            self.prev_chapter_button.setEnabled(total_chapters > 1)
            self.next_chapter_button.setEnabled(total_chapters > 1)
        
        run_async(load, update_ui)
    
    def _load_chapter(self, chapter_id: int, start_position: int = 0):
        """Load chapter content."""
        if not self.current_book_id:
            return
        
        async def load():
            try:
                # reading_service.get_chapter is sync
                return self.reading_service.get_chapter(self.current_book_id, chapter_id)
            except Exception as e:
                return {"error": str(e)}
        
        def update_ui(chapter_data):
            if "error" in chapter_data:
                QMessageBox.critical(self, "Lỗi", f"Không thể tải chương:\n{chapter_data['error']}")
                return
            
            self.current_chapter_id = chapter_id
            self.current_chapter_index = chapter_data['chapter_index']
            
            # Display content
            content = f"<h2>{chapter_data['title']}</h2>\n\n"
            if chapter_data.get('html_content'):
                content += chapter_data['html_content']
            else:
                content += chapter_data['content'].replace('\n', '<br>')
            
            self.content_text.setHtml(content)
            
            # Update text length
            plain_text = self.content_text.toPlainText()
            self.current_text_length = len(plain_text)
            
            # Set position slider
            if self.current_text_length > 0:
                self.position_slider.setMaximum(100)
                self.read_from_position_button.setEnabled(True)
            else:
                self.position_slider.setMaximum(0)
                self.read_from_position_button.setEnabled(False)
            
            # Set cursor position
            if start_position > 0 and start_position < self.current_text_length:
                cursor = self.content_text.textCursor()
                cursor.setPosition(start_position)
                self.content_text.setTextCursor(cursor)
                self.content_text.ensureCursorVisible()
            
            # Highlight current chapter
            self.chapter_list.setCurrentRow(self.current_chapter_index)
            
            # Update position slider (silent to avoid scroll issues)
            self._update_position_slider_silent()
        
        run_async(load, update_ui)
    
    def _on_chapter_selected(self, item):
        """Handle chapter selection."""
        if item and self.current_book_id:
            row = self.chapter_list.currentRow()
            if self.book_data and row < len(self.book_data.get("chapters", [])):
                chapter = self.book_data["chapters"][row]
                self._load_chapter(chapter['id'])
    
    def _on_chapter_double_clicked(self, item):
        """Handle chapter double-click - start reading."""
        self._on_chapter_selected(item)
        QTimer.singleShot(300, self._toggle_tts)
    
    def _prev_chapter(self):
        """Go to previous chapter."""
        if self.current_chapter_index > 0 and self.book_data:
            chapter = self.book_data["chapters"][self.current_chapter_index - 1]
            self._load_chapter(chapter['id'])
    
    def _next_chapter(self):
        """Go to next chapter."""
        if self.book_data and self.current_chapter_index < len(self.book_data["chapters"]) - 1:
            chapter = self.book_data["chapters"][self.current_chapter_index + 1]
            self._load_chapter(chapter['id'])
    
    def _load_reading_position(self):
        """Load saved reading position."""
        if not self.current_book_id:
            return
        
        async def load():
            try:
                # reading_service.get_reading_position is sync
                return self.reading_service.get_reading_position(self.current_book_id)
            except Exception as e:
                return None
        
        def update_ui(position_data):
            if position_data and position_data.get("chapter_index") is not None:
                chapter_index = position_data["chapter_index"]
                position = position_data.get("position", 0)
                
                if self.book_data and chapter_index < len(self.book_data["chapters"]):
                    chapter = self.book_data["chapters"][chapter_index]
                    self._load_chapter(chapter['id'], start_position=position)
        
        run_async(load, update_ui)
    
    def _save_reading_position(self):
        """Save reading position."""
        if not self.current_book_id or not self.content_text:
            return
        
        cursor = self.content_text.textCursor()
        position = cursor.position()
        
        async def save():
            try:
                # reading_service.save_reading_position is sync
                return self.reading_service.save_reading_position(
                    self.current_book_id,
                    self.current_chapter_index,
                    position
                )
            except Exception as e:
                print(f"Error saving position: {e}")
        
        run_async(save, lambda x: None)
    
    def _load_bookmarks(self):
        """Load bookmarks."""
        if not self.current_book_id:
            return
        
        async def load():
            try:
                # reading_service.get_bookmarks is sync
                return self.reading_service.get_bookmarks(self.current_book_id)
            except Exception as e:
                return []
        
        def update_ui(bookmarks):
            self.bookmark_list.clear()
            for bm in bookmarks:
                note = bm.get("note") or f"Vị trí {bm['position']}"
                item_text = f"Chương {bm['chapter_index'] + 1}\n{note[:50]}..."
                self.bookmark_list.addItem(item_text)
                item = self.bookmark_list.item(self.bookmark_list.count() - 1)
                item.setData(Qt.UserRole, bm)
        
        run_async(load, update_ui)
    
    def _add_bookmark(self):
        """Add bookmark."""
        if not self.current_book_id:
            return
        
        cursor = self.content_text.textCursor()
        position = cursor.position()
        
        plain_text = self.content_text.toPlainText()
        start = max(0, position - 50)
        end = min(len(plain_text), position + 50)
        context = plain_text[start:end].strip()
        note = context[:100] + "..." if len(context) > 100 else context
        
        async def add():
            try:
                # reading_service.add_bookmark is sync
                return self.reading_service.add_bookmark(
                    self.current_book_id,
                    self.current_chapter_index,
                    position,
                    note
                )
            except Exception as e:
                return {"error": str(e)}
        
        def update_ui(result):
            if "error" not in result:
                toast_success("Đã thêm bookmark!")
                self._load_bookmarks()
        
        run_async(add, update_ui)
    
    def _on_bookmark_selected(self, item):
        """Handle bookmark selection."""
        if item:
            bookmark = item.data(Qt.UserRole)
            if bookmark and self.book_data:
                chapter_index = bookmark["chapter_index"]
                position = bookmark["position"]
                
                if chapter_index < len(self.book_data["chapters"]):
                    chapter = self.book_data["chapters"][chapter_index]
                    self._load_chapter(chapter['id'], start_position=position)
    
    def _on_bookmark_double_clicked(self, item):
        """Handle bookmark double-click - read from bookmark."""
        self._on_bookmark_selected(item)
        if item:
            bookmark = item.data(Qt.UserRole)
            if bookmark:
                QTimer.singleShot(300, lambda: self._read_from_position(bookmark["position"]))
    
    def _search_text(self):
        """Search in book."""
        query = self.search_input.text().strip()
        if not query or not self.current_book_id:
            return
        
        # Simple search - could be enhanced with backend search API
        plain_text = self.content_text.toPlainText()
        query_lower = query.lower()
        content_lower = plain_text.lower()
        
        if query_lower in content_lower:
            pos = content_lower.find(query_lower)
            cursor = self.content_text.textCursor()
            cursor.setPosition(pos)
            cursor.setPosition(pos + len(query), QTextCursor.KeepAnchor)
            self.content_text.setTextCursor(cursor)
            self.content_text.ensureCursorVisible()
    
    def _toggle_tts(self):
        """Toggle TTS - read from beginning."""
        if not self.tts_engine or not self.content_text:
            print("[reading_tab] _toggle_tts: TTS engine hoặc content không tồn tại")
            return
        
        print(f"[reading_tab] _toggle_tts: is_paused={self.tts_engine.is_paused}, is_speaking={self.tts_engine.is_speaking}")
        
        if self.tts_engine.is_paused:
            print("[reading_tab] _toggle_tts: Gọi resume()")
            self.tts_engine.resume()
            self.tts_play_button.setEnabled(False)
            self.tts_pause_button.setEnabled(True)
            self.tts_stop_button.setEnabled(True)
            return
        
        print("[reading_tab] _toggle_tts: Gọi _read_from_position(0)")
        self._read_from_position(0)
    
    def _read_from_current_position(self):
        """Read from current cursor position."""
        cursor = self.content_text.textCursor()
        position = cursor.position()
        self._read_from_position(position)
    
    def _read_from_position(self, start_position: int = 0):
        """Read from specific position."""
        if not self.tts_engine or not self.content_text:
            print("[reading_tab] TTS engine hoặc content_text không tồn tại")
            QMessageBox.warning(self, "Lỗi", "TTS engine chưa được khởi tạo. Vui lòng vào Cài đặt để chọn engine TTS.")
            return
        
        plain_text = self.content_text.toPlainText()
        
        if not plain_text or not plain_text.strip():
            print("[reading_tab] Văn bản trống")
            QMessageBox.warning(self, "Lỗi", "Không có văn bản để đọc!")
            return
        
        if start_position >= 0 and start_position < len(plain_text):
            text_to_read = plain_text[start_position:]
            self.read_start_position = start_position
        else:
            text_to_read = plain_text
            self.read_start_position = 0
        
        if not text_to_read.strip():
            print("[reading_tab] Văn bản sau khi cắt trống")
            return
        
        cursor = self.content_text.textCursor()
        cursor.setPosition(start_position)
        self.content_text.setTextCursor(cursor)
        self.content_text.ensureCursorVisible()
        
        print(f"[reading_tab] Bắt đầu đọc {len(text_to_read)} ký tự với engine: {type(self.tts_engine).__name__}")
        
        # Show loading indicator
        original_text = self.tts_play_button.text()
        self.tts_play_button.setText("⏳")
        self.tts_play_button.setEnabled(False)
        self.tts_pause_button.setEnabled(False)
        self.tts_stop_button.setEnabled(False)
        
        # Force UI update to show loading indicator
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        try:
            self.tts_engine.speak(text_to_read)
            
            # Keep loading indicator until TTS actually starts
            # Check periodically if TTS has started speaking
            from PySide6.QtCore import QTimer
            check_count = [0]  # Use list to allow modification in nested function
            
            def check_speaking():
                check_count[0] += 1
                
                # If TTS is speaking, restore buttons
                if self.tts_engine and self.tts_engine.is_speaking:
                    self.tts_play_button.setText(original_text)
                    self.tts_play_button.setEnabled(False)
                    self.tts_pause_button.setEnabled(True)
                    self.tts_stop_button.setEnabled(True)
                    print("[reading_tab] TTS đã bắt đầu phát, restore buttons")
                # If checked 20 times (10 seconds) and still not speaking, restore anyway
                elif check_count[0] >= 20:
                    self.tts_play_button.setText(original_text)
                    self.tts_play_button.setEnabled(True)
                    self.tts_pause_button.setEnabled(False)
                    self.tts_stop_button.setEnabled(False)
                    print("[reading_tab] Timeout: TTS không bắt đầu sau 10 giây")
                # Otherwise, check again after 500ms
                else:
                    QTimer.singleShot(500, check_speaking)
            
            # Start checking after 500ms
            QTimer.singleShot(500, check_speaking)
            print("[reading_tab] Đã gọi speak() thành công, đang chờ TTS bắt đầu...")
        except Exception as e:
            # Restore button on error
            self.tts_play_button.setText(original_text)
            self.tts_play_button.setEnabled(True)
            self.tts_pause_button.setEnabled(False)
            self.tts_stop_button.setEnabled(False)
            
            print(f"[reading_tab] Lỗi khi gọi speak(): {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Lỗi TTS", f"Không thể đọc văn bản:\n{str(e)}\n\nVui lòng kiểm tra:\n- Kết nối internet (nếu dùng Google TTS)\n- Cài đặt TTS engine")
    
    def _read_selected_text(self):
        """Read selected text."""
        if not self.tts_engine:
            return
        
        cursor = self.content_text.textCursor()
        selected_text = cursor.selectedText()
        
        if not selected_text or not selected_text.strip():
            return
        
        self.tts_engine.speak(selected_text)
        self.tts_play_button.setEnabled(False)
        self.tts_pause_button.setEnabled(True)
        self.tts_stop_button.setEnabled(True)
    
    def _pause_tts(self):
        """Pause TTS."""
        if self.tts_engine and self.tts_engine.is_speaking:
            self.tts_engine.pause()
            print("[reading_tab] Đã pause TTS, enable nút Play để resume")
            # Enable Play button so user can resume
            self.tts_play_button.setEnabled(True)
            # Disable Pause button (already paused)
            self.tts_pause_button.setEnabled(False)
            # Keep Stop button enabled
            self.tts_stop_button.setEnabled(True)
    
    def _stop_tts(self):
        """Stop TTS."""
        if self.tts_engine:
            self.tts_engine.stop()
            self.tts_play_button.setEnabled(True)
            self.tts_pause_button.setEnabled(False)
            self.tts_stop_button.setEnabled(False)
    
    def _on_cursor_position_changed(self):
        """Handle cursor position change."""
        # Only update slider if not user-initiated (to prevent scroll reset)
        if not hasattr(self, '_programmatic_cursor_move'):
            self._programmatic_cursor_move = False
        
        if not self._programmatic_cursor_move:
            self._update_position_slider_silent()
        
        if self.current_text_length > 0:
            self.read_from_position_button.setEnabled(True)
    
    def _update_position_slider_silent(self):
        """Update position slider without triggering scroll (for cursor changes)."""
        if self.current_text_length == 0:
            return
        
        cursor = self.content_text.textCursor()
        position = cursor.position()
        
        percentage = int((position / self.current_text_length) * 100) if self.current_text_length > 0 else 0
        percentage = max(0, min(100, percentage))
        
        # Block signals to prevent _on_position_changed from being called
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(percentage)
        self.position_slider.blockSignals(False)
        
        self.position_label.setText(f"{percentage}%")
    
    def _on_selection_changed(self):
        """Handle text selection change."""
        cursor = self.content_text.textCursor()
        has_selection = cursor.hasSelection()
        self.tts_play_selection_button.setEnabled(has_selection)
        
        if has_selection:
            selected_text = cursor.selectedText()
            self.selection_info_label.setText(f"Đã chọn: {len(selected_text)} ký tự - Click 'Đọc đoạn đã chọn' để nghe")
        else:
            self.selection_info_label.setText("Chọn đoạn văn và click 'Đọc đoạn đã chọn'")
    
    def _update_position_slider(self):
        """Update position slider based on cursor position."""
        if self.current_text_length == 0:
            return
        
        cursor = self.content_text.textCursor()
        position = cursor.position()
        
        percentage = int((position / self.current_text_length) * 100) if self.current_text_length > 0 else 0
        percentage = max(0, min(100, percentage))
        
        if not self.position_slider.isSliderDown():
            # Block signals to prevent feedback loop that causes scroll reset
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(percentage)
            self.position_slider.blockSignals(False)
        
        self.position_label.setText(f"{percentage}%")
    
    def _on_position_changed(self, value):
        """Handle position slider change."""
        if self.current_text_length == 0:
            return
        
        position = int((value / 100.0) * self.current_text_length)
        position = max(0, min(self.current_text_length - 1, position))
        
        self.position_label.setText(f"{value}%")
        
        if not self.position_slider.isSliderDown():
            cursor = self.content_text.textCursor()
            cursor.setPosition(position)
            self.content_text.setTextCursor(cursor)
            self.content_text.ensureCursorVisible()
    
    def _on_position_slider_released(self):
        """Handle position slider release."""
        value = self.position_slider.value()
        if self.current_text_length == 0:
            return
        
        position = int((value / 100.0) * self.current_text_length)
        position = max(0, min(self.current_text_length - 1, position))
        
        cursor = self.content_text.textCursor()
        cursor.setPosition(position)
        self.content_text.setTextCursor(cursor)
        self.content_text.ensureCursorVisible()
        
        self.read_from_position_button.setEnabled(True)
    
    def _show_settings(self):
        """Show settings dialog."""
        print(f"[reading_tab] _show_settings - Settings trước khi mở dialog: {self.settings}")
        
        dialog = SettingsDialog(self, self.settings, voice_loader=self._get_voice_options)
        if dialog.exec() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            print(f"[reading_tab] Settings mới từ dialog: {new_settings}")
            
            old_engine = self.settings.get("tts_engine", "pyttsx3")
            old_voice_id = self.settings.get("tts_voice_id")
            
            self.settings.update(new_settings)
            print(f"[reading_tab] Settings sau khi update: {self.settings}")
            
            new_engine = self.settings.get("tts_engine", "pyttsx3")
            new_voice_id = self.settings.get("tts_voice_id")
            
            self._refresh_available_voices(new_engine)
            
            should_reinit = (
                old_engine != new_engine or
                old_voice_id != new_voice_id or
                self.tts_engine is None
            )
            
            print(f"[reading_tab] Engine thay đổi: {old_engine} → {new_engine}, should_reinit={should_reinit}")
            
            if should_reinit:
                if self.tts_engine:
                    self.tts_engine.stop()
                print(f"[reading_tab] Gọi _init_tts() để khởi tạo lại engine")
                self._init_tts()
            elif self.tts_engine:
                self.tts_engine.set_rate(self.settings.get("tts_speed", 150))
            
            self._apply_settings()
    
    def _show_context_menu(self, position):
        """Show context menu on right-click - uses TextContextMenuMixin."""
        # Get selected text using mixin helper
        selected_text = self._get_selected_text_from_widget(self.content_text)
        
        if not selected_text:
            return
        
        # Create base menu from mixin (includes all translation options + Gemini AI + dictionary + TTS)
        menu = self.create_text_context_menu(selected_text)
        
        menu.addSeparator()
        
        # Add 'Save to Flashcard'
        save_vocab_action = QAction("💾 Lưu vào Flashcard", self)
        save_vocab_action.triggered.connect(
            lambda: self._save_word_to_vocab(selected_text)
        )
        menu.addAction(save_vocab_action)
        
        # Show menu at cursor position
        menu.exec(self.content_text.mapToGlobal(position))

    def _save_word_to_vocab(self, word: str):
        """Save word to vocabulary with context from current book."""
        full_text = self.content_text.toPlainText()
        
        # Find context sentence
        import re
        sentences = re.split(r'([。！？.!?\n])', full_text)
        context_sentence = ""
        
        reconstructed = []
        for i in range(0, len(sentences)-1, 2):
            reconstructed.append(sentences[i] + sentences[i+1])
        if len(sentences) % 2 != 0:
            reconstructed.append(sentences[-1])
            
        for s in reconstructed:
            if word in s:
                context_sentence = s.strip()
                break
        
        if not context_sentence:
            context_sentence = word
            
        async def prepare():
            try:
                from frontend.services.translator import TranslatorService
                from frontend.utils.language_utils import detect_language
                lang = detect_language(word)
                meaning = TranslatorService.translate(word, "auto", "vi")
                ctx_trans = TranslatorService.translate(context_sentence, "auto", "vi")
                return {"meaning": meaning, "ctx_trans": ctx_trans, "lang": lang}
            except Exception as e:
                return {"error": str(e)}
                
        def on_prepared(result):
            if "error" in result:
                QMessageBox.warning(self, "Lỗi", f"Không thể chuẩn bị dữ liệu: {result['error']}")
                return
                
            from frontend.ui.tabs.youtube_tab_dialogs import SaveVocabDialog
            dialog = SaveVocabDialog(
                self, word, context_sentence, 
                result.get("meaning", ""), result.get("ctx_trans", "")
            )
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                lang = result.get("lang", "en")
                is_jp = lang in ['ja', 'jp', 'japanese']
                
                if is_jp:
                    save_data = {
                        "lang": "jp",
                        "word_kanji": data["word"],
                        "word_kana": "",
                        "meaning_vi": data["meaning"],
                        "example_jp": data["context"],
                        "example_vi": data["translation"]
                    }
                else:
                    save_data = {
                        "lang": "en",
                        "word": data["word"],
                        "meaning_vi": data["meaning"],
                        "example_en": data["context"],
                        "example_vi": data["translation"]
                    }
                self._submit_vocab_save(save_data)
                
        run_async(prepare, on_prepared)

    def _submit_vocab_save(self, data):
        async def save():
            return self.vocab_service.save(data)
            
        def on_saved(result):
            toast_success("Đã lưu từ vựng vào Flashcard!")
            
        run_async(save, on_saved)

    
    def _lookup_word(self, word: str, dictionary_id: str = None, source_lang: str = "auto"):
        """Look up word in dictionary."""
        if not word:
            QMessageBox.warning(self, "Cảnh báo", "Không có từ được chọn!")
            return
        
        if not self.dictionary_dialog:
            self.dictionary_dialog = DictionaryLookupDialog(self)
            self.dictionary_dialog.finished.connect(lambda _: setattr(self, "dictionary_dialog", None))
        
        self.dictionary_dialog.set_lookup(word, source_lang, dictionary_id)
        self.dictionary_dialog.show()
        self.dictionary_dialog.raise_()
        self.dictionary_dialog.activateWindow()
    
        
    
    def _on_anchor_clicked(self, url: QUrl):
        """Handle link clicks in the book content."""
        if url.scheme() in ('http', 'https'):
            import webbrowser
            webbrowser.open(url.toString())
        else:
            # Internal anchor or link
            fragment = url.fragment()
            if fragment:
                self.content_text.scrollToAnchor(fragment)
            else:
                # Might be a link to another internal file/chapter
                # For now, we try to see if it's a simple anchor click
                self.content_text.setSource(url)

    def closeEvent(self, event):
        """Handle close event."""
        if self.tts_engine:
            self.tts_engine.stop()
        self._save_reading_position()
        event.accept()

