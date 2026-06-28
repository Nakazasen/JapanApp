"""Article reader widget with Furigana support.

Full-screen reader mode for articles with:
- Clean typography
- Furigana toggle for Japanese (displayed as parentheses since QTextBrowser doesn't support ruby)
- TTS support with Play/Stop
- Dictionary lookup on text selection (using TextContextMenuMixin)
"""

import re
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget, QCheckBox, QMessageBox, QMenu,
    QSlider
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QDesktopServices, QCursor, QAction
from PySide6.QtCore import QUrl

# Import mixin for text context menu functionality
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin


from frontend.ui.styles.theme import ThemeColors

class ArticleReader(QDialog, TextContextMenuMixin):
    """Full-screen article reader with Furigana support.
    
    Features:
    - Dynamic Theme (Light/Dark)
    - Furigana toggle for Japanese text (parentheses format)
    - TTS Play/Pause/Resume button
    - Text selection context menu for dictionary lookup
    - External link opening
    """
    
    # Signals
    lookup_word = Signal(str)
    speak_text = Signal(str)
    
    def __init__(self, article, parent=None):
        super().__init__(parent)
        self.article = article
        self._furigana_enabled = True
        self._furigana_service = None
        self._clean_content = ""  # Plain text for TTS
        self._tts_state = "stopped"  # "stopped", "synthesizing", "playing", "paused"
        self._tts_thread = None
        self._tts_speed = 1.0  # TTS speed multiplier
        
        self._setup_ui()
        self._load_content()
    
    def _get_furigana_service(self):
        """Lazy-load furigana service."""
        if self._furigana_service is None:
            try:
                # Lazy import to avoid module loading issues in QThread
                from frontend.services.japanese.furigana_service import FuriganaService
                self._furigana_service = FuriganaService()
            except Exception as e:
                print(f"[WARN ArticleReader] FuriganaService init failed: {e}")
        return self._furigana_service
    
    def _setup_ui(self):
        self.setWindowTitle("📖 Article Reader")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Theme colors for dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ThemeColors.BG_PRIMARY};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # === Header Bar ===
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-bottom: 1px solid {ThemeColors.BORDER};
                padding: 12px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        
        # Title
        source_name = getattr(self.article, 'source_name', '')
        self._is_japanese = source_name in ["Qiita", "Zenn", "Hatena"]
        
        title_icon = "🇯🇵" if self._is_japanese else "🌐"
        title_label = QLabel(f"{title_icon} {source_name}")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.PRIMARY};
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Furigana toggle (only for Japanese)
        if self._is_japanese:
            self.furigana_toggle = QCheckBox("振り仮名 (Furigana)")
            self.furigana_toggle.setChecked(self._furigana_enabled)
            self.furigana_toggle.setStyleSheet(f"""
                QCheckBox {{
                    color: {ThemeColors.TEXT_SECONDARY};
                    font-size: 12px;
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 4px;
                    background-color: {ThemeColors.BG_SECONDARY};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {ThemeColors.PRIMARY};
                    border-color: {ThemeColors.PRIMARY};
                }}
            """)
            self.furigana_toggle.toggled.connect(self._on_furigana_toggled)
            header_layout.addWidget(self.furigana_toggle)
        
        # TTS Play/Pause button
        self.tts_btn = QPushButton("🔊 Đọc bài")
        self.tts_btn.setMinimumWidth(100)
        
        # TTS Stop button (Always visible but disabled when stopped)
        self.stop_btn = QPushButton("⏹️ Dừng")
        self.stop_btn.setMinimumWidth(80)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover:enabled {{
                background-color: {ThemeColors.DANGER};
                color: white;
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.BG_PRIMARY};
                color: {ThemeColors.TEXT_SECONDARY};
            }}
        """)
        
        # Configure style
        self._update_tts_button_style("stopped")
        
        self.tts_btn.clicked.connect(self._on_tts_clicked)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        
        header_layout.addWidget(self.tts_btn)
        header_layout.addWidget(self.stop_btn)
        
        # TTS Speed control
        speed_label = QLabel("🚀")
        speed_label.setToolTip("Tốc độ đọc")
        speed_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY};")
        header_layout.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)   # 0.5x
        self.speed_slider.setMaximum(200)  # 2.0x
        self.speed_slider.setValue(100)     # 1.0x default
        self.speed_slider.setFixedWidth(80)
        self.speed_slider.setToolTip("Tốc độ đọc: 1.0x")
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        self.speed_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {ThemeColors.BORDER};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {ThemeColors.PRIMARY};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {ThemeColors.PRIMARY_HOVER};
            }}
        """)
        header_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("1.0x")
        self.speed_label.setFixedWidth(35)
        self.speed_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 11px;")
        header_layout.addWidget(self.speed_label)
        
        # Open in browser button
        open_btn = QPushButton("🔗 Mở nguồn")
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ThemeColors.PRIMARY};
                border: 1px solid {ThemeColors.PRIMARY};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.PRIMARY}20;
            }}
        """)
        open_btn.clicked.connect(self._open_in_browser)
        header_layout.addWidget(open_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ThemeColors.TEXT_SECONDARY};
                border: none;
                border-radius: 16px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.DANGER}20;
                color: {ThemeColors.DANGER};
            }}
        """)
        close_btn.clicked.connect(self._on_close)
        header_layout.addWidget(close_btn)
        
        layout.addWidget(header)
        
        # === Content Area ===
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.anchorClicked.connect(self._on_link_clicked)
        self.content_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.content_browser.customContextMenuRequested.connect(self._show_context_menu)
        self.content_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {ThemeColors.BG_PRIMARY};
                color: {ThemeColors.TEXT_PRIMARY};
                border: none;
                padding: 40px;
                selection-background-color: {ThemeColors.PRIMARY_LIGHT};
                selection-color: {ThemeColors.TEXT_INVERSE};
            }}
        """)
        
        layout.addWidget(self.content_browser)
        
        # Timer to check TTS status
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._check_tts_status)
    
    def _update_tts_button_style(self, state: str):
        """Update TTS UI based on state: stopped, synthesizing, playing, paused."""
        self.tts_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        if state == "synthesizing":
            self.tts_btn.setText("⏳ Đang tạo...")
            self.tts_btn.setEnabled(False)
            self.tts_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_SECONDARY}; border-radius: 6px; padding: 8px 16px; font-weight: bold; }}
            """)
            self.stop_btn.setEnabled(True)
            
        elif state == "playing":
            self.tts_btn.setText("⏸️ Tạm dừng")
            self.tts_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.ACCENT};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {ThemeColors.ACCENT_HOVER}; }}
            """)
            
        elif state == "paused":
            self.tts_btn.setText("▶️ Tiếp tục")
            self.tts_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.SUCCESS};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {ThemeColors.SUCCESS_HOVER}; }}
            """)
            
        else:  # stopped
            self.tts_btn.setText("🔊 Đọc bài")
            self.tts_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {ThemeColors.PRIMARY_HOVER}; }}
            """)
            self.stop_btn.setEnabled(False)
    
    def _show_context_menu(self, position):
        """Show context menu with dictionary lookup, translation, and TTS options.
        
        Uses TextContextMenuMixin for full functionality like YouTube tab.
        """
        selected_text = self.content_browser.textCursor().selectedText().strip()
        
        if not selected_text:
            # No selection - show simple menu
            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {ThemeColors.BG_SECONDARY};
                    color: {ThemeColors.TEXT_PRIMARY};
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 8px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 8px 20px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background-color: {ThemeColors.BG_TERTIARY};
                }}
            """)
            copy_action = QAction("📋 Sao chép (chọn text trước)", menu)
            copy_action.setEnabled(False)
            menu.addAction(copy_action)
            menu.exec(self.content_browser.mapToGlobal(position))
            return
        
        # Use mixin's full menu with translation, dictionary, and TTS
        menu = self.create_text_context_menu(selected_text)
        
        # Add copy action
        menu.addSeparator()
        copy_action = QAction("📋 Sao chép", menu)
        copy_action.triggered.connect(self.content_browser.copy)
        menu.addAction(copy_action)
        
        menu.exec(self.content_browser.mapToGlobal(position))
    
    def _lookup_word(self, word: str):
        """Lookup word in dictionary using TextContextMenuMixin."""
        # Use mixin method for proper dictionary lookup
        detected_lang = "ja" if self._is_japanese else "en"
        self._mixin_lookup_word(word, source_lang=detected_lang)
    
    def _speak_selected(self, text: str):
        """Speak the selected text using mixin method."""
        if not text:
            return
        # Use mixin method for TTS
        self._mixin_speak_text(text[:500])
    
    def _clean_html_content(self, content: str) -> str:
        """Clean HTML content - remove iframes, scripts, etc."""
        if not content:
            return ""
        
        # Remove iframe tags completely
        content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<iframe[^>]*/>', '', content, flags=re.IGNORECASE)
        
        # Remove script tags
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove style tags
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove video/audio embeds
        content = re.sub(r'<video[^>]*>.*?</video>', '[Video]', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<audio[^>]*>.*?</audio>', '[Audio]', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove object/embed tags
        content = re.sub(r'<object[^>]*>.*?</object>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<embed[^>]*/>', '', content, flags=re.IGNORECASE)
        
        # Clean up HTML entities
        content = content.replace('&nbsp;', ' ')
        
        return content
    
    def _add_furigana_parentheses(self, text: str) -> str:
        """Add furigana in parentheses format since QTextBrowser doesn't support ruby."""
        service = self._get_furigana_service()
        if not service:
            return text
        
        try:
            tokens = service.tokenize(text)
            result_parts = []
            
            for token in tokens:
                if token.is_kanji and token.reading and token.reading != token.text:
                    result_parts.append(
                        f'{token.text}<span style="color:{ThemeColors.ACCENT};'
                        f'font-size:0.75em;vertical-align:super;">({token.reading})</span>'
                    )
                else:
                    result_parts.append(token.text)
            
            return ''.join(result_parts)
        except Exception as e:
            print(f"[WARN] Furigana processing failed: {e}")
            return text
    
    def _process_content_with_furigana(self, content: str) -> str:
        """Process content adding furigana, but skip code blocks and URLs."""
        if not content:
            return ""
        
        content = self._clean_html_content(content)
        
        code_pattern = re.compile(r'(```[\s\S]*?```|`[^`]+`)')
        parts = code_pattern.split(content)
        result_parts = []
        
        for part in parts:
            if code_pattern.match(part):
                result_parts.append(part)
            else:
                url_pattern = re.compile(r'(https?://[^\s<>"]+)')
                sub_parts = url_pattern.split(part)
                
                processed_sub = []
                for sub in sub_parts:
                    if url_pattern.match(sub):
                        processed_sub.append(sub)
                    else:
                        processed_sub.append(self._add_furigana_parentheses(sub))
                
                result_parts.append(''.join(processed_sub))
        
        return ''.join(result_parts)
    
    def _load_content(self):
        """Load article content into the browser."""
        title = getattr(self.article, 'title', 'Untitled')
        content = getattr(self.article, 'content', '') or getattr(self.article, 'summary', '')
        author = getattr(self.article, 'author', '')
        url = getattr(self.article, 'url', '')
        tags = getattr(self.article, 'tags', [])
        published = getattr(self.article, 'published_at', None)
        
        # If no content, try to fetch from URL
        if not content and url:
            self._show_loading_content(title, author, url, tags, published)
            self._fetch_content_async(url)
            return
        
        self._render_content(title, content, author, url, tags, published)
    
    def _show_loading_content(self, title, author, url, tags, published):
        """Show loading indicator while fetching content."""
        pub_str = published.strftime("%Y-%m-%d %H:%M") if published else ""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: "Meiryo UI", "Segoe UI", Arial, sans-serif;
                    background-color: {ThemeColors.BG_PRIMARY};
                    color: {ThemeColors.TEXT_PRIMARY};
                    text-align: center;
                    padding: 40px 20px;
                }}
                h1 {{
                    font-size: 22px;
                    color: {ThemeColors.TEXT_PRIMARY};
                    margin-bottom: 16px;
                }}
                .meta {{ color: {ThemeColors.TEXT_SECONDARY}; font-size: 13px; margin-bottom: 30px; }}
                .loading {{
                    font-size: 16px;
                    color: {ThemeColors.PRIMARY};
                    animation: pulse 1.5s infinite;
                }}
                @keyframes pulse {{
                    0%, 100% {{ opacity: 0.5; }}
                    50% {{ opacity: 1; }}
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="meta">
                {'👤 ' + author + ' · ' if author else ''}
                {'📅 ' + pub_str if pub_str else ''}
            </div>
            <div class="loading">⏳ Đang tải nội dung bài viết...</div>
            <p style="color: {ThemeColors.TEXT_SECONDARY}; margin-top: 20px; font-size: 12px;">
                Đang trích xuất nội dung từ: {url[:60]}...
            </p>
        </body>
        </html>
        """
        self.content_browser.setHtml(html)
    
    def _fetch_content_async(self, url: str):
        """Fetch content from URL asynchronously."""
        import threading
        
        def fetch():
            try:
                from frontend.services.news.content_extractor import ContentExtractor
                import asyncio
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                text, html_content = loop.run_until_complete(ContentExtractor.extract_article(url))
                loop.close()
                
                # Update article with fetched content
                if text:
                    self.article.content = text
                    # Emit signal to update UI from main thread
                    QTimer.singleShot(0, self._on_content_fetched)
                else:
                    QTimer.singleShot(0, lambda: self._show_fetch_error("Không thể trích xuất nội dung"))
                    
            except Exception as e:
                print(f"[ArticleReader] Fetch error: {e}")
                QTimer.singleShot(0, lambda: self._show_fetch_error(str(e)))
        
        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
    
    def _on_content_fetched(self):
        """Called when content has been fetched."""
        title = getattr(self.article, 'title', 'Untitled')
        content = getattr(self.article, 'content', '')
        author = getattr(self.article, 'author', '')
        url = getattr(self.article, 'url', '')
        tags = getattr(self.article, 'tags', [])
        published = getattr(self.article, 'published_at', None)
        
        self._render_content(title, content, author, url, tags, published)
    
    def _show_fetch_error(self, error: str):
        """Show error message when content fetch fails."""
        url = getattr(self.article, 'url', '')
        title = getattr(self.article, 'title', 'Untitled')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: "Meiryo UI", "Segoe UI", Arial, sans-serif;
                    background-color: {ThemeColors.BG_PRIMARY};
                    color: {ThemeColors.TEXT_PRIMARY};
                    padding: 40px 20px;
                }}
                h1 {{ font-size: 22px; margin-bottom: 20px; }}
                .error {{ color: {ThemeColors.DANGER}; margin: 20px 0; }}
                .tip {{ 
                    background-color: {ThemeColors.BG_SECONDARY}; 
                    padding: 16px; 
                    border-radius: 8px; 
                    margin-top: 20px;
                    border: 1px solid {ThemeColors.BORDER};
                }}
                a {{ color: {ThemeColors.PRIMARY}; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p class="error">⚠️ Không thể tải nội dung bài viết</p>
            <p style="color: {ThemeColors.TEXT_SECONDARY};">Lỗi: {error}</p>
            <div class="tip">
                <p>💡 <b>Mẹo:</b> Nhấn nút <b>"Mở nguồn"</b> ở trên để đọc bài viết trực tiếp trên trình duyệt.</p>
                <p style="margin-top: 10px;">
                    <a href="{url}">🔗 {url[:80]}...</a>
                </p>
            </div>
        </body>
        </html>
        """
        self.content_browser.setHtml(html)
    
    def _render_content(self, title, content, author, url, tags, published):
        """Render article content to HTML."""
        # Store clean content for TTS
        self._clean_content = self._clean_html_content(content) if content else ""
        self._clean_content = re.sub(r'<[^>]+>', '', self._clean_content)
        
        # Clean content first
        content = self._clean_html_content(content) if content else ""
        
        # Process content for furigana if Japanese and enabled
        if self._is_japanese and self._furigana_enabled and content:
            title_with_furigana = self._add_furigana_parentheses(title)
            content_with_furigana = self._process_content_with_furigana(content)
        else:
            title_with_furigana = title
            content_with_furigana = content
        
        # Format published date
        pub_str = published.strftime("%Y-%m-%d %H:%M") if published else ""
        
        # Build tags HTML
        tags_html = ""
        if tags:
            tag_items = ''.join([
                f'<span style="background-color: {ThemeColors.PRIMARY}20; color: {ThemeColors.PRIMARY}; '
                f'padding: 4px 10px; border-radius: 12px; font-size: 11px; margin-right: 6px;">'
                f'{tag}</span>'
                for tag in tags[:8]
            ])
            tags_html = f'<div style="margin: 16px 0;">{tag_items}</div>'
        
        # Convert markdown-style content to HTML
        if content_with_furigana:
            # Code blocks - keep dark theme for code for contrast, or adapt?
            # Let's adapt to be neutral slate-800 for dark mode feel, or slate-100 for light.
            # safe option: ThemeColors.BG_TERTIARY (Slate 100) or Slate 900 depending on preference.
            # Using dark code blocks usually looks good in both.
            content_with_furigana = re.sub(
                r'```(\w*)\n?([\s\S]*?)```',
                f'<pre style="background-color: #1e293b; color: #f8fafc; padding: 16px; border-radius: 8px; '
                f'overflow-x: auto; border-left: 3px solid {ThemeColors.ACCENT}; margin: 16px 0;">'
                r'<code>\2</code></pre>',
                content_with_furigana
            )
            
            content_with_furigana = re.sub(
                r'`([^`]+)`', 
                f'<code style="background-color: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.DANGER}; padding: 2px 6px; border-radius: 4px;">\\1</code>', 
                content_with_furigana
            )
            
            # Headings
            content_with_furigana = re.sub(r'^### (.+)$', f'<h3 style="color: {ThemeColors.PRIMARY}; margin-top: 24px;">\\1</h3>', content_with_furigana, flags=re.MULTILINE)
            content_with_furigana = re.sub(r'^## (.+)$', f'<h2 style="color: {ThemeColors.PRIMARY}; margin-top: 24px;">\\1</h2>', content_with_furigana, flags=re.MULTILINE)
            content_with_furigana = re.sub(r'^# (.+)$', f'<h1 style="color: {ThemeColors.TEXT_PRIMARY}; margin-top: 24px;">\\1</h1>', content_with_furigana, flags=re.MULTILINE)
            
            lines = content_with_furigana.split('\n')
            formatted_lines = []
            in_pre = False
            for line in lines:
                if '<pre' in line:
                    in_pre = True
                if '</pre>' in line:
                    in_pre = False
                
                if not in_pre and line.strip() and not line.strip().startswith('<'):
                    formatted_lines.append(f'<p style="margin-bottom: 12px; line-height: 1.8;">{line}</p>')
                else:
                    formatted_lines.append(line)
            content_with_furigana = '\n'.join(formatted_lines)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: "Meiryo UI", "Yu Gothic UI", "Hiragino Kaku Gothic ProN", 
                                 "Segoe UI", Arial, sans-serif;
                    background-color: {ThemeColors.BG_PRIMARY};
                    color: {ThemeColors.TEXT_PRIMARY};
                    line-height: 1.8;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 0 20px;
                    font-size: 15px;
                }}
                h1 {{
                    font-size: 24px;
                    font-weight: bold;
                    color: {ThemeColors.TEXT_PRIMARY};
                    margin-bottom: 16px;
                    line-height: 1.5;
                    border-bottom: 2px solid {ThemeColors.PRIMARY};
                    padding-bottom: 16px;
                }}
                h2 {{ color: {ThemeColors.PRIMARY}; }}
                h3 {{ color: {ThemeColors.PRIMARY}; }}
                .meta {{
                    color: {ThemeColors.TEXT_SECONDARY};
                    font-size: 13px;
                    margin-bottom: 20px;
                }}
                .meta a {{
                    color: {ThemeColors.PRIMARY};
                    text-decoration: none;
                }}
                .content {{
                    font-size: 15px;
                    color: {ThemeColors.TEXT_PRIMARY};
                }}
                a {{
                    color: {ThemeColors.PRIMARY};
                    text-decoration: none;
                }}
                pre {{
                    background-color: #1e293b;
                    color: #f8fafc;
                    padding: 16px;
                    border-radius: 8px;
                    overflow-x: auto;
                    border-left: 3px solid {ThemeColors.ACCENT};
                    margin: 16px 0;
                }}
                code {{
                    font-family: "Consolas", "Monaco", "Courier New", monospace;
                    font-size: 13px;
                }}
                .tip {{
                    background-color: {ThemeColors.BG_SECONDARY};
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 20px;
                    font-size: 12px;
                    color: {ThemeColors.TEXT_SECONDARY};
                }}
            </style>
        </head>
        <body>
            <h1>{title_with_furigana}</h1>
            
            <div class="meta">
                {'👤 ' + author + ' · ' if author else ''}
                {'📅 ' + pub_str + ' · ' if pub_str else ''}
                <a href="{url}">🔗 Xem bài gốc</a>
            </div>
            
            {tags_html}
            
            {f'''<div class="tip">
                💡 <b>Mẹo:</b> Bôi đen text và chuột phải để tra từ điển | 
                Chữ <span style="color:{ThemeColors.ACCENT};">(màu cam)</span> là cách đọc Hiragana
            </div>''' if self._is_japanese else '''<div class="tip">
                💡 <b>Mẹo:</b> Bôi đen text và chuột phải để tra từ điển hoặc nghe phát âm
            </div>'''}
            
            <div class="content">
                {content_with_furigana if content_with_furigana else f'<p style="color: {ThemeColors.TEXT_SECONDARY};">Nhấn "Mở nguồn" để xem nội dung đầy đủ.</p>'}
            </div>
        </body>
        </html>
        """
        
        self.content_browser.setHtml(html)
    
    def _on_furigana_toggled(self, enabled: bool):
        """Handle furigana toggle."""
        self._furigana_enabled = enabled
        self._load_content()
    
    def _on_speed_changed(self, value: int):
        """Handle TTS speed slider change."""
        speed = value / 100.0
        self.speed_label.setText(f"{speed:.1f}x")
        self.speed_slider.setToolTip(f"Tốc độ đọc: {speed:.1f}x")
        
        # Store for TTS use
        self._tts_speed = speed
    
    def _on_tts_clicked(self):
        """Handle TTS button click - toggle Play/Pause/Resume."""
        from frontend.services.tts import TTSService
        
        if self._tts_state == "playing":
            TTSService.pause_audio()
            self._tts_state = "paused"
            self._update_tts_button_style("paused")
        elif self._tts_state == "paused":
            TTSService.resume_audio()
            self._tts_state = "playing"
            self._update_tts_button_style("playing")
        elif self._tts_state == "stopped":
            # Start new playback
            title = getattr(self.article, 'title', '')
            text_to_speak = title + ". " + self._clean_content if self._clean_content else title
            if not text_to_speak.strip(): return
            
            text_to_speak = text_to_speak[:1200]
            lang = "ja" if self._is_japanese else "en"
            
            # Update UI to synthesizing
            self._tts_state = "synthesizing"
            self._update_tts_button_style("synthesizing")
            self._status_timer.start(500)
            
            import threading
            def run_tts():
                try:
                    TTSService.speak_and_play(text_to_speak, lang=lang)
                except Exception as e:
                    print(f"[ERROR TTS] {e}")
                finally:
                    # Thread finished normally
                    pass
            
            # Kill any existing thread before starting (though service lock handles it)
            self._tts_thread = threading.Thread(target=run_tts, daemon=True)
            self._tts_thread.start()

    def _on_stop_clicked(self):
        """Handle stop button click."""
        from frontend.services.tts import TTSService
        TTSService.stop_audio()
        self._tts_state = "stopped"
        self._update_tts_button_style("stopped")
        self._status_timer.stop()
    
    def _check_tts_status(self):
        """Check TTS playback status and update button."""
        from frontend.services.tts import TTSService
        
        # Check synthesis state
        if TTSService._is_synthesizing:
            if self._tts_state != "synthesizing":
                self._tts_state = "synthesizing"
                self._update_tts_button_style("synthesizing")
            return

        # Check playing state
        is_playing = TTSService.is_playing()
        
        if is_playing:
            if self._tts_state != "playing" and self._tts_state != "paused":
                self._tts_state = "playing"
                self._update_tts_button_style("playing")
        elif self._tts_state != "paused" and self._tts_state != "stopped":
            # Not playing and not paused -> it finished or was stopped
            self._tts_state = "stopped"
            self._update_tts_button_style("stopped")
            self._status_timer.stop()
    
    def _on_close(self):
        """Handle close - stop TTS if playing."""
        from frontend.services.tts import TTSService
        TTSService.stop_audio()
        self._status_timer.stop()
        self.close()
    
    def _open_in_browser(self):
        """Open article URL in system browser."""
        url = getattr(self.article, 'url', '')
        if url:
            QDesktopServices.openUrl(QUrl(url))
    
    def _on_link_clicked(self, url: QUrl):
        """Handle link clicks in content."""
        QDesktopServices.openUrl(url)
    
    def closeEvent(self, event):
        """Ensure TTS stops when dialog closes."""
        from frontend.services.tts import TTSService
        TTSService.stop_audio()
        self._status_timer.stop()
        super().closeEvent(event)
