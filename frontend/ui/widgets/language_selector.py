from PySide6.QtWidgets import QComboBox, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from frontend.ui.styles.theme import ThemeColors
from frontend.core.user_settings import UserSettings
import os

class LanguageSelector(QWidget):
    """
    A stylish dropdown to select the application language (Context).
    """
    language_changed = Signal(str) # Emits 'en' or 'jp'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = UserSettings()
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # ComboBox with custom styling
        self.combo = QComboBox()
        self.combo.setCursor(Qt.PointingHandCursor)
        self.combo.setIconSize(QSize(24, 24))
        
        # Apply Enterprise Style
        self.combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ThemeColors.BG_TERTIARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 8px;
                padding: 5px 10px;
                color: {ThemeColors.TEXT_PRIMARY};
                font-weight: bold;
                min-width: 120px;
            }}
            QComboBox:hover {{
                border: 1px solid {ThemeColors.ACCENT};
                background-color: {ThemeColors.BG_SECONDARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none; /* Hide default arrow or use custom SVG if needed */
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {ThemeColors.TEXT_SECONDARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ThemeColors.BG_SECONDARY};
                border: 1px solid {ThemeColors.BORDER};
                selection-background-color: {ThemeColors.ACCENT}33; /* 20% opacity */
                selection-color: {ThemeColors.TEXT_PRIMARY};
                outline: none;
            }}
        """)

        # Add Items
        # Note: Using emoji flags for simplicity, can replace with actual icons
        self.combo.addItem("🇺🇸 English", "en")
        self.combo.addItem("🇯🇵 Tiếng Nhật", "jp")

        # Set current selection based on settings
        current_lang = self.settings.current_language
        index = self.combo.findData(current_lang)
        if index >= 0:
            self.combo.setCurrentIndex(index)
        
        self.combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(self.combo)

    def _on_changed(self, index):
        lang_code = self.combo.itemData(index)
        if lang_code:
            self.settings.current_language = lang_code
            self.language_changed.emit(lang_code)
