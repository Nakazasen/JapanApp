from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QPushButton, QListWidget, QStackedWidget, QListWidgetItem,
    QGridLayout, QComboBox, QLineEdit, QSplitter, QTextEdit,
    QScrollArea, QDialog, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QAction, QTextCursor
from frontend.services.reading_practice_service import get_reading_practice_service
from frontend.utils.async_helpers import run_async
from frontend.utils.language_utils import detect_language
from frontend.ui.mixins.text_context_menu_mixin import TextContextMenuMixin
from frontend.ui.tabs.youtube_tab_dialogs import SaveVocabDialog
from frontend.services import get_vocab_service, get_tts_service
from frontend.ui.widgets.dictionary_dialog import DictionaryLookupDialog
from frontend.services.analysis_service import get_analysis_service
import re
import json
import os
from frontend.ui.styles.theme import ThemeColors

class SentenceCard(QFrame):
    """Widget to display a single sentence analysis."""
    def __init__(self, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setObjectName("SentenceCard")
        # Inline style removed - handled by main.qss
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)
        
        # Original (Japanese)
        jp_text = data.get('original') or data.get('jp') or ''
        self.original = QLabel(jp_text)
        self.original.setObjectName("lb_original")
        self.original.setWordWrap(True)
        self.original.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.original)
        
        # Translation (Vietnamese)
        vi_text = data.get('translation') or data.get('vi') or ''
        self.trans = QLabel(vi_text)
        self.trans.setObjectName("lb_trans")
        self.trans.setWordWrap(True)
        self.trans.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # Force show
        self.trans.setVisible(bool(vi_text))
        layout.addWidget(self.trans)
        
        # Grammar Notes
        notes = data.get('grammar_notes') or data.get('notes') or ''
        if notes:
            self.grammar = QLabel(f"💡 {notes}")
            self.grammar.setObjectName("lb_grammar")
            self.grammar.setWordWrap(True)
            self.grammar.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(self.grammar)

