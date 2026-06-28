"""YouTube tab."""
# Standard library
from typing import Optional, Dict, List

# Third-party
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QTextEdit, QTextBrowser, QLabel, QSplitter, QMenu, QMessageBox, QDialog,
    QFrame, QSizePolicy, QComboBox, QInputDialog
)
from PySide6.QtCore import Qt, QPoint, QUrl, QPropertyAnimation, QEasingCurve, QRect, QSettings
from PySide6.QtGui import QAction, QTextCursor, QColor, QTextFormat

# Local
from frontend.utils.async_helpers import run_async
from frontend.utils.language_utils import detect_language
from frontend.services.youtube_service import YouTubeService
from frontend.services.translator import TranslatorService
from frontend.services.tts import TTSService, get_tts_service
from frontend.services.dictionary_service import DictionaryService
from frontend.services import get_vocab_service
from frontend.ui.widgets.dictionary_dialog import DictionaryLookupDialog
from frontend.ui.tabs.youtube_tab_dialogs import SaveVocabDialog, ChannelManagerDialog
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin
from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning
from frontend.ui.styles.theme import ThemeColors


# Try to import QWebEngineView for YouTube embedding
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage
    WEBENGINE_AVAILABLE = True
    
    class CustomWebEnginePage(QWebEnginePage):
        """Custom QWebEnginePage với context menu đã được tùy chỉnh."""
        
        def createStandardContextMenu(self):
            """Tạo context menu tùy chỉnh, loại bỏ các mục không cần thiết."""
            menu = super().createStandardContextMenu()
            
            if menu is None:
                return None
            
            # Danh sách các từ khóa cần loại bỏ (không phân biệt hoa thường)
            keywords_to_remove = [
                "save page",
                "open link in new tab",
                "open link in new window",
                "save link"
            ]
            
            # Danh sách các action cần loại bỏ
            actions_to_remove = []
            
            for action in menu.actions():
                if action is None:
                    continue
                    
                text = action.text()
                if not text:
                    continue
                    
                text_lower = text.lower()
                # Loại bỏ các mục có chứa các từ khóa không mong muốn
                if any(keyword in text_lower for keyword in keywords_to_remove):
                    actions_to_remove.append(action)
            
            # Xóa các action không mong muốn
            for action in actions_to_remove:
                menu.removeAction(action)
            
            return menu

    class CustomWebEngineView(QWebEngineView):
        """Custom QWebEngineView sử dụng CustomWebEnginePage."""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            # Tạo custom page với context menu đã được tùy chỉnh
            custom_page = CustomWebEnginePage(self)
            self.setPage(custom_page)
    
except ImportError:
    WEBENGINE_AVAILABLE = False
    print("[WARNING] QWebEngineWidgets not available. YouTube video embedding disabled.")
    print("[INFO] Install PySide6-WebEngine: pip install PySide6-WebEngine")


