"""Scan Review Dialog for reviewing and importing scanned vocabulary.

This module provides a dialog for users to review, edit, and selectively
import vocabulary items extracted from images via AI scanning.
"""
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView,
    QAbstractItemView, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal


class ScanReviewDialog(QDialog):
    """Dialog for reviewing and importing scanned vocabulary items."""
    
    # Emitted when user confirms import with selected items
    import_requested = Signal(list)
    
    # Column indices
    COL_SELECT = 0
    COL_KANJI = 1
    COL_FURIGANA = 2
    COL_MEANING = 3
    COL_SINO = 4
    
    
    def __init__(self, parent=None, vocab_list: List[Dict[str, Any]] = None, model_name: str = ""):
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
            vocab_list: List of vocabulary items to display
            model_name: Name of the AI model used
        """
        super().__init__(parent)
        self.vocab_list = vocab_list or []
        self.model_name = model_name
        self.selected_items: List[Dict[str, Any]] = []
        
        self._init_ui()
        self._populate_table()
    
    def _init_ui(self):
        """Initialize the UI components."""
        title = "📷 Kết quả quét ảnh"
        if self.model_name:
            title += f" ({self.model_name})"
        self.setWindowTitle(title)
        
        self.setMinimumSize(800, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Header
        model_info = f"<b>Mô hình: {self.model_name}</b><br>" if self.model_name else ""
        header_label = QLabel(
            f"{model_info}"
            "Dưới đây là danh sách từ vựng được trích xuất từ ảnh.\n"
            "Bạn có thể chỉnh sửa nội dung bằng cách double-click vào ô.\n"
            "Chọn các từ muốn lưu rồi nhấn 'Import đã chọn'."
        )
        header_label.setWordWrap(True)
        header_label.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Select all checkbox
        select_all_layout = QHBoxLayout()
        self.select_all_cb = QCheckBox("Chọn tất cả")
        self.select_all_cb.stateChanged.connect(self._on_select_all_changed)
        select_all_layout.addWidget(self.select_all_cb)
        
        # Item count label
        self.count_label = QLabel("")
        select_all_layout.addWidget(self.count_label)
        select_all_layout.addStretch()
        layout.addLayout(select_all_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "☑", "Kanji", "Furigana", "Nghĩa tiếng Việt", "Âm Hán Việt"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_SELECT, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_KANJI, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_FURIGANA, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_MEANING, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_SINO, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setColumnWidth(self.COL_SELECT, 40)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        # Allow editing
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | 
            QAbstractItemView.EditTrigger.EditKeyPressed
        )
        
        # Connect item changed signal for tracking checkbox changes
        self.table.itemChanged.connect(self._on_item_changed)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("📥 Import đã chọn")
        self.import_btn.clicked.connect(self._on_import_clicked)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.import_btn)
        
        layout.addLayout(button_layout)
        
        # Update count
        self._update_count()
    
    def _populate_table(self):
        """Populate the table with vocabulary items."""
        self.table.setRowCount(len(self.vocab_list))
        
        for row, item in enumerate(self.vocab_list):
            # Checkbox column
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | 
                Qt.ItemFlag.ItemIsEnabled
            )
            checkbox_item.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, self.COL_SELECT, checkbox_item)
            
            # Kanji
            kanji_item = QTableWidgetItem(item.get("kanji", ""))
            self.table.setItem(row, self.COL_KANJI, kanji_item)
            
            # Furigana
            furigana_item = QTableWidgetItem(item.get("furigana", ""))
            self.table.setItem(row, self.COL_FURIGANA, furigana_item)
            
            # Meaning
            meaning_item = QTableWidgetItem(item.get("meaning_vi", ""))
            self.table.setItem(row, self.COL_MEANING, meaning_item)
            
            # Sino-Vietnamese
            sino_item = QTableWidgetItem(item.get("sino_vietnamese", ""))
            self.table.setItem(row, self.COL_SINO, sino_item)
        
        # Check select all by default
        self.select_all_cb.setChecked(True)
        self._update_count()
    
    def _on_select_all_changed(self, state):
        """Handle select all checkbox state change."""
        check_state = Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked
        
        # Block signals to prevent multiple updates
        self.table.blockSignals(True)
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, self.COL_SELECT)
            if item:
                item.setCheckState(check_state)
        
        self.table.blockSignals(False)
        self._update_count()
    
    def _on_item_changed(self, item):
        """Handle table item change."""
        if item.column() == self.COL_SELECT:
            self._update_count()
    
    def _update_count(self):
        """Update the selected count label."""
        selected = self._get_selected_count()
        total = self.table.rowCount()
        self.count_label.setText(f"({selected}/{total} đã chọn)")
        
        # Update import button
        self.import_btn.setEnabled(selected > 0)
        self.import_btn.setText(f"📥 Import đã chọn ({selected})")
    
    def _get_selected_count(self) -> int:
        """Get the number of selected items."""
        count = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, self.COL_SELECT)
            if item and item.checkState() == Qt.CheckState.Checked:
                count += 1
        return count
    
    def _on_import_clicked(self):
        """Handle import button click."""
        self.selected_items = self._get_selected_items()
        
        if not self.selected_items:
            QMessageBox.warning(
                self, 
                "Thông báo", 
                "Vui lòng chọn ít nhất một từ để import."
            )
            return
        
        # Emit signal and close dialog
        self.import_requested.emit(self.selected_items)
        self.accept()
    
    def _get_selected_items(self) -> List[Dict[str, Any]]:
        """Get all selected vocabulary items with their (possibly edited) values."""
        items = []
        
        for row in range(self.table.rowCount()):
            checkbox = self.table.item(row, self.COL_SELECT)
            if checkbox and checkbox.checkState() == Qt.CheckState.Checked:
                # Get current cell values (may have been edited)
                item = {
                    "kanji": self.table.item(row, self.COL_KANJI).text().strip(),
                    "furigana": self.table.item(row, self.COL_FURIGANA).text().strip(),
                    "meaning_vi": self.table.item(row, self.COL_MEANING).text().strip(),
                    "sino_vietnamese": self.table.item(row, self.COL_SINO).text().strip(),
                }
                items.append(item)
        
        return items
    
    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Public method to get selected items after dialog closes.
        
        Returns:
            List of selected vocabulary dictionaries
        """
        return self.selected_items


