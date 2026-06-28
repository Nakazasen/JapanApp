import json
import os
import requests
import markdown
from urllib.parse import quote
from typing import Dict, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget,
    QTextBrowser, QLabel, QFrame, QGridLayout, QScrollArea, QPushButton,
    QSizePolicy, QSplitter, QDialog, QApplication
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QByteArray, QBuffer
from PySide6.QtGui import QFont, QColor, QMovie, QPixmap
from frontend.ui.styles.theme import ThemeColors

class GifDownloader(QThread):
    """Worker thread to download GIF data or load from local cache."""
    finished = Signal(bytes)
    error = Signal(str)

    def __init__(self, url: str, char: str, type_name: str):
        super().__init__()
        self.url = url
        self.char = char
        self.type_name = type_name
        # Thư mục lưu cache: data/assets/kana/hiragana/あ.gif
        self.cache_dir = os.path.join('frontend', 'data', 'assets', 'kana', self.type_name.lower())
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_path = os.path.join(self.cache_dir, f"{self.char}.gif")

    def run(self):
        try:
            # 1. Kiểm tra cache offline trước
            if os.path.exists(self.cache_path):
                print(f"DEBUG: Loading {self.char} from local cache")
                with open(self.cache_path, 'rb') as f:
                    self.finished.emit(f.read())
                return

            # 2. Nếu không có, mới tải từ mạng
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            print(f"DEBUG: Downloading GIF from {self.url}")
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 3. Lưu vào cache để dùng offline sau này
            with open(self.cache_path, 'wb') as f:
                f.write(response.content)
            
            print(f"DEBUG: Successfully downloaded and cached {self.char}")
            self.finished.emit(response.content)
        except Exception as e:
            print(f"DEBUG: Error in GifDownloader: {e}")
            self.error.emit(str(e))

from frontend.services.audio_service import AudioService