class YouTubeTab(QWidget, TextContextMenuMixin):
    """YouTube video learning tab with context menu from mixin."""
    
    def __init__(self):
        super().__init__()
        self.youtube_service = YouTubeService()
        self.translator_service = TranslatorService()
        self.tts_service = get_tts_service()
        self.vocab_service = get_vocab_service()
        self.dictionary_dialog = None
        
        # State initialization early
        self.current_video_id = None
        self.transcript_segments = []
        self.highlight_timer = None
        self.user_is_selecting_text = False
        self.current_highlighted_segment = None
        self.playlist_cache = {}
        self.segment_ranges = []
        self.transcript_panel_hidden = False
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI - Video Immersion Center Edition."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setStyleSheet(f"""
            QWidget#YouTubeTab {{ background-color: {ThemeColors.BG_PRIMARY}; }}
            QFrame#SearchPanel {{ 
                background-color: {ThemeColors.BG_SECONDARY}; 
                border-radius: 0px; 
            }}
            QLabel#WhiteLbl {{ color: {ThemeColors.TEXT_PRIMARY}; }}
            
            QLineEdit#SearchInput {{
                background: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
            }}
            
            QPushButton#ActionBtn {{
                background: {ThemeColors.PRIMARY};
                color: white;
                font-weight: bold;
                border-radius: 18px;
                padding: 0; 
                margin: 0;
                border: none;
                font-size: 13px;
            }}
            QPushButton#ActionBtn:hover {{ background: {ThemeColors.PRIMARY_HOVER}; }}
            
            QTextEdit#TranscriptView {{
                background: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 12px;
                padding: 20px;
                font-size: 15px;
                line-height: 1.8;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            
            QPushButton#RoundBtn {{
                background: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.TEXT_PRIMARY};
                border: none;
                padding: 0;
                margin: 0;
            }}
            QPushButton#RoundBtn:hover {{ background: {ThemeColors.SECONDARY}; }}
            
            QComboBox {{
                background: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 12px;
                padding: 5px 10px;
            }}
            
            QFrame#PlayerContainer {{
                background: black;
                border-radius: 12px;
                border: 1px solid {ThemeColors.BORDER};
            }}
        """)
        self.setObjectName("YouTubeTab")

        # Top Bar: Search & Discovery
        self.search_panel = QFrame()
        self.search_panel.setObjectName("SearchPanel")
        self.search_panel.setFixedHeight(90) # Height for better spacing
        search_layout = QHBoxLayout(self.search_panel)
        search_layout.setContentsMargins(15, 5, 15, 5)
        search_layout.setSpacing(10)
        
        # --- LEFT SECTION: Logo & Level ---
        left_group = QWidget()
        left_lay = QHBoxLayout(left_group)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(10)
        
        logo = QLabel("📺 YOUTUBE")
        logo = QLabel("📺 YOUTUBE")
        logo.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.ACCENT}; margin-right: 5px;")
        left_lay.addWidget(logo)
        
        left_lay.addWidget(QLabel("Mức độ:", styleSheet=f"color: {ThemeColors.TEXT_PRIMARY};"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["Tất cả", "N5", "N4", "N3", "N2", "N1"])
        self.level_filter.setFixedWidth(75)
        left_lay.addWidget(self.level_filter)
        
        search_layout.addWidget(left_group)
        
        # --- CENTER SECTION: Channel Management ---
        mid_group = QWidget()
        mid_lay = QHBoxLayout(mid_group)
        mid_lay.setContentsMargins(0, 0, 0, 0)
        mid_lay.setSpacing(5)
        
        mid_lay.addWidget(QLabel("Kênh:", styleSheet=f"color: {ThemeColors.TEXT_PRIMARY};"))
        self.channel_filter = QComboBox()
        self.channel_filter.setFixedWidth(160)
        self.channel_filter.currentIndexChanged.connect(self._on_channel_changed)
        mid_lay.addWidget(self.channel_filter)
        
        mid_lay.addSpacing(5) # Add space to prevent overlap
        
        # Small buttons for channel management
        btn_container = QWidget()
        btn_lay = QHBoxLayout(btn_container)
        btn_lay.setContentsMargins(0, 0, 0, 0)
        btn_lay.setSpacing(6)
        
        self.add_channel_btn = QPushButton("+")
        self.add_channel_btn.setObjectName("RoundBtn")
        self.add_channel_btn.setFixedSize(26, 26)
        self.add_channel_btn.setStyleSheet("border-radius: 13px; font-weight: bold; font-size: 16px;")
        self.add_channel_btn.setToolTip("Thêm kênh mới")
        self.add_channel_btn.clicked.connect(self._add_new_channel)
        btn_lay.addWidget(self.add_channel_btn)
        
        self.remove_channel_btn = QPushButton("-")
        self.remove_channel_btn.setObjectName("RoundBtn")
        self.remove_channel_btn.setFixedSize(26, 26)
        self.remove_channel_btn.setToolTip("Xóa kênh")
        self.remove_channel_btn.setStyleSheet(f"background: {ThemeColors.DANGER}; border-radius: 13px; color: white; font-weight: bold; font-size: 16px;")
        self.remove_channel_btn.clicked.connect(self._remove_current_channel)
        btn_lay.addWidget(self.remove_channel_btn)

        self.manage_channel_btn = QPushButton("⇅")
        self.manage_channel_btn.setObjectName("RoundBtn")
        self.manage_channel_btn.setFixedSize(26, 26)
        self.manage_channel_btn.setStyleSheet("border-radius: 13px; color: white; font-size: 14px;")
        self.manage_channel_btn.clicked.connect(self._open_channel_manager)
        btn_lay.addWidget(self.manage_channel_btn)
        
        mid_lay.addWidget(btn_container)
        search_layout.addWidget(mid_group)

        # --- RIGHT SECTION: Search & Playlist ---
        right_group = QWidget()
        right_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_lay = QHBoxLayout(right_group)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(8)
        
        self.playlist_filter = QComboBox()
        self.playlist_filter.setFixedWidth(130)
        self.playlist_filter.addItem("Tất cả video", None)
        self.playlist_filter.setEnabled(True) 
        self.playlist_filter.currentIndexChanged.connect(self._on_playlist_changed)
        right_lay.addWidget(self.playlist_filter)
        
        # Refresh playlist button
        self.refresh_playlist_btn = QPushButton("🔄")
        self.refresh_playlist_btn.setObjectName("RoundBtn")
        self.refresh_playlist_btn.setFixedSize(26, 26)
        self.refresh_playlist_btn.setStyleSheet("border-radius: 13px; font-size: 12px;")
        self.refresh_playlist_btn.setToolTip("Quét lại Playlist")
        self.refresh_playlist_btn.clicked.connect(self._refresh_playlists)
        right_lay.addWidget(self.refresh_playlist_btn)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Dán URL hoặc tìm kiếm video...")
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_input.setFixedHeight(34)
        self.search_input.returnPressed.connect(self._search_videos)
        right_lay.addWidget(self.search_input)
        
        self.search_btn = QPushButton("Tìm kiếm")
        self.search_btn.setObjectName("ActionBtn")
        self.search_btn.setFixedSize(120, 36)
        self.search_btn.clicked.connect(self._search_videos)
        right_lay.addWidget(self.search_btn)
        
        self.show_transcript_btn = QPushButton("📄")
        self.show_transcript_btn.setObjectName("RoundBtn")
        self.show_transcript_btn.setFixedSize(34, 34)
        self.show_transcript_btn.setStyleSheet("border-radius: 17px; background: #57606f;")
        self.show_transcript_btn.clicked.connect(self._toggle_transcript_visibility)
        right_lay.addWidget(self.show_transcript_btn)
        
        search_layout.addWidget(right_group)
        
        main_layout.addWidget(self.search_panel)

        # Main Splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {ThemeColors.BORDER}; }}")
        
        # LEFT: Discovery & Search Result
        left_side = QWidget()
        left_side_lay = QVBoxLayout(left_side)
        left_side_lay.setContentsMargins(20, 20, 10, 20)
        
        left_side_lay.addWidget(QLabel("🔍 KẾT QUẢ TÌM KIẾM", styleSheet=f"font-weight: bold; color: {ThemeColors.TEXT_SECONDARY};"))
        self.video_list = QListWidget()
        self.video_list.setStyleSheet(f"""
            QListWidget {{ background: {ThemeColors.BG_SECONDARY}; border-radius: 12px; border: 1px solid {ThemeColors.BORDER}; }}
            QListWidget::item {{ padding: 15px; border-bottom: 1px solid {ThemeColors.BORDER}; color: {ThemeColors.TEXT_PRIMARY}; }}
            QListWidget::item:selected {{ background: {ThemeColors.PRIMARY_LIGHT}; color: {ThemeColors.PRIMARY}; font-weight: bold; }}
        """)
        self.video_list.itemClicked.connect(self._load_video)
        left_side_lay.addWidget(self.video_list)
        
        left_side_lay.addWidget(QLabel("✨ VIDEO LIÊN QUAN", styleSheet=f"font-weight: bold; color: {ThemeColors.TEXT_SECONDARY}; margin-top: 10px;"))
        self.related_videos_list = QListWidget()
        self.related_videos_list.itemClicked.connect(self._load_related_video)
        self.related_videos_list.setFixedHeight(200)
        self.related_videos_list.setStyleSheet(f"background: {ThemeColors.BG_SECONDARY}; border-radius: 12px; border: 1px solid {ThemeColors.BORDER}; color: {ThemeColors.TEXT_PRIMARY};")
        left_side_lay.addWidget(self.related_videos_list)
        
        self.main_splitter.addWidget(left_side)
        
        # RIGHT: Player & Transcript
        right_side = QWidget()
        right_side_lay = QVBoxLayout(right_side)
        right_side_lay.setContentsMargins(10, 20, 20, 20)
        
        self.content_splitter = QSplitter(Qt.Vertical)
        
        # Player Container
        player_container = QFrame()
        player_container.setObjectName("PlayerContainer")
        player_container.setStyleSheet(f"background: black; border-radius: 12px; border: 2px solid {ThemeColors.BORDER};")
        player_container_lay = QVBoxLayout(player_container)
        player_container_lay.setContentsMargins(0, 0, 0, 0)
        
        if WEBENGINE_AVAILABLE:
            self.video_player = CustomWebEngineView()
            self.video_player.titleChanged.connect(self._on_player_title_changed)
            player_container_lay.addWidget(self.video_player)
        else:
            fallback = QLabel("⚠ Cần cài đặt PySide6-WebEngine để xem video trực tiếp.\nSử dụng: pip install PySide6-WebEngine")
            fallback.setStyleSheet("color: white; font-size: 14px;")
            fallback.setAlignment(Qt.AlignCenter)
            player_container_lay.addWidget(fallback)
            self.video_player = None
        
        self.content_splitter.addWidget(player_container)
        
        # Transcript Container
        self.transcript_panel = QWidget()
        transcript_inner_lay = QVBoxLayout(self.transcript_panel)
        transcript_inner_lay.setContentsMargins(0, 10, 0, 0)
        
        transcript_inner_lay.addWidget(QLabel("📄 BẢN DỊCH / PHỤ ĐỀ", styleSheet=f"font-weight: bold; color: {ThemeColors.TEXT_SECONDARY};"))
        self.transcript_viewer = QTextEdit()
        self.transcript_viewer.setObjectName("TranscriptView")
        self.transcript_viewer.setReadOnly(True)
        self.transcript_viewer.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        self.transcript_viewer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.transcript_viewer.customContextMenuRequested.connect(self._show_transcript_context_menu)
        self.transcript_viewer.selectionChanged.connect(self._on_selection_changed)
        transcript_inner_lay.addWidget(self.transcript_viewer)
        
        self.content_splitter.addWidget(self.transcript_panel)
        
        # Set default sizes for content splitter (video:transcript ratio)
        # Video player should take 70% of vertical space, transcript 30%
        self.content_splitter.setStretchFactor(0, 7)  # Video player
        self.content_splitter.setStretchFactor(1, 3)  # Transcript
        
        right_side_lay.addWidget(self.content_splitter)
        self.main_splitter.addWidget(right_side)
        
        # Set default sizes for main splitter (left:right ratio)
        # Left sidebar (video list) takes 1 part, right (player+transcript) takes 2 parts
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(self.main_splitter)
        
        # Init data
        self._get_default_channels()
        self._load_saved_channels()

    def _get_default_channels(self):
        """Return list of default channels (Name, Handle/URL).
        
        Note: These are just default suggestions. Users can add/remove channels freely.
        Handles have been verified via YouTube search.
        """
        return [
            ("Tất cả kênh", None),
            ("Thảo Nguyên Nihongo", "@thaonguyennihongo2021"),
            ("Bite Size Japanese", "@BitesizeJapanese1"),
            ("MAIの日本語Podcast", "@MaichanJapanesePodcast"),
            ("PAPAKEN-family", "@PAPAKEN4"),
            ("Wasabi Japanese", "@WasabiJapanese"),
            ("Emma:)Japanese", "@emma.japanese"),
            ("Naoko Japanese", "@DailyJapanese"),
            ("YUYUの日本語Podcast", "@yuyunihongopodcast"),
            ("Paru Sensei", "@parusensei")  # Needs verification
        ]

    def _load_saved_channels(self):
        self.settings = QSettings("EnglishApp", "YouTubeChannels")
        saved_data = self.settings.value("channel_list_v2", []) # Use v2 for name/handle storage
        
        if not saved_data:
            # Fallback to old format or defaults
            old_channels = self.settings.value("channel_list", [])
            if not old_channels:
                saved_data = self._get_default_channels()
            else:
                saved_data = [(c, None) for c in old_channels]
                if ("Tất cả kênh", None) not in saved_data:
                    saved_data.insert(0, ("Tất cả kênh", None))
        
        self.channel_filter.blockSignals(True)
        self.channel_filter.clear()
        for name, handle in saved_data:
            self.channel_filter.addItem(name, handle)
        self.channel_filter.blockSignals(False)
        
    def _add_new_channel(self):
        channel_name, ok = QInputDialog.getText(self, "Thêm kênh mới", "Nhập tên/Handle kênh (Ví dụ: @thaonguyennihongo):")
        if ok and channel_name:
            channel_name = channel_name.strip()
            if not channel_name:
                return
            
            # Simplified: Use the input as both name and handle if it starts with @
            handle = channel_name if channel_name.startswith("@") else None
            display_name = channel_name
            
            if self.channel_filter.findText(display_name) != -1:
                QMessageBox.warning(self, "Lỗi", "Kênh này đã có trong danh sách!")
                return
                
            self.channel_filter.addItem(display_name, handle)
            self.channel_filter.setCurrentText(display_name)
            self._save_channels()
            toast_success(f"Đã thêm kênh '{display_name}'!")

    def _save_channels(self):
        """Save channel list including name/handle data."""
        channels_data = []
        for i in range(self.channel_filter.count()):
            name = self.channel_filter.itemText(i)
            handle = self.channel_filter.itemData(i)
            channels_data.append((name, handle))
            
        self.settings.setValue("channel_list_v2", channels_data)
        # Also save simple list for older versions/compatibility
        self.settings.setValue("channel_list", [c[0] for c in channels_data])
    
    def _on_channel_changed(self, index):
        """Handle channel selection change - clear URL and load playlists."""
        current_text = self.search_input.text().strip()
        selected_channel_name = self.channel_filter.currentText()
        selected_channel_handle = self.channel_filter.currentData()
        
        # Use handle if available, otherwise name
        identifier = selected_channel_handle or selected_channel_name
        
        # Reset playlist filter - block signals to avoid triggering search immediately
        self.playlist_filter.blockSignals(True)
        self.playlist_filter.clear()
        self.playlist_filter.addItem("Tất cả video", None)
        self.playlist_filter.setEnabled(False)
        self.playlist_filter.blockSignals(False)
        
        # If a specific channel is selected (not "All"), fetch playlists
        if identifier and selected_channel_name != "Tất cả kênh":
            self._fetch_playlists(identifier)
        
        # If search input contains a YouTube URL, clear it when changing channel
        # This allows the user to search by the new channel instead of loading old URL
        if "youtube.com" in current_text or "youtu.be" in current_text:
            self.search_input.clear()
            
            # Auto-search for new channel if it's not "Tất cả kênh"
            if selected_channel_name and selected_channel_name != "Tất cả kênh":
                # Trigger search for new channel after a short delay
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, self._search_videos)

    def _fetch_playlists(self, channel_identifier):
        """Fetch playlists for the selected channel.
        
        Args:
            channel_identifier: The handle (@xxx) or channel name
        """
        # Ensure we're using a proper handle format
        # If identifier doesn't start with @, try to find it from defaults or current selection
        actual_identifier = channel_identifier
        
        if not channel_identifier.startswith("@"):
            # First, check if current selection has a handle stored
            current_handle = self.channel_filter.currentData()
            if current_handle and current_handle.startswith("@"):
                actual_identifier = current_handle
            else:
                # Look up in defaults
                for name, handle in self._get_default_channels():
                    if name == channel_identifier and handle:
                        actual_identifier = handle
                        break
        
        print(f"[Playlist] Using identifier: {actual_identifier} (original: {channel_identifier})")
        
        # Check cache first
        if actual_identifier in self.playlist_cache:
            self._update_playlist_ui(self.playlist_cache[actual_identifier])
            return

        # Show loading indicator
        self.playlist_filter.blockSignals(True)
        self.playlist_filter.clear()
        self.playlist_filter.addItem("⏳ Đang tải Playlist...", None)
        self.playlist_filter.setEnabled(True)
        self.playlist_filter.blockSignals(False)
        
        # Track loading state
        self._playlist_loading = True
        self._playlist_channel = actual_identifier
        self._playlist_fetch_completed = False  # Reset flag for new fetch
        self._pending_playlists = None  # Clear any pending playlists
        
        def fetch_in_background():
            """Fetch playlists in a background thread."""
            import threading
            
            def worker():
                try:
                    print(f"[Playlist] Starting fetch for: {actual_identifier}")
                    playlists = self.youtube_service.get_channel_playlists(actual_identifier)
                    print(f"[Playlist] Fetch completed: {len(playlists) if playlists else 0} playlists found")
                    
                    # Mark fetch as completed IMMEDIATELY (before scheduling UI update)
                    # This prevents timeout from overwriting results
                    self._playlist_fetch_completed = True
                    
                    # Schedule UI update on main thread using proper cross-thread invocation
                    def update_ui():
                        # Only update if we're still loading this channel
                        if not hasattr(self, '_playlist_loading') or not self._playlist_loading:
                            print(f"[Playlist] update_ui skipped - not loading")
                            return
                        if hasattr(self, '_playlist_channel') and self._playlist_channel != actual_identifier:
                            print(f"[Playlist] update_ui skipped - channel changed")
                            return
                            
                        self._playlist_loading = False
                        print(f"[Playlist] Updating UI with {len(playlists) if playlists else 0} playlists")
                        
                        if playlists:
                            self.playlist_cache[actual_identifier] = playlists
                            self._update_playlist_ui(playlists)
                        else:
                            self.playlist_filter.blockSignals(True)
                            self.playlist_filter.clear()
                            self.playlist_filter.addItem("Tất cả video", None)
                            self.playlist_filter.addItem("📭 (Không có Playlist công khai)", None)
                            self.playlist_filter.blockSignals(False)
                            self.playlist_filter.setEnabled(True)
                    
                    # Store pending update data and trigger from main thread
                    self._pending_playlists = playlists
                    self._pending_playlist_channel = actual_identifier
                    
                except Exception as e:
                    print(f"[Playlist] Fetch error: {e}")
                    from PySide6.QtCore import QTimer
                    def show_error():
                        if hasattr(self, '_playlist_loading') and self._playlist_loading:
                            self._playlist_loading = False
                            self.playlist_filter.blockSignals(True)
                            self.playlist_filter.clear()
                            self.playlist_filter.addItem("Tất cả video", None)
                            self.playlist_filter.addItem("⚠️ (Lỗi tải Playlist)", None)
                            self.playlist_filter.blockSignals(False)
                    QTimer.singleShot(0, show_error)
            
            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
        
        # Set a timeout to show message if loading takes too long
        def show_timeout_message():
            # Only show timeout if fetch hasn't completed successfully
            if hasattr(self, '_playlist_fetch_completed') and self._playlist_fetch_completed:
                print(f"[Playlist] Timeout ignored - fetch already completed for: {actual_identifier}")
                return
            if hasattr(self, '_playlist_loading') and self._playlist_loading:
                if hasattr(self, '_playlist_channel') and self._playlist_channel == actual_identifier:
                    self._playlist_loading = False
                    self.playlist_filter.blockSignals(True)
                    self.playlist_filter.clear()
                    self.playlist_filter.addItem("Tất cả video", None)
                    self.playlist_filter.addItem("⏱️ (Timeout - Kênh quá lớn)", None)
                    self.playlist_filter.blockSignals(False)
                    print(f"[Playlist] Timeout reached for: {actual_identifier}")
        
        from PySide6.QtCore import QTimer
        QTimer.singleShot(8000, show_timeout_message)  # 8 second timeout for overall operation
        
        # Polling timer to check for pending playlists (runs on main thread)
        def check_pending_playlists():
            if hasattr(self, '_pending_playlists') and self._pending_playlists is not None:
                playlists = self._pending_playlists
                channel = getattr(self, '_pending_playlist_channel', None)
                self._pending_playlists = None  # Clear pending
                
                # Verify we're still waiting for this channel
                if hasattr(self, '_playlist_loading') and self._playlist_loading:
                    if hasattr(self, '_playlist_channel') and self._playlist_channel == channel:
                        self._playlist_loading = False
                        print(f"[Playlist] Processing pending UI update with {len(playlists)} playlists")
                        
                        if playlists:
                            self.playlist_cache[channel] = playlists
                            self._update_playlist_ui(playlists)
                        else:
                            self.playlist_filter.blockSignals(True)
                            self.playlist_filter.clear()
                            self.playlist_filter.addItem("Tất cả video", None)
                            self.playlist_filter.addItem("📭 (Không có Playlist công khai)", None)
                            self.playlist_filter.blockSignals(False)
                            self.playlist_filter.setEnabled(True)
                        return  # Done, no need to poll more
            
            # Keep polling if still loading
            if hasattr(self, '_playlist_loading') and self._playlist_loading:
                QTimer.singleShot(100, check_pending_playlists)  # Poll every 100ms
        
        # Start polling after a short delay
        QTimer.singleShot(100, check_pending_playlists)
        
        # Start background fetch immediately
        fetch_in_background()
        
    def _update_playlist_ui(self, playlists):
        """Update the playlist combobox with a limit to prevent UI hanging."""
        self.playlist_filter.blockSignals(True)
        self.playlist_filter.clear()
        self.playlist_filter.addItem("Tất cả video", None)
        
        if not playlists:
            self.playlist_filter.setEnabled(True) # Keep enabled to allow "All videos"
            self.playlist_filter.addItem("(Không tìm thấy playlist)", None)
            self.playlist_filter.blockSignals(False)
            return
            
        self.playlist_filter.setEnabled(True)
        # Limit to top 50 playlists to avoid UI freeze on large channels like Tsuji-chan Nel
        display_list = playlists[:50]
        
        for p in display_list:
            title = p.get("title", "Untitled Playlist")
            url = p.get("url")
            self.playlist_filter.addItem(f"📁 {title}", url)
            
        if len(playlists) > 50:
            self.playlist_filter.addItem(f"... và {len(playlists)-50} playlist khác", None)
            
        self.playlist_filter.blockSignals(False)

    def _on_playlist_changed(self, index):
        """Handle playlist selection."""
        # Only trigger search if it's a real playlist (url exists)
        url = self.playlist_filter.currentData()
        text = self.playlist_filter.currentText()
        
        if url:
            print(f"[YouTubeTab] Playlist selected: {text}")
            # Clear search input to prioritize playlist results
            self.search_input.clear()
            self._search_videos()
        elif index == 0: # "Tất cả video"
            print("[YouTubeTab] 'All videos' selected")
            self._search_videos()
    
    def _refresh_playlists(self):
        """Refresh/retry playlist loading for the current channel."""
        selected_channel_name = self.channel_filter.currentText()
        selected_channel_handle = self.channel_filter.currentData()
        
        if selected_channel_name == "Tất cả kênh":
            toast_info("Vui lòng chọn một kênh cụ thể trước khi quét Playlist!")
            return
        
        identifier = selected_channel_handle or selected_channel_name
        
        # Clear cache for this channel
        if identifier in self.playlist_cache:
            del self.playlist_cache[identifier]
            print(f"[Playlist] Cleared cache for: {identifier}")
        
        # Show refreshing state
        self.playlist_filter.blockSignals(True)
        self.playlist_filter.clear()
        self.playlist_filter.addItem("🔄 Đang quét lại...", None)
        self.playlist_filter.blockSignals(False)
        
        # Re-fetch playlists
        self._fetch_playlists(identifier)
    
    def _remove_current_channel(self):
        """Remove the currently selected channel from the list."""
        current_channel = self.channel_filter.currentText()
        current_index = self.channel_filter.currentIndex()
        
        # Prevent removing "Tất cả kênh"
        if current_channel == "Tất cả kênh":
            QMessageBox.warning(self, "Không thể xóa", "Không thể xóa kênh 'Tất cả kênh'!")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Xác nhận xóa", 
            f"Bạn có chắc muốn xóa kênh '{current_channel}' khỏi danh sách?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from combobox
            self.channel_filter.removeItem(current_index)
            
            # Save updated list
            self._save_channels()
            
            # Select "Tất cả kênh" after deletion
            self.channel_filter.setCurrentIndex(0)
            
            toast_success(f"Đã xóa kênh '{current_channel}'!")

    def _open_channel_manager(self):
        """Open dialog to reorder channels."""
        # Get current channels (excluding 'Tất cả kênh' which should stay top)
        current_channels = []
        for i in range(self.channel_filter.count()):
            name = self.channel_filter.itemText(i)
            handle = self.channel_filter.itemData(i)
            if name != "Tất cả kênh":
                current_channels.append((name, handle))
        
        from frontend.ui.tabs.youtube_tab_dialogs import ChannelManagerDialog
        dialog = ChannelManagerDialog(current_channels, self)
        if dialog.exec():
            new_channels = dialog.get_channels()
            
            # Reconstruct list with "Tất cả kênh" at top
            final_list = [("Tất cả kênh", None)]
            final_list.extend(new_channels)
            
            # Update combobox
            current_selection = self.channel_filter.currentText()
            self.channel_filter.blockSignals(True)
            self.channel_filter.clear()
            for name, handle in final_list:
                self.channel_filter.addItem(name, handle)
            self.channel_filter.blockSignals(False)
            
            # Restore selection if possible
            index = self.channel_filter.findText(current_selection)
            if index >= 0:
                self.channel_filter.setCurrentIndex(index)
            else:
                self.channel_filter.setCurrentIndex(0)
                
            # Save
            self._save_channels()

    def _search_videos(self):
        """Search YouTube videos or load video from URL."""
        input_text = self.search_input.text().strip()
        selected_channel_handle = self.channel_filter.currentData()
        selected_channel_name = self.channel_filter.currentText()
        
        if not input_text:
            # If empty but channel selected, we search for channel
            if selected_channel_name == "Tất cả kênh":
                toast_info("Vui lòng nhập từ khóa hoặc chọn kênh để tìm kiếm!")
                return
            query = ""
        else:
            query = input_text

        # Check if it's a direct URL or ID
        extracted_id = self.youtube_service.extract_video_id(input_text)
        if extracted_id and ("youtube.com" in input_text or "youtu.be" in input_text):
            self._load_video_by_id(extracted_id)
            return

        # Get selected level and channel
        level = self.level_filter.currentText()
        
        # Determine strict channel browse mode
        identifier = selected_channel_handle or selected_channel_name
        is_channel_browse = (selected_channel_name != "Tất cả kênh" and not query)
        
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Đang tải...")
        
        async def search():
            try:
                selected_playlist_url = self.playlist_filter.currentData()
                selected_playlist_text = self.playlist_filter.currentText()
                
                # PRIORITY 1: Specific Playlist
                if selected_playlist_url and selected_playlist_url != "":
                    print(f"[YouTube] Mode: Playlist - {selected_playlist_text} ({selected_playlist_url})")
                    results = self.youtube_service.get_playlist_videos(selected_playlist_url)
                    if results:
                        return results
                    print("[YouTube] Playlist mode returned no results, falling back...")
                
                # PRIORITY 2: Strict Channel Browse (when no query and no playlist)
                if is_channel_browse:
                    print(f"[YouTube] Mode: Channel Browse - {identifier}")
                    return self.youtube_service.get_channel_videos(identifier)
                
                # PRIORITY 3: General Search
                print(f"[YouTube] Mode: General Search")
                search_parts = []
                if level != "Tất cả":
                    search_parts.append(f"JLPT {level}")
                if query:
                    search_parts.append(query)
                if selected_channel_name != "Tất cả kênh":
                    search_parts.append(selected_channel_name)
                
                final_query = " ".join(search_parts)
                print(f"[YouTube] Search Query: {final_query}")
                return self.youtube_service.search_videos(final_query)
            except Exception as e:
                print(f"[YouTube] Search Error: {e}")
                return {"error": str(e)}
        
        def update_ui(result):
            self.search_btn.setEnabled(True)
            self.search_btn.setText("Tìm kiếm")
            
            videos = []
            if isinstance(result, list):
                videos = result
            elif isinstance(result, dict):
                if "error" in result:
                    self.video_list.clear()
                    self.video_list.addItem(f"Lỗi: {result['error']}")
                    return
                elif "videos" in result:
                    videos = result["videos"]

            # Explicit filtering by channel if selected
            if selected_channel_name != "Tất cả kênh":
                # Skip filtering if the channel name looks like a URL or Handle (contains @, http, www)
                # This fixes issues where user inputs "@handle" but YouTube API returns "Display Name"
                is_url_or_handle = any(x in selected_channel_name.lower() for x in ["@", "http", "www", ".com"])
                
                if not is_url_or_handle:
                    # Use a slightly loose match for channel names
                    filtered = []
                    # Clean up selected channel name for comparison
                    clean_target = selected_channel_name.lower().replace("channel", "").strip()
                    
                    for v in videos:
                        v_channel = v.get("channel_name", "").lower()
                        # Allow match if target is in channel name OR channel name is in target
                        if clean_target in v_channel or v_channel in clean_target:
                            filtered.append(v)
                    
                    # Only apply filter if it didn't remove everything
                    # If filter resulted in 0 videos, it's likely a name mismatch, so show all search results
                    if filtered:
                        videos = filtered

            if videos:
                self.video_list.clear()
                for video in videos:
                    video_id = video.get("id") or video.get("video_id")
                    title = video.get("title", "Unknown")
                    channel_name = video.get("channel_name", "")
                    duration = video.get("duration", 0)
                    
                    minutes = duration // 60
                    seconds = duration % 60
                    duration_str = f"{minutes}:{seconds:02d}"
                    
                    item_text = f"{title}\n{channel_name} - {duration_str}"
                    self.video_list.addItem(item_text)
                    self.video_list.item(self.video_list.count() - 1).setData(Qt.UserRole, video_id)
                
                if self.video_list.count() > 0:
                    self.video_list.setCurrentRow(0)
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(100, lambda: self._load_video(self.video_list.currentItem()))
            else:
                self.video_list.clear()
                self.video_list.addItem("Không tìm thấy video nào phù hợp với bộ lọc")

        run_async(search, update_ui)
    
    def _on_player_title_changed(self, title):
        """Handle title changes from the video player (used for detecting video changes)."""
        if title.startswith("VIDEO_ID:"):
            new_video_id = title.replace("VIDEO_ID:", "")
            if new_video_id and new_video_id != self.current_video_id:
                self._load_video_by_id(new_video_id)

    def _load_video(self, item):
        """Load video from list item."""
        if not item:
            return
        video_id = item.data(Qt.UserRole)
        self._load_video_by_id(video_id)

    def _load_video_by_id(self, video_id: str):
        """Core logic to load video and transcript by ID."""
        if not video_id:
            return
        
        # Always update current ID and search bar
        self.current_video_id = video_id
        self.search_input.setText(f"https://www.youtube.com/watch?v={video_id}")
        
        # Load video player
        if WEBENGINE_AVAILABLE and self.video_player:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            # YouTube embed options
            embed_url = (
                f"https://www.youtube-nocookie.com/embed/{video_id}"
                f"?enablejsapi=1"
                f"&rel=1"
                f"&modestbranding=1"
                f"&playsinline=1"
                f"&iv_load_policy=3"
            )
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    body {{
                        margin: 0;
                        padding: 0;
                        background-color: #000;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        overflow: hidden;
                        font-family: Arial, sans-serif;
                    }}
                    .video-container {{
                        position: relative;
                        width: 100%;
                        height: 100%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    iframe {{
                        width: 100%;
                        height: 100%;
                        border: none;
                    }}
                    .fallback-message {{
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        color: #fff;
                        text-align: center;
                        padding: 30px;
                        background-color: rgba(0, 0, 0, 0.95);
                        border-radius: 10px;
                        max-width: 800px;
                        width: 90%;
                        z-index: 10;
                    }}
                    .fallback-message.hidden {{
                        display: none;
                    }}
                    .fallback-message h3 {{
                        color: #ff6b6b;
                        margin-bottom: 15px;
                        font-size: 20px;
                    }}
                    .fallback-message p {{
                        margin: 10px 0;
                        line-height: 1.6;
                    }}
                    .fallback-message a {{
                        color: #4dabf7;
                        text-decoration: none;
                        font-weight: bold;
                    }}
                    .fallback-message a:hover {{
                        text-decoration: underline;
                    }}
                    .thumbnail-container {{
                        margin: 20px 0;
                        cursor: pointer;
                        position: relative;
                    }}
                    .thumbnail-container img {{
                        max-width: 100%;
                        border-radius: 8px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.5);
                    }}
                    .play-overlay {{
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        width: 80px;
                        height: 80px;
                        background-color: rgba(255, 0, 0, 0.9);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 30px;
                    }}
                </style>
                <script>
                    (function() {{
                        let fallbackShown = false;
                        let player = null;
                        
                        function showFallback() {{
                            fallbackShown = true;
                            let fallback = document.getElementById('fallback-msg');
                            if (fallback) {{
                                fallback.classList.remove('hidden');
                                if (iframe) {{
                                    iframe.style.display = 'none';
                                }}
                            }}
                        }}
                        
                        // YouTube IFrame API
                        function onYouTubeIframeAPIReady() {{
                            if (typeof YT === 'undefined' || !YT.Player) {{
                                console.log('YouTube IFrame API not loaded');
                                return;
                            }}
                            
                            try {{
                                player = new YT.Player('youtube-player', {{
                                    videoId: '{video_id}',
                                    playerVars: {{
                                        'enablejsapi': 1,
                                        'rel': 1,
                                        'modestbranding': 1,
                                        'playsinline': 1,
                                        'iv_load_policy': 3
                                    }},
                                    events: {{
                                        'onReady': onPlayerReady,
                                        'onStateChange': onPlayerStateChange,
                                        'onError': onPlayerError
                                    }}
                                }});
                            }} catch (e) {{
                                console.log('Failed to create YouTube player:', e);
                                showFallback();
                            }}
                        }}
                        
                        function onPlayerReady(event) {{
                            console.log('YouTube player ready');
                            // Store player globally so Python can access it
                            window.player = player;
                        }}
                        
                        function onPlayerStateChange(event) {{
                            // When playing (state=1) or serving cued (state=5), update title with ID to notify Python
                            if (event.data == YT.PlayerState.PLAYING || event.data == YT.PlayerState.CUED) {{
                                var data = player.getVideoData();
                                if (data && data.video_id) {{
                                    document.title = "VIDEO_ID:" + data.video_id;
                                }}
                            }}
                        }}
                        
                        function onPlayerError(event) {{
                            console.log('YouTube player error:', event.data);
                                    showFallback();
                                }}
                        
                        // Load YouTube IFrame API
                        if (typeof YT === 'undefined') {{
                            let tag = document.createElement('script');
                            tag.src = 'https://www.youtube.com/iframe_api';
                            let firstScriptTag = document.getElementsByTagName('script')[0];
                            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
                            
                            // Set callback
                            window.onYouTubeIframeAPIReady = onYouTubeIframeAPIReady;
                        }} else {{
                            onYouTubeIframeAPIReady();
                        }}
                    }})();
                </script>
            </head>
            <body>
                <div class="video-container">
                    <div id="youtube-player"></div>
                    <div class="fallback-message hidden" id="fallback-msg">
                        <h3>⚠ Video không thể phát trong ứng dụng</h3>
                        <p>Một số video YouTube không cho phép nhúng hoặc bị chặn theo khu vực.</p>
                        <div class="thumbnail-container" onclick="window.open('{video_url}', '_blank')">
                            <img src="{thumbnail_url}" alt="Video thumbnail" onerror="this.src='https://img.youtube.com/vi/{video_id}/hqdefault.jpg'">
                            <div class="play-overlay">▶</div>
                        </div>
                        <p>Nhấn vào hình ảnh hoặc nút <strong>"🌐 Mở trong trình duyệt"</strong> ở phía trên để xem video.</p>
                        <p>Hoặc truy cập trực tiếp: <a href="{video_url}" target="_blank">{video_url}</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            self.video_player.setHtml(html_content, QUrl("https://www.youtube-nocookie.com"))
            
            
            # Enable open browser button
            if hasattr(self, 'open_browser_btn'):
                self.open_browser_btn.setEnabled(True)
        elif not WEBENGINE_AVAILABLE:
            # Fallback: open in browser
            import webbrowser
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            webbrowser.open(video_url)
            toast_info(
                "Video đã được mở trong trình duyệt. Cài đặt PySide6-WebEngine để xem trực tiếp trong ứng dụng."
            )
        
        # Update UI directly (already in main thread)
        self.transcript_viewer.setText("Đang tải transcript...")
        
        async def fetch_transcript():
            try:
                return self.youtube_service.get_transcript(video_id)
            except Exception as e:
                print(f"[ERROR] Transcript fetch failed: {e}")
                return {"error": str(e)}
        
        def on_transcript_result(result: Dict) -> None:
            if "error" in result:
                self.transcript_viewer.setText(f"Lỗi: {result['error']}")
                self.transcript_segments = []
            else:
                segments = result.get('segments', [])
                transcript_text = result.get('transcript', '')
                
                if segments and len(segments) > 0:
                    # Store segments for highlighting
                    self.transcript_segments = segments
                    # Display transcript with HTML for highlighting
                    self._display_transcript_with_html(segments)
                elif transcript_text:
                    # Fallback to plain text if no segments
                    self.transcript_viewer.setText(transcript_text)
                    self.transcript_segments = []
                else:
                    self.transcript_viewer.setText("Video này không có transcript.")
                    self.transcript_segments = []
        
        run_async(fetch_transcript, on_transcript_result)
        
        # Load related videos
        self._load_related_videos(video_id)
        
        # Set optimal splitter sizes for better video viewing experience
        # Use QTimer to ensure widgets are rendered before setting sizes
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._set_optimal_splitter_sizes)
    
    def _load_related_video(self, item):
        """Load a related video when clicked."""
        if not item:
            return
        
        video_id = item.data(Qt.UserRole)
        if not video_id:
            return
        
        self._load_video_by_id(video_id)
    
    def _load_related_videos(self, video_id: str):
        """Load related videos from the same channel."""
        async def load_related():
            try:
                return self.youtube_service.get_related_videos(video_id)
            except Exception as e:
                print(f"[ERROR youtube_tab] Failed to load related videos: {e}")
                return {"videos": []}
        
        def update_ui(result):
            self.related_videos_list.clear()
            videos = result.get("videos", [])
            if videos:
                for video in videos:
                    # Support both 'id' and 'video_id' for robust mapping
                    video_id_rel = video.get("id") or video.get("video_id")
                    title = video.get("title", "Unknown")
                    channel = video.get("channel_name", "")
                    duration = video.get("duration", 0)
                    
                    # Format duration
                    minutes = duration // 60
                    seconds = duration % 60
                    duration_str = f"{minutes}:{seconds:02d}"
                    
                    item_text = f"{title}\n{channel} - {duration_str}"
                    self.related_videos_list.addItem(item_text)
                    # Store video_id in item data
                    self.related_videos_list.item(self.related_videos_list.count() - 1).setData(Qt.UserRole, video_id_rel)
            else:
                self.related_videos_list.addItem("Không có video liên quan")
        
        run_async(load_related, update_ui)
    
    def _set_optimal_splitter_sizes(self):
        """Set optimal sizes for content splitter to make video player larger by default."""
        # Get total height of the content splitter
        total_height = self.content_splitter.height()
        
        if total_height > 100:  # Only set if widget is properly sized
            # Video player gets 70% of height, transcript gets 30%
            video_height = int(total_height * 0.7)
            transcript_height = int(total_height * 0.3)
            
            # Set the sizes
            self.content_splitter.setSizes([video_height, transcript_height])
            
            # Debug log
            print(f"[YouTube] Set splitter sizes - Video: {video_height}px, Transcript: {transcript_height}px")
    
    def _toggle_transcript_visibility(self):
        """Toggle transcript panel visibility using button in search bar."""
        self.transcript_panel_hidden = not self.transcript_panel_hidden
        
        if self.transcript_panel_hidden:
            # Hide transcript panel
            self.transcript_panel.hide()
            self.show_transcript_btn.setToolTip("Hiển thị Transcript")
            self.show_transcript_btn.setStyleSheet("border-radius: 17px; background: #2c3e50; color: white;")
            
            # Adjust vertical splitter to give all space to video (top widget)
            sizes = self.content_splitter.sizes()
            total = sum(sizes)
            self.content_splitter.setSizes([total, 0])
        else:
            # Show transcript panel
            self.transcript_panel.show()
            self.show_transcript_btn.setToolTip("Ẩn Transcript")
            self.show_transcript_btn.setStyleSheet("border-radius: 17px; background: #57606f; color: white;")
            
            # Restore splitter sizes (70% video, 30% transcript)
            total_height = self.content_splitter.height()
            if total_height > 0:
                self.content_splitter.setSizes([int(total_height * 0.7), int(total_height * 0.3)])
            else:
                self.content_splitter.setSizes([500, 200])
    
    def _open_video_in_browser(self, video_id: str = None):
        """Open video in default browser."""
        if not video_id:
            video_id = self.current_video_id
        if not video_id:
            QMessageBox.warning(self, "Cảnh báo", "Không có video nào được chọn!")
            return
        
        import webbrowser
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        webbrowser.open(video_url)
    
    def _show_transcript_context_menu(self, position: QPoint):
        """Show context menu for transcript viewer - uses TextContextMenuMixin."""
        # Get selected text using mixin helper
        selected_text = self._get_selected_text_from_widget(self.transcript_viewer)
        
        if not selected_text:
            return
        
        # Create base menu from mixin (includes all translation options + Gemini AI + dictionary + TTS)
        menu = self.create_text_context_menu(selected_text)
        
        menu.addSeparator()
        
        # YouTube-specific: Save to Vocab/Flashcard
        save_vocab_action = QAction("💾 Lưu vào Flashcard", self)
        save_vocab_action.triggered.connect(
            lambda: self._save_word_to_vocab(selected_text)
        )
        menu.addAction(save_vocab_action)
        
        # Show menu at cursor position
        menu.exec(self.transcript_viewer.mapToGlobal(position))

    
    def _translate_selected_text(self, text: str, source_lang: str = "auto", target_lang: str = None):
        """Translate selected text.
        
        This method is now largely redundant as TextContextMenuMixin provides it,
        but we keep it if any YouTube-specific logic is needed.
        """
        # However, we fix it to not use self.client.
        
        async def translate():
            try:
                from frontend.services.translator import TranslatorService
                if source_lang == "auto" and target_lang is None:
                    # Implement auto-detect logic similar to mixin
                    detected_lang = detect_language(text)
                    translations = {}
                    
                    if detected_lang in ["ja", "jp"]:
                        translations["English"] = TranslatorService.translate(text, "ja", "en")
                        translations["Tiếng Việt"] = TranslatorService.translate(text, "ja", "vi")
                    elif detected_lang == "en":
                        translations["Tiếng Việt"] = TranslatorService.translate(text, "en", "vi")
                        translations["日本語"] = TranslatorService.translate(text, "en", "ja")
                    else:
                        translations["English"] = TranslatorService.translate(text, detected_lang, "en")
                        translations["Tiếng Việt"] = TranslatorService.translate(text, detected_lang, "vi")
                    
                    return {"success": True, "original": text, "detected_lang": detected_lang, "translations": translations}
                else:
                    t_lang = target_lang or "vi"
                    result = TranslatorService.translate(text, source_lang, t_lang)
                    return {"success": True, "result": {"translated": result}}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def show_result(result):
            if result.get("success"):
                if "translations" in result:
                    self._show_translation_dialog(text, result.get("detected_lang", "auto"), result.get("translations", {}))
                else:
                    trans_result = result.get("result", {})
                    translated_text = trans_result.get("translated", "")
                    lang_names = {"en": "English", "ja": "日本語", "vi": "Tiếng Việt"}
                    translations = {lang_names.get(target_lang or "vi", "Dịch"): translated_text}
                    self._show_translation_dialog(text, source_lang, translations)
            else:
                QMessageBox.warning(self, "Lỗi dịch", f"Không thể dịch văn bản: {result.get('error', 'Unknown error')}")
        
        run_async(translate, show_result)
    
    def _show_translation_dialog(self, original_text: str, source_lang: str, translations: dict):
        """Show translation result in a dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Kết quả dịch")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Original text
        layout.addWidget(QLabel(f"<b>Văn bản gốc ({source_lang}):</b>"))
        original_label = QLabel(original_text)
        original_label.setWordWrap(True)
        original_label.setStyleSheet(f"background-color: {ThemeColors.BG_TERTIARY}; padding: 5px; border: 1px solid {ThemeColors.BORDER}; color: {ThemeColors.TEXT_PRIMARY};")
        layout.addWidget(original_label)
        
        # Translations
        layout.addWidget(QLabel("<b>Bản dịch:</b>"))
        for lang, translated_text in translations.items():
            lang_label = QLabel(f"<b>{lang}:</b>")
            layout.addWidget(lang_label)
            
            # Check if this is Japanese translation with hiragana
            if isinstance(translated_text, dict) and "with_hiragana" in translated_text:
                # Show version with hiragana
                trans_label = QLabel(translated_text["with_hiragana"])
                trans_label.setWordWrap(True)
                trans_label.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; padding: 5px; border: 1px solid {ThemeColors.BORDER}; margin-bottom: 5px; font-size: 14px; color: {ThemeColors.TEXT_PRIMARY};")
                layout.addWidget(trans_label)
                
                # Also show original without hiragana in smaller text
                if translated_text.get("original"):
                    original_label = QLabel(f"<i>({translated_text['original']})</i>")
                    original_label.setWordWrap(True)
                    original_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; padding: 2px; margin-bottom: 10px; font-size: 12px;")
                    layout.addWidget(original_label)
            else:
                trans_label = QLabel(translated_text)
                trans_label.setWordWrap(True)
                trans_label.setStyleSheet(f"background-color: {ThemeColors.BG_SECONDARY}; padding: 5px; border: 1px solid {ThemeColors.BORDER}; margin-bottom: 10px; color: {ThemeColors.TEXT_PRIMARY};")
                layout.addWidget(trans_label)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
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
    
    def _display_transcript_with_html(self, segments):
        """Display transcript with optimized text insertion for fast highlighting."""
        if not segments:
            return
        
        # Reset state
        self.current_highlighted_segment = None
        self.user_is_selecting_text = False
        self.segment_ranges = []
        
        self.transcript_viewer.clear()
        
        # We use a cursor to insert text and track positions
        cursor = self.transcript_viewer.textCursor()
        
        # Set basic format
        fmt = cursor.charFormat()
        fmt.setFontFamily("Arial")
        fmt.setFontPointSize(12)
        cursor.setCharFormat(fmt)
        
        for i, segment in enumerate(segments):
            text = segment.get('text', '').strip()
            if not text:
                self.segment_ranges.append(None)
                continue
                
            start_pos = cursor.position()
            cursor.insertText(text + " ")
            end_pos = cursor.position()
            
            self.segment_ranges.append((start_pos, end_pos))
        
        # Scroll to top
        self.transcript_viewer.moveCursor(QTextCursor.Start)
        
        # Start timer to update highlight
        self._start_highlight_timer()
    
    def _start_highlight_timer(self):
        """Start timer to update transcript highlight based on video time."""
        from PySide6.QtCore import QTimer
        
        if self.highlight_timer:
            self.highlight_timer.stop()
            self.highlight_timer.deleteLater()
        
        # Create QTimer with self as parent to ensure proper lifecycle management
        self.highlight_timer = QTimer(self)
        # Use lambda to wrap the method call to avoid slot lookup issues
        self.highlight_timer.timeout.connect(lambda: self._do_highlight_update())
        self.highlight_timer.start(100)  # Update every 100ms for smooth highlighting
        
    def _do_highlight_update(self):
        """Wrapper for transcript highlight update to avoid Qt slot issues."""
        try:
            self._update_transcript_highlight()
        except Exception as e:
            # Silently ignore errors to prevent timer spam in console
            pass
    
    def _on_selection_changed(self):
        """Handle text selection change - pause highlighting while selecting."""
        cursor = self.transcript_viewer.textCursor()
        self.user_is_selecting_text = cursor.hasSelection()
    
    def _update_transcript_highlight(self):
        """Update transcript highlight based on current video time."""
        if not self.video_player or not self.transcript_segments:
            return
        
        # Don't update highlight if user is selecting text
        if self.user_is_selecting_text:
            return
        
        # Get current time from YouTube player via JavaScript
        # Use YouTube IFrame API that was loaded in the HTML
        script = """
        (function() {
            try {
                // Check if player exists in parent window
                if (typeof window.player !== 'undefined' && window.player && window.player.getCurrentTime) {
                    return window.player.getCurrentTime();
                }
                // Fallback: try to get from iframe (may not work due to CORS)
                var iframe = document.getElementById('youtube-player');
                if (iframe && iframe.contentWindow) {
                    try {
                        // This will fail due to CORS, but we try anyway
                        var time = iframe.contentWindow.getCurrentTime();
                        return time;
                    } catch(e) {
                        // CORS error - expected
                    }
                }
            } catch(e) {
                // Ignore errors
            }
            return null;
        })();
        """
        
        def handle_time(time_result):
            """Handle time result from JavaScript."""
            try:
                if time_result and time_result != 'null':
                    current_time = float(time_result)
                    if current_time >= 0:
                        self._highlight_segment_at_time(current_time)
            except (ValueError, TypeError):
                pass
        
        # Execute JavaScript and get result
        self.video_player.page().runJavaScript(script, handle_time)
        
    def _highlight_segment_at_time(self, current_time):
        """Highlight transcript segment at given time using ExtraSelections."""
        if not self.transcript_segments or not self.segment_ranges:
            return
        
        if self.user_is_selecting_text:
            return
        
        HIGHLIGHT_OFFSET = 0.0 # Removing negative offset as faster 50ms timer should be enough
        adjusted_time = current_time + HIGHLIGHT_OFFSET
        
        # Find segment
        active_segment_idx = None
        for i, segment in enumerate(self.transcript_segments):
            start = segment.get('start', 0)
            duration = segment.get('duration', 0)
            end = start + duration
            
            if start <= adjusted_time < end:
                active_segment_idx = i
                break
        
        if active_segment_idx == self.current_highlighted_segment:
            return
        
        self.current_highlighted_segment = active_segment_idx
        
        # Create highligh selection
        selections = []
        
        if active_segment_idx is not None and active_segment_idx < len(self.segment_ranges):
            rng = self.segment_ranges[active_segment_idx]
            if rng:
                selection = QTextEdit.ExtraSelection()
                selection.format.setBackground(QColor(ThemeColors.PRIMARY_LIGHT)) # Light highlight
                selection.format.setProperty(QTextFormat.Property.UserProperty, True) # Mark as highlight
                
                cursor = self.transcript_viewer.textCursor()
                cursor.setPosition(rng[0])
                cursor.setPosition(rng[1], QTextCursor.KeepAnchor)
                selection.cursor = cursor
                selections.append(selection)
        
        self.transcript_viewer.setExtraSelections(selections)
        
        # Auto-scroll
        if active_segment_idx is not None:
             self._scroll_to_segment(active_segment_idx)

    def _scroll_to_segment(self, segment_idx):
        """Scroll transcript viewer to show specific segment."""
        if segment_idx is not None and segment_idx < len(self.segment_ranges):
             rng = self.segment_ranges[segment_idx]
             if rng:
                 cursor = self.transcript_viewer.textCursor()
                 cursor.setPosition(rng[0])
                 self.transcript_viewer.setTextCursor(cursor)
                 self.transcript_viewer.ensureCursorVisible()

    def _save_word_to_vocab(self, word: str):
        """Open dialog to save word to vocabulary with context."""
        context_sentence = ""
        
        # 1. Find context from transcript segments
        for segment in self.transcript_segments:
            seg_text = segment.get("text", "")
            if word in seg_text:
                context_sentence = seg_text
                break
        
        if not context_sentence:
            # Fallback
            context_sentence = word
            
        # 2. Async prepare data (translate context and word)
        self.transcript_viewer.setDisabled(True)  # Disable while loading
        
        async def prepare_data():
            try:
                # Basic language detection
                lang = detect_language(word)
                
                # Translate word to VI for meaning using local service
                from frontend.services.translator import TranslatorService
                meaning_val = TranslatorService.translate(word, "auto", "vi")
                
                # Translate context sentence
                ctx_val = TranslatorService.translate(context_sentence, "auto", "vi")
                
                return {
                    "meaning": meaning_val,
                    "context_trans": ctx_val,
                    "lang": lang
                }
                
                return {
                    "meaning": meaning_val,
                    "context_trans": ctx_val,
                    "lang": lang
                }
            except Exception as e:
                print(f"[ERROR] Prepare save data error: {e}")
                return {"error": str(e)}

        def on_prepared(result):
            self.transcript_viewer.setDisabled(False)
            
            meaning = result.get("meaning", "")
            ctx_trans = result.get("context_trans", "")
            lang = result.get("lang", "en")
            
            dialog = SaveVocabDialog(self, word, context_sentence, meaning, ctx_trans)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                
                # Prepare save data
                is_jp = lang in ['ja', 'jp', 'japanese']
                
                if is_jp:
                    save_data = {
                        "lang": "jp", # Must match backend expectation ('jp' or 'en')
                        "word_kanji": data["word"],
                        "word_kana": "", # Should Ideally fetch this too, but for now empty or same
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
                
                # Submit save
                self._submit_vocab_save(save_data)
        
        run_async(prepare_data, on_prepared)

    def _submit_vocab_save(self, data):
        """Submit data to vocab service."""
        async def save():
            try:
                return self.vocab_service.save(data)
            except Exception as e:
                return {"error": str(e)}
        
        def on_saved(result):
            if isinstance(result, dict) and result.get("error"):
                QMessageBox.warning(self, "Lỗi", f"Không thềElưu từ: {result['error']}")
            elif isinstance(result, dict) and not result.get("success", True):
                 # Some API returns might just be the object, or {success: false}
                 pass
            
            # Assuming success if no error (vocab_service.save usually returns the saved object)
            toast_success("Đã lưu từ vựng vào Flashcard!\nHãy kiểm tra trong Dashboard hoặc Từ vựng.")
        
        run_async(save, on_saved)


