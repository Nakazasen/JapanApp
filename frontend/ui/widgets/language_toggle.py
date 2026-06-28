"""Language toggle widget for switching between news sources.

Provides segmented control: [Global (EN)] - [Japan (JP)] - [Mixed]
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QButtonGroup
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont


class LanguageToggle(QFrame):
    """Segmented control for language selection.
    
    Signals:
        language_changed(str): Emitted when selection changes.
                               Values: "global", "japan", "mixed"
    """
    
    language_changed = Signal(str)
    
    # Cyberpunk colors
    COLORS = {
        "bg": "#1a1a2e",
        "border": "#2a2a3e",
        "selected_bg": "#00f5ff",
        "selected_text": "#0a0a0f",
        "unselected_bg": "transparent",
        "unselected_text": "#71717a",
        "hover_bg": "#2a2a3e",
    }
    
    MODES = [
        ("global", "🌐 Global", "en"),
        ("japan", "🇯🇵 Japan", "jp"),
        ("mixed", "🔀 Mixed", "mixed"),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_mode = "japan"  # Default to Japan for this feature
        self._buttons = {}
        self._setup_ui()
    
    def _setup_ui(self):
        self.setObjectName("LanguageToggle")
        self.setStyleSheet(f"""
            LanguageToggle {{
                background-color: {self.COLORS['bg']};
                border: 1px solid {self.COLORS['border']};
                border-radius: 8px;
                padding: 2px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        for mode_id, label, lang_code in self.MODES:
            btn = QPushButton(label)
            btn.setObjectName(f"toggle_{mode_id}")
            btn.setCheckable(True)
            btn.setProperty("mode_id", mode_id)
            btn.setMinimumWidth(100)
            btn.setMinimumHeight(32)
            
            # Set initial style
            self._apply_button_style(btn, is_selected=(mode_id == self._current_mode))
            
            if mode_id == self._current_mode:
                btn.setChecked(True)
            
            btn.clicked.connect(lambda checked, m=mode_id: self._on_button_clicked(m))
            
            self.button_group.addButton(btn)
            self._buttons[mode_id] = btn
            layout.addWidget(btn)
    
    def _apply_button_style(self, btn: QPushButton, is_selected: bool):
        """Apply style to button based on selection state."""
        if is_selected:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.COLORS['selected_bg']};
                    color: {self.COLORS['selected_text']};
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 12px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.COLORS['unselected_bg']};
                    color: {self.COLORS['unselected_text']};
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background-color: {self.COLORS['hover_bg']};
                    color: #e4e4e7;
                }}
            """)
    
    def _on_button_clicked(self, mode_id: str):
        """Handle button click."""
        if mode_id == self._current_mode:
            return
        
        # Update styles
        for m_id, btn in self._buttons.items():
            self._apply_button_style(btn, is_selected=(m_id == mode_id))
        
        self._current_mode = mode_id
        self.language_changed.emit(mode_id)
    
    def get_current_mode(self) -> str:
        """Get current language mode."""
        return self._current_mode
    
    def set_mode(self, mode_id: str):
        """Programmatically set mode."""
        if mode_id in self._buttons:
            self._on_button_clicked(mode_id)
            self._buttons[mode_id].setChecked(True)
