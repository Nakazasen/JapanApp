"""Cyberpunk-styled news card widget.

Each card displays:
- Title (with optional Furigana for Japanese)
- Source icon and name
- Tags (colored chips)
- Time (relative)
- Hot metrics (upvotes/stocks)
"""

from datetime import datetime
from typing import Optional, List
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGraphicsDropShadowEffect, QWidget
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QFont, QCursor
from frontend.ui.styles.theme import ThemeColors


class TagChip(QFrame):
    """Small colored tag chip."""
    
    # Color palette for different tag categories
    TAG_COLORS = {
        "python": "#3776ab",
        "machinelearning": "#ff6b6b",
        "ai": "#a855f7",
        "deeplearning": "#f59e0b",
        "llm": "#10b981",
        "docker": "#2496ed",
        "gpu": "#76b900",
        "openai": "#412991",
        "default": "#6366f1",
    }
    
    def __init__(self, tag: str, parent=None):
        super().__init__(parent)
        self.tag = tag
        self._setup_ui()
    
    def _setup_ui(self):
        # Find color for this tag
        tag_lower = self.tag.lower().replace("-", "").replace("_", "")
        color = self.TAG_COLORS.get(tag_lower, self.TAG_COLORS["default"])
        
        self.setStyleSheet(f"""
            TagChip {{
                background-color: {color}40;
                border: 1px solid {color};
                border-radius: 10px;
                padding: 2px 8px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(0)
        
        label = QLabel(self.tag)
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        layout.addWidget(label)


class NewsCard(QFrame):
    """Cyberpunk-styled news article card.
    
    Features:
    - Glowing border on hover
    - Furigana support for Japanese titles
    - Animated interactions
    - Save/Bookmark button
    """
    
    clicked = Signal(object)  # Emits article data
    save_clicked = Signal(object, bool)  # Emits (article, new_saved_state)
    
    def __init__(self, article, parent=None):
        super().__init__(parent)
        self.article = article
        self._is_hovered = False
        self._glow_opacity = 0
        self._is_saved = getattr(article, 'is_saved', False)
        
        self._setup_ui()
        self._setup_effects()
    
    def _setup_ui(self):
        self.setObjectName("NewsCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedWidth(320)
        
        # Base style
        self._apply_style(hover=False)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        
        # === Header: Source + Time ===
        header = QHBoxLayout()
        header.setSpacing(8)
        
        # Source indicator
        source_name = getattr(self.article, 'source_name', 'Unknown')
        is_japanese = source_name in ["Qiita", "Zenn", "Hatena"]
        
        source_icon = "🇯🇵" if is_japanese else "🌐"
        source_label = QLabel(f"{source_icon} {source_name}")
        source_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.PRIMARY};
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        header.addWidget(source_label)
        
        header.addStretch()
        
        # Time
        time_text = self._format_time(getattr(self.article, 'published_at', None))
        time_label = QLabel(time_text)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.TEXT_SECONDARY};
                font-size: 10px;
                background: transparent;
            }}
        """)
        header.addWidget(time_label)
        
        layout.addLayout(header)
        
        # === Title ===
        title = getattr(self.article, 'title', 'Untitled')
        # Truncate long titles
        if len(title) > 80:
            title = title[:77] + "..."
        
        # Check if has furigana version
        furigana_title = getattr(self.article, 'furigana_title', None)
        
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY};
                font-size: 14px;
                font-weight: bold;
                line-height: 1.4;
                background: transparent;
            }}
        """)
        layout.addWidget(title_label)
        
        # === Tags ===
        tags = getattr(self.article, 'tags', [])
        if tags:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(6)
            tags_layout.setContentsMargins(0, 0, 0, 0)
            
            # Show max 3 tags
            for tag in tags[:3]:
                chip = TagChip(tag)
                tags_layout.addWidget(chip)
            
            if len(tags) > 3:
                more_label = QLabel(f"+{len(tags) - 3}")
                more_label.setStyleSheet(f"""
                    QLabel {{
                        color: {ThemeColors.TEXT_SECONDARY};
                        font-size: 10px;
                        background: transparent;
                    }}
                """)
                tags_layout.addWidget(more_label)
            
            tags_layout.addStretch()
            layout.addLayout(tags_layout)
        
        # === Footer: Metrics + Save Button ===
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(12)
        
        # Metrics container
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)
        
        # Upvotes/Likes
        upvotes = getattr(self.article, 'upvotes', 0)
        if upvotes > 0:
            upvote_label = QLabel(f"🔥 {upvotes}")
            upvote_label.setStyleSheet(f"""
                QLabel {{
                    color: {ThemeColors.DANGER};
                    font-size: 11px;
                    background: transparent;
                }}
            """)
            metrics_layout.addWidget(upvote_label)
        
        # Stocks (Qiita bookmarks)
        stocks = getattr(self.article, 'stocks', 0)
        if stocks > 0:
            stock_label = QLabel(f"📌 {stocks}")
            stock_label.setStyleSheet(f"""
                QLabel {{
                    color: {ThemeColors.PRIMARY};
                    font-size: 11px;
                    background: transparent;
                }}
            """)
            metrics_layout.addWidget(stock_label)
        
        # Comments
        comments = getattr(self.article, 'comments_count', 0)
        if comments > 0:
            comment_label = QLabel(f"💬 {comments}")
            comment_label.setStyleSheet(f"""
                QLabel {{
                    color: {ThemeColors.TEXT_SECONDARY};
                    font-size: 11px;
                    background: transparent;
                }}
            """)
            metrics_layout.addWidget(comment_label)
        
        footer_layout.addLayout(metrics_layout)
        footer_layout.addStretch()
        
        # Save/Bookmark Button
        self.save_btn = QPushButton()
        self._update_save_button()
        self.save_btn.setFixedSize(28, 28)
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.clicked.connect(self._on_save_clicked)
        footer_layout.addWidget(self.save_btn)
        
        layout.addLayout(footer_layout)
    
    def _update_save_button(self):
        """Update save button appearance based on saved state."""
        if self._is_saved:
            self.save_btn.setText("⭐")
            self.save_btn.setToolTip("Bỏ lưu")
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.ACCENT};
                    border: none;
                    border-radius: 14px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: #fcd34d;
                }}
            """)
        else:
            self.save_btn.setText("☆")
            self.save_btn.setToolTip("Lưu bài viết")
            self.save_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ThemeColors.BORDER};
                    border: none;
                    border-radius: 14px;
                    font-size: 14px;
                    color: {ThemeColors.TEXT_SECONDARY};
                }}
                QPushButton:hover {{
                    background-color: {ThemeColors.ACCENT};
                    color: #000;
                }}
            """)
    
    def _on_save_clicked(self):
        """Handle save button click."""
        self._is_saved = not self._is_saved
        self._update_save_button()
        self.save_clicked.emit(self.article, self._is_saved)
    
    def set_saved(self, saved: bool):
        """Programmatically set saved state."""
        self._is_saved = saved
        self._update_save_button()
    
    def _setup_effects(self):
        """Setup glow effect for hover."""
        self.glow_effect = QGraphicsDropShadowEffect(self)
        self.glow_effect.setBlurRadius(0)
        self.glow_effect.setColor(QColor(ThemeColors.PRIMARY))
        self.glow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self.glow_effect)
    
    def _apply_style(self, hover: bool = False):
        """Apply card style based on hover state."""
        if hover:
            self.setStyleSheet(f"""
                NewsCard {{
                    background-color: {ThemeColors.BG_TERTIARY};
                    border: 1px solid {ThemeColors.PRIMARY};
                    border-radius: 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                NewsCard {{
                    background-color: {ThemeColors.BG_SECONDARY};
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 12px;
                }}
            """)
    
    def _format_time(self, dt: Optional[datetime]) -> str:
        """Format datetime as relative time."""
        if not dt:
            return ""
        
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        if seconds < 60:
            return "vừa xong"
        elif seconds < 3600:
            return f"{int(seconds // 60)} phút trước"
        elif seconds < 86400:
            return f"{int(seconds // 3600)} giờ trước"
        elif seconds < 604800:
            return f"{int(seconds // 86400)} ngày trước"
        else:
            return dt.strftime("%d/%m/%Y")
    
    def enterEvent(self, event):
        """Mouse enter - show glow."""
        self._is_hovered = True
        self._apply_style(hover=True)
        
        # Animate glow
        if self.glow_effect:
            self.glow_effect.setBlurRadius(20)
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Mouse leave - hide glow."""
        self._is_hovered = False
        self._apply_style(hover=False)
        
        # Remove glow
        if self.glow_effect:
            self.glow_effect.setBlurRadius(0)
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle click."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.article)
        super().mousePressEvent(event)
