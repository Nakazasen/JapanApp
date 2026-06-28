"""AI Writing Coach Tab - Complete overhaul with Draft system and Smart Highlighting."""
# Standard library
import base64
import os
import tempfile
from typing import Optional, Dict, List

# Third-party
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QSplitter, QListWidget, QComboBox, QProgressBar,
    QMenu, QMessageBox, QDialog, QInputDialog, QListWidgetItem,
    QFrame, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextBrowser, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QAction, QTextCursor, QTextCharFormat, QColor, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# Local
from frontend.utils.async_helpers import run_async
from frontend.utils.language_utils import detect_language
from frontend.services.dictionary_service import DictionaryService
from frontend.services.writing_service import WritingService
from frontend.services.translator import TranslatorService
from frontend.services.tts import TTSService, get_tts_service
from frontend.ui.widgets.dictionary_dialog import DictionaryLookupDialog
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin
from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning


class ScoreBadge(QLabel):
    """Circular score badge widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(120, 120)
        self.set_score(0)
        
    def set_score(self, score: float):
        """Update score display with color coding."""
        if score >= 8:
            color = "#4CAF50"  # Green
            bg = "#E8F5E9"
        elif score >= 6:
            color = "#FF9800"  # Orange
            bg = "#FFF3E0"
        else:
            color = "#F44336"  # Red
            bg = "#FFEBEE"
            
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {color};
                border: 4px solid {color};
                border-radius: 60px;
                font-size: 36px;
                font-weight: bold;
            }}
        """)
        self.setText(f"{score:.1f}")


