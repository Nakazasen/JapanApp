import sys
import os
import subprocess
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QPushButton, QListWidget, QStackedWidget, QListWidgetItem,
    QGridLayout, QComboBox, QLineEdit, QSplitter, QTextEdit,
    QScrollArea, QStyle, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from frontend.services.listening_practice_service import get_listening_practice_service
from frontend.services.analysis_service import get_analysis_service
from frontend.services.vocab_service import get_vocab_service
from frontend.utils.async_helpers import run_async
from PySide6.QtWidgets import QDialog, QScrollArea
from frontend.core.config import settings
from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning
from frontend.ui.styles.theme import ThemeColors

class QuestionBlock(QFrame):
    """Widget for a single question with its own audio and transcript."""
    def __init__(self, data: Dict[str, Any], index: int, media_player: QMediaPlayer, parent=None):
        super().__init__(parent)
        self.data = data
        self.index = index
        self.media_player = media_player
        self.setObjectName("QuestionBlock")
        self.setStyleSheet(f"""
            QFrame#QuestionBlock {{ background: {ThemeColors.BG_SECONDARY}; border-radius: 12px; margin-bottom: 20px; border: 1px solid {ThemeColors.BORDER}; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 1. Title
        title_lbl = QLabel(f"Câu {index+1}: {data['question_text']}")
        title_lbl.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {ThemeColors.TEXT_PRIMARY};")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)
        
        # 2. Options
        self.btn_group = []
        for opt, text in data["options"].items():
            btn = QPushButton(f"{opt}. {text}")
            btn.setStyleSheet(f"text-align: left; padding: 12px; background: {ThemeColors.BG_PRIMARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 8px; font-size: 14px; color: {ThemeColors.TEXT_PRIMARY};")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, b=btn, o=opt, c=data['correct_option'], e=data.get('explanation', ''): self._check_answer(b, o, c, e))
            layout.addWidget(btn)
            self.btn_group.append(btn)
            
        self.feedback_lbl = QLabel()
        self.feedback_lbl.setWordWrap(True)
        self.feedback_lbl.hide()
        layout.addWidget(self.feedback_lbl)
        
        # 3. Audio & Transcript Controls
        ctrl_layout = QVBoxLayout()
        ctrl_layout.setSpacing(10)
        
        if data.get('audio_path'):
            self.play_btn = QPushButton(" ▶ TIẾP TỤC")
            self.play_btn.setFixedHeight(45)
            self.play_btn.setCursor(Qt.PointingHandCursor)
            self.play_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {ThemeColors.PRIMARY}; color: {ThemeColors.TEXT_INVERSE}; font-weight: bold; border-radius: 22px; font-size: 14px; }}
                QPushButton:hover {{ background-color: {ThemeColors.PRIMARY_HOVER}; }}
            """)
            self.play_btn.clicked.connect(self._toggle_audio)
            ctrl_layout.addWidget(self.play_btn)
            
            self.transcript_btn = QPushButton("📝 Hiện Transcript")
            self.transcript_btn.setCheckable(True)
            self.transcript_btn.setStyleSheet(f"background: transparent; color: {ThemeColors.TEXT_SECONDARY}; font-size: 13px; font-weight: bold; border: none;")
            self.transcript_btn.clicked.connect(self._toggle_transcript)
            ctrl_layout.addWidget(self.transcript_btn, 0, Qt.AlignCenter)
            
            self.transcript_area = QTextEdit()
            self.transcript_area.setReadOnly(True)
            self.transcript_area.setPlainText(data.get('transcript') or "Đang chờ cập nhật transcript...")
            self.transcript_area.setStyleSheet(f"background: {ThemeColors.BG_PRIMARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 8px; padding: 10px; font-style: italic; color: {ThemeColors.TEXT_SECONDARY};")
            self.transcript_area.setMaximumHeight(150)
            self.transcript_area.hide()
            ctrl_layout.addWidget(self.transcript_area)
            
        layout.addLayout(ctrl_layout)

    def _toggle_audio(self):
        # We need to tell the parent (the tab) to handle the audio source change
        # For simplicity, we'll emit a signal or just call a method on parent if it exists
        # But we can also do it here if we have the media_player
        
        path = self.data.get('audio_path')
        if not path: return
        
        current_source = self.media_player.source().toLocalFile()
        target_path = os.path.join(settings.project_root, path.lstrip('/'))
        
        if current_source != target_path:
            self.media_player.setSource(QUrl.fromLocalFile(target_path))
            self.media_player.play()
            self.play_btn.setText(" ‖ TẠM DỪNG")
        else:
            if self.media_player.playbackState() == QMediaPlayer.PlayingState:
                self.media_player.pause()
                self.play_btn.setText(" ▶ TIẾP TỤC")
            else:
                self.media_player.play()
                self.play_btn.setText(" ‖ TẠM DỪNG")
                
    def _toggle_transcript(self):
        visible = self.transcript_btn.isChecked()
        self.transcript_area.setVisible(visible)
        self.transcript_btn.setText("📝 Ẩn Transcript" if visible else "📝 Hiện Transcript")

    def _check_answer(self, btn, selected_opt, correct_opt, explanation):
        if selected_opt == correct_opt:
            btn.setStyleSheet(f"text-align: left; padding: 12px; background: {ThemeColors.SUCCESS}40; border: 2px solid {ThemeColors.SUCCESS}; border-radius: 8px; color: {ThemeColors.SUCCESS}; font-weight: bold;")
            self.feedback_lbl.setText(f"✅ Chính xác! \n{explanation}")
            self.feedback_lbl.setStyleSheet(f"color: {ThemeColors.SUCCESS}; font-size: 14px; font-style: italic;")
            self.feedback_lbl.show()
        else:
            btn.setStyleSheet(f"text-align: left; padding: 12px; background: {ThemeColors.DANGER}40; border: 2px solid {ThemeColors.DANGER}; border-radius: 8px; color: {ThemeColors.DANGER};")
            self.feedback_lbl.setText("❌ Sai rồi, thử lại nhé!")
            self.feedback_lbl.setStyleSheet(f"color: {ThemeColors.DANGER}; font-size: 14px;")
            self.feedback_lbl.show()

