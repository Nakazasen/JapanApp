"""Import CSV Dialog for bulk vocabulary import.

Allows users to:
- Select CSV/Excel file
- Set default curriculum/source and level
- Preview imported data
- Import with progress tracking
"""
from typing import Optional, List, Dict, Any
import csv
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QFileDialog, QTextEdit,
    QProgressBar, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt, Signal


class ImportCSVDialog(QDialog):
    """Dialog for importing vocabulary from CSV files."""
    
    import_completed = Signal(dict)  # Emits import result
    
    def __init__(
        self,
        parent=None,
        lang: str = "jp",
        topics: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize import dialog.
        
        Args:
            parent: Parent widget
            lang: Current language ("jp" or "en")
            topics: List of available topics
        """
        super().__init__(parent)
        self.lang = lang
        self.topics = topics or []
        self.file_path = None
        self.preview_data = []
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("📥 Import từ vựng từ CSV")
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
        defaults_group = QGroupBox("⚙️ Cài đặt mặc định cho từ mới")
        defaults_layout = QVBoxLayout(defaults_group)
        
        # Topic
        topic_row = QHBoxLayout()
        topic_row.addWidget(QLabel("Chủ đề:"))
        self.topic_combo = QComboBox()
        self.topic_combo.addItem("(Không chọn)", None)
        for topic in self.topics:
            icon = topic.get('icon', '📁')
            name = topic.get('name', 'Unknown')
            self.topic_combo.addItem(f"{icon} {name}", topic.get('id'))
        topic_row.addWidget(self.topic_combo, 1)
        defaults_layout.addLayout(topic_row)
        
        # Source/Curriculum
        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("Giáo trình:"))
        self.source_combo = QComboBox()
        self.source_combo.setEditable(True)
        self.source_combo.addItem("(Không chọn)")
        
        from frontend.models.vocab import JAPANESE_SOURCES, ENGLISH_SOURCES
        preset_sources = JAPANESE_SOURCES if self.lang == "jp" else ENGLISH_SOURCES
        self.source_combo.addItems(preset_sources)
        source_row.addWidget(self.source_combo, 1)
        defaults_layout.addLayout(source_row)
        
        # Level
        level_row = QHBoxLayout()
        level_row.addWidget(QLabel("Cấp độ:"))
        self.level_combo = QComboBox()
        self.level_combo.addItem("(Không chọn)")
        
        from frontend.models.vocab import JAPANESE_LEVELS, ENGLISH_LEVELS
        preset_levels = JAPANESE_LEVELS if self.lang == "jp" else ENGLISH_LEVELS
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
            "Từ", "Phiên âm", "Nghĩa", "Cấp độ", "Giáo trình"
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
            "File CSV cần có header với các cột (bắt buộc: <b>word, meaning</b>):\n"
            "• <b>word</b> - Từ vựng\n"
            "• <b>meaning</b> - Nghĩa tiếng Việt\n"
            "• <b>reading</b> (tùy chọn) - Phiên âm (Hiragana/IPA)\n"
            "• <b>example</b> (tùy chọn) - Câu ví dụ\n"
            "• <b>level</b> (tùy chọn) - Cấp độ (N3, IELTS 6.5, ...)\n"
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
            "",
            "CSV/Excel/PDF Files (*.csv *.xlsx *.xls *.pdf);;All Files (*)"
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
            if self.file_path.endswith('.pdf'):
                self._load_pdf()
            elif self.file_path.endswith(('.xlsx', '.xls')):
                self._load_excel()
            else:
                self._load_csv()
            
            # Update preview table
            self.preview_table.setRowCount(min(10, len(self.preview_data)))
            
            for row_idx, row in enumerate(self.preview_data[:10]):
                self.preview_table.setItem(row_idx, 0, QTableWidgetItem(row.get('word', '')))
                self.preview_table.setItem(row_idx, 1, QTableWidgetItem(row.get('reading', '')))
                self.preview_table.setItem(row_idx, 2, QTableWidgetItem(row.get('meaning', '')))
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
            self.preview_data = []

    def _load_pdf(self) -> None:
        """Load data from PDF file."""
        try:
            from frontend.services.pdf_vocab_parser import PDFVocabParser
            parser = PDFVocabParser()
            self.preview_data = parser.extract_from_pdf(self.file_path)
            
            if not self.preview_data:
                QMessageBox.warning(
                    self, "Không tìm thấy dữ liệu",
                    "Không thể trích xuất từ vựng từ file PDF này.\n"
                    "Hãy chắc chắn file là dạng text (không phải ảnh scan) và có cấu trúc bảng hoặc danh sách rõ ràng."
                )
        except ImportError:
             QMessageBox.warning(
                self, "Thiếu thư viện",
                "Cần cài đặt pdfplumber để đọc file PDF:\n"
                "pip install pdfplumber"
            )
        except Exception as e:
            QMessageBox.warning(self, "Lỗi đọc PDF", f"Lỗi khi đọc file PDF:\n{str(e)}")
            self.preview_data = []
        """Perform the import operation."""
        if not self.preview_data:
            return
        
        # Get defaults
        default_topic_id = self.topic_combo.currentData()
        
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
        
        # Do import via VocabService
        from frontend.services import get_vocab_service
        vocab_service = get_vocab_service()
        
        result = vocab_service.bulk_import(
            items=self.preview_data,
            lang=self.lang,
            default_topic_id=default_topic_id,
            default_source=default_source,
            default_level=default_level
        )
        
        self.progress_bar.setValue(len(self.preview_data))
        
        # Show result
        if result.get('success'):
            QMessageBox.information(
                self, "Import thành công",
                f"Đã import: {result.get('imported', 0)} từ\n"
                f"Bỏ qua (trùng lặp): {result.get('skipped', 0)} từ\n"
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
