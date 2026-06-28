"""Practice Settings Dialog for configuring flashcard study sessions.

Allows users to:
- Select topic/deck to practice
- Filter by mastery status (New, Learning, Hard, Mastered)
- Set number of cards per session
- Choose practice mode (Flashcard, Quiz, Type Answer)
"""
from typing import List, Dict, Any, Optional, Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QGroupBox, QButtonGroup,
    QRadioButton, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal


class PracticeSettingsDialog(QDialog):
    """Dialog for configuring practice/study session settings."""
    
    # Signal emitted when user confirms settings
    settings_confirmed = Signal(dict)  # Emits practice configuration
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
        lang: str = "jp"
    ):
        """Initialize practice settings dialog.
        
        Args:
            parent: Parent widget
            topics: List of available topics/decks
            lang: Current language ("jp" or "en")
        """
        super().__init__(parent)
        self.topics = topics or []
        self.lang = lang
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("⚙️ Cài đặt Luyện tập")
        self.setMinimumWidth(400)
        self.setMinimumHeight(450)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # ===== Topic Selection =====
        topic_group = QGroupBox("📂 Chọn chủ đề")
        topic_layout = QVBoxLayout(topic_group)
        
        self.topic_combo = QComboBox()
        self.topic_combo.addItem("📚 Tất cả từ vựng", None)
        for topic in self.topics:
            icon = topic.get('icon', '📁')
            name = topic.get('name', 'Unknown')
            self.topic_combo.addItem(f"{icon} {name}", topic.get('id'))
        
        topic_layout.addWidget(QLabel("Chọn chủ đề/bộ từ để luyện:"))
        topic_layout.addWidget(self.topic_combo)
        layout.addWidget(topic_group)
        
        # ===== Source/Curriculum Filter =====
        source_group = QGroupBox("📖 Lọc theo Giáo trình")
        source_layout = QVBoxLayout(source_group)
        
        # Source Material dropdown
        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Giáo trình:"))
        self.source_combo = QComboBox()
        self.source_combo.addItem("Tất cả giáo trình", None)
        # Populate with preset sources based on language
        from frontend.models.vocab import JAPANESE_SOURCES, ENGLISH_SOURCES
        preset_sources = JAPANESE_SOURCES if self.lang == "jp" else ENGLISH_SOURCES
        for src in preset_sources:
            self.source_combo.addItem(src, src)
        source_row.addWidget(self.source_combo, 1)
        source_layout.addLayout(source_row)
        
        # Level dropdown
        level_row = QHBoxLayout()
        level_row.addWidget(QLabel("Cấp độ:"))
        self.level_combo = QComboBox()
        self.level_combo.addItem("Tất cả cấp độ", None)
        from frontend.models.vocab import JAPANESE_LEVELS, ENGLISH_LEVELS
        preset_levels = JAPANESE_LEVELS if self.lang == "jp" else ENGLISH_LEVELS
        for lvl in preset_levels:
            self.level_combo.addItem(lvl, lvl)
        level_row.addWidget(self.level_combo, 1)
        source_layout.addLayout(level_row)
        
        layout.addWidget(source_group)
        
        # ===== Filter by Status =====
        status_group = QGroupBox("🎯 Lọc theo trạng thái")
        status_layout = QVBoxLayout(status_group)
        
        self.status_new = QCheckBox("🆕 Từ mới (New)")
        self.status_new.setChecked(True)
        
        self.status_learning = QCheckBox("📖 Đang học (Learning)")
        self.status_learning.setChecked(True)
        
        self.status_hard = QCheckBox("❗ Từ khó (Hard)")
        self.status_hard.setChecked(True)
        
        self.status_mastered = QCheckBox("✅ Đã thuộc (Mastered)")
        self.status_mastered.setChecked(False)
        
        status_layout.addWidget(self.status_new)
        status_layout.addWidget(self.status_learning)
        status_layout.addWidget(self.status_hard)
        status_layout.addWidget(self.status_mastered)
        layout.addWidget(status_group)

        
        # ===== Session Settings =====
        session_group = QGroupBox("📊 Cài đặt phiên học")
        session_layout = QVBoxLayout(session_group)
        
        # Card limit
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Số lượng từ tối đa:"))
        self.card_limit_spin = QSpinBox()
        self.card_limit_spin.setMinimum(5)
        self.card_limit_spin.setMaximum(100)
        self.card_limit_spin.setValue(20)
        self.card_limit_spin.setSuffix(" từ")
        limit_layout.addWidget(self.card_limit_spin)
        limit_layout.addStretch()
        session_layout.addLayout(limit_layout)
        
        # Include SRS due words
        self.include_due = QCheckBox("🔔 Ưu tiên từ đến hạn ôn (SRS)")
        self.include_due.setChecked(True)
        session_layout.addWidget(self.include_due)
        
        # Shuffle order
        self.shuffle_order = QCheckBox("🔀 Xáo trộn thứ tự")
        self.shuffle_order.setChecked(True)
        session_layout.addWidget(self.shuffle_order)
        
        layout.addWidget(session_group)
        
        # ===== Practice Mode =====
        mode_group = QGroupBox("🎮 Chế độ luyện tập")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_button_group = QButtonGroup(self)
        
        self.mode_flashcard = QRadioButton("🃏 Flashcard (Lật thẻ)")
        self.mode_flashcard.setChecked(True)
        self.mode_button_group.addButton(self.mode_flashcard, 1)
        
        self.mode_quiz = QRadioButton("❓ Quiz (Trắc nghiệm)")
        self.mode_button_group.addButton(self.mode_quiz, 2)
        
        self.mode_typing = QRadioButton("⌨️ Typing (Gõ đáp án)")
        self.mode_button_group.addButton(self.mode_typing, 3)
        
        mode_layout.addWidget(self.mode_flashcard)
        mode_layout.addWidget(self.mode_quiz)
        mode_layout.addWidget(self.mode_typing)
        layout.addWidget(mode_group)
        
        # ===== Buttons =====
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.start_btn = QPushButton("🚀 Bắt đầu luyện tập")
        self.start_btn.setDefault(True)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)
        layout.addLayout(button_layout)
    
    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self.start_btn.clicked.connect(self._on_start_clicked)
    
    def _on_start_clicked(self) -> None:
        """Handle start button click."""
        settings = self.get_settings()
        
        # Validate at least one status is selected
        if not any([
            settings['filter_new'],
            settings['filter_learning'],
            settings['filter_hard'],
            settings['filter_mastered']
        ]):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Cảnh báo",
                "Vui lòng chọn ít nhất một trạng thái từ vựng để luyện tập!"
            )
            return
        
        self.settings_confirmed.emit(settings)
        self.accept()
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current practice settings.
        
        Returns:
            Dictionary containing all practice configuration
        """
        # Get selected mode
        mode_id = self.mode_button_group.checkedId()
        mode_map = {1: "flashcard", 2: "quiz", 3: "typing"}
        
        return {
            # Topic filter
            'topic_id': self.topic_combo.currentData(),
            'topic_name': self.topic_combo.currentText(),
            
            # Source/Curriculum filters
            'source_material': self.source_combo.currentData(),
            'level': self.level_combo.currentData(),
            
            # Status filters
            'filter_new': self.status_new.isChecked(),
            'filter_learning': self.status_learning.isChecked(),
            'filter_hard': self.status_hard.isChecked(),
            'filter_mastered': self.status_mastered.isChecked(),
            
            # Session settings
            'card_limit': self.card_limit_spin.value(),
            'include_due': self.include_due.isChecked(),
            'shuffle': self.shuffle_order.isChecked(),
            
            # Practice mode
            'mode': mode_map.get(mode_id, "flashcard"),
            
            # Language
            'lang': self.lang
        }

    
    def set_topics(self, topics: List[Dict[str, Any]]) -> None:
        """Update available topics.
        
        Args:
            topics: List of topic dictionaries with 'id', 'name', 'icon'
        """
        self.topics = topics
        self.topic_combo.clear()
        self.topic_combo.addItem("📚 Tất cả từ vựng", None)
        for topic in topics:
            icon = topic.get('icon', '📁')
            name = topic.get('name', 'Unknown')
            self.topic_combo.addItem(f"{icon} {name}", topic.get('id'))


class TopicManagerDialog(QDialog):
    """Dialog for managing vocabulary topics/decks."""
    
    topic_created = Signal(dict)  # Emits new topic data
    topic_deleted = Signal(int)   # Emits topic id to delete
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        topics: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize topic manager dialog.
        
        Args:
            parent: Parent widget
            topics: Existing topics list
        """
        super().__init__(parent)
        self.topics = topics or []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("📂 Quản lý chủ đề/bộ từ")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Topic list
        self.topic_list = QScrollArea()
        self.topic_list.setWidgetResizable(True)
        self.topic_list_widget = QWidget()
        self.topic_list_layout = QVBoxLayout(self.topic_list_widget)
        self.topic_list_layout.addStretch()
        self.topic_list.setWidget(self.topic_list_widget)
        layout.addWidget(self.topic_list, 1)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)
        
        # Add new topic section
        add_group = QGroupBox("➕ Thêm chủ đề mới")
        add_layout = QVBoxLayout(add_group)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Tên:"))
        self.new_topic_name = QComboBox()
        self.new_topic_name.setEditable(True)
        self.new_topic_name.addItems([
            "N5 Vocabulary", "N4 Vocabulary", "N3 Vocabulary", 
            "N2 Vocabulary", "N1 Vocabulary",
            "JLPT Grammar", "IT Vocabulary", "Business Japanese",
            "Daily Conversation", "Anime/Manga"
        ])
        name_layout.addWidget(self.new_topic_name, 1)
        add_layout.addLayout(name_layout)
        
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(QLabel("Icon:"))
        self.new_topic_icon = QComboBox()
        self.new_topic_icon.addItems([
            "📚", "📖", "📝", "🎌", "🗾", "💼", "💻", "🎮", 
            "🎬", "📺", "🎵", "🏫", "✈️", "🍣", "⭐"
        ])
        icon_layout.addWidget(self.new_topic_icon)
        icon_layout.addStretch()
        
        self.add_topic_btn = QPushButton("➕ Thêm chủ đề")
        self.add_topic_btn.clicked.connect(self._add_topic)
        icon_layout.addWidget(self.add_topic_btn)
        add_layout.addLayout(icon_layout)
        
        layout.addWidget(add_group)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        # Populate existing topics
        self._refresh_topic_list()
    
    def _refresh_topic_list(self) -> None:
        """Refresh the topic list display."""
        # Clear existing items (except stretch)
        while self.topic_list_layout.count() > 1:
            item = self.topic_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add topic items
        for topic in self.topics:
            item_widget = self._create_topic_item(topic)
            self.topic_list_layout.insertWidget(
                self.topic_list_layout.count() - 1,  # Before stretch
                item_widget
            )
    
    def _create_topic_item(self, topic: Dict[str, Any]) -> QWidget:
        """Create a widget for displaying a single topic.
        
        Args:
            topic: Topic data dictionary
            
        Returns:
            Widget displaying the topic
        """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)
        
        icon = topic.get('icon', '📁')
        name = topic.get('name', 'Unknown')
        count = topic.get('word_count', 0)
        
        label = QLabel(f"{icon}  <b>{name}</b>  ({count} từ)")
        layout.addWidget(label, 1)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedWidth(40)
        delete_btn.setToolTip("Xóa chủ đề")
        delete_btn.clicked.connect(lambda: self._delete_topic(topic.get('id')))
        layout.addWidget(delete_btn)
        
        return frame
    
    def _add_topic(self) -> None:
        """Handle adding a new topic."""
        name = self.new_topic_name.currentText().strip()
        icon = self.new_topic_icon.currentText()
        
        if not name:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên chủ đề!")
            return
        
        new_topic = {
            'name': name,
            'icon': icon,
            'description': '',
            'word_count': 0
        }
        
        self.topic_created.emit(new_topic)
        self.new_topic_name.setCurrentText("")
    
    def _delete_topic(self, topic_id: int) -> None:
        """Handle deleting a topic.
        
        Args:
            topic_id: ID of topic to delete
        """
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            "Bạn có chắc muốn xóa chủ đề này?\n"
            "(Các từ vựng trong chủ đề sẽ không bị xóa)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.topic_deleted.emit(topic_id)
