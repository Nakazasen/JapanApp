"""Import Grammar CSV Dialog for bulk grammar import.

Allows users to:
- Select CSV/Excel file
- Set default category/source and level
- Preview imported data
- Import with progress tracking
"""
from typing import Optional, List, Dict, Any
import csv
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QFileDialog, QTextEdit,
    QProgressBar, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt, Signal

from frontend.core.database import get_session


class ImportGrammarCSVDialog(QDialog):
    """Dialog for importing grammar from CSV files."""
    
    import_completed = Signal(dict)  # Emits import result
    
    def __init__(
        self,
        parent=None,
        lang: str = "jp",
        categories: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize import dialog.
        
        Args:
            parent: Parent widget
            lang: Current language ("jp" or "en")
            categories: List of available categories
        """
        super().__init__(parent)
        self.lang = lang
        self.categories = categories or []
        self.file_path = None
        self.preview_data = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("📥 Import ngữ pháp từ CSV")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # ===== File Selection =====
        file_group = QGroupBox("📁 Chọn file")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_label = QLabel("Chưa chọn file...")
        self.file_path_label.setStyleSheet("color: #666;")
        file_layout.addWidget(self.file_path_label, 1)
        
        self.browse_btn = QPushButton("📂 Duyệt...")
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_btn)
        
        layout.addWidget(file_group)
        
        # ===== Default Settings =====
        defaults_group = QGroupBox("⚙️ Cài đặt mặc định cho mục mới")
        defaults_layout = QVBoxLayout(defaults_group)
        
        # Category
        cat_row = QHBoxLayout()
        cat_row.addWidget(QLabel("Chủ đề:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("(Không chọn)", None)
        for cat in self.categories:
            icon = cat.get('icon', '📁')
            name = cat.get('name', 'Unknown')
            self.category_combo.addItem(f"{icon} {name}", cat.get('id'))
        cat_row.addWidget(self.category_combo, 1)
        defaults_layout.addLayout(cat_row)
        
        # Source/Curriculum
        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Giáo trình:"))
        self.source_combo = QComboBox()
        self.source_combo.setEditable(True)
        self.source_combo.addItem("(Không chọn)")
        
        from frontend.models.grammar import JAPANESE_GRAMMAR_SOURCES, ENGLISH_GRAMMAR_SOURCES
        preset_sources = JAPANESE_GRAMMAR_SOURCES if self.lang == "jp" else ENGLISH_GRAMMAR_SOURCES
        self.source_combo.addItems(preset_sources)
        source_row.addWidget(self.source_combo, 1)
        defaults_layout.addLayout(source_row)
        
        # Level
        level_row = QHBoxLayout()
        level_row.addWidget(QLabel("Cấp độ:"))
        self.level_combo = QComboBox()
        self.level_combo.addItem("(Không chọn)")
        
        from frontend.models.grammar import JAPANESE_GRAMMAR_LEVELS, ENGLISH_GRAMMAR_LEVELS
        preset_levels = JAPANESE_GRAMMAR_LEVELS if self.lang == "jp" else ENGLISH_GRAMMAR_LEVELS
        self.level_combo.addItems(preset_levels)
        level_row.addWidget(self.level_combo, 1)
        defaults_layout.addLayout(level_row)
        
        layout.addWidget(defaults_group)
        
        # ===== Preview =====
        preview_group = QGroupBox("👁️ Xem trước dữ liệu")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels([
            "Tiêu đề", "Pattern", "Ý nghĩa", "Cấp độ", "Giáo trình"
        ])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_table.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_table)
        
        self.preview_count_label = QLabel("0 dòng sẽ được import")
        preview_layout.addWidget(self.preview_count_label)
        
        layout.addWidget(preview_group)
        
        # ===== CSV Format Help =====
        help_group = QGroupBox("📝 Định dạng CSV")
        help_layout = QVBoxLayout(help_group)
        help_text = QLabel(
            "File CSV cần có header với các cột (bắt buộc: <b>title</b>):\n"
            "• <b>title</b> - Tên ngữ pháp (bắt buộc)\n"
            "• <b>pattern</b> (tùy chọn) - Cấu trúc (ví dụ: Vて + ください)\n"
            "• <b>description</b> (tùy chọn) - Ý nghĩa / giải thích\n"
            "• <b>usage_notes</b> (tùy chọn) - Cách dùng\n"
            "• <b>level</b> (tùy chọn) - Cấp độ (N3, B2, ...)\n"
            "• <b>source</b> (tùy chọn) - Giáo trình"
        )
        help_text.setTextFormat(Qt.RichText)
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #555; font-size: 12px;")
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        
        # ===== Progress =====
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # ===== Buttons =====
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.import_btn = QPushButton("📥 Import")
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 25px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.import_btn.clicked.connect(self._do_import)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.import_btn)
        layout.addLayout(button_layout)
    
    def _browse_file(self) -> None:
        """Open file browser for CSV selection."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file CSV",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_label.setText(os.path.basename(file_path))
            self.file_path_label.setStyleSheet("color: #333; font-weight: bold;")
            self._load_preview()
    
    def _load_preview(self) -> None:
        """Load and preview CSV data."""
        if not self.file_path:
            return
        
        try:
            # Detect file type and read
            if self.file_path.endswith(('.xlsx', '.xls')):
                self._load_excel()
            else:
                self._load_csv()
            
            # Update preview table
            self.preview_table.setRowCount(min(10, len(self.preview_data)))
            
            for row_idx, row in enumerate(self.preview_data[:10]):
                self.preview_table.setItem(row_idx, 0, QTableWidgetItem(row.get('title', '')))
                self.preview_table.setItem(row_idx, 1, QTableWidgetItem(row.get('pattern', '')))
                self.preview_table.setItem(row_idx, 2, QTableWidgetItem(row.get('description', '')))
                self.preview_table.setItem(row_idx, 3, QTableWidgetItem(row.get('level', '')))
                self.preview_table.setItem(row_idx, 4, QTableWidgetItem(row.get('source', '')))
            
            count = len(self.preview_data)
            self.preview_count_label.setText(
                f"<b>{count}</b> dòng sẽ được import" + 
                (" (chỉ hiển thị 10 dòng đầu)" if count > 10 else "")
            )
            self.import_btn.setEnabled(count > 0)
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi đọc file", f"Không thể đọc file:\n{str(e)}")
            self.preview_data = []
            self.import_btn.setEnabled(False)
    
    def _load_csv(self) -> None:
        """Load data from CSV file."""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.preview_data = list(reader)
    
    def _load_excel(self) -> None:
        """Load data from Excel file."""
        try:
            import pandas as pd
            df = pd.read_excel(self.file_path)
            self.preview_data = df.to_dict('records')
        except ImportError:
            QMessageBox.warning(
                self, "Thiếu thư viện",
                "Cần cài đặt pandas và openpyxl để đọc file Excel:\n"
                "pip install pandas openpyxl"
            )
            self.preview_data = []
    
    def _do_import(self) -> None:
        """Perform the import operation."""
        if not self.preview_data:
            return
        
        # Get defaults
        default_category_id = self.category_combo.currentData()
        
        default_source = self.source_combo.currentText()
        if default_source == "(Không chọn)":
            default_source = None
        
        default_level = self.level_combo.currentText()
        if default_level == "(Không chọn)":
            default_level = None
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.preview_data))
        self.progress_bar.setValue(0)
        self.import_btn.setEnabled(False)
        
        # Do import via GrammarFetcherService
        from frontend.services.grammar_fetcher_service import GrammarFetcherService
        service = GrammarFetcherService()
        
        with get_session() as session:
            result = service.bulk_import(
                items=self.preview_data,
                lang=self.lang,
                session=session,
                default_category_id=default_category_id,
                default_source=default_source,
                default_level=default_level
            )
        
        self.progress_bar.setValue(len(self.preview_data))
        
        # Show result
        if result.get('success'):
            QMessageBox.information(
                self, "Import thành công",
                f"Đã import: {result.get('imported', 0)} ngữ pháp\n"
                f"Bỏ qua (trùng lặp): {result.get('skipped', 0)} mục\n"
                f"Lỗi: {len(result.get('errors', []))} dòng"
            )
            self.import_completed.emit(result)
            self.accept()
        else:
            QMessageBox.warning(
                self, "Lỗi Import",
                f"Không thể import:\n{result.get('error', 'Unknown error')}"
            )
            self.import_btn.setEnabled(True)
