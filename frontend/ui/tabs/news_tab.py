"""Real-time Tech Hub - Cyberpunk News Tab.

A bilingual (EN/JP) news aggregator for hardcore developers.
Features:
- Multi-source aggregation (Qiita, Hacker News, etc.)
- Furigana support for Japanese articles
- Smart filtering by tech tags
- Cyberpunk/Minimalist UI

Version: 2.0 - Complete redesign
"""

# Standard library
import asyncio
from typing import Optional, List
from datetime import datetime, timezone

# Third-party
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSplitter, QComboBox, QLineEdit,
    QProgressBar, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QFont, QColor
from frontend.ui.styles.theme import ThemeColors

# Local - UI widgets
from frontend.ui.widgets.news_card import NewsCard
from frontend.ui.widgets.language_toggle import LanguageToggle
from frontend.ui.widgets.article_reader import ArticleReader
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin

# Local - Services
from frontend.services.news.base_client import Article, SourceLanguage
from frontend.services.news.aggregator import TechHubAggregator
from frontend.services.news.smart_filter import SmartFilter, HARDCORE_TAGS
from frontend.services.news.cache_service import NewsCacheService


# =============================================================================
# ASYNC WORKER FOR NEWS FETCHING
# =============================================================================

class NewsFetchWorker(QObject):
    """Worker for fetching news in background thread."""
    
    finished = Signal(list)  # List of articles
    error = Signal(str)
    progress = Signal(int, str)  # percent, message
    
    def __init__(self, mode: str = "japan", tags: Optional[List[str]] = None):
        super().__init__()
        self.mode = mode
        self.tags = tags
        self._is_cancelled = False
        self._aggregator = None # Initialize in run()
    
    def cancel(self):
        """Cancel the fetch operation."""
        self._is_cancelled = True
    
    def run(self):
        """Fetch articles based on mode."""
        print(f"[NewsFetchWorker] Starting run() for mode={self.mode}")
        try:
            # Initialize aggregator here (on background thread)
            if self._aggregator is None:
                print("[NewsFetchWorker] Initializing TechHubAggregator...")
                self._aggregator = TechHubAggregator()
            
            print("[NewsFetchWorker] Creating event loop...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self._is_cancelled:
                print("[NewsFetchWorker] Cancelled before start")
                return
                
            self.progress.emit(20, f"Đang kết nối tới các nguồn tin ({self.mode})...")
            print(f"[NewsFetchWorker] Calling aggregator.fetch_all()...")
            
            # Use aggregator for multi-source fetching with 20s timeout
            articles = loop.run_until_complete(
                self._aggregator.fetch_all(
                    mode=self.mode,
                    tags=self.tags,
                    max_articles=40,
                    timeout_seconds=20  # 20 seconds per source
                )
            )
            
            print(f"[NewsFetchWorker] Got {len(articles)} articles")
            
            if self._is_cancelled:
                print("[NewsFetchWorker] Cancelled after fetch")
                return
            
            self.progress.emit(90, "Đang xử lý dữ liệu...")
            
            # Sort by date
            def normalize_dt(dt):
                if dt is None:
                    return datetime.min
                if dt.tzinfo is not None:
                    return dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt
            
            articles.sort(
                key=lambda a: normalize_dt(a.published_at),
                reverse=True
            )
            
            self.progress.emit(100, "Hoàn tất!")
            print(f"[NewsFetchWorker] Emitting finished signal with {len(articles)} articles")
            self.finished.emit(articles)
            
            loop.close()
            print("[NewsFetchWorker] Done!")
            
        except Exception as e:
            import traceback
            print(f"[NewsFetchWorker] ERROR: {e}")
            traceback.print_exc()
            self.error.emit(str(e))
        finally:
            if self._aggregator:
                # Ensure aggregator sessions are closed
                try:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self._aggregator.close())
                    loop.close()
                    print("[NewsFetchWorker] Aggregator closed")
                except:
                    pass


# =============================================================================
# MAIN NEWS TAB
# =============================================================================