class DraftListDialog(QDialog):
    """Dialog to manage drafts."""
    def __init__(self, parent=None, drafts=None, on_delete=None):
        super().__init__(parent)
        self.setWindowTitle("📂 Bài viết đã lưu")
        self.resize(450, 400)
        self.on_delete = on_delete
        self.selected_draft = None
        
        layout = QVBoxLayout(self)
        
        # List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.list_widget)
        
        if drafts:
            self.refresh_list(drafts)
            
        # Buttons
        btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("📖 Mở")
        load_btn.clicked.connect(self.accept)
        
        del_btn = QPushButton("🗑️ Xóa")
        del_btn.setStyleSheet("background-color: #ffcdd2;")
        del_btn.clicked.connect(self._delete_selected)
        
        cancel_btn = QPushButton("Đóng")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def refresh_list(self, drafts):
        self.list_widget.clear()
        for d in drafts:
            date_str = str(d.get('updated_at', ''))[:10]
            lang_icon = "🇬🇧" if d.get('language') == 'en' else "🇯🇵"
            display = f"{lang_icon} {d.get('title', 'Untitled')}  •  {date_str}"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, d)
            self.list_widget.addItem(item)
            
    def _delete_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Chọn bài", "Vui lòng chọn một bài để xóa!")
            return
        
        draft = item.data(Qt.UserRole)
        if QMessageBox.question(
            self, "Xác nhận xóa", 
            f"Bạn có chắc muốn xóa bài \"{draft.get('title')}\"?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.on_delete:
                self.on_delete(draft.get('id'), item)
                
    def accept(self):
        item = self.list_widget.currentItem()
        if item:
            self.selected_draft = item.data(Qt.UserRole)
            super().accept()
        else:
            QMessageBox.warning(self, "Chọn bài", "Vui lòng chọn một bài để mở!")


class WritingTab(QWidget, TextContextMenuMixin):
    """AI Writing Coach - Learn to write better with AI feedback."""
    
    def __init__(self):
        super().__init__()
    def __init__(self):
        super().__init__()
        self.writing_service = WritingService()
        self.translator_service = TranslatorService()
        self.tts_service = get_tts_service()
        self.current_draft = None
        self.media_player = None
        self.audio_output = None
        self.dictionary_dialog = None
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the AI Writing Coach UI - Premium Studio Edition."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Apply Global Tab Styling
        self.setStyleSheet("""
            QWidget#WritingTab { background-color: #f8f9fa; }
            QFrame#ControlPanel { 
                background-color: #1a1a2e; 
                border-radius: 0px; 
            }
            QLabel { color: #2c3e50; }
            QLabel#WhiteLabel { color: #ffffff; }
            QLabel#SectionHeader { 
                font-size: 18px; 
                font-weight: bold; 
                color: #1a1a2e;
                margin-bottom: 5px;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                background: white;
            }
            QPushButton#PrimaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4b6cb7, stop:1 #182848);
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
            }
            QPushButton#PrimaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5d7cc2, stop:1 #243b55);
            }
            QPushButton#SecondaryBtn {
                background: white;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 8px 15px;
            }
            QPushButton#SecondaryBtn:hover {
                background: #f1f2f6;
            }
        """)
        self.setObjectName("WritingTab")

        # Top Control Bar (Dark Theme)
        self.control_panel = QFrame()
        self.control_panel.setObjectName("ControlPanel")
        self.control_panel.setFixedHeight(70)
        control_layout = QHBoxLayout(self.control_panel)
        control_layout.setContentsMargins(20, 0, 20, 0)
        
        logo_lbl = QLabel("✍️ AI WRITING STUDIO")
        logo_lbl.setObjectName("WhiteLabel")
        logo_lbl.setStyleSheet("font-size: 18px; font-weight: 900; letter-spacing: 1px;")
        control_layout.addWidget(logo_lbl)
        
        control_layout.addStretch()
        
        control_layout.addWidget(QLabel("Ngôn ngữ:", objectName="WhiteLabel"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["🇬🇧 Tiếng Anh", "🇯🇵 Tiếng Nhật"])
        self.lang_combo.setFixedWidth(160)
        self.lang_combo.setStyleSheet("""
            QComboBox { background: #16213e; color: white; border: 1px solid #4a4e69; }
            QComboBox QAbstractItemView { background: #16213e; color: white; }
        """)
        control_layout.addWidget(self.lang_combo)
        
        control_layout.addSpacing(20)
        
        self.open_btn = QPushButton("📂 Thư viện bài viết")
        self.open_btn.setObjectName("SecondaryBtn")
        self.open_btn.setStyleSheet("background: transparent; color: white; border: 1px solid #4a4e69;")
        self.open_btn.clicked.connect(self._open_drafts_dialog)
        control_layout.addWidget(self.open_btn)
        
        self.save_btn = QPushButton("💾 Lưu nháp")
        self.save_btn.setObjectName("SecondaryBtn")
        self.save_btn.setStyleSheet("background: #4a4e69; color: white; border: none;")
        self.save_btn.clicked.connect(self._save_draft)
        control_layout.addWidget(self.save_btn)
        
        main_layout.addWidget(self.control_panel)

        # Main Workspace Splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setStyleSheet("QSplitter::handle { background-color: #dcdde1; }")
        
        # ========== LEFT PANEL: Editor ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(30, 30, 30, 30)
        left_layout.setSpacing(15)
        
        # -- Topic section (Glass Card) --
        topic_card = QFrame()
        topic_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        topic_layout = QVBoxLayout(topic_card)
        topic_layout.setContentsMargins(15, 15, 15, 15)
        
        topic_header_layout = QHBoxLayout()
        topic_header_layout.addWidget(QLabel("📝 CHỦ ĐỀ BÀI VIẾT"))
        topic_header_layout.addStretch()
        
        self.suggest_topic_btn = QPushButton("🎲 Gợi ý chủ đề AI")
        self.suggest_topic_btn.setFixedWidth(150)
        self.suggest_topic_btn.clicked.connect(self._generate_topic)
        self.suggest_topic_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0a500; color: white; font-weight: bold;
                border-radius: 4px; padding: 5px; font-size: 11px;
            }
            QPushButton:hover { background-color: #d48f00; }
        """)
        topic_header_layout.addWidget(self.suggest_topic_btn)
        topic_layout.addLayout(topic_header_layout)
        
        self.topic_input = QComboBox()
        self.topic_input.setEditable(True)
        self.topic_input.setPlaceholderText("Nhập chủ đề bạn muốn luyện tập...")
        self.topic_input.setStyleSheet("font-size: 14px; padding: 10px; border: 1px solid #eee;")
        topic_layout.addWidget(self.topic_input)
        
        left_layout.addWidget(topic_card)
        
        # -- Editor area --
        self.text_editor = QTextEdit()
        self.text_editor.setPlaceholderText("Hãy bắt đầu bài viết của bạn tại đây...")
        self.text_editor.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 25px;
                font-size: 16px;
                line-height: 1.8;
                color: #2c3e50;
                selection-background-color: #3498db;
            }
        """)
        self.text_editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_editor.customContextMenuRequested.connect(self._show_context_menu)
        left_layout.addWidget(self.text_editor, stretch=1)
        
        # -- Bottom Stats & Action --
        bottom_bar = QHBoxLayout()
        self.word_count_label = QLabel("0 từ")
        self.word_count_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        self.text_editor.textChanged.connect(self._update_word_count)
        bottom_bar.addWidget(self.word_count_label)
        
        bottom_bar.addStretch()
        
        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet("color: #3498db; font-style: italic;")
        bottom_bar.addWidget(self.loading_label)
        
        self.review_btn = QPushButton("🚀 CHẤM BÀI VỚI AI")
        self.review_btn.setObjectName("PrimaryBtn")
        self.review_btn.clicked.connect(self._review_writing)
        bottom_bar.addWidget(self.review_btn)
        
        left_layout.addLayout(bottom_bar)
        
        self.main_splitter.addWidget(left_panel)
        
        # ========== RIGHT PANEL: Feedback (Dashboard style) ==========
        self.feedback_panel = QWidget()
        self.feedback_panel.setStyleSheet("background-color: #f1f2f6;")
        feedback_layout = QVBoxLayout(self.feedback_panel)
        feedback_layout.setContentsMargins(25, 30, 25, 25)
        feedback_layout.setSpacing(20)
        
        # Header with score
        score_card = QFrame()
        score_card.setStyleSheet("background: white; border-radius: 15px; border: 1px solid #e0e0e0;")
        score_card_layout = QHBoxLayout(score_card)
        score_card_layout.setContentsMargins(20, 20, 20, 20)
        
        score_info_layout = QVBoxLayout()
        score_info_layout.addWidget(QLabel("📊 ĐIỂM ĐÁNH GIÁ", styleSheet="font-weight: bold; color: #7f8c8d;"))
        self.score_title = QLabel("Cần đánh giá")
        self.score_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1a1a2e;")
        score_info_layout.addWidget(self.score_title)
        score_card_layout.addLayout(score_info_layout)
        
        score_card_layout.addStretch()
        self.score_badge = ScoreBadge()
        score_card_layout.addWidget(self.score_badge)
        
        feedback_layout.addWidget(score_card)
        
        # General comment card
        comment_card = QFrame()
        comment_card.setStyleSheet("background: #e3f2fd; border-radius: 10px; padding: 5px;")
        comment_layout = QVBoxLayout(comment_card)
        self.comment_label = QLabel("Chưa có nhận xét. Bấm 'Chấm bài' để xem đánh giá từ AI.")
        self.comment_label.setWordWrap(True)
        self.comment_label.setStyleSheet("font-size: 14px; color: #0d47a1; line-height: 1.5;")
        comment_layout.addWidget(self.comment_label)
        feedback_layout.addWidget(comment_card)
        
        # Tabs for details
        self.feedback_tabs = QTabWidget()
        self.feedback_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #dcdde1; border-radius: 8px; background: white; top: -1px; }
            QTabBar::tab {
                background: #f1f2f6; 
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                color: #7f8c8d;
            }
            QTabBar::tab:selected { background: white; color: #1a1a2e; font-weight: bold; }
        """)
        
        # Corrected version
        self.corrected_browser = QTextBrowser()
        self.corrected_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.corrected_browser.customContextMenuRequested.connect(
            lambda pos: self.show_text_context_menu(self.corrected_browser, pos)
        )
        self.feedback_tabs.addTab(self.corrected_browser, "📄 Bài sửa")
        
        # Error mapping
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(3)
        self.error_table.setHorizontalHeaderLabels(["Lỗi", "Gợi ý", "Lý do"])
        self.error_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.error_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.error_table.customContextMenuRequested.connect(self._show_error_table_context_menu)
        self.feedback_tabs.addTab(self.error_table, "📋 Chi tiết lỗi")
        
        # Tips
        self.tips_browser = QTextBrowser()
        self.tips_browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tips_browser.customContextMenuRequested.connect(
            lambda pos: self.show_text_context_menu(self.tips_browser, pos)
        )
        self.feedback_tabs.addTab(self.tips_browser, "💡 Mẹo học")
        
        feedback_layout.addWidget(self.feedback_tabs, stretch=1)
        
        self.feedback_panel.setVisible(False)
        self.main_splitter.addWidget(self.feedback_panel)
        
        # Sizing
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(self.main_splitter)
        
    def _show_context_menu(self, position):
        """Show context menu with translation/dictionary options."""
        self.show_text_context_menu(self.text_editor, position)
    
    def _show_error_table_context_menu(self, position):
        """Show context menu for error table with translation options."""
        # Get selected cell text
        item = self.error_table.itemAt(position)
        if not item:
            return
        
        selected_text = item.text().strip()
        if not selected_text:
            return
        
        # Create context menu with translation options
        menu = QMenu(self)
        
        # Translate action
        translate_action = QAction("🌐 Dịch (Tự phát hiện ngôn ngữ)", self)
        translate_action.triggered.connect(lambda: self._translate_text(selected_text, "auto", None))
        menu.addAction(translate_action)
        
        menu.addSeparator()
        
        # Manual translate options
        translate_jp_vi = QAction("🇯🇵 → 🇻🇳 Dịch Nhật → Việt", self)
        translate_jp_vi.triggered.connect(lambda: self._translate_text(selected_text, "ja", "vi"))
        menu.addAction(translate_jp_vi)
        
        translate_en_vi = QAction("🇬🇧 → 🇻🇳 Dịch Anh → Việt", self)
        translate_en_vi.triggered.connect(lambda: self._translate_text(selected_text, "en", "vi"))
        menu.addAction(translate_en_vi)
        
        menu.addSeparator()
        
        # Dictionary lookup
        dict_action = QAction("📚 Tra từ điển", self)
        dict_action.triggered.connect(lambda: self._lookup_word(selected_text))
        menu.addAction(dict_action)
        
        menu.addSeparator()
        
        # TTS
        speak_action = QAction("🔊 Đọc văn bản", self)
        speak_action.triggered.connect(lambda: self._mixin_speak_text(selected_text))
        menu.addAction(speak_action)
        
        menu.exec(self.error_table.mapToGlobal(position))
    
    def _translate_text(self, text: str, source_lang: str, target_lang: str):
        """Translate text and show result."""
        if not text:
            return
        
        async def translate():
            try:
                # TranslatorService is synchronous
                if source_lang == "auto" and target_lang is None:
                    # Auto-detect and translate to Vietnamese
                    detected_lang = detect_language(text)
                    if detected_lang in ["ja", "japanese", "jp"]:
                        result = self.translator_service.translate(text, "ja", "vi")
                    elif detected_lang in ["en", "english"]:
                        result = self.translator_service.translate(text, "en", "vi")
                    else:
                        result = self.translator_service.translate(text, detected_lang, "vi")
                    return {"success": True, "translated": result, "source": detected_lang}
                else:
                    result = self.translator_service.translate(text, source_lang, target_lang)
                    return {"success": True, "translated": result, "source": source_lang}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def show_result(result):
            if result.get("success"):
                translated = result.get("translated", "")
                source = result.get("source", "auto")
                lang_names = {"ja": "Nhật", "en": "Anh", "vi": "Việt", "auto": "Tự động"}
                toast_success(f"Dịch ({lang_names.get(source, source)}): {translated}")
            else:
                toast_error(f"Không thể dịch: {result.get('error', 'Unknown error')}")
        
        run_async(translate, show_result)
    
    def _lookup_word(self, word: str):
        """Open dictionary lookup dialog."""
        if not word:
            return
        
        if not self.dictionary_dialog:
            self.dictionary_dialog = DictionaryLookupDialog(self)
            self.dictionary_dialog.finished.connect(lambda _: setattr(self, "dictionary_dialog", None))
        
        detected_lang = detect_language(word)
        self.dictionary_dialog.set_lookup(word, detected_lang, None)
        self.dictionary_dialog.show()
        self.dictionary_dialog.raise_()
        self.dictionary_dialog.activateWindow()
    
        
    def _update_word_count(self):
        """Update word count display."""
        text = self.text_editor.toPlainText().strip()
        words = len(text.split()) if text else 0
        self.word_count_label.setText(f"{words} từ")
        
    def _get_current_lang(self) -> str:
        """Get current language code."""
        return "en" if self.lang_combo.currentIndex() == 0 else "jp"
        
    # ========== Draft Management ==========
    
    def _save_draft(self):
        """Save current text as draft."""
        text = self.text_editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập nội dung bài viết trước!")
            return
            
        # Get title
        if self.current_draft:
            title = self.current_draft.get('title', 'Untitled')
        else:
            topic = self.topic_input.currentText().strip()
            if topic:
                title = topic[:50]  # Truncate
            else:
                title, ok = QInputDialog.getText(
                    self, "Lưu nháp", "Nhập tiêu đề bài viết:"
                )
                if not ok or not title:
                    return
                    
        draft_data = {
            "title": title,
            "content": text,
            "language": self._get_current_lang()
        }
        
        if self.current_draft:
            draft_data["id"] = self.current_draft.get("id")
            
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Đang lưu...")
        
        async def save():
            # WritingService is synchronous
            return self.writing_service.save_draft(draft_data)
            
        def on_done(result):
            self.save_btn.setEnabled(True)
            self.save_btn.setText("💾 Lưu nháp")
            
            if result and result.get("id"):
                self.current_draft = result
                toast_success(f"Đã lưu bài \"{title}\"!")
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể lưu bài viết!")
                
        run_async(save, on_done)
        
    def _open_drafts_dialog(self):
        """Open dialog to manage drafts."""
        self.open_btn.setEnabled(False)
        self.open_btn.setText("Đang tải...")
        
        async def load():
            # WritingService is synchronous
            return self.writing_service.get_drafts()
            
        def on_done(drafts):
            self.open_btn.setEnabled(True)
            self.open_btn.setText("📂 Bài đã lưu")
            
            if not drafts:
                toast_info("Chưa có bài nào được lưu!")
                return
                
            dialog = DraftListDialog(
                self, 
                drafts=drafts,
                on_delete=self._delete_draft_callback
            )
            
            if dialog.exec() == QDialog.Accepted and dialog.selected_draft:
                self._load_draft(dialog.selected_draft)
                
        run_async(load, on_done)
        
    def _delete_draft_callback(self, draft_id: int, list_item):
        """Callback to delete draft from dialog."""
        async def delete():
            # WritingService is synchronous
            return self.writing_service.delete_draft(draft_id)
            
        def on_done(result):
            if result and result.get("ok"):
                # Remove from list
                row = list_item.listWidget().row(list_item)
                list_item.listWidget().takeItem(row)
                
                # Clear if it was current draft
                if self.current_draft and self.current_draft.get("id") == draft_id:
                    self.current_draft = None
                    
        run_async(delete, on_done)
        
    def _load_draft(self, draft: Dict):
        """Load a draft into the editor."""
        self.current_draft = draft
        self.text_editor.setPlainText(draft.get("content", ""))
        
        # Set language
        lang = draft.get("language", "en")
        self.lang_combo.setCurrentIndex(0 if lang == "en" else 1)
        
        # Set topic
        self.topic_input.setCurrentText(draft.get("title", ""))
        
        # Clear highlighting
        self._clear_highlighting()
        
        # Hide feedback panel
        self.feedback_panel.setVisible(False)
        
    # ========== AI Features ==========
    
    def _generate_topic(self):
        """Generate a writing topic using AI."""
        self.suggest_topic_btn.setEnabled(False)
        self.suggest_topic_btn.setText("⏳...")
        
        lang = self._get_current_lang()
        
        async def generate():
            # WritingService is synchronous (Gemini)
            return self.writing_service.generate_topic(lang)
            
        def on_done(result):
            self.suggest_topic_btn.setEnabled(True)
            self.suggest_topic_btn.setText("🎲 Gợi ý")
            
            if result.get("success"):
                topic = result.get("topic", "").strip()
                if topic:
                    # Add to combo and select
                    self.topic_input.insertItem(0, topic)
                    self.topic_input.setCurrentIndex(0)
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể tạo chủ đề. Vui lòng thử lại!")
                
        run_async(generate, on_done)
        
    def _review_writing(self):
        """Submit writing for AI review."""
        text = self.text_editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập nội dung bài viết!")
            return
            
        if len(text.split()) < 10:
            QMessageBox.warning(self, "Lỗi", "Bài viết quá ngắn! Vui lòng viết ít nhất 10 từ.")
            return
            
        self._set_loading(True)
        
        lang = self._get_current_lang()
        
        async def review():
            # WritingService is synchronous (Gemini)
            return self.writing_service.review_writing(text, lang)
            
        def on_done(result):
            self._set_loading(False)
            
            if result.get("success"):
                self._display_feedback(result)
            else:
                QMessageBox.warning(
                    self, "Lỗi", 
                    f"Không thể chấm bài: {result.get('error', 'Unknown error')}"
                )
                
        run_async(review, on_done)
        
    def _set_loading(self, loading: bool):
        """Show/hide loading state."""
        if loading:
            self.review_btn.setEnabled(False)
            self.review_btn.setText("⏳ Đang phân tích...")
            self.loading_label.setText("AI đang đọc bài của bạn...")
        else:
            self.review_btn.setEnabled(True)
            self.review_btn.setText("📝 Chấm bài ngay")
            self.loading_label.setText("")
            
    def _display_feedback(self, result: Dict):
        """Display AI feedback in the right panel."""
        # Show feedback panel
        self.feedback_panel.setVisible(True)
        
        # Update score
        score = result.get("score", 0)
        self.score_badge.set_score(score)
        
        # General comment
        comment = result.get("general_comment", "")
        self.comment_label.setText(f"💬 {comment}")
        
        # Corrected text with diff highlighting
        corrected = result.get("corrected_text", "")
        original = self.text_editor.toPlainText()
        
        # Simple diff display
        if corrected and corrected != original:
            html = f"""
            <h3>Bản gốc:</h3>
            <p style="color: #666; text-decoration: line-through;">{original}</p>
            <h3>Bản sửa:</h3>
            <p style="color: #2e7d32;">{corrected}</p>
            """
        else:
            html = f"<p style='color: green;'>✓ Bài viết không có lỗi lớn!</p>"
        self.corrected_browser.setHtml(html)
        
        # Error table
        feedback = result.get("detailed_feedback", [])
        self.error_table.setRowCount(len(feedback))
        
        for i, item in enumerate(feedback):
            self.error_table.setItem(i, 0, QTableWidgetItem(item.get("part", "")))
            self.error_table.setItem(i, 1, QTableWidgetItem(item.get("fix", "")))
            self.error_table.setItem(i, 2, QTableWidgetItem(item.get("reason", "")))
            
        # Grammar tips
        tips = result.get("grammar_tips", [])
        if tips:
            tips_html = "<ul>" + "".join([f"<li>{tip}</li>" for tip in tips]) + "</ul>"
        else:
            tips_html = "<p>Không có mẹo bổ sung.</p>"
        self.tips_browser.setHtml(tips_html)
        
        # Apply visual highlighting to errors
        self._highlight_errors(feedback)
        
    def _highlight_errors(self, feedback: List[Dict]):
        """Apply wavy red underline to errors in the editor."""
        # First clear existing highlighting
        self._clear_highlighting()
        
        if not feedback:
            return
            
        # Prepare error format
        error_format = QTextCharFormat()
        error_format.setUnderlineStyle(QTextCharFormat.WaveUnderline)
        error_format.setUnderlineColor(QColor("#F44336"))  # Red
        
        doc = self.text_editor.document()
        
        for item in feedback:
            error_text = item.get("part", "")
            fix_text = item.get("fix", "")
            reason = item.get("reason", "")
            
            if not error_text:
                continue
                
            # Find and highlight all occurrences
            cursor = QTextCursor(doc)
            while True:
                cursor = doc.find(error_text, cursor)
                if cursor.isNull():
                    break
                    
                # Apply format
                cursor.mergeCharFormat(error_format)
                
    def _clear_highlighting(self):
        """Clear all error highlighting from editor."""
        cursor = self.text_editor.textCursor()
        cursor.select(QTextCursor.Document)
        
        # Reset format
        normal_format = QTextCharFormat()
        normal_format.setUnderlineStyle(QTextCharFormat.NoUnderline)
        cursor.mergeCharFormat(normal_format)
        
        # Restore cursor position
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
