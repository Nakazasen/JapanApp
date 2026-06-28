import json
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon
from frontend.ui.styles.theme import ThemeColors
from frontend.ui.styles.animations import AnimationService
from frontend.core.user_settings import UserSettings
from frontend.ui.widgets.language_selector import LanguageSelector

class SidebarWidget(QWidget):
    """
    Vertical sidebar navigation widget with Context-Aware Menu.
    """
    page_changed = Signal(int)  # Emits the index of the page to switch to
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self.expanded_width = 250
        self.collapsed_width = 80 # Slightly wider for flags
        self.is_collapsed = False
        self.setFixedWidth(self.expanded_width)
        
        self.settings = UserSettings()
        self.menu_config = self._load_menu_config()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        # --- App Title / Logo Area ---
        self.title_frame = QFrame()
        self.title_frame.setFixedHeight(70)
        
        # Toggle Button
        self.toggle_btn = QPushButton("≡")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {ThemeColors.PRIMARY};
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.BG_TERTIARY};
                border-radius: 4px;
            }}
        """)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
        # Header layout
        header_layout = QHBoxLayout(self.title_frame)
        header_layout.setContentsMargins(10, 0, 5, 0)
        header_layout.addWidget(self.toggle_btn)
        
        # Language Selector (Replaces Title in Enterprise Mode)
        self.lang_selector = LanguageSelector()
        self.lang_selector.language_changed.connect(self.reload_menu)
        header_layout.addWidget(self.lang_selector)
        
        self.layout.addWidget(self.title_frame)
        
        # --- Navigation Items Container ---
        self.nav_container = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(2)
        self.layout.addWidget(self.nav_container)
        
        self.buttons = []
        self.current_index = 0
        
        # Initial Load
        self.reload_menu(self.settings.current_language)
        
        # Spacer
        self.layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # --- Bottom Area ---
        self.bottom_label = QLabel("v2.0 Enterprise")
        self.bottom_label.setAlignment(Qt.AlignCenter)
        self.bottom_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; padding: 10px; font-size: 11px;")
        self.layout.addWidget(self.bottom_label)

    def _load_menu_config(self):
        """Load menu structure from JSON."""
        config_path = os.path.join('frontend', 'config', 'menu_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading menu config: {e}")
            return {}

    def reload_menu(self, language_code: str):
        """Re-render menu items based on selected language."""
        # Clear existing buttons and separators from layout
        while self.nav_layout.count():
            item = self.nav_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.buttons = []
        
        # 1. Global Items
        for item in self.menu_config.get('global_top', []):
            self._add_menu_item(item)
            
        # 2. Context Specific Items
        context_items = self.menu_config.get('context_menus', {}).get(language_code, [])
        if context_items:
            self._add_separator(f"{'LEARNING' if language_code == 'en' else '学習'}")
            for item in context_items:
                self._add_menu_item(item)
                
        # 3. Tools
        self._add_separator("TOOLS")
        for item in self.menu_config.get('tools', []):
            self._add_menu_item(item)

        # 4. Global Bottom (Settings)
        self._add_separator("SYSTEM")
        for item in self.menu_config.get('global_bottom', []):
            self._add_menu_item(item)
            
        # Restore selection if possible, else select first
        if self.buttons:
            self.buttons[0].setChecked(True)

    def _add_menu_item(self, item_data):
        """Helper to create a unified menu button."""
        text = item_data['name']
        icon_emoji = self._get_icon(item_data['icon'])
        target = item_data['target']
        
        btn = QPushButton(f"  {icon_emoji}  {text}")
        btn.setCheckable(True)
        btn.setProperty("class", "nav-btn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda checked, t=target, b=btn: self._on_btn_clicked(t, b))
        
        self.nav_layout.addWidget(btn)
        self.buttons.append(btn)

    def _add_separator(self, title):
        """Add a labeled separator."""
        if self.is_collapsed: return # No separators in collapsed mode
        
        label = QLabel(title)
        label.setStyleSheet(f"""
            color: {ThemeColors.TEXT_SECONDARY}; 
            font-size: 10px; 
            font-weight: bold; 
            padding: 10px 0 5px 15px;
            text-transform: uppercase;
        """)
        self.nav_layout.addWidget(label)
        # Store definition to remove on collapse if needed (simplified here)

    def _get_icon(self, icon_name):
        """Map icon names to Emojis (Temporary, can use SVGs later)."""
        icons = {
            "Dashboard": "🏠", "Settings": "⚙️", 
            "Vocabulary": "📘", "Grammar": "📖", 
            "Chart": "📊", "Listening": "🎧", "Reading": "👁️", "Test": "📝", "Robot": "🤖",
            "Info": "ℹ️", "Kanji": "⛩️", "Writing": "✍️", "Speaking": "🗣️",
            "YouTube": "📺", "News": "📰", "Book": "📕"
        }
        return icons.get(icon_name, "🔹")

    def _on_btn_clicked(self, target, clicked_btn):
        # Uncheck others
        for btn in self.buttons:
            btn.setChecked(btn == clicked_btn)
            
        if isinstance(target, int):
            self.page_changed.emit(target)
        # Handle string targets (like 'settings') in MainWindow if needed
        # For now assuming int mapping in MainWindow

    def toggle_sidebar(self):
        """Toggle sidebar with animation."""
        self.is_collapsed = not self.is_collapsed
        start_w = self.width()
        target_w = self.collapsed_width if self.is_collapsed else self.expanded_width
        
        AnimationService.animate_width(self, start_w, target_w)
        
        # Simple visibility toggle for now
        self.lang_selector.setVisible(not self.is_collapsed)
        self.bottom_label.setVisible(not self.is_collapsed)
        
        # Re-render menu to show/hide text
        # (In a real app, we'd update existing buttons instead of full reload for performance)
        self.reload_menu(self.settings.current_language)
