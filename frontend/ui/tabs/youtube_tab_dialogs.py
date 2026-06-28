from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QComboBox, QListWidget, QAbstractItemView
)
from typing import List, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

class ChannelManagerDialog(QDialog):
    """Dialog to manage and reorder YouTube channels."""
    
    def __init__(self, channels: List[tuple], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sắp xếp danh sách kênh")
        self.resize(400, 500)
        self.channels = channels # List of (name, handle)
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        info_lbl = QLabel("💡 Kéo thả để sắp xếp thứ tự ưu tiên của các kênh:")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #666; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(info_lbl)
        
        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        
        for name, handle in self.channels:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, handle)
            self.list_widget.addItem(item)
            
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        layout.addWidget(self.list_widget)
        
        # Manipulation Buttons (Up/Down)
        move_layout = QHBoxLayout()
        self.btn_up = QPushButton("▲ Lên")
        self.btn_down = QPushButton("▼ Xuống")
        
        for btn in [self.btn_up, self.btn_down]:
            btn.setFixedWidth(100)
        
        self.btn_up.clicked.connect(self._move_up)
        self.btn_down.clicked.connect(self._move_down)
        
        move_layout.addStretch()
        move_layout.addWidget(self.btn_up)
        move_layout.addWidget(self.btn_down)
        move_layout.addStretch()
        layout.addLayout(move_layout)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        
        self.cancel_btn = QPushButton("Hủy bỏ")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("padding: 8px;")
        
        self.save_btn = QPushButton("Lưu thay đổi")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71; 
                color: white; 
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
    def _move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentRow(row - 1)
            
    def _move_down(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentRow(row + 1)
            
    def get_channels(self) -> List[tuple]:
        """Return the ordered list of (name, handle) tuples."""
        results = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            results.append((item.text(), item.data(Qt.UserRole)))
        return results

class SaveVocabDialog(QDialog):
    """Dialog to save vocabulary with context."""
    
    def __init__(self, parent=None, word: str = "", context: str = "", meaning: str = "", translation: str = "", topics: List[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Lưu từ vựng kèm ngữ cảnh")
        self.setFixedWidth(500)
        self.vocab_data = {}
        self.topics = topics or []
        self._init_ui(word, context, meaning, translation)
        
    def _init_ui(self, word, context, meaning, translation):
        layout = QVBoxLayout(self)
        
        # Word
        layout.addWidget(QLabel("Từ vựng:"))
        self.word_input = QLineEdit(word)
        layout.addWidget(self.word_input)
        
        # Meaning
        layout.addWidget(QLabel("Nghĩa (Tiếng Việt):"))
        self.meaning_input = QLineEdit(meaning)
        layout.addWidget(self.meaning_input)
        
        # Context (Origin)
        layout.addWidget(QLabel("Câu ví dụ (Ngữ cảnh):"))
        self.context_input = QTextEdit()
        self.context_input.setPlainText(context)
        self.context_input.setMaximumHeight(80)
        layout.addWidget(self.context_input)
        
        # Context (Translation)
        layout.addWidget(QLabel("Dịch câu ví dụ:"))
        self.translation_input = QTextEdit()
        self.translation_input.setPlainText(translation)
        self.translation_input.setMaximumHeight(80)
        layout.addWidget(self.translation_input)

        # Topic Selection
        layout.addWidget(QLabel("Chủ đề (Flashcard Deck):"))
        self.topic_combo = QComboBox()
        self.topic_combo.addItem("📂 Không phân loại (Mặc định)", None)
        if self.topics:
            for t in self.topics:
                self.topic_combo.addItem(f"📘 {t['name']}", t['id'])
        layout.addWidget(self.topic_combo)
        
        self.new_topic_input = QLineEdit()
        self.new_topic_input.setPlaceholderText("Hoặc tạo chủ đề mới...")
        layout.addWidget(self.new_topic_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = QPushButton("Lưu")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
    def get_data(self):
        """Get the data from inputs."""
        return {
            "word": self.word_input.text().strip(),
            "meaning": self.meaning_input.text().strip(),
            "context": self.context_input.toPlainText().strip(),
            "translation": self.translation_input.toPlainText().strip(),
            "topic_id": self.topic_combo.currentData(),
            "new_topic_name": self.new_topic_input.text().strip()
        }