class SentenceCard(QFrame):
    """Widget to display a single sentence analysis."""
    def __init__(self, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setObjectName("SentenceCard")
        self.setStyleSheet(f"""
            QFrame#SentenceCard {{ 
                background: {ThemeColors.BG_PRIMARY}; border-radius: 12px; 
                border: 1px solid {ThemeColors.BORDER}; margin-bottom: 10px;
            }}
            QFrame#SentenceCard:hover {{ border: 1px solid {ThemeColors.PRIMARY}; background: {ThemeColors.BG_SECONDARY}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Original
        jp = data.get('original') or data.get('jp') or ''
        self.original = QLabel(jp)
        self.original.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        self.original.setWordWrap(True)
        self.original.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.original)
        
        # Translation
        vi = data.get('translation') or data.get('vi') or ''
        self.trans = QLabel(vi)
        self.trans.setStyleSheet(f"font-size: 14px; color: {ThemeColors.SUCCESS}; font-weight: 500;")
        self.trans.setWordWrap(True)
        self.trans.setVisible(bool(vi))
        layout.addWidget(self.trans)

class ListeningPracticeTab(QWidget):
    """JLPT Listening Practice Tab."""
    
    def __init__(self):
        super().__init__()
        self.practice_service = get_listening_practice_service()
        self.analysis_service = get_analysis_service()
        self.vocab_service = get_vocab_service()
        
        self.current_category_id: Optional[int] = None
        self.current_detail: Optional[Dict[str, Any]] = None
        
        # Audio Player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self._init_ui()
        self._load_categories()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # ===== LEFT SIDEBAR =====
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.BG_SECONDARY};
                border-radius: 8px;
            }}
            QLabel {{ color: {ThemeColors.TEXT_PRIMARY}; }}
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        header = QLabel("🎧 Luyện nghe (Listening)")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ThemeColors.ACCENT};")
        sidebar_layout.addWidget(header)
        
        # Stats Panel
        self.stats_group = QFrame()
        self.stats_group.setStyleSheet(f"background-color: {ThemeColors.BG_TERTIARY}; border-radius: 8px; padding: 10px;")
        stats_layout = QGridLayout(self.stats_group)
        
        stats_layout.addWidget(QLabel("🔊 Tổng số:"), 0, 0)
        self.total_lbl = QLabel("0")
        self.total_lbl.setStyleSheet(f"color: {ThemeColors.PRIMARY}; font-weight: bold;")
        stats_layout.addWidget(self.total_lbl, 0, 1)
        
        stats_layout.addWidget(QLabel("✅ Đã nghe:"), 1, 0)
        self.completed_lbl = QLabel("0")
        self.completed_lbl.setStyleSheet(f"color: {ThemeColors.SUCCESS}; font-weight: bold;")
        stats_layout.addWidget(self.completed_lbl, 1, 1)
        
        sidebar_layout.addWidget(self.stats_group)
        
        # Big Study Button
        self.study_btn = QPushButton("🚀 Bắt đầu nghe!")
        self.study_btn.setFixedHeight(50)
        self.study_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SUCCESS}; color: {ThemeColors.TEXT_INVERSE}; font-weight: bold; border-radius: 10px;
            }}
            QPushButton:hover {{ background-color: {ThemeColors.SUCCESS_HOVER}; }}
        """)
        sidebar_layout.addWidget(self.study_btn)
        
        # Category List
        sidebar_layout.addWidget(QLabel("📂 Trình độ JLPT:"))
        self.category_list = QListWidget()
        self.category_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; color: {ThemeColors.TEXT_PRIMARY}; }}
            QListWidget::item {{ padding: 8px 12px; border-radius: 6px; }}
            QListWidget::item:selected {{ background-color: {ThemeColors.ACCENT}; color: {ThemeColors.BG_PRIMARY}; }}
        """)
        self.category_list.itemClicked.connect(self._on_category_selected)
        sidebar_layout.addWidget(self.category_list)
        
        main_layout.addWidget(self.sidebar)
        
        # ===== MAIN CONTENT =====
        self.content_stack = QStackedWidget()
        
        # 1. List View
        self.list_view = self._create_list_view()
        self.content_stack.addWidget(self.list_view)
        
        # 2. Detail/Study View
        self.study_view = self._create_study_view()
        self.content_stack.addWidget(self.study_view)
        
        main_layout.addWidget(self.content_stack)

    def _create_list_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Initialize item_list first
        self.item_list = QListWidget()
        
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm bài nghe...")
        toolbar.addWidget(self.search_input)
        
        self.transcribe_btn = QPushButton("🎙️ AI Transcribe")
        self.transcribe_btn.setStyleSheet(f"background: {ThemeColors.PRIMARY}; color: {ThemeColors.TEXT_INVERSE}; padding: 5px 15px; border-radius: 4px; font-weight: bold;")
        self.transcribe_btn.clicked.connect(self._run_transcription)
        toolbar.addWidget(self.transcribe_btn)
        
        self.add_btn = QPushButton("➕ Thêm bài")
        self.add_btn.setStyleSheet(f"background: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.TEXT_PRIMARY}; padding: 5px 10px; border-radius: 4px;")
        toolbar.addWidget(self.add_btn)
        
        layout.addLayout(toolbar)
        
        self.item_list.setStyleSheet(f"""
            QListWidget {{ border: 1px solid {ThemeColors.BORDER}; border-radius: 8px; font-size: 14px; outline: none; background: {ThemeColors.BG_PRIMARY}; }}
            QListWidget::item {{ padding: 15px; border-bottom: 1px solid {ThemeColors.BORDER}; color: {ThemeColors.TEXT_PRIMARY}; }}
            QListWidget::item:hover {{ background: {ThemeColors.BG_SECONDARY}; }}
            QListWidget::item:selected {{ 
                background-color: {ThemeColors.BG_TERTIARY}; 
                color: {ThemeColors.PRIMARY}; 
                font-weight: bold;
                border-left: 5px solid {ThemeColors.PRIMARY};
            }}
        """)
        self.item_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.item_list)
        
        return widget

    def _create_study_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        nav_bar = QHBoxLayout()
        back_btn = QPushButton("⬅️ Quay lại danh sách")
        back_btn.clicked.connect(self._go_back)
        back_btn.setStyleSheet(f"background: transparent; color: {ThemeColors.PRIMARY}; font-weight: bold;")
        nav_bar.addWidget(back_btn)
        
        nav_bar.addStretch()
        
        self.study_title_lbl = QLabel("Tiêu đề bài nghe")
        self.study_title_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        nav_bar.addWidget(self.study_title_lbl)
        
        nav_bar.addStretch()
        
        # Action Buttons
        self.smart_mode_btn = QPushButton("✨ Song ngữ")
        self.smart_mode_btn.setCheckable(True)
        self.smart_mode_btn.clicked.connect(self._toggle_smart_mode)
        self.smart_mode_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.BG_TERTIARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 15px; padding: 5px 15px; color: {ThemeColors.TEXT_PRIMARY}; }}
            QPushButton:checked {{ background: {ThemeColors.BG_SECONDARY}; border: 1px solid {ThemeColors.PRIMARY}; color: {ThemeColors.PRIMARY}; font-weight: bold; }}
        """)
        nav_bar.addWidget(self.smart_mode_btn)
        
        self.vocab_btn = QPushButton("📖 Từ vựng")
        self.vocab_btn.clicked.connect(self._show_vocab_dialog)
        self.vocab_btn.setStyleSheet(f"QPushButton {{ background: {ThemeColors.BG_TERTIARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 15px; padding: 5px 15px; color: {ThemeColors.TEXT_PRIMARY}; }}")
        nav_bar.addWidget(self.vocab_btn)
        
        self.analyze_btn = QPushButton("⚙️ Phân tích AI")
        self.analyze_btn.clicked.connect(self._analyze_content)
        self.analyze_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.PRIMARY}; color: {ThemeColors.TEXT_INVERSE}; border-radius: 15px; padding: 5px 15px; font-weight: bold; }}
            QPushButton:hover {{ background: {ThemeColors.PRIMARY_HOVER}; }}
        """)
        nav_bar.addWidget(self.analyze_btn)
        
        layout.addLayout(nav_bar)
        
        # Player Area (reduced height)
        player_frame = QFrame()
        player_frame.setStyleSheet(f"background: {ThemeColors.BG_SECONDARY}; border-radius: 12px; padding: 15px;")
        player_layout = QVBoxLayout(player_frame)
        
        # Remove title from inside player since it's in header now
        
        ctrl_layout = QHBoxLayout()
        self.play_btn = QPushButton(" PHÁT AUDIO")
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)) # Use standard icon if available
        self.play_btn.clicked.connect(self._toggle_audio)
        self.play_btn.setMinimumWidth(150) # Use minimum width instead of fixed
        self.play_btn.setFixedHeight(45)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY}; 
                color: {ThemeColors.TEXT_INVERSE}; 
                font-weight: bold; 
                border-radius: 22px;
                font-size: 14px;
                padding: 10px;
                border: 2px solid {ThemeColors.PRIMARY_HOVER};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.PRIMARY_HOVER};
            }}
        """)
        ctrl_layout.addWidget(self.play_btn)
        
        player_layout.addLayout(ctrl_layout)
        
        # Transcript Section
        self.toggle_transcript_btn = QPushButton("📝 Hiện Transcript")
        self.toggle_transcript_btn.setCheckable(True)
        self.toggle_transcript_btn.clicked.connect(self._toggle_transcript)
        self.toggle_transcript_btn.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; border: none; font-weight: bold; margin-top: 10px;")
        player_layout.addWidget(self.toggle_transcript_btn)
        
        self.transcript_stack = QStackedWidget()
        
        # Page 0: Normal Transcript
        self.transcript_area = QTextEdit()
        self.transcript_area.setReadOnly(True)
        self.transcript_area.setStyleSheet(f"background: {ThemeColors.BG_PRIMARY}; border-radius: 6px; padding: 15px; color: {ThemeColors.TEXT_PRIMARY}; font-size: 14px; line-height: 1.6;")
        self.transcript_area.setMaximumHeight(300)
        self.transcript_stack.addWidget(self.transcript_area)
        
        # Page 1: Smart Bilingual View (Dynamic Cards)
        self.smart_transcript_scroll = QScrollArea()
        self.smart_transcript_scroll.setWidgetResizable(True)
        self.smart_transcript_scroll.setStyleSheet(f"background: {ThemeColors.BG_PRIMARY}; border: none; border-radius: 6px;")
        self.smart_transcript_scroll.setMaximumHeight(350)
        
        self.smart_transcript_container = QWidget()
        self.smart_transcript_layout = QVBoxLayout(self.smart_transcript_container)
        self.smart_transcript_layout.setContentsMargins(10, 10, 10, 10)
        self.smart_transcript_layout.addStretch()
        
        self.smart_transcript_scroll.setWidget(self.smart_transcript_container)
        self.transcript_stack.addWidget(self.smart_transcript_scroll)
        
        self.transcript_stack.setVisible(False)
        self.player_area = player_frame
        layout.addWidget(self.player_area)
        
        # Question Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        
        self.question_container = QVBoxLayout()
        self.scroll_layout.addLayout(self.question_container)
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)
        
        return widget

    def _go_back(self):
        self.media_player.stop()
        self.play_btn.setText(" PHÁT AUDIO") # Reset text
        self.content_stack.setCurrentIndex(0)

    def _toggle_audio(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_btn.setText(" TIẾP TỤC")
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_btn.setText(" TẠM DỪNG")
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

    def _load_categories(self):
        async def fetch():
            return self.practice_service.list_categories()
        
        def populate(cats):
            self.category_list.clear()
            for c in cats:
                item = QListWidgetItem(f"{c['icon'] or '🎧'} {c['name']}")
                item.setData(Qt.UserRole, c['id'])
                self.category_list.addItem(item)
            
            stats = self.practice_service.get_stats()
            self.total_lbl.setText(str(stats["total"]))
            self.completed_lbl.setText(str(stats["completed"]))
            
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
                li = QListWidgetItem(f"🔊 {i['title']} ({i['question_count']} câu hỏi)")
                li.setData(Qt.UserRole, i['id'])
                self.item_list.addItem(li)
                
        run_async(fetch, populate)

    def _on_item_double_clicked(self, item):
        item_id = item.data(Qt.UserRole)
        self._open_study_item(item_id)

    def _run_transcription(self):
        """Invoke the AI transcription script."""
        if getattr(self, "is_transcribing", False):
            QMessageBox.warning(self, "Thông báo", "Quá trình Transcribe đang chạy, vui lòng đợi xong.")
            return

        reply = QMessageBox.question(
            self, "Xác nhận", 
            "Bắt đầu tự động chuyển đổi Audio sang Transcript bằng AI?\n\n"
            "Quá trình này sẽ sử dụng kĩ thuật Batch & Waterfall (Gemini API) để tối ưu chi phí.\n"
            "Lưu ý: Có thể mất vài phút tùy số lượng bài nghe.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No: return
        self.is_transcribing = True
        
        progress = QProgressDialog("Đang xử lý chuyển đổi AI... Vui lòng không tắt ứng dụng.", None, 0, 0, self)
        progress.setWindowTitle("AI Transcribe")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        async def run_script():
            try:
                # Use sys.executable to stay in the same environment (venv)
                py_path = sys.executable
                script_path = os.path.join(os.getcwd(), "backend", "scripts", "transcribe_listening.py")
                
                # Check if script exists
                if not os.path.exists(script_path):
                    return {"success": False, "error": f"Không tìm thấy file script tại: {script_path}"}
                
                # Execute subprocess with unbuffered output (-u) and inherited console
                process = subprocess.Popen(
                    [py_path, "-u", script_path],
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    text=True,
                    encoding='utf-8',
                    cwd=os.getcwd()
                )
                process.wait()
                
                if process.returncode == 0:
                    return {"success": True}
                else:
                    return {"success": False, "err": "Process exited with errors."}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def on_finished(result):
            progress.close()
            self.is_transcribing = False
            if result.get("success"):
                toast_success("Đã hoàn thành chuyển đổi AI cho các bài nghe thiếu!")
                self._load_items() # Refresh current list
            else:
                err_msg = result.get("err") or result.get("error") or "Unknown error"
                QMessageBox.critical(self, "Lỗi", f"Quá trình chuyển đổi thất bại:\n{err_msg}")
        
        run_async(run_script, on_finished)

    def _open_study_item(self, item_id):
        detail = self.practice_service.get_item_detail(item_id)
        if not detail: return
        
        self.current_detail = detail
        self.study_title_lbl.setText(detail["title"])
        
        if detail["audio_path"]:
            # Clean audio path (strip leading slash if present)
            clean_path = detail["audio_path"].lstrip('/')
            if detail["audio_path"].startswith("http"):
                self.media_player.setSource(QUrl(detail["audio_path"]))
            else:
                self.media_player.setSource(QUrl.fromLocalFile(os.path.join(settings.project_root, clean_path)))
        
        # Clear questions
        while self.question_container.count():
            child = self.question_container.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        # Set transcript
        self.transcript_area.setText(detail["transcript"] or "Chưa có transcript.")
        
        # Clear and Render Smart Transcript
        while self.smart_transcript_layout.count():
            item = self.smart_transcript_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        if detail.get("analysis"):
            for sentence in detail["analysis"]:
                if not sentence: continue
                card = SentenceCard(sentence)
                self.smart_transcript_layout.insertWidget(self.smart_transcript_layout.count() - 1, card)
        else:
            self.smart_transcript_layout.insertWidget(0, QLabel("Chưa có dữ liệu phân tích song ngữ."))
        
        # Reset View
        self.transcript_stack.setVisible(False)
        self.transcript_stack.setCurrentIndex(0)
        self.toggle_transcript_btn.setChecked(False)
        self.toggle_transcript_btn.setText("📝 Hiện Transcript")
        self.smart_mode_btn.setChecked(False)
            
        # Decide whether to show global player
        self.player_area.setVisible(detail["audio_path"] != "per_question" and bool(detail["audio_path"]))
        
        for idx, q in enumerate(detail["questions"]):
            block = QuestionBlock(q, idx, self.media_player)
            self.question_container.addWidget(block)

        self.content_stack.setCurrentIndex(1)

    def _toggle_transcript(self):
        is_visible = self.toggle_transcript_btn.isChecked()
        self.transcript_stack.setVisible(is_visible)
        self.toggle_transcript_btn.setText("📝 Ẩn Transcript" if is_visible else "📝 Hiện Transcript")

    def _toggle_smart_mode(self):
        if not self.current_detail or not self.current_detail.get("analysis"):
            if self.smart_mode_btn.isChecked():
                self.smart_mode_btn.setChecked(False)
            
            reply = QMessageBox.question(
                self, "Chưa phân tích",
                "Bài nghe này chưa được phân tích AI (song ngữ & tách câu).\nBạn có muốn chạy phân tích ngay không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._analyze_content()
            return

        if self.smart_mode_btn.isChecked():
            self.transcript_stack.setCurrentIndex(1)
            self.transcript_stack.setVisible(True)
            self.toggle_transcript_btn.setChecked(True)
            self.toggle_transcript_btn.setText("📝 Ẩn Transcript")
        else:
            self.transcript_stack.setCurrentIndex(0)

    def _analyze_content(self):
        """Call AI to analyze the listening transcript."""
        if not self.current_detail: return
        
        text = self.current_detail.get("transcript")
        if not text or len(text) < 20:
            QMessageBox.warning(self, "Thiếu Transcript", "Cần có Transcript đầy đủ trước khi phân tích AI.")
            return

        progress = QProgressDialog("Đang trích xuất từ vựng và dịch song ngữ... (Khoảng 15-30 giây)", "Hủy", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        async def run_ai():
            return await self.analysis_service.analyze_reading_passage(text) # Reusable for any text

        def on_finished(result):
            progress.close()
            if result.get("success"):
                data = result.get("data", {})
                self.practice_service.update_item_analysis(
                    self.current_detail["id"],
                    vocabulary=data.get("vocabulary", []),
                    translation=data.get("translation", ""),
                    analysis=data.get("sentences", [])
                )
                toast_success("Đã phân tích xong! Hãy thử bật chế độ 'Song ngữ'.")
                self._open_study_item(self.current_detail["id"])
            else:
                QMessageBox.critical(self, "Lỗi", f"Không thể phân tích: {result.get('error')}")

        run_async(run_ai, on_finished)

    def _show_vocab_dialog(self):
        if not self.current_detail: return
        
        vocab_list = self.current_detail.get("vocabulary")
        if not vocab_list:
            reply = QMessageBox.question(
                self, "Chưa có từ vựng",
                "Bài nghe này chưa có dữ liệu từ vựng AI.\nBạn có muốn chạy phân tích ngay không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._analyze_content()
            return
        
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QComboBox, QLineEdit, QListWidgetItem
        dialog = QDialog(self)
        dialog.setWindowTitle("📖 Từ vựng Bài nghe")
        dialog.resize(550, 600)
        layout = QVBoxLayout(dialog)
        
        topic_layout = QHBoxLayout()
        topic_layout.addWidget(QLabel("📂 Lưu vào Deck:"))
        self.vocab_dialog_topic_combo = QComboBox()
        self.vocab_dialog_topic_combo.addItem("📂 Không phân loại", None)
        
        topics = self.vocab_service.list_topics("jp")
        for t in topics:
            self.vocab_dialog_topic_combo.addItem(f"📘 {t['name']}", t['id'])
        topic_layout.addWidget(self.vocab_dialog_topic_combo, 1)
        layout.addLayout(topic_layout)
        
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        list_widget.setStyleSheet(f"""
            QListWidget {{ border: 1px solid {ThemeColors.BORDER}; border-radius: 4px; background: {ThemeColors.BG_PRIMARY}; color: {ThemeColors.TEXT_PRIMARY}; }}
            QListWidget::item {{ padding: 8px; border-bottom: 1px solid {ThemeColors.BORDER}; }}
            QListWidget::item:selected {{ background-color: {ThemeColors.BG_TERTIARY}; color: {ThemeColors.PRIMARY}; }}
        """)
        for v in vocab_list:
            item = QListWidgetItem(f"{v.get('word')} ({v.get('reading')}) - {v.get('type')}\n👉 {v.get('meaning')}")
            item.setData(Qt.UserRole, v)
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("💾 Lưu Flashcard")
        save_btn.setStyleSheet(f"background: {ThemeColors.SUCCESS}; color: {ThemeColors.TEXT_INVERSE}; padding: 8px 15px; border-radius: 6px;")
        save_btn.clicked.connect(lambda: self._save_multiple_vocab(list_widget.selectedItems(), dialog))
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()

    def _save_multiple_vocab(self, selected_items, dialog):
        if not selected_items: return
        
        topic_id = self.vocab_dialog_topic_combo.currentData()
        count = 0
        for item in selected_items:
            v = item.data(Qt.UserRole)
            # Match the VocabService.add_vocab signature
            self.vocab_service.add_vocab(
                word=v.get("word"),
                reading=v.get("reading"),
                meaning=v.get("meaning"),
                pos=v.get("type"),
                lang="jp",
                topic_id=topic_id
            )
            count += 1
            
        toast_success(f"Đã lưu {count} từ vựng vào bộ sưu tập!")
        dialog.accept()

    def _check_answer(self, btn, selected_opt, correct_opt, explanation):
        feedback_lbl = btn.property("feedback_label")
        
        if selected_opt == correct_opt:
            btn.setStyleSheet("text-align: left; padding: 10px; background: #d4edda; border: 2px solid #28a745; border-radius: 8px; color: #155724; font-weight: bold;")
            feedback_lbl.setText(f"✅ Chính xác! \n{explanation}")
            feedback_lbl.setStyleSheet("color: #155724; margin-left: 10px; font-style: italic;")
            feedback_lbl.show()
        else:
            btn.setStyleSheet("text-align: left; padding: 10px; background: #f8d7da; border: 2px solid #dc3545; border-radius: 8px; color: #721c24;")
            # Don't show explanation on wrong answer immediately, acting as a hint? 
            # Or show it? Let's just show "Sai rồi" for now.
            feedback_lbl.setText("❌ Sai rồi, thử lại nhé!")
            feedback_lbl.setStyleSheet("color: #dc3545; margin-left: 10px;")
            feedback_lbl.show()
