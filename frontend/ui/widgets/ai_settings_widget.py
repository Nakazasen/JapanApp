"""
AI Settings Widget - Dynamic Model Manager & Playground
========================================================
PySide6 port from leetcode_mastery for EnglishApp.
Provides UI for managing AI models and testing connections.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QFrame, QHeaderView, QMessageBox,
    QGroupBox, QTextEdit, QCheckBox, QSpinBox, QDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, QThread, QSettings
from PySide6.QtGui import QFont, QColor

from frontend.services.ai_service import AIConfigManager, test_single_model_connection, get_config_manager


class TestConnectionWorker(QThread):
    """Background worker for testing model connection."""
    result_ready = Signal(dict)
    
    def __init__(self, api_key: str, model_name: str, test_prompt: str):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        self.test_prompt = test_prompt
    
    def run(self):
        result = test_single_model_connection(
            self.api_key, self.model_name, self.test_prompt
        )
        self.result_ready.emit(result)


class AISettingsWidget(QDialog):
    """
    Settings dialog for AI configuration.
    
    Features:
    - Model list management (CRUD)
    - Priority ordering (Move Up/Down)
    - Playground for testing connections
    """
    
    config_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.test_worker = None
        
        self.setWindowTitle("⚙️ AI Settings & Playground")
        self.setMinimumSize(700, 600)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # API Key Section
        api_group = self._create_api_key_section()
        layout.addWidget(api_group)
        
        # Model Manager Section
        model_group = self._create_model_manager_section()
        layout.addWidget(model_group)
        
        # Playground Section
        playground_group = self._create_playground_section()
        layout.addWidget(playground_group)
        
        # Pomodoro Section
        pomo_group = self._create_pomodoro_section()
        layout.addWidget(pomo_group)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Lưu Cấu Hình")
        save_btn.clicked.connect(self.save_config)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                padding: 12px 25px;
                font-size: 14px;
            }
        """)
        btn_layout.addWidget(save_btn)
        
        reload_btn = QPushButton("🔄 Tải Lại")
        reload_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(reload_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog, QMessageBox {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                padding: 8px;
                color: white;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 8px;
                border: none;
            }
            QTableWidget {
                background-color: #252526;
                color: white;
                border: 1px solid #3c3c3c;
                gridline-color: #3c3c3c;
                selection-background-color: #094771;
            }
            QSpinBox, QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3c3c3c;
                padding: 4px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton#ActionBtn {
                padding: 0px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #555;
            }
            /* Specialized Action Buttons */
            QPushButton#UpBtn { background-color: #2e7d32; }
            QPushButton#UpBtn:hover { background-color: #388e3c; }
            QPushButton#DownBtn { background-color: #1565c0; }
            QPushButton#DownBtn:hover { background-color: #1976d2; }
            QPushButton#DelBtn { background-color: #c62828; }
            QPushButton#DelBtn:hover { background-color: #d32f2f; }
            QTableWidget::item:selected {
                background-color: #094771;
                color: white;
            }
        """)
    
    def _create_api_key_section(self) -> QGroupBox:
        """Create API keys section handles multiple keys."""
        group = QGroupBox("🔑 Danh sách API Keys (Xoay vòng tự động - 1 key mỗi dòng)")
        layout = QVBoxLayout(group)
        
        self.api_keys_text = QTextEdit()
        self.api_keys_text.setPlaceholderText("Dán danh sách API Keys vào đây, mỗi dòng một key...")
        self.api_keys_text.setAcceptRichText(False)
        self.api_keys_text.setFixedHeight(80)
        layout.addWidget(self.api_keys_text)
        
        help_label = QLabel("💡 Mẹo: Hệ thống sẽ tự động chuyển sang Key tiếp theo khi Key hiện tại hết hạn mức.")
        help_label.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
        layout.addWidget(help_label)
        
        return group
    
    def _create_model_manager_section(self) -> QGroupBox:
        """Create model list management section."""
        group = QGroupBox("📋 Danh sách Model (Waterfall Priority)")
        layout = QVBoxLayout(group)
        
        # Table
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(4)
        self.model_table.setHorizontalHeaderLabels(["Model ID", "Active", "Timeout (s)", "Actions"])
        self.model_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.model_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.model_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.model_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.model_table.setColumnWidth(1, 60)
        self.model_table.setColumnWidth(2, 80)
        self.model_table.setColumnWidth(3, 170)
        self.model_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.model_table)
        
        # Add new model row
        add_layout = QHBoxLayout()
        
        self.new_model_input = QLineEdit()
        self.new_model_input.setPlaceholderText("gemini-3.0-future")
        add_layout.addWidget(self.new_model_input, 1)
        
        add_btn = QPushButton("➕ Thêm Model Mới")
        add_btn.clicked.connect(self.add_model)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        return group
    
    def _create_playground_section(self) -> QGroupBox:
        """Create playground testing section."""
        group = QGroupBox("🧪 Playground - Test Connection")
        layout = QVBoxLayout(group)
        
        test_row = QHBoxLayout()
        test_row.addWidget(QLabel("Model:"))
        self.test_model_selector = QComboBox()
        self.test_model_selector.setEditable(True)
        self.test_model_selector.setPlaceholderText("Chọn hoặc nhập model để test...")
        test_row.addWidget(self.test_model_selector, 1)
        layout.addLayout(test_row)
        
        # Test prompt
        prompt_row = QHBoxLayout()
        prompt_row.addWidget(QLabel("Prompt:"))
        self.test_prompt_input = QLineEdit("Hello, are you alive?")
        prompt_row.addWidget(self.test_prompt_input, 1)
        layout.addLayout(prompt_row)
        
        # Test button and result
        action_row = QHBoxLayout()
        
        self.test_btn = QPushButton("🚀 Test Connection")
        self.test_btn.clicked.connect(self.run_test)
        action_row.addWidget(self.test_btn)
        
        self.test_result_label = QLabel("")
        self.test_result_label.setStyleSheet("font-size: 12px;")
        action_row.addWidget(self.test_result_label, 1)
        
        layout.addLayout(action_row)
        
        # Response area
        self.test_response = QTextEdit()
        self.test_response.setReadOnly(True)
        self.test_response.setMaximumHeight(100)
        self.test_response.setPlaceholderText("Kết quả test sẽ hiển thị ở đây...")
        layout.addWidget(self.test_response)
        
        return group

    def _create_pomodoro_section(self) -> QGroupBox:
        """Create Pomodoro timer settings section."""
        group = QGroupBox("🍅 Pomodoro Timer Settings")
        layout = QHBoxLayout(group)
        
        self.pomo_settings = QSettings("EnglishApp", "Pomodoro")
        
        # Work
        work_layout = QVBoxLayout()
        work_layout.addWidget(QLabel("Học (m):"))
        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 120)
        self.work_spin.setValue(self.pomo_settings.value("work_duration", 25, type=int))
        work_layout.addWidget(self.work_spin)
        layout.addLayout(work_layout)
        
        # Short Break
        sb_layout = QVBoxLayout()
        sb_layout.addWidget(QLabel("Nghỉ ngắn:"))
        self.sb_spin = QSpinBox()
        self.sb_spin.setRange(1, 30)
        self.sb_spin.setValue(self.pomo_settings.value("short_break_duration", 5, type=int))
        sb_layout.addWidget(self.sb_spin)
        layout.addLayout(sb_layout)
        
        # Long Break
        lb_layout = QVBoxLayout()
        lb_layout.addWidget(QLabel("Nghỉ dài:"))
        self.lb_spin = QSpinBox()
        self.lb_spin.setRange(1, 60)
        self.lb_spin.setValue(self.pomo_settings.value("long_break_duration", 15, type=int))
        lb_layout.addWidget(self.lb_spin)
        layout.addLayout(lb_layout)
        
        return group
    
    def load_data(self):
        """Load current configuration into UI."""
        self.config_manager.load_config()
        # API Keys
        keys = self.config_manager.api_keys
        if keys:
            self.api_keys_text.setPlainText("\n".join(keys))
        else:
            # Fallback for old single key config
            self.api_keys_text.setPlainText(self.config_manager.api_key)
        
        # Model Table
        self.model_table.setRowCount(0)
        for model in self.config_manager.waterfall_strategy:
            self._add_model_row(model)
        
        self._update_playground_models()
    
    def _add_model_row(self, model: dict):
        """Add a row to the model table."""
        row = self.model_table.rowCount()
        self.model_table.insertRow(row)
        
        # Model ID
        item = QTableWidgetItem(model["model_id"])
        item.setForeground(QColor("white"))
        self.model_table.setItem(row, 0, item)
        
        # Active checkbox
        active_widget = QWidget()
        active_layout = QHBoxLayout(active_widget)
        active_layout.setContentsMargins(0, 0, 0, 0)
        active_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        active_cb = QCheckBox()
        active_cb.setChecked(model.get("is_active", True))
        active_layout.addWidget(active_cb)
        self.model_table.setCellWidget(row, 1, active_widget)
        
        # Timeout
        timeout_widget = QSpinBox()
        timeout_widget.setRange(1, 60)
        timeout_widget.setValue(model.get("timeout", 10))
        self.model_table.setCellWidget(row, 2, timeout_widget)
        
        # Action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)
        actions_layout.setSpacing(2)
        
        up_btn = QPushButton("▲")
        up_btn.setObjectName("UpBtn")
        up_btn.setFixedSize(30, 25)
        up_btn.setToolTip("Di chuyển lên")
        up_btn.clicked.connect(self.move_model_up)
        actions_layout.addWidget(up_btn)
        
        down_btn = QPushButton("▼")
        down_btn.setObjectName("DownBtn")
        down_btn.setFixedSize(30, 25)
        down_btn.setToolTip("Di chuyển xuống")
        down_btn.clicked.connect(self.move_model_down)
        actions_layout.addWidget(down_btn)
        
        del_btn = QPushButton("✕")
        del_btn.setObjectName("DelBtn")
        del_btn.setFixedSize(30, 25)
        del_btn.setToolTip("Xóa Model")
        del_btn.clicked.connect(self.delete_model)
        actions_layout.addWidget(del_btn)
        
        self.model_table.setCellWidget(row, 3, actions_widget)
        self._update_playground_models()
    
    def _update_playground_models(self):
        """Sync the combo box in Playground with the model table."""
        current_text = self.test_model_selector.currentText()
        self.test_model_selector.clear()
        
        models = []
        for row in range(self.model_table.rowCount()):
            item = self.model_table.item(row, 0)
            if item:
                models.append(item.text())
        
        self.test_model_selector.addItems(models)
        
        # Restore or set default
        if current_text:
            self.test_model_selector.setCurrentText(current_text)
        elif models:
            self.test_model_selector.setCurrentIndex(0)
    
    def add_model(self):
        """Add new model from input."""
        model_id = self.new_model_input.text().strip()
        if not model_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên model!")
            return
        
        # Check duplicate
        for row in range(self.model_table.rowCount()):
            if self.model_table.item(row, 0).text() == model_id:
                QMessageBox.warning(self, "Lỗi", f"Model '{model_id}' đã tồn tại!")
                return
        
        self._add_model_row({"model_id": model_id, "is_active": True, "timeout": 10})
        self.new_model_input.clear()
        self._update_playground_models()
    
    def _get_sender_row(self) -> int:
        """Helper to get the row index of the widget that sent the signal."""
        sender = self.sender()
        if not sender:
            return -1
        
        # More robust way: find which cell widget contains the sender
        for r in range(self.model_table.rowCount()):
            cell_widget = self.model_table.cellWidget(r, 3)
            if cell_widget and cell_widget.isAncestorOf(sender):
                return r
        return -1

    def delete_model(self):
        """Delete model at row."""
        row = self._get_sender_row()
        if row < 0: return

        if self.model_table.rowCount() <= 1:
            QMessageBox.warning(self, "Lỗi", "Phải giữ ít nhất 1 model!")
            return
        
        model_id = self.model_table.item(row, 0).text()
        reply = QMessageBox.question(
            self, "Xác nhận", f"Xóa model '{model_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.model_table.removeRow(row)
            self._update_playground_models()
    
    def move_model_up(self):
        """Move model up in priority."""
        row = self._get_sender_row()
        if row > 0:
            self._swap_rows(row, row - 1)
    
    def move_model_down(self):
        """Move model down in priority."""
        row = self._get_sender_row()
        if row >= 0 and row < self.model_table.rowCount() - 1:
            self._swap_rows(row, row + 1)
    
    def _swap_rows(self, row1: int, row2: int):
        """Swap two rows in the table."""
        # Get data
        data1 = self._get_row_data(row1)
        data2 = self._get_row_data(row2)
        
        # Clear and re-add
        self.model_table.removeRow(max(row1, row2))
        self.model_table.removeRow(min(row1, row2))
        
        self.model_table.insertRow(min(row1, row2))
        self._set_row_data(min(row1, row2), data2 if row1 < row2 else data1)
        
        self.model_table.insertRow(max(row1, row2))
        self._set_row_data(max(row1, row2), data1 if row1 < row2 else data2)
    
    def _get_row_data(self, row: int) -> dict:
        """Get model data from table row."""
        active_widget = self.model_table.cellWidget(row, 1)
        active_cb = active_widget.findChild(QCheckBox)
        timeout_widget = self.model_table.cellWidget(row, 2)
        
        return {
            "model_id": self.model_table.item(row, 0).text(),
            "is_active": active_cb.isChecked() if active_cb else True,
            "timeout": timeout_widget.value() if timeout_widget else 10
        }
    
    def _set_row_data(self, row: int, data: dict):
        """Set model data to table row."""
        # Model ID
        item = QTableWidgetItem(data["model_id"])
        item.setForeground(QColor("white"))
        self.model_table.setItem(row, 0, item)
        
        active_widget = QWidget()
        active_layout = QHBoxLayout(active_widget)
        active_layout.setContentsMargins(0, 0, 0, 0)
        active_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        active_cb = QCheckBox()
        active_cb.setChecked(data.get("is_active", True))
        active_layout.addWidget(active_cb)
        self.model_table.setCellWidget(row, 1, active_widget)
        
        timeout_widget = QSpinBox()
        timeout_widget.setRange(1, 60)
        timeout_widget.setValue(data.get("timeout", 10))
        self.model_table.setCellWidget(row, 2, timeout_widget)
        
        # Recreate action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)
        actions_layout.setSpacing(2)
        
        up_btn = QPushButton("▲")
        up_btn.setObjectName("UpBtn")
        up_btn.setFixedSize(30, 25)
        up_btn.setToolTip("Di chuyển lên")
        up_btn.clicked.connect(self.move_model_up)
        actions_layout.addWidget(up_btn)
        
        down_btn = QPushButton("▼")
        down_btn.setObjectName("DownBtn")
        down_btn.setFixedSize(30, 25)
        down_btn.setToolTip("Di chuyển xuống")
        down_btn.clicked.connect(self.move_model_down)
        actions_layout.addWidget(down_btn)
        
        del_btn = QPushButton("✕")
        del_btn.setObjectName("DelBtn")
        del_btn.setFixedSize(30, 25)
        del_btn.setToolTip("Xóa Model")
        del_btn.clicked.connect(self.delete_model)
        actions_layout.addWidget(del_btn)
        
        self.model_table.setCellWidget(row, 3, actions_widget)
    
    def save_config(self):
        """Save current UI state to config."""
        # API Key
        keys_text = self.api_keys_text.toPlainText().strip()
        keys = [k.strip() for k in keys_text.split("\n") if k.strip()]
        self.config_manager.api_keys = keys
        
        # Model list
        models = []
        for row in range(self.model_table.rowCount()):
            models.append(self._get_row_data(row))
        
        self.config_manager.waterfall_strategy = models
        
        # Save Pomodoro Settings
        self.pomo_settings.setValue("work_duration", self.work_spin.value())
        self.pomo_settings.setValue("short_break_duration", self.sb_spin.value())
        self.pomo_settings.setValue("long_break_duration", self.lb_spin.value())
        
        # Notify main window if it exists
        parent_window = self.window()
        if hasattr(parent_window, 'pomodoro_widget'):
            parent_window.pomodoro_widget.reload_settings()
        
        if self.config_manager.save_config():
            QMessageBox.information(self, "Thành công", "✅ Đã lưu cấu hình!")
            self.config_changed.emit()
        else:
            QMessageBox.critical(self, "Lỗi", "❌ Không thể lưu cấu hình!")
    
    def run_test(self):
        """Run connection test in background."""
        keys_text = self.api_keys_text.toPlainText().strip()
        keys = [k.strip() for k in keys_text.split("\n") if k.strip()]
        api_key = keys[0] if keys else ""
        model_name = self.test_model_selector.currentText().strip()
        test_prompt = self.test_prompt_input.text().strip() or "Ping"
        
        if not api_key:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập API Key!")
            return
        
        if not model_name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên Model!")
            return
        
        self.test_btn.setDisabled(True)
        self.test_btn.setText("⏳ Đang test...")
        self.test_result_label.setText("🔄 Connecting...")
        self.test_response.clear()
        
        self.test_worker = TestConnectionWorker(api_key, model_name, test_prompt)
        self.test_worker.result_ready.connect(self._on_test_result)
        self.test_worker.start()
    
    def _on_test_result(self, result: dict):
        """Handle test result."""
        self.test_btn.setDisabled(False)
        self.test_btn.setText("🚀 Test Connection")
        
        if result.get("success"):
            self.test_result_label.setText(f"✅ SUCCESS - Latency: {result['latency']}")
            self.test_result_label.setStyleSheet("color: #4CAF50; font-size: 12px;")
            self.test_response.setText(f"Response:\n{result.get('reply', '')}")
        else:
            self.test_result_label.setText("❌ FAILED")
            self.test_result_label.setStyleSheet("color: #f44336; font-size: 12px;")
            self.test_response.setText(f"Error:\n{result.get('error', 'Unknown error')}")
