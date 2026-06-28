"""Dictionary lookup dialog widget."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox
)
from PySide6.QtCore import QUrl, Qt
from frontend.services.dictionary_service import DictionaryService

# Try to import QWebEngineView for dictionary lookup
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEnginePage
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class DictionaryLookupDialog(QDialog):
    """Dialog for looking up words in various online dictionaries."""
    
    def __init__(self, parent=None, word: str = "", source_lang: str = "auto"):
        super().__init__(parent)
        self.word = word
        self.source_lang = source_lang
        self.current_dictionary = None
        self._suppress_signal = False
        self.init_ui()
        if word:
            self.set_lookup(word, source_lang)
    
    def init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle(f"Tra từ: {self.word}")
        self.setMinimumSize(900, 700)
        self.setWindowModality(Qt.NonModal)
        
        layout = QVBoxLayout(self)
        
        # Dictionary selector
        dict_layout = QHBoxLayout()
        dict_layout.addWidget(QLabel("Từ điển:"))
        
        self.dict_combo = QComboBox()
        dictionaries = DictionaryService.get_available_dictionaries()
        for dict_id, dict_name in dictionaries.items():
            self.dict_combo.addItem(dict_name, dict_id)
        self.dict_combo.currentIndexChanged.connect(self.on_dictionary_changed)
        dict_layout.addWidget(self.dict_combo)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Tải lại")
        refresh_btn.clicked.connect(self.refresh_page)
        dict_layout.addWidget(refresh_btn)
        
        # Open in browser button
        browser_btn = QPushButton("🌐 Mở trong trình duyệt")
        browser_btn.clicked.connect(self.open_in_browser)
        dict_layout.addWidget(browser_btn)
        
        dict_layout.addStretch()
        layout.addLayout(dict_layout)
        
        # Web view for dictionary content
        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            layout.addWidget(self.web_view)
        else:
            # Fallback: show message
            no_webengine_label = QLabel(
                "⚠️ QWebEngineWidgets chưa được cài đặt.\n"
                "Vui lòng cài đặt: pip install PySide6-WebEngine\n\n"
                "Hoặc sử dụng nút 'Mở trong trình duyệt' để tra từ."
            )
            no_webengine_label.setWordWrap(True)
            no_webengine_label.setStyleSheet("color: #FF6600; padding: 20px;")
            layout.addWidget(no_webengine_label)
            self.web_view = None
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def set_lookup(self, word: str, source_lang: str = "auto", dictionary_id: str = None):
        """Update the dialog to show dictionary lookup for another word."""
        if not word:
            return
        
        self.word = word
        self.source_lang = source_lang or "auto"
        self.setWindowTitle(f"Tra từ: {self.word}")
        
        dict_id = dictionary_id or DictionaryService.detect_best_dictionary(self.word, self.source_lang)
        if dict_id:
            self._set_current_dictionary(dict_id)
            self.load_dictionary(dict_id)
    
    def on_dictionary_changed(self, index):
        """Handle dictionary selection change."""
        if self._suppress_signal:
            return
        
        dict_id = self.dict_combo.itemData(index)
        if dict_id:
            self.load_dictionary(dict_id)
    
    def load_dictionary(self, dict_id: str):
        """Load a dictionary page."""
        if not self.word:
            return
        
        url = DictionaryService.get_dictionary_url(
            dict_id, 
            self.word, 
            self.source_lang
        )
        
        if not url:
            QMessageBox.warning(self, "Lỗi", f"Không thể tạo URL cho từ điển: {dict_id}")
            return
        
        self.current_dictionary = dict_id
        
        if self.web_view:
            self.web_view.setUrl(QUrl(url))
    
    def refresh_page(self):
        """Refresh the current dictionary page."""
        if self.current_dictionary:
            self.load_dictionary(self.current_dictionary)
    
    def _set_current_dictionary(self, dict_id: str):
        """Set combo selection without triggering reload twice."""
        if not dict_id:
            return
        self._suppress_signal = True
        try:
            for i in range(self.dict_combo.count()):
                if self.dict_combo.itemData(i) == dict_id:
                    self.dict_combo.setCurrentIndex(i)
                    break
        finally:
            self._suppress_signal = False
    
    def open_in_browser(self):
        """Open current dictionary page in external browser."""
        if not self.current_dictionary:
            return
        
        url = DictionaryService.get_dictionary_url(
            self.current_dictionary,
            self.word,
            self.source_lang
        )
        
        if url:
            import webbrowser
            webbrowser.open(url)