class KanaDetailDialog(QDialog):
    """Dialog showing character details, animated stroke order, and mnemonics."""
    
    def __init__(self, data: Dict, type_name: str, parent=None):
        super().__init__(parent)
        self.data = data
        self.type_name = type_name
        self.char_raw = data.get('char', '')
        self.movies = []
        self.buffers = []
        self._init_ui()
        self._load_gifs()
        self._try_load_mnemonic_image()

    def _init_ui(self):
        self.setWindowTitle(f"Cách viết: {self.char_raw}")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ThemeColors.BG_PRIMARY};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QLabel#Title {{
                font-size: 60px;
                font-weight: bold;
                color: {ThemeColors.ACCENT};
            }}
            QLabel#Mnemonic {{
                font-size: 15px;
                color: {ThemeColors.TEXT_SECONDARY};
                background-color: {ThemeColors.BG_SECONDARY};
                padding: 15px;
                border-radius: 10px;
            }}
            QPushButton#CloseBtn {{
                background-color: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.TEXT_PRIMARY};
                border-radius: 5px;
                padding: 8px 20px;
            }}
            QPushButton#CloseBtn:hover {{
                background-color: {ThemeColors.SECONDARY};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QHBoxLayout()
        header.setSpacing(20)
        
        # Character Title (Big)
        title_label = QLabel(self.char_raw)
        title_label.setObjectName("Title")
        header.addWidget(title_label)
        
        # Info Column (Romaji + Audio FAB)
        info_col = QVBoxLayout()
        info_col.setSpacing(10)
        
        # Romaji
        romaji_label = QLabel(f"Romaji: {self.data.get('romaji', '').upper()}")
        romaji_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        info_col.addWidget(romaji_label)
        
        # Audio FAB (Floating Action Button style)
        self.audio_btn = QPushButton("🔊")
        self.audio_btn.setFixedSize(60, 60)
        self.audio_btn.setCursor(Qt.PointingHandCursor)
        self.audio_btn.setToolTip("Nghe phát âm chuẩn")
        self.audio_btn.clicked.connect(self._play_audio)
        self.audio_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.ACCENT};
                border: 2px solid {ThemeColors.BG_SECONDARY};
                border-radius: 30px;
                font-size: 28px;
                color: {ThemeColors.TEXT_INVERSE};
                qproperty-iconSize: 32px 32px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.ACCENT_HOVER};
                margin-top: -2px; /* Lift effect */
                border: 2px solid {ThemeColors.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.ACCENT};
                margin-top: 2px;
            }}
        """)
        
        # Layout for FAB to be aligned left nicely
        fab_row = QHBoxLayout()
        fab_row.addWidget(self.audio_btn)
        label_hint = QLabel("Nghe phát âm")
        label_hint.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 14px; font-style: italic;")
        fab_row.addWidget(label_hint)
        fab_row.addStretch()
        
        info_col.addLayout(fab_row)
        info_col.addStretch()
        
        header.addLayout(info_col)
        header.addStretch()
        main_layout.addLayout(header)

        # Body: GIFs Container
        self.gifs_layout = QHBoxLayout()
        self.gifs_layout.setSpacing(10)
        self.gifs_layout.setAlignment(Qt.AlignCenter)
        
        # We will dynamically add GIF labels here
        self.gif_labels = []
        for c in self.char_raw:
            label = QLabel("Đang tải...")
            label.setFixedSize(180, 180)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(f"background-color: {ThemeColors.BG_GRID}; border-radius: 10px; color: {ThemeColors.TEXT_PRIMARY};")
            self.gif_labels.append(label)
            self.gifs_layout.addWidget(label)
            
        main_layout.addLayout(self.gifs_layout)

        # Mnemonic Image
        self.image_container = QLabel()
        self.image_container.setFixedSize(320, 180) 
        self.image_container.setAlignment(Qt.AlignCenter)
        self.image_container.setStyleSheet(f"""
            QLabel {{
                background-color: {ThemeColors.BG_TERTIARY};
                border: 2px dashed {ThemeColors.BORDER};
                border-radius: 12px;
                color: {ThemeColors.TEXT_SECONDARY};
                font-size: 13px;
            }}
        """)
        self.image_container.setText("🖼️ Hình ảnh minh họa\n(Sẽ cập nhật sau)")
        
        img_layout = QHBoxLayout()
        img_layout.addStretch()
        img_layout.addWidget(self.image_container)
        img_layout.addStretch()
        main_layout.addLayout(img_layout)

        # Mnemonic Text
        mn_title = QLabel("💡 Mẹo nhớ:")
        mn_title.setStyleSheet(f"font-weight: bold; color: {ThemeColors.ACCENT}; font-size: 14px;")
        main_layout.addWidget(mn_title)
        
        self.mnemonic_label = QLabel(self.data.get('mnemonic', 'Chưa có mẹo nhớ.'))
        self.mnemonic_label.setObjectName("Mnemonic")
        self.mnemonic_label.setWordWrap(True)
        main_layout.addWidget(self.mnemonic_label)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        close_btn = QPushButton("Đóng")
        close_btn.setObjectName("CloseBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        main_layout.addLayout(footer)

    def _play_audio(self):
        """Play native audio via service."""
        if not hasattr(self, 'audio_service'):
            try:
                self.audio_service = AudioService()
            except Exception as e:
                print(f"[KanaDetail] Audio service init failed: {e}")
                return
        
        self.audio_service.play_kana(self.char_raw)

    def _try_load_mnemonic_image(self):
        """Try to load an image from assets/kana/mnemonics/CHAR.{png,jpg,svg}."""
        try:
            base_path = os.path.join('frontend', 'data', 'assets', 'kana', 'mnemonics')
            extensions = ['.png', '.jpg', '.jpeg', '.svg']
            
            for ext in extensions:
                image_path = os.path.join(base_path, f"{self.char_raw}{ext}")
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        self.image_container.setPixmap(pixmap.scaled(300, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        self.image_container.setText("")
                        # Remove border/bg to show image cleanly
                        self.image_container.setStyleSheet("background: transparent; border: none;")
                    break # Stop after finding first match
        except Exception as e:
            print(f"Image load error: {e}")

    def _load_gifs(self):
        for i, char in enumerate(self.char_raw):
            # GitHub source URL (base type lowercase)
            base_type = self.type_name.lower()
            url = f'https://raw.githubusercontent.com/jcsirot/kanji.gif/master/{base_type}/gif/150x150/{quote(char)}.gif'
            
            downloader = GifDownloader(url, char, self.type_name)
            downloader.finished.connect(lambda data, idx=i: self._on_gif_loaded(data, idx))
            downloader.error.connect(lambda err, idx=i: self.gif_labels[idx].setText("Lỗi"))
            downloader.start()
            # Keep a reference to prevent GC
            if not hasattr(self, '_downloaders'): self._downloaders = []
            self._downloaders.append(downloader)


    def _on_gif_loaded(self, data: bytes, index: int):
        buf = QBuffer()
        buf.setData(data)
        buf.open(QBuffer.ReadOnly)
        self.buffers.append(buf) # Keep reference
        
        movie = QMovie(buf, QByteArray("GIF"))
        self.movies.append(movie)
        
        label = self.gif_labels[index]
        label.setMovie(movie)
        movie.setScaledSize(QSize(160, 160))
        movie.start()

class KanaCell(QFrame):
    """A cell in the Kana grid representing a single character."""
    clicked = Signal(dict)
    
    def __init__(self, data: Dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.char = data.get('char', '')
        self.romaji = data.get('romaji', '')
        self._init_ui()
        
    def _init_ui(self):
        self.setObjectName("KanaCell")
        self.setFixedSize(80, 100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(2)
        
        # Character
        self.char_label = QLabel(self.char)
        self.char_label.setAlignment(Qt.AlignCenter)
        self.char_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        layout.addWidget(self.char_label)
        
        # Romaji
        self.romaji_label = QLabel(self.romaji)
        self.romaji_label.setAlignment(Qt.AlignCenter)
        self.romaji_label.setStyleSheet(f"font-size: 14px; color: {ThemeColors.TEXT_SECONDARY};")
        layout.addWidget(self.romaji_label)
        
        if not self.char:
            self.setStyleSheet("background: transparent; border: none;")
            self.char_label.setText("")
            self.romaji_label.setText("")
        else:
            self.setStyleSheet(f"""
                QFrame#KanaCell {{
                    background-color: {ThemeColors.BG_SECONDARY};
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 12px;
                }}
                QFrame#KanaCell:hover {{
                    background-color: {ThemeColors.BG_TERTIARY};
                    border: 1px solid {ThemeColors.ACCENT};
                }}
            """)
            self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if self.char:
            self.clicked.emit(self.data)
        super().mousePressEvent(event)

class KanaGridWidget(QWidget):
    """Widget displaying an interactive grid of Kana characters."""
    kana_clicked = Signal(dict, str) # Emits (data, type_name)
    
    def __init__(self, data_path: str, type_name: str):
        super().__init__()
        self.data_path = data_path
        self.type_name = type_name
        self._init_ui()
        self._load_data()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Scroll Area for the grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.container = QWidget()
        self.grid_layout = QVBoxLayout(self.container)
        self.grid_layout.setSpacing(20)
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        
    def _load_data(self):
        if not os.path.exists(self.data_path):
            return
            
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Add Seion (Main characters)
            self._add_section("Bảng chữ cái cơ bản (Seion)", data.get("seion", []), columns=5)
            
            # Add Dakuon (Voiced characters)
            if data.get("dakuon"):
                self._add_section("Bảng âm đục (Dakuon)", data.get("dakuon", []), columns=5)
                
            # Add Yoon (Contracted sounds)
            if data.get("yoon"):
                self._add_section("Bảng âm ghép (Yoon)", data.get("yoon", []), columns=3)
                
        except Exception as e:
            print(f"Error loading kana data: {e}")

    def _add_section(self, title: str, items: List[Dict], columns: int):
        section_label = QLabel(title)
        section_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.ACCENT}; margin-top: 20px;")
        self.grid_layout.addWidget(section_label)
        
        grid_frame = QFrame()
        grid = QGridLayout(grid_frame)
        grid.setSpacing(10)
        
        for i, item in enumerate(items):
            row = i // columns
            col = i % columns
            cell = KanaCell(item)
            cell.clicked.connect(lambda data, t=self.type_name: self.kana_clicked.emit(data, t))
            grid.addWidget(cell, row, col)
            
        self.grid_layout.addWidget(grid_frame)

class IntroductionTab(QWidget):
    """Main tab for Introduction to Japanese."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        self.setObjectName("IntroductionTab")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Splitter for sidebar and content
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar Navigation
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("""
            QListWidget#Sidebar {{
                background-color: {ThemeColors.BG_SECONDARY};
                border: none;
                color: {ThemeColors.TEXT_SECONDARY};
                padding-top: 10px;
            }}
            QListWidget#Sidebar::item {{
                padding: 15px 20px;
                border: none;
                font-size: 14px;
            }}
            QListWidget#Sidebar::item:selected {{
                background-color: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.PRIMARY};
                border-left: 4px solid {ThemeColors.PRIMARY};
            }}
            QListWidget#Sidebar::item:hover:!selected {{
                background-color: {ThemeColors.BG_TERTIARY};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """)
        
        # Add navigation items
        items = [
            ("📖 Lịch sử & Nguồn gốc", "history"),
            ("💡 Phương pháp học", "methodology"),
            ("🇯🇵 Bảng chữ cái Hiragana", "hiragana"),
            ("🇯🇵 Bảng chữ cái Katakana", "katakana")
        ]
        
        for text, key in items:
            self.sidebar.addItem(text)
            
        self.sidebar.currentRowChanged.connect(self._on_nav_changed)
        
        # Content Area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background-color: {ThemeColors.BG_PRIMARY};")
        
        # View: Markdown Viewer
        self.md_viewer = QTextBrowser()
        self.md_viewer.setOpenExternalLinks(True)
        self.md_viewer.setStyleSheet("""
            QTextBrowser {{
                background-color: {ThemeColors.BG_PRIMARY};
                border: none;
                color: {ThemeColors.TEXT_PRIMARY};
                font-size: 16px;
                line-height: 1.6;
            }}
        """)
        
        # View: Hiragana Grid
        hiragana_path = os.path.join("frontend", "data", "content", "intro", "hiragana.json")
        self.hiragana_grid = KanaGridWidget(hiragana_path, "Hiragana")
        self.hiragana_grid.kana_clicked.connect(self._show_kana_details)
        
        # View: Katakana Grid
        katakana_path = os.path.join("frontend", "data", "content", "intro", "katakana.json")
        self.katakana_grid = KanaGridWidget(katakana_path, "Katakana")
        self.katakana_grid.kana_clicked.connect(self._show_kana_details)
        
        # Register views
        self.content_stack.addWidget(self.md_viewer)     # Index 0/1 (History/Methodology share this)
        self.content_stack.addWidget(self.hiragana_grid) # Index 2
        self.content_stack.addWidget(self.katakana_grid) # Index 3
        
        # Add to splitter
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.content_stack)
        
        layout.addWidget(self.splitter)
        
        # Default selection
        self.sidebar.setCurrentRow(0)
        
    def _on_nav_changed(self, index: int):
        if index == 0:
            self._display_markdown("history.md")
            self.content_stack.setCurrentIndex(0)
        elif index == 1:
            self._display_markdown("methodology.md")
            self.content_stack.setCurrentIndex(0)
        elif index == 2:
            self.content_stack.setCurrentIndex(1)
        elif index == 3:
            self.content_stack.setCurrentIndex(2)
            
    def _display_markdown(self, filename: str):
        path = os.path.join("frontend", "data", "content", "intro", filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Convert markdown to HTML (Remove nl2br to avoid extra breaks)
                html_content = markdown.markdown(content, extensions=['extra', 'sane_lists'])
                
                # Apply premium CSS
                full_html = f"""
                <html>
                <head>
                <style>
                    body {{
                        background-color: {ThemeColors.BG_PRIMARY};
                        color: {ThemeColors.TEXT_PRIMARY};
                        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        font-size: 16px;
                        line-height: 1.6;
                        padding: 20px 40px;
                    }}
                    h1 {{
                        color: {ThemeColors.ACCENT};
                        border-bottom: 2px solid {ThemeColors.BORDER};
                        padding-bottom: 10px;
                        margin: 0 0 15px 0;
                        font-size: 30px;
                        text-align: center;
                    }}
                    h3 {{
                        color: {ThemeColors.PRIMARY};
                        margin: 20px 0 10px 0;
                        font-size: 22px;
                    }}
                    h4 {{
                        color: {ThemeColors.TEXT_SECONDARY};
                        margin: 15px 0 5px 0;
                        font-size: 18px;
                    }}
                    p {{
                        margin: 0 0 10px 0;
                        text-align: justify;
                    }}
                    img {{
                        border-radius: 12px;
                        display: block;
                        margin: 5px auto 20px auto;
                        box-shadow: 0 5px 20px rgba(0,0,0,0.4);
                        border: 1px solid {ThemeColors.BORDER};
                        max-width: 100%;
                    }}
                    hr {{
                        border: 0;
                        height: 1px;
                        background: linear-gradient(to right, transparent, {ThemeColors.BORDER}, transparent);
                        margin: 20px 0;
                    }}
                    blockquote {{
                        background-color: {ThemeColors.BG_SECONDARY};
                        border-left: 4px solid {ThemeColors.ACCENT};
                        padding: 15px;
                        border-radius: 0 8px 8px 0;
                        margin: 15px 0;
                        font-style: italic;
                        color: {ThemeColors.TEXT_SECONDARY};
                    }}
                    ul {{
                        padding-left: 20px;
                    }}
                    li {{
                        margin-bottom: 10px;
                    }}
                </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
                self.md_viewer.setHtml(full_html)
        else:
            self.md_viewer.setHtml(f"<h1 style='color:red;'>Lỗi</h1><p>Không tìm thấy file: {filename}</p>")

    def _show_kana_details(self, data: Dict, type_name: str):
        """Show the animated writing and mnemonic dialog."""
        dialog = KanaDetailDialog(data, type_name, self)
        dialog.exec()