class ReadingPracticeTab(QWidget, TextContextMenuMixin):
    """JLPT Reading Practice Tab."""
    
    def __init__(self):
        super().__init__()
        self.practice_service = get_reading_practice_service()
        self.vocab_service = get_vocab_service()
        self.analysis_service = get_analysis_service()
        self.tts_service = get_tts_service()
        self.current_category_id: Optional[int] = None
        self.dictionary_dialog: Optional[DictionaryLookupDialog] = None
        self._init_ui()
        self._load_categories()

    def _init_ui(self):
        """Initialize UI - Mastery Suite Edition."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Inline styles removed - now in main.qss
        self.setObjectName("ReadingPracticeTab")

        # ========== SIDEBAR: Levels & Stats ==========
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        sidebar_layout.addWidget(QLabel("📚 SKILL LEVELS", objectName="SidebarLabel"))
        
        # Stats Card
        stat_card = QFrame()
        stat_card.setObjectName("StatCard")
        stat_lay = QGridLayout(stat_card)
        
        stat_lay.addWidget(QLabel("Tổng bài:", objectName="WhiteLabels"), 0, 0)
        self.total_lbl = QLabel("0")
        self.total_lbl.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-weight: bold; font-size: 16px;")
        stat_lay.addWidget(self.total_lbl, 0, 1)
        
        stat_lay.addWidget(QLabel("Hoàn thành:", objectName="WhiteLabels"), 1, 0)
        self.completed_lbl = QLabel("0")
        self.completed_lbl.setStyleSheet(f"color: {ThemeColors.SUCCESS}; font-weight: bold; font-size: 16px;")
        stat_lay.addWidget(self.completed_lbl, 1, 1)
        sidebar_layout.addWidget(stat_card)
        
        # Category List (JLPT Levels)
        self.category_list = QListWidget()
        self.category_list.itemClicked.connect(self._on_category_selected)
        sidebar_layout.addWidget(self.category_list)
        
        sidebar_layout.addStretch()
        
        self.study_btn = QPushButton("🔥 LUYỆN TẬP NGAY")
        self.study_btn.setObjectName("PrimaryBtn")
        sidebar_layout.addWidget(self.study_btn)
        
        main_layout.addWidget(sidebar)

        # ========== MAIN AREA: Stacked (List / Study) ==========
        self.content_stack = QStackedWidget()
        
        # 1. Discover View
        self.discover_view = self._create_discover_view()
        self.content_stack.addWidget(self.discover_view)
        
        # 2. Mastery View (Study)
        self.mastery_view = self._create_mastery_view()
        self.content_stack.addWidget(self.mastery_view)
        
        main_layout.addWidget(self.content_stack)

    def _create_discover_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("🔍 Tìm bài đọc theo tiêu đề...")
        toolbar.addWidget(self.search_input, 1)
        
        self.add_btn = QPushButton("➕ Thêm bài mới")
        # Keep inline style for simple buttons if needed, or move to QSS
        self.add_btn.setStyleSheet(f"background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; padding: 8px 15px; border-radius: 6px;")
        toolbar.addWidget(self.add_btn)
        layout.addLayout(toolbar)
        
        # Content List (Grid-like list items)
        self.item_list = QListWidget()
        self.item_list.setObjectName("ItemList")
        self.item_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.item_list)
        
        return widget

    def _create_mastery_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background: {ThemeColors.BG_PRIMARY}; border-bottom: 1px solid {ThemeColors.BORDER};")
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(20, 0, 20, 0)
        
        back_btn = QPushButton("⬅️ Quay lại danh sách")
        back_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))
        back_btn.setStyleSheet(f"background: transparent; color: {ThemeColors.PRIMARY}; font-weight: bold;")
        header_lay.addWidget(back_btn)
        
        header_lay.addStretch()
        
        self.passage_title = QLabel("Tiêu đề bài đọc")
        self.passage_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        header_lay.addWidget(self.passage_title)
        
        header_lay.addStretch()
        
        # Toolbar Actions
        self.smart_mode_btn = QPushButton("✨ Song ngữ")
        self.smart_mode_btn.setCheckable(True)
        self.smart_mode_btn.setToolTip("Xem song ngữ từng câu (Cần Phân tích AI trước)")
        self.smart_mode_btn.clicked.connect(self._toggle_smart_mode)
        self.smart_mode_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.BG_TERTIARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 15px; padding: 5px 15px; color: {ThemeColors.TEXT_PRIMARY}; }}
            QPushButton:checked {{ background: {ThemeColors.BG_SECONDARY}; border: 1px solid {ThemeColors.PRIMARY}; color: {ThemeColors.PRIMARY}; font-weight: bold; }}
            QPushButton:disabled {{ color: {ThemeColors.TEXT_SECONDARY}; background: {ThemeColors.BG_GRID}; }}
        """)
        header_lay.addWidget(self.smart_mode_btn)
        
        # Audio Play Button
        self.audio_btn = QPushButton("🎧 Nghe bài")
        self.audio_btn.clicked.connect(self._toggle_audio)
        self.audio_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.BG_TERTIARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 15px; padding: 5px 15px; color: {ThemeColors.TEXT_PRIMARY}; }}
            QPushButton:hover {{ background: {ThemeColors.BG_SECONDARY}; }}
        """)
        header_lay.addWidget(self.audio_btn)
        
        # Pause Button (initially hidden, shown when audio is playing)
        self.pause_audio_btn = QPushButton("⏸️ Tạm dừng")
        self.pause_audio_btn.clicked.connect(self._pause_audio)
        self.pause_audio_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.WARNING}40; border: 1px solid {ThemeColors.WARNING}; color: {ThemeColors.WARNING}; font-weight: bold; border-radius: 15px; padding: 5px 15px; }}
            QPushButton:hover {{ background: {ThemeColors.WARNING}60; }}
        """)
        self.pause_audio_btn.hide()
        header_lay.addWidget(self.pause_audio_btn)
        
        # Resume Button (initially hidden, shown when audio is paused)
        self.resume_audio_btn = QPushButton("▶️ Tiếp tục")
        self.resume_audio_btn.clicked.connect(self._resume_audio)
        self.resume_audio_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.SUCCESS}40; border: 1px solid {ThemeColors.SUCCESS}; color: {ThemeColors.SUCCESS}; font-weight: bold; border-radius: 15px; padding: 5px 15px; }}
            QPushButton:hover {{ background: {ThemeColors.SUCCESS}60; color: {ThemeColors.TEXT_INVERSE}; }}
        """)
        self.resume_audio_btn.hide()
        header_lay.addWidget(self.resume_audio_btn)
        
        # Stop Button (reset to beginning)
        self.stop_audio_btn = QPushButton("⏹️ Dừng hẳn")
        self.stop_audio_btn.clicked.connect(self._stop_audio)
        self.stop_audio_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.DANGER}40; border: 1px solid {ThemeColors.DANGER}; color: {ThemeColors.DANGER}; font-weight: bold; border-radius: 15px; padding: 5px 15px; }}
            QPushButton:hover {{ background: {ThemeColors.DANGER}60; color: {ThemeColors.TEXT_INVERSE}; }}
        """)
        self.stop_audio_btn.hide()
        header_lay.addWidget(self.stop_audio_btn)
        
        self.vocab_btn = QPushButton("📖 Từ vựng")
        self.vocab_btn.clicked.connect(self._show_vocab_dialog)
        self.vocab_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.BG_TERTIARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 15px; padding: 5px 15px; color: {ThemeColors.TEXT_PRIMARY}; }}
        """)
        header_lay.addWidget(self.vocab_btn)
        
        self.analyze_btn = QPushButton("⚙️ Phân tích AI")
        self.analyze_btn.clicked.connect(self._analyze_content)
        self.analyze_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.PRIMARY}; color: {ThemeColors.TEXT_INVERSE}; border-radius: 15px; padding: 5px 15px; font-weight: bold; }}
            QPushButton:hover {{ background: {ThemeColors.PRIMARY_HOVER}; }}
        """)
        header_lay.addWidget(self.analyze_btn)
        
        header_lay.addStretch()
        layout.addWidget(header)
        
        # Study Splitter
        study_splitter = QSplitter(Qt.Horizontal)
        study_splitter.setHandleWidth(1)
        study_splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {ThemeColors.BORDER}; }}")
        
        # Left: Passage
        passage_panel = QFrame()
        passage_panel.setStyleSheet(f"background: {ThemeColors.BG_PRIMARY};")
        pass_lay = QVBoxLayout(passage_panel)
        pass_lay.setContentsMargins(40, 40, 40, 40)
        
        # Text View (Standard)
        self.passage_content = QTextEdit()
        self.passage_content.setReadOnly(True)
        self.passage_content.setStyleSheet(f"font-size: 18px; line-height: 1.8; color: {ThemeColors.TEXT_PRIMARY}; border: none;")
        self.passage_content.setContextMenuPolicy(Qt.CustomContextMenu)
        self.passage_content.customContextMenuRequested.connect(self._show_context_menu)
        self.passage_content.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard | Qt.LinksAccessibleByMouse
        )
        
        # Smart View (Sentences)
        self.smart_view_scroll = QScrollArea()
        self.smart_view_scroll.setWidgetResizable(True)
        self.smart_view_scroll.setStyleSheet("background: transparent; border: none;")
        self.smart_view_content = QWidget()
        self.smart_view_layout = QVBoxLayout(self.smart_view_content)
        self.smart_view_layout.setSpacing(15)
        self.smart_view_layout.addStretch()
        self.smart_view_scroll.setWidget(self.smart_view_content)
        
        # Stack to switch between Text and Smart View
        self.passage_stack = QStackedWidget()
        self.passage_stack.addWidget(self.passage_content)       # Index 0
        self.passage_stack.addWidget(self.smart_view_scroll)     # Index 1
        
        pass_lay.addWidget(self.passage_stack)
        study_splitter.addWidget(passage_panel)
        
        # Right: Questions
        question_panel = QWidget()
        question_panel.setStyleSheet(f"background: {ThemeColors.BG_SECONDARY};")
        ques_lay = QVBoxLayout(question_panel)
        ques_lay.setContentsMargins(25, 30, 25, 30)
        
        ques_lay.addWidget(QLabel("📝 CÂU HỎI ĐÁNH GIÁ", styleSheet=f"font-weight: bold; color: {ThemeColors.TEXT_SECONDARY}; letter-spacing: 1px;"))
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.scroll_content = QWidget()
        self.question_container = QVBoxLayout(self.scroll_content)
        self.question_container.setSpacing(20)
        self.question_container.addStretch()
        
        self.scroll.setWidget(self.scroll_content)
        ques_lay.addWidget(self.scroll)
        
        study_splitter.addWidget(question_panel)
        
        study_splitter.setStretchFactor(0, 3)
        study_splitter.setStretchFactor(1, 2)
        
        layout.addWidget(study_splitter)
        
        return widget

    def _load_categories(self):
        async def fetch():
            return self.practice_service.list_categories()
        
        def populate(cats):
            self.category_list.clear()
            first_valid_cat_id = None
            
            for c in cats:
                count_str = f" ({c['count']})" if c['count'] > 0 else ""
                item = QListWidgetItem(f"{c['icon'] or '📖'} {c['name']}{count_str}")
                item.setData(Qt.UserRole, c['id'])
                # Highlight if it has items
                if c['count'] > 0:
                    # Removed hardcoded Qt.white which caused invisible text on light theme
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    if not first_valid_cat_id:
                        first_valid_cat_id = c['id']
                else:
                    # Indicate empty categories visually (e.g. italics) instead of hardcoded gray
                    font = item.font()
                    font.setItalic(True)
                    item.setFont(font)
                    
                self.category_list.addItem(item)
            
            # Load stats
            stats = self.practice_service.get_stats()
            self.total_lbl.setText(str(stats["total"]))
            self.completed_lbl.setText(str(stats["completed"]))
            
            # Auto-select if needed
            if not self.current_category_id and first_valid_cat_id:
                # Find item with this ID and select it
                for i in range(self.category_list.count()):
                    it = self.category_list.item(i)
                    if it.data(Qt.UserRole) == first_valid_cat_id:
                        self.category_list.setCurrentItem(it)
                        self._on_category_selected(it)
                        break
            
        run_async(fetch, populate)

    def _on_category_selected(self, item):
        self.current_category_id = item.data(Qt.UserRole)
        self._load_items()

    def _load_items(self):
        if not self.current_category_id: return
        
        async def fetch():
            return self.practice_service.list_items(self.current_category_id)
        
        def populate(items):
            self.item_list.clear()
            for i in items:
                li = QListWidgetItem(f"📄 {i['title']} ({i['question_count']} câu hỏi)")
                li.setData(Qt.UserRole, i['id'])
                self.item_list.addItem(li)
                
        run_async(fetch, populate)

    def _on_item_double_clicked(self, item):
        item_id = item.data(Qt.UserRole)
        self._open_study_item(item_id)

    def _open_study_item(self, item_id):
        detail = self.practice_service.get_item_detail(item_id)
        if not detail: return
        
        self.passage_title.setText(detail["title"])
        self.passage_content.setPlainText(detail["content"] or "")
        
        # Clear questions
        while self.question_container.count():
            child = self.question_container.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        # Add questions
        for idx, q in enumerate(detail["questions"]):
            q_lbl = QLabel(f"Câu {idx+1}: {q['question_text']}")
            q_lbl.setStyleSheet("font-weight: bold; margin-top: 10px;")
            self.question_container.addWidget(q_lbl)
            
            # Feedback label (hidden initially)
            feedback = QLabel()
            feedback.setWordWrap(True)
            feedback.hide()
            
            btn_group = []
            for opt, text in q["options"].items():
                btn = QPushButton(f"{opt}. {text}")
                btn.setStyleSheet(f"text-align: left; padding: 10px; background: {ThemeColors.BG_PRIMARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 6px; color: {ThemeColors.TEXT_PRIMARY};")
                btn.setCursor(Qt.PointingHandCursor)
                
                # Connect click event
                # Use default defaults to capture loop variables safely
                btn.clicked.connect(lambda checked=False, b=btn, o=opt, c=q['correct_option'], e=q['explanation']: self._check_answer(b, o, c, e))
                
                self.question_container.addWidget(btn)
                btn_group.append(btn)
            
            # Link feedback label to buttons so handler can find it
            for b in btn_group:
                b.setProperty("feedback_label", feedback)
                
            self.question_container.addWidget(feedback)
                
        self.content_stack.setCurrentIndex(1)
        self.current_detail = detail # Store for access
        
        # Check analysis status
        has_analysis = bool(detail.get("analysis"))
        
        # Always enable buttons, handle missing data in clicks
        self.smart_mode_btn.setEnabled(True)
        self.vocab_btn.setEnabled(True)
        
        # Show analyze button if not done, or maybe always allow re-analyze?
        # Let's keep hiding it to reduce clutter, but allow access via other buttons
        self.analyze_btn.setVisible(True) # Just always show it as requested
        
        # Stop any playing audio and hide controls
        self.tts_service.stop_audio()
        self.audio_btn.setText("🎧 Nghe bài")
        self._hide_all_audio_controls()
        
        if has_analysis:
            self._render_smart_view(detail["analysis"])
        else:
            self.smart_mode_btn.setChecked(False)
            self.passage_stack.setCurrentIndex(0)

    def _toggle_audio(self):
        """Start audio playback."""
        if not hasattr(self, 'current_detail') or not self.current_detail:
            return

        # Stop existing audio first
        self.tts_service.stop_audio()
        self._hide_all_audio_controls()

        # Check if audio exists
        audio_path = self.current_detail.get("audio_path")
        
        if audio_path and os.path.exists(audio_path):
            self.tts_service.play_audio(audio_path)
            self._show_playing_controls()
        else:
            # Generate audio
            text = self.current_detail.get("content")
            if not text: return
            
            toast_info("Đang tạo file âm thanh, vui lòng đợi (lần đầu sẽ lâu)...")
            
            async def generate():
                # Extract clean text from analysis if possible, usually just content is fine
                # Assuming japanese
                voice = "ja-JP-NanamiNeural" 
                
                # Create directory if needed
                import os
                save_dir = os.path.join(os.getcwd(), "data", "audio_cache")
                os.makedirs(save_dir, exist_ok=True)
                
                filename = f"reading_{self.current_detail['id']}.mp3"
                path = os.path.join(save_dir, filename)
                
                return await self.tts_service.synthesize_async(text, voice, path)

            def on_generated(result):
                if result:
                    # Update DB
                    self.practice_service.update_item_audio(self.current_detail["id"], result)
                    self.current_detail["audio_path"] = result
                    
                    # Play
                    self.tts_service.play_audio(result)
                    self._show_playing_controls()
                else:
                    QMessageBox.warning(self, "Lỗi", "Không thể tạo âm thanh.")

            run_async(generate, on_generated)
    
    def _show_playing_controls(self):
        """Show controls when audio is playing."""
        self.pause_audio_btn.show()
        self.stop_audio_btn.show()
        self.resume_audio_btn.hide()
    
    def _show_paused_controls(self):
        """Show controls when audio is paused."""
        self.pause_audio_btn.hide()
        self.resume_audio_btn.show()
        self.stop_audio_btn.show()
    
    def _hide_all_audio_controls(self):
        """Hide all audio control buttons."""
        self.pause_audio_btn.hide()
        self.resume_audio_btn.hide()
        self.stop_audio_btn.hide()
    
    def _pause_audio(self):
        """Pause currently playing audio."""
        self.tts_service.pause_audio()
        self._show_paused_controls()
    
    def _resume_audio(self):
        """Resume paused audio."""
        self.tts_service.resume_audio()
        self._show_playing_controls()
            
    def _stop_audio(self):
        """Stop audio completely."""
        self.tts_service.stop_audio()
        self._hide_all_audio_controls()

    def _analyze_content(self):
        """Call AI to analyze the reading passage."""
        if not hasattr(self, 'current_detail') or not self.current_detail:
            return

        from PySide6.QtWidgets import QProgressDialog
        
        text = self.current_detail["content"]
        if not text: return

        # Show progress
        progress = QProgressDialog("Đang trích xuất từ vựng và phân tích ngữ pháp... (Có thể mất 15-30s)", "Hủy", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        async def run_ai():
            return await self.analysis_service.analyze_reading_passage(text)

        def on_finished(result):
            progress.close()
            if result.get("success"):
                data = result.get("data", {})
                
                # Save to DB
                self.practice_service.update_item_analysis(
                    self.current_detail["id"],
                    vocabulary=data.get("vocabulary", []),
                    translation=data.get("translation", ""),
                    analysis=data.get("sentences", [])
                )
                
                toast_success("Đã phân tích xong! Hãy thử chế độ Song ngữ.")
                
                # Reload item
                self._open_study_item(self.current_detail["id"])
            else:
                QMessageBox.critical(self, "Lỗi", f"Không thể phân tích: {result.get('error')}")

        run_async(run_ai, on_finished)

    def _render_smart_view(self, sentences: List[Dict]):
        """Render sentence cards."""
        # Clear old items
        while self.smart_view_layout.count():
            item = self.smart_view_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        if not sentences: return
        
        for sent_data in sentences:
            if not sent_data: continue
            card = SentenceCard(sent_data)
            self.smart_view_layout.addWidget(card)
            
        self.smart_view_layout.addStretch()

    def _toggle_smart_mode(self):
        # Check if we have analysis
        if not self.current_detail or not self.current_detail.get("analysis"):
            # Restore button state if it was checked
            if self.smart_mode_btn.isChecked():
                self.smart_mode_btn.setChecked(False)
                
            reply = QMessageBox.question(
                self, "Chưa phân tích",
                "Bài đọc này chưa được phân tích AI (dịch & tách câu).\nBạn có muốn chạy phân tích ngay không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._analyze_content()
            return

        if self.smart_mode_btn.isChecked():
            self.passage_stack.setCurrentIndex(1)
        else:
            self.passage_stack.setCurrentIndex(0)
            
    def _show_vocab_dialog(self):
        if not hasattr(self, 'current_detail'): return
        
        vocab_list = self.current_detail.get("vocabulary")
        if not vocab_list:
            reply = QMessageBox.question(
                self, "Chưa có từ vựng",
                "Bài đọc này chưa có dữ liệu từ vựng AI.\nBạn có muốn chạy phân tích ngay không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._analyze_content()
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📖 Từ vựng Bài học")
        dialog.resize(550, 650)
        layout = QVBoxLayout(dialog)
        
        # Instructions
        info_label = QLabel("💡 Chọn nhiều từ (Ctrl+Click hoặc Shift+Click) rồi nhấn 'Lưu các từ đã chọn'")
        info_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)
        
        # Topic selection for batch save
        topic_layout = QHBoxLayout()
        topic_layout.addWidget(QLabel("📂 Lưu vào Deck:"))
        self.vocab_dialog_topic_combo = QComboBox()
        self.vocab_dialog_topic_combo.addItem("📂 Không phân loại (Mặc định)", None)
        
        # Load topics
        topics = self.vocab_service.list_topics("jp")  # Assuming Japanese reading
        for t in topics:
            self.vocab_dialog_topic_combo.addItem(f"📘 {t['name']}", t['id'])
        
        topic_layout.addWidget(self.vocab_dialog_topic_combo, 1)
        
        # Create new topic inline
        self.new_topic_input = QLineEdit()
        self.new_topic_input.setPlaceholderText("Hoặc tạo deck mới...")
        self.new_topic_input.setMaximumWidth(180)
        topic_layout.addWidget(self.new_topic_input)
        layout.addLayout(topic_layout)
        
        # List with multi-selection
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.ExtendedSelection)  # Enable multi-select
        list_widget.setStyleSheet(f"""
            QListWidget::item:selected {{ 
                background: {ThemeColors.BG_TERTIARY}; 
                border-left: 4px solid {ThemeColors.PRIMARY};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """)
        
        for v in vocab_list:
            # v: {word, reading, meaning, type}
            w = v.get("word", "")
            r = v.get("reading", "")
            m = v.get("meaning", "")
            t = v.get("type", "")
            
            item = QListWidgetItem(f"{w} ({r}) - {t}\n👉 {m}")
            item.setData(Qt.UserRole, v)  # Store full vocab data
            list_widget.addItem(item)
            
        layout.addWidget(list_widget)
        
        # Button layout
        btn_layout = QHBoxLayout()
        
        # Counter label
        self.selected_count_label = QLabel("Đã chọn: 0 từ")
        self.selected_count_label.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-weight: bold;")
        btn_layout.addWidget(self.selected_count_label)
        
        # Update counter on selection change
        list_widget.itemSelectionChanged.connect(
            lambda: self.selected_count_label.setText(f"Đã chọn: {len(list_widget.selectedItems())} từ")
        )
        
        btn_layout.addStretch()
        
        # Save selected button
        save_btn = QPushButton("💾 Lưu các từ đã chọn vào Flashcard")
        save_btn.setStyleSheet(f"background-color: {ThemeColors.SUCCESS}; color: {ThemeColors.TEXT_INVERSE}; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        save_btn.clicked.connect(lambda: self._save_multiple_vocab(list_widget.selectedItems(), dialog))
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _save_multiple_vocab(self, selected_items, dialog):
        """Save multiple selected vocabulary items to flashcard."""
        if not selected_items:
            QMessageBox.warning(self, "Chưa chọn từ", "Vui lòng chọn ít nhất 1 từ để lưu!")
            return
        
        # Get or create topic
        topic_id = self.vocab_dialog_topic_combo.currentData()
        new_topic_name = self.new_topic_input.text().strip()
        
        if new_topic_name:
            # Create new topic
            result = self.vocab_service.create_topic(new_topic_name, "jp", f"Từ vựng từ bài đọc")
            if result.get("success"):
                topic_id = result.get("id")
            else:
                QMessageBox.warning(self, "Lỗi", f"Không thể tạo chủ đề: {result.get('error')}")
                return
        
        # Save each word
        saved_count = 0
        skipped_count = 0
        
        for item in selected_items:
            vocab_data = item.data(Qt.UserRole)
            if not vocab_data:
                continue
            
            word = vocab_data.get("word", "")
            meaning = vocab_data.get("meaning", "")
            reading = vocab_data.get("reading", "")
            
            # Find example sentence from passage
            full_text = self.passage_content.toPlainText()
            sentences = re.split(r'([。！？.!?\n])', full_text)
            example_sentence = ""
            
            # Reconstruct sentences with their punctuation
            reconstructed = []
            for i in range(0, len(sentences)-1, 2):
                reconstructed.append(sentences[i] + sentences[i+1])
            if len(sentences) % 2 != 0:
                reconstructed.append(sentences[-1])
            
            for s in reconstructed:
                if word in s:
                    example_sentence = s.strip()
                    break
            
            # Prepare save data
            save_data = {
                "lang": "jp",
                "word_kanji": word,
                "word_kana": reading,
                "meaning_vi": meaning,
                "example_jp": example_sentence,
                "topic_id": topic_id,
                "source_material": f"Luyện đọc: {self.current_detail.get('title', '')}"
            }
            
            # Save via service
            async def do_save(data):
                return self.vocab_service.save_jp_vocab(data)
            
            result = self.vocab_service.save_jp_vocab(save_data)
            if result.get("success"):
                saved_count += 1
            else:
                skipped_count += 1
        
        # Show result
        dialog.close()
        
        topic_name = self.vocab_dialog_topic_combo.currentText() if not new_topic_name else new_topic_name
        toast_success(
            f"✅ Đã lưu {saved_count} từ vào '{topic_name}'. ⏭️ Bỏ qua {skipped_count} từ (đã tồn tại)"
        )

    def _save_selected_vocab(self, item):
        if not item: return
        word = item.data(Qt.UserRole)
        self._show_context_menu(QPoint(0,0)) # Hacky re-use or just call save logic directly
        # Better call direct logic
        self._save_word_to_vocab(word)

    def _check_answer(self, btn, selected_opt, correct_opt, explanation):
        """Handle answer selection."""
        feedback_lbl = btn.property("feedback_label")
        
        if selected_opt == str(correct_opt):
            # Correct styles
            btn.setStyleSheet("text-align: left; padding: 10px; background: #d4edda; border: 2px solid #28a745; border-radius: 6px; color: #155724; font-weight: bold;")
            
            feedback_text = f"✅ Chính xác!\n\n💡 Giải thích: {explanation}" if explanation else "✅ Chính xác!"
            feedback_lbl.setText(feedback_text)
            feedback_lbl.setStyleSheet("color: #155724; margin-top: 10px; padding: 10px; background: #e8f5e9; border-radius: 6px;")
            feedback_lbl.show()
        else:
            # Wrong styles
            btn.setStyleSheet("text-align: left; padding: 10px; background: #f8d7da; border: 2px solid #dc3545; border-radius: 6px; color: #721c24;")
            
            feedback_lbl.setText("❌ Sai rồi, hãy thử lại!")
            feedback_lbl.setStyleSheet("color: #dc3545; margin-top: 10px; font-weight: bold;")
            feedback_lbl.show()

    def _show_context_menu(self, position: QPoint):
        """Show context menu for passage content."""
        selected_text = self._get_selected_text_from_widget(self.passage_content)
        if not selected_text:
            return
            
        # Create base context menu from mixin
        menu = self.create_text_context_menu(selected_text)
        
        menu.addSeparator()
        
        # Add 'Save to Flashcard'
        save_vocab_action = QAction("💾 Lưu vào Flashcard", self)
        save_vocab_action.triggered.connect(
            lambda: self._save_word_to_vocab(selected_text)
        )
        menu.addAction(save_vocab_action)
        
        menu.exec(self.passage_content.mapToGlobal(position))

    def _save_word_to_vocab(self, word: str):
        """Save word to vocabulary with context from current passage."""
        # Find context sentence
        full_text = self.passage_content.toPlainText()
        
        # Find a sentence containing the word
        # Simple regex split by Japanese/English punctuation
        sentences = re.split(r'([。！？.!?\n])', full_text)
        context_sentence = ""
        
        # Reconstruct sentences with their punctuation
        reconstructed = []
        for i in range(0, len(sentences)-1, 2):
            reconstructed.append(sentences[i] + sentences[i+1])
        if len(sentences) % 2 != 0:
            reconstructed.append(sentences[-1])
            
        for s in reconstructed:
            if word in s:
                context_sentence = s.strip()
                break
        
        if not context_sentence:
            context_sentence = word
            
        # Prepare data (translate word and context)
        async def prepare():
            try:
                from frontend.services.translator import TranslatorService
                lang = detect_language(word)
                meaning = TranslatorService.translate(word, "auto", "vi")
                ctx_trans = TranslatorService.translate(context_sentence, "auto", "vi")
                return {"meaning": meaning, "ctx_trans": ctx_trans, "lang": lang}
            except Exception as e:
                return {"error": str(e)}
                
        def on_prepared(result):
            if "error" in result:
                QMessageBox.warning(self, "Lỗi", f"Không thể chuẩn bị dữ liệu: {result['error']}")
                return
            
            # Load topics for dialog
            topics = self.vocab_service.list_topics("jp")
                
            dialog = SaveVocabDialog(
                self, word, context_sentence, 
                result.get("meaning", ""), result.get("ctx_trans", ""),
                topics=topics
            )
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                lang = result.get("lang", "en")
                is_jp = lang in ['ja', 'jp', 'japanese']
                
                # Handle topic creation if needed
                topic_id = data.get("topic_id")
                new_topic_name = data.get("new_topic_name", "").strip()
                
                if new_topic_name:
                    topic_result = self.vocab_service.create_topic(new_topic_name, "jp", "Từ vựng từ bài đọc")
                    if topic_result.get("success"):
                        topic_id = topic_result.get("id")
                
                if is_jp:
                    save_data = {
                        "lang": "jp",
                        "word_kanji": data["word"],
                        "word_kana": "",
                        "meaning_vi": data["meaning"],
                        "example_jp": data["context"],
                        "example_vi": data["translation"],
                        "topic_id": topic_id,
                        "source_material": f"Luyện đọc: {self.current_detail.get('title', '')}"
                    }
                else:
                    save_data = {
                        "lang": "en",
                        "word": data["word"],
                        "meaning_vi": data["meaning"],
                        "example_en": data["context"],
                        "example_vi": data["translation"],
                        "topic_id": topic_id,
                        "source_material": f"Luyện đọc: {self.current_detail.get('title', '')}"
                    }
                self._submit_vocab_save(save_data, topic_id)
                
        run_async(prepare, on_prepared)

    def _submit_vocab_save(self, data, topic_id=None):
        topic_name = ""
        if topic_id:
            topics = self.vocab_service.list_topics(data.get("lang", "jp"))
            for t in topics:
                if t.get("id") == topic_id:
                    topic_name = t.get("name", "")
                    break
        
        async def save():
            if data.get("lang") == "jp":
                return self.vocab_service.save_jp_vocab(data)
            return self.vocab_service.save(data)
            
        def on_saved(result):
            if result.get("success"):
                msg = "✅ Đã lưu từ vựng vào Flashcard!"
                if topic_name:
                    msg += f"\n\n📂 Deck: {topic_name}\n💡 Mẹo: Vào tab 'Từ vựng', lọc theo Deck này để xem!"
                toast_success(msg)
            else:
                toast_error(f"Không thể lưu: {result.get('error')}")
            
        run_async(save, on_saved)

    def _mixin_lookup_word(self, word: str, dictionary_id: str = None, source_lang: str = "auto"):
        """Override mixin lookup to ensure dialog works."""
        if not word: return
        
        if not self.dictionary_dialog:
            self.dictionary_dialog = DictionaryLookupDialog(self)
            self.dictionary_dialog.finished.connect(lambda _: setattr(self, "dictionary_dialog", None))
        
        self.dictionary_dialog.set_lookup(word, source_lang, dictionary_id)
        self.dictionary_dialog.show()
        self.dictionary_dialog.raise_()
        self.dictionary_dialog.activateWindow()