class NewsTab(QWidget, TextContextMenuMixin):
    """Real-time Tech Hub - Cyberpunk News Tab.
    
    Features:
    - Language toggle: Global / Japan / Mixed
    - Masonry card layout
    - Furigana support for Japanese
    - Smart tag filtering
    """
    
    def __init__(self):
        super().__init__()
        self._articles: List[Article] = []
        self._current_mode = "japan"
        self._is_fetching = False
        self._worker = None
        self._worker_thread = None
        self._article_cards: List[NewsCard] = []
        self._new_articles_count = 0  # Count of new articles from background sync
        
        # In-memory cache: {(mode, tags_tuple): (timestamp, articles)}
        self._news_cache = {}
        self._cache_expiry = 300  # 5 minutes
        
        # SQLite cache service for offline storage
        self._cache_service = NewsCacheService(user_id=1)
        
        # Background sync service
        self._setup_background_sync()
        
        self._init_ui()
        
        # Auto-load after UI is ready
        QTimer.singleShot(500, self._refresh_articles)
    
    def _setup_background_sync(self):
        """Initialize background sync service."""
        try:
            from frontend.services.news.background_sync import get_background_sync_service
            
            self._sync_service = get_background_sync_service()
            self._sync_service.set_mode(self._current_mode)
            
            # Connect signals
            self._sync_service.new_articles_available.connect(self._on_new_articles_available)
            self._sync_service.sync_started.connect(self._on_sync_started)
            self._sync_service.sync_completed.connect(self._on_sync_completed)
            
            # Start background sync
            self._sync_service.start()
            
            print("[NewsTab] Background sync service started")
        except Exception as e:
            print(f"[NewsTab] Failed to start background sync: {e}")
            self._sync_service = None
    
    def _on_new_articles_available(self, new_count: int):
        """Handle new articles notification from background sync."""
        self._new_articles_count += new_count
        self._update_refresh_button_badge()
        print(f"[NewsTab] {new_count} new articles available (total: {self._new_articles_count})")
    
    def _on_sync_started(self):
        """Handle background sync started."""
        # Optional: show subtle indicator
        pass
    
    def _on_sync_completed(self, total: int):
        """Handle background sync completed."""
        # Optional: log completion
        pass
    
    def _update_refresh_button_badge(self):
        """Update refresh button to show new article count."""
        if self._new_articles_count > 0:
            self.refresh_btn.setText(f"🔄 Làm mới ({self._new_articles_count} mới)")
            self.refresh_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.ACCENT};
                    color: {ThemeColors.TEXT_INVERSE};
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {ThemeColors.ACCENT};
                }}
            """)
        else:
            self.refresh_btn.setText("🔄 Làm mới")
            self.refresh_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.BG_TERTIARY};
                    color: {ThemeColors.TEXT_PRIMARY};
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {ThemeColors.SECONDARY};
                }}
                QPushButton:disabled {{
                    background-color: {ThemeColors.BG_SECONDARY};
                    color: {ThemeColors.TEXT_SECONDARY};
                }}
            """)
    
    def _init_ui(self):
        """Initialize the Cyberpunk UI."""
        # Apply dark background
        self.setStyleSheet(f"""
            NewsTab {{
                background-color: {ThemeColors.BG_PRIMARY};
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === HEADER BAR ===
        header = self._create_header()
        main_layout.addWidget(header)
        
        # === PROGRESS BAR ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeColors.BG_PRIMARY};
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.PRIMARY};
            }}
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)
        
        # === STATUS LABEL ===
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.TEXT_SECONDARY};
                font-size: 12px;
                padding: 8px 20px;
                background-color: {ThemeColors.BG_PRIMARY};
            }}
        """)
        self.status_label.hide()
        main_layout.addWidget(self.status_label)
        
        # === CONTENT AREA (Scrollable) ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {ThemeColors.BG_PRIMARY};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {ThemeColors.BG_PRIMARY};
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {ThemeColors.BORDER};
                border-radius: 4px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {ThemeColors.PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        # Content container
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {ThemeColors.BG_PRIMARY};
            }}
        """)
        
        self.cards_layout = QVBoxLayout(self.content_widget)
        self.cards_layout.setContentsMargins(20, 20, 20, 20)
        self.cards_layout.setSpacing(0)
        
        # Grid container for masonry-like layout
        self.grid_widget = QWidget()
        self.grid_layout = QHBoxLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        
        self.cards_layout.addWidget(self.grid_widget)
        self.cards_layout.addStretch()
        
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_header(self) -> QFrame:
        """Create the header bar with controls."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-bottom: 1px solid {ThemeColors.BORDER};
            }}
        """)
        
        # Use VBoxLayout to stack Title and Controls vertically
        # This prevents overlapping on small screens
        main_layout = QVBoxLayout(header)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # === Row 1: Title Area ===
        title_row = QHBoxLayout()
        
        title_info = QVBoxLayout()
        title_info.setSpacing(2)
        
        title = QLabel("⚡ Real-time Tech Hub")
        title.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-size: 18px; font-weight: bold; background: transparent;")
        title_info.addWidget(title)
        
        subtitle = QLabel("Tin công nghệ song ngữ cho Developer")
        subtitle.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        title_info.addWidget(subtitle)
        
        title_row.addLayout(title_info)
        title_row.addStretch() # Spacer
        
        main_layout.addLayout(title_row)
        
        # === Row 2: Controls Area ===
        controls_row = QHBoxLayout()
        controls_row.setSpacing(10)
        
        # 1. Language Toggle
        self.language_toggle = LanguageToggle()
        self.language_toggle.language_changed.connect(self._on_language_changed)
        controls_row.addWidget(self.language_toggle)
        
        # 2. Tag Filter
        self.tag_combo = QComboBox()
        self.tag_combo.addItem("📋 Tất cả tags", None)
        self.tag_combo.addItem("🐍 Python", ["Python"])
        self.tag_combo.addItem("🤖 AI/ML", ["MachineLearning", "AI", "DeepLearning"])
        self.tag_combo.addItem("🔮 LLM/GenAI", ["LLM", "OpenAI", "ChatGPT", "GenAI"])
        self.tag_combo.addItem("🐳 DevOps", ["Docker", "Kubernetes", "GitHub"])
        self.tag_combo.addItem("🎮 GPU/CUDA", ["GPU", "CUDA", "NVIDIA"])
        self.tag_combo.setMinimumWidth(120) # Slightly reduced min width
        self.tag_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ThemeColors.BG_PRIMARY};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 12px;
            }}
            QComboBox:hover {{ border-color: {ThemeColors.PRIMARY}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {ThemeColors.TEXT_SECONDARY};
                margin-right: 8px;
            }}
        """)
        self.tag_combo.currentIndexChanged.connect(self._on_tag_filter_changed)
        controls_row.addWidget(self.tag_combo, 1) # Give it stretch factor
        
        # 3. Refresh Button
        self.refresh_btn = QPushButton("🔄 Làm mới")
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY};
                color: {ThemeColors.TEXT_INVERSE};
                border: none;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.PRIMARY_HOVER}; }}
            QPushButton:disabled {{ background-color: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_SECONDARY}; }}
        """)
        self.refresh_btn.clicked.connect(lambda: self._refresh_articles(force=True))
        controls_row.addWidget(self.refresh_btn)
        
        # 4. Saved Button
        self.saved_btn = QPushButton("⭐ Đã lưu")
        self.saved_btn.setToolTip("Xem bài viết đã lưu")
        self.saved_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.ACCENT};
                border: 1px solid {ThemeColors.ACCENT};
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.ACCENT}; color: {ThemeColors.BG_PRIMARY}; }}
        """)
        self.saved_btn.clicked.connect(self._show_saved_articles)
        controls_row.addWidget(self.saved_btn)

        main_layout.addLayout(controls_row)
        
        return header
    
    def _show_saved_articles(self):
        """Display only saved/bookmarked articles from cache."""
        try:
            saved_articles = self._cache_service.get_cached_articles(only_saved=True, limit=50)
            if saved_articles:
                self._clear_cards()
                self.status_label.setText(f"⭐ Hiển thị {len(saved_articles)} bài viết đã lưu")
                self.status_label.show()
                self._display_cards(saved_articles)
            else:
                self._clear_cards()
                self.status_label.setText("📭 Chưa có bài viết nào được lưu. Nhấn ☆ để lưu!")
                self.status_label.show()
        except Exception as e:
            print(f"[NewsTab] Error loading saved: {e}")
            self.status_label.setText("❌ Lỗi tải bài viết đã lưu")
            self.status_label.show()
    
    def _on_language_changed(self, mode: str):
        """Handle language toggle change."""
        self._current_mode = mode
        self._refresh_articles()
    
    def _on_tag_filter_changed(self, index: int):
        """Handle tag filter change."""
        self._refresh_articles()
    
    def _refresh_articles(self, force: bool = False):
        """Refresh articles from sources safely with caching."""
        if self._is_fetching:
            print("[NewsTab] Busy, ignoring request")
            return
            
        # Get selected tags as a hashable tuple
        selected_tags = self.tag_combo.currentData()
        tags_tuple = tuple(selected_tags) if selected_tags else None
        cache_key = (self._current_mode, tags_tuple)
        
        # Check cache
        import time
        if not force and cache_key in self._news_cache:
            timestamp, cached_articles = self._news_cache[cache_key]
            if time.time() - timestamp < self._cache_expiry:
                print(f"[NewsTab] Using cached articles for {cache_key}")
                self._on_articles_loaded(cached_articles)
                return
            
        self._is_fetching = True
        
        # Reset new articles badge
        self._new_articles_count = 0
        self._update_refresh_button_badge()
        
        # Update background sync mode
        if self._sync_service:
            self._sync_service.set_mode(self._current_mode)
        
        # Cancel any existing fetch properly
        if self._worker:
            self._worker.cancel()
        
        # Show loading state
        self._clear_cards()
        self._show_loading()
        
        # Lock UI
        self.refresh_btn.setEnabled(False)
        self.language_toggle.setEnabled(False)
        self.tag_combo.setEnabled(False)
        
        # Create worker & thread safely
        try:
            self._worker = NewsFetchWorker(
                mode=self._current_mode,
                tags=selected_tags
            )
            
            # Create thread
            self._worker_thread = QThread()
            self._worker.moveToThread(self._worker_thread)
            
            # Connect signals
            self._worker_thread.started.connect(self._worker.run)
            
            def on_finished(articles):
                # Update in-memory cache
                if articles:
                    self._news_cache[cache_key] = (time.time(), articles)
                    # Save to SQLite for offline access
                    try:
                        cached = self._cache_service.cache_articles(articles)
                        print(f"[NewsTab] Cached {cached} new articles to SQLite")
                    except Exception as e:
                        print(f"[NewsTab] Cache error: {e}")
                self._on_articles_loaded(articles)
                
            self._worker.finished.connect(on_finished)
            self._worker.error.connect(self._on_fetch_error)
            self._worker.progress.connect(self._on_fetch_progress)
            
            # Advanced Cleanup to prevent "thread destroyed while running" crash
            def cleanup():
                self._is_fetching = False
                self.refresh_btn.setEnabled(True)
                self.language_toggle.setEnabled(True)
                self.tag_combo.setEnabled(True)
                if self._worker_thread:
                    self._worker_thread.quit()
            
            self._worker.finished.connect(cleanup)
            self._worker.error.connect(cleanup)
            
            # Start
            print(f"[NewsTab] Starting worker thread for mode={self._current_mode}...")
            self._worker_thread.start()
            print("[NewsTab] Worker thread started")
            
        except Exception as e:
            print(f"[NewsTab] Error creating worker: {e}")
            import traceback
            traceback.print_exc()
            self._is_fetching = False
            self.refresh_btn.setEnabled(True)
            self.language_toggle.setEnabled(True)
            self.tag_combo.setEnabled(True)
            self._on_fetch_error(f"Không thể khởi tạo bộ tải tin: {e}")
    
    def _show_loading(self):
        """Show loading state."""
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.status_label.setText("🔄 Đang tải tin tức...")
        self.status_label.show()
    
    def _hide_loading(self):
        """Hide loading state."""
        self.progress_bar.hide()
        self.status_label.hide()
    
    def _on_fetch_progress(self, percent: int, message: str):
        """Update progress bar."""
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"🔄 {message}")
    
    def _on_articles_loaded(self, articles: List[Article]):
        """Handle loaded articles."""
        self._hide_loading()
        self._articles = articles
        
        if not articles:
            # Try loading from SQLite cache as fallback
            try:
                mode_lang = self._current_mode
                cached_articles = self._cache_service.get_cached_articles(
                    language=mode_lang, limit=40
                )
                if cached_articles:
                    print(f"[NewsTab] Loaded {len(cached_articles)} articles from offline cache")
                    self.status_label.setText("📦 Đang hiển thị tin từ bộ nhớ đệm (offline)")
                    self.status_label.show()
                    self._display_cards(cached_articles)
                    return
            except Exception as e:
                print(f"[NewsTab] Failed to load cache: {e}")
            
            # No online and no cache
            msg = "📭 Không tìm thấy bài viết nào."
            if self._current_mode in ["japan", "mixed"]:
                msg += " (Có thể do giới hạn API Qiita, hãy thử lại sau ít phút)"
            
            self.status_label.setText(msg)
            self.status_label.show()
        else:
            self._display_cards(articles)
    
    def _on_fetch_error(self, error: str):
        """Handle fetch error."""
        self._hide_loading()
        msg = f"❌ Lỗi: {error}"
        if "403" in error or "Rate limit" in error:
            msg = "⚠️ Giới hạn tốc độ truy cập (Rate Limit). Hãy đợi 5-10 phút."
        elif "timeout" in error.lower() or "Timeout" in error:
            msg = "⏱️ Kết nối quá chậm. Đang tải từ bộ nhớ đệm..."
            
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.DANGER};
                font-size: 12px;
                padding: 8px 20px;
                line-height: 1.4;
                background-color: {ThemeColors.BG_PRIMARY};
            }}
        """)
        self.status_label.show()
        
        # Try to load from cache as fallback
        try:
            cached_articles = self._cache_service.get_cached_articles(
                language=self._current_mode, limit=40
            )
            if cached_articles:
                print(f"[NewsTab] Loaded {len(cached_articles)} from cache after error")
                self._display_cards(cached_articles)
                self.status_label.setText(f"📦 Hiển thị {len(cached_articles)} tin từ bộ nhớ đệm (offline)")
        except Exception as e:
            print(f"[NewsTab] Cache fallback failed: {e}")
    
    def _clear_cards(self):
        """Clear all article cards."""
        for card in self._article_cards:
            card.deleteLater()
        self._article_cards.clear()
        
        # Clear existing grid columns
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _display_cards(self, articles: List[Article]):
        """Display articles as cards in grid."""
        self._clear_cards()
        
        # Create column containers
        num_columns = 3
        columns = []
        
        for _ in range(num_columns):
            col_widget = QWidget()
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(0, 0, 0, 0)
            col_layout.setSpacing(16)
            col_layout.setAlignment(Qt.AlignTop)
            columns.append((col_widget, col_layout))
            self.grid_layout.addWidget(col_widget)
        
        # Distribute cards across columns (round-robin)
        for i, article in enumerate(articles):
            col_idx = i % num_columns
            
            card = NewsCard(article)
            card.clicked.connect(self._on_card_clicked)
            card.save_clicked.connect(self._on_save_clicked)
            
            columns[col_idx][1].addWidget(card)
            self._article_cards.append(card)
        
        # Add stretch to each column
        for col_widget, col_layout in columns:
            col_layout.addStretch()
    
    def _on_save_clicked(self, article: Article, is_saved: bool):
        """Handle save/bookmark toggle from card."""
        try:
            url = getattr(article, 'url', None)
            if url:
                result = self._cache_service.toggle_saved(url)
                if result is not None:
                    print(f"[NewsTab] Article {'saved' if result else 'unsaved'}: {url[:50]}...")
                else:
                    # Article not in cache yet, cache it first
                    self._cache_service.cache_articles([article])
                    self._cache_service.toggle_saved(url)
                    print(f"[NewsTab] Cached and saved: {url[:50]}...")
        except Exception as e:
            print(f"[NewsTab] Save error: {e}")
    
    def _on_card_clicked(self, article: Article):
        """Handle card click - open reader."""
        reader = ArticleReader(article, self)
        reader.speak_text.connect(self._speak_text)
        reader.exec()
    
    def _speak_text(self, text: str):
        """TTS for article content."""
        try:
            # Detect language from first article source or content
            source_name = getattr(self._articles[0], 'source_name', '') if self._articles else ''
            is_japanese = source_name in ["Qiita", "Zenn", "Hatena"]
            
            # For NewsTab, we just use the mixin's speak method which handles synthesis and playback
            self._mixin_speak_text(text[:500])
        except Exception as e:
            print(f"[ERROR NewsTab] TTS failed: {e}")
    
    # Context menu methods from mixin
    def _show_context_menu(self, position):
        """Show context menu - uses TextContextMenuMixin."""
        pass  # Implemented by cards and reader