class ApiKeyInputDialog(QDialog):
    """Dialog for inputting Gemini API key."""
    
    def __init__(self, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.api_key = ""
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        from PySide6.QtWidgets import QLineEdit
        
        self.setWindowTitle("🔑 Nhập API Key")
        self.setFixedSize(500, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        info_label = QLabel(
            "Để sử dụng tính năng Quét ảnh (AI), bạn cần có Google Gemini API Key.<br><br>"
            "1. Truy cập: <a href='https://aistudio.google.com/app/apikey'>https://aistudio.google.com/app/apikey</a><br>"
            "2. Tạo API Key miễn phí<br>"
            "3. Dán API Key vào ô bên dưới"
        )
        info_label.setWordWrap(True)
        info_label.setOpenExternalLinks(True)  # Cho phép click mở trình duyệt
        layout.addWidget(info_label)
        
        # API Key input
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Paste your Gemini API Key here...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addWidget(self.key_input)
        
        # Show/hide toggle
        self.show_key_btn = QPushButton("👁")
        self.show_key_btn.setFixedWidth(30)
        self.show_key_btn.clicked.connect(self._toggle_key_visibility)
        key_layout.addWidget(self.show_key_btn)
        
        layout.addLayout(key_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Xác nhận")
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _toggle_key_visibility(self):
        """Toggle API key visibility."""
        from PySide6.QtWidgets import QLineEdit
        if self.key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("🙈")
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("👁")
    
    def _on_ok(self):
        """Handle OK button click."""
        self.api_key = self.key_input.text().strip()
        if not self.api_key:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập API Key")
            return
        self.accept()
    
    def get_api_key(self) -> str:
        """Get the entered API key."""
        return self.api_key
