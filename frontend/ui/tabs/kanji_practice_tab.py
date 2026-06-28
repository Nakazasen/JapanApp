from frontend.services.kanji_practice_service import get_kanji_practice_service
from frontend.services.analysis_service import get_analysis_service
from frontend.services.vocab_service import get_vocab_service
from frontend.utils.async_helpers import run_async
from typing import Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, 
    QPushButton, QListWidget, QStackedWidget, QListWidgetItem,
    QScrollArea, QProgressDialog, QMessageBox, QTextEdit, QDialog, QStyle
)
from PySide6.QtCore import Qt
import os
from frontend.utils.toast_helper import toast_success, toast_error, toast_info, toast_warning
from frontend.ui.styles.theme import ThemeColors

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
        self.trans = QLabel(vi)
        self.trans.setStyleSheet(f"font-size: 14px; color: {ThemeColors.SUCCESS}; font-weight: 500;")
        self.trans.setWordWrap(True)
        self.trans.setVisible(bool(vi))
        layout.addWidget(self.trans)

class KanjiPracticeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.service = get_kanji_practice_service()
        self.analysis_service = get_analysis_service()
        self.vocab_service = get_vocab_service()
        self.current_detail = None
        self._init_ui()
        self._load_items()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet(f"background: {ThemeColors.BG_SECONDARY}; color: {ThemeColors.TEXT_PRIMARY};")
        sidebar_lay = QVBoxLayout(self.sidebar)
        sidebar_lay.addWidget(QLabel("🈴 LUYỆN HÁN TỰ (JT4Y)"))
        
        self.item_list = QListWidget()
        self.item_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; color: {ThemeColors.TEXT_PRIMARY}; outline: none; }}
            QListWidget::item {{ padding: 10px; border-radius: 4px; margin-bottom: 2px; }}
            QListWidget::item:hover {{ background: {ThemeColors.BG_TERTIARY}; }}
            QListWidget::item:selected {{ background-color: {ThemeColors.ACCENT}; color: {ThemeColors.BG_PRIMARY}; font-weight: bold; }}
        """)
        self.item_list.itemClicked.connect(self._on_item_clicked)
        sidebar_lay.addWidget(self.item_list)
        main_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.welcome = QLabel("Chọn một bài luyện tập để bắt đầu")
        self.welcome.setAlignment(Qt.AlignCenter)
        self.stack.addWidget(self.welcome)
        
        # Detail View
        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        
        # Nav Bar
        nav_bar = QHBoxLayout()
        back_btn = QPushButton("⬅️ Quay lại")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        back_btn.setStyleSheet(f"background: transparent; color: {ThemeColors.PRIMARY}; font-weight: bold;")
        nav_bar.addWidget(back_btn)
        
        nav_bar.addStretch()
        self.study_title_lbl = QLabel("Tiêu đề")
        self.study_title_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ThemeColors.TEXT_PRIMARY};")
        nav_bar.addWidget(self.study_title_lbl)
        nav_bar.addStretch()
        
        self.smart_mode_btn = QPushButton("✨ Song ngữ")
        self.smart_mode_btn.setCheckable(True)
        self.smart_mode_btn.clicked.connect(self._toggle_smart_mode)
        self.smart_mode_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.BG_TERTIARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 15px; padding: 5px 15px; color: {ThemeColors.TEXT_PRIMARY}; }}
            QPushButton:checked {{ background: {ThemeColors.BG_SECONDARY}; border: 1px solid {ThemeColors.PRIMARY}; color: {ThemeColors.PRIMARY}; font-weight: bold; }}
        """)
        nav_bar.addWidget(self.smart_mode_btn)
        
        self.kanji_btn = QPushButton("📖 Hán tự")
        self.kanji_btn.clicked.connect(self._show_vocab_dialog)
        self.kanji_btn.setStyleSheet(f"QPushButton {{ background: {ThemeColors.BG_TERTIARY}; border: 1px solid {ThemeColors.BORDER}; border-radius: 15px; padding: 5px 15px; color: {ThemeColors.TEXT_PRIMARY}; }}")
        nav_bar.addWidget(self.kanji_btn)
        
        self.analyze_btn = QPushButton("⚙️ Phân tích AI")
        self.analyze_btn.clicked.connect(self._analyze_content)
        self.analyze_btn.setStyleSheet(f"""
            QPushButton {{ background: {ThemeColors.PRIMARY}; color: {ThemeColors.TEXT_INVERSE}; border-radius: 15px; padding: 5px 15px; font-weight: bold; }}
            QPushButton:hover {{ background: {ThemeColors.PRIMARY_HOVER}; }}
        """)
        nav_bar.addWidget(self.analyze_btn)
        
        detail_layout.addLayout(nav_bar)
        
        # Transcript Stack (for Song ngữ)
        self.transcript_stack = QStackedWidget()
        self.transcript_stack.setVisible(False)
        
        self.transcript_area = QTextEdit()
        self.transcript_area.setReadOnly(True)
        self.transcript_area.setStyleSheet(f"background: {ThemeColors.BG_SECONDARY}; border-radius: 6px; padding: 15px; color: {ThemeColors.TEXT_PRIMARY}; font-size: 14px;")
        self.transcript_area.setMaximumHeight(200)
        self.transcript_stack.addWidget(self.transcript_area)
        
        self.smart_transcript_scroll = QScrollArea()
        self.smart_transcript_scroll.setWidgetResizable(True)
        self.smart_transcript_scroll.setMaximumHeight(300)
        self.smart_transcript_container = QWidget()
        self.smart_transcript_layout = QVBoxLayout(self.smart_transcript_container)
        self.smart_transcript_layout.addStretch()
        self.smart_transcript_scroll.setWidget(self.smart_transcript_container)
        self.transcript_stack.addWidget(self.smart_transcript_scroll)
        
        detail_layout.addWidget(self.transcript_stack)
        
        self.study_view = QScrollArea()
        self.study_view.setWidgetResizable(True)
        self.study_content = QWidget()
        self.study_layout = QVBoxLayout(self.study_content)
        self.study_view.setWidget(self.study_content)
        detail_layout.addWidget(self.study_view)
        
        self.stack.addWidget(self.detail_widget)
        main_layout.addWidget(self.stack)

    def _load_items(self):
        async def fetch(): return self.service.list_items()
        def populate(items):
            self.item_list.clear()
            for i in items:
                li = QListWidgetItem(f"📝 {i['title']} ({i['question_count']} câu)")
                li.setData(Qt.UserRole, i['id'])
                self.item_list.addItem(li)
        run_async(fetch, populate)

    def _on_item_clicked(self, item):
        item_id = item.data(Qt.UserRole)
        detail = self.service.get_item_detail(item_id)
        if not detail: return

        self.current_detail = detail
        self.study_title_lbl.setText(detail["title"])
        
        while self.study_layout.count():
            child = self.study_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        # Reset Transcript Stack
        self.transcript_stack.setVisible(False)
        self.smart_mode_btn.setChecked(False)
        self.transcript_area.setText(detail.get("transcript") or "Chưa có nội dung văn bản.")
        
        # Render Smart Transcript
        while self.smart_transcript_layout.count() > 1:
            child = self.smart_transcript_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        if detail.get("analysis"):
            for sentence in detail["analysis"]:
                if not sentence: continue
                card = SentenceCard(sentence)
                self.smart_transcript_layout.insertWidget(self.smart_transcript_layout.count() - 1, card)
            
        # self.study_layout.addWidget(QLabel(f"<h2>{detail['title']}</h2>"))
        
        for idx, q in enumerate(detail['questions']):
            q_lbl = QLabel(f"<b>Câu {idx+1}:</b> {q['question_text']}")
            q_lbl.setWordWrap(True)
            self.study_layout.addWidget(q_lbl)
            
            feedback = QLabel()
            feedback.hide()
            
            for opt, text in q['options'].items():
                btn = QPushButton(f"{opt}. {text}")
                btn.setStyleSheet(f"text-align: left; padding: 8px; margin: 2px; color: {ThemeColors.TEXT_PRIMARY};")
                btn.clicked.connect(lambda chk=False, b=btn, o=opt, c=q['correct_option'], e=q['explanation'], f=feedback: self._check(b, o, c, e, f))
                self.study_layout.addWidget(btn)
            self.study_layout.addWidget(feedback)
            
        self.study_layout.addStretch()
        self.stack.setCurrentIndex(1)

    def _check(self, btn, selected, correct, explanation, feedback):
        if selected == correct:
            btn.setStyleSheet(f"background: {ThemeColors.SUCCESS}40; color: {ThemeColors.SUCCESS}; text-align: left; padding: 8px;")
            feedback.setText(f"✅ Đúng! {explanation}")
            feedback.setStyleSheet(f"color: {ThemeColors.SUCCESS};")
        else:
            btn.setStyleSheet(f"background: {ThemeColors.DANGER}40; color: {ThemeColors.DANGER}; text-align: left; padding: 8px;")
            feedback.setText("❌ Sai rồi!")
            feedback.setStyleSheet(f"color: {ThemeColors.DANGER};")
        feedback.show()

    def _toggle_smart_mode(self):
        if not self.current_detail or not self.current_detail.get("analysis"):
            self.smart_mode_btn.setChecked(False)
            reply = QMessageBox.question(
                self, "Chưa phân tích",
                "Bài này chưa được phân tích AI. Bạn có muốn phân tích ngay không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._analyze_content()
            return
        
        is_on = self.smart_mode_btn.isChecked()
        self.transcript_stack.setVisible(is_on)
        self.transcript_stack.setCurrentIndex(1 if is_on else 0)

    def _analyze_content(self):
        if not self.current_detail: return
        text = self.current_detail.get("transcript")
        if not text:
            # Fallback: combine question texts
            text = "\n".join([q["question_text"] for q in self.current_detail["questions"]])
            
        progress = QProgressDialog("Đang phân tích AI...", "Hủy", 0, 0, self)
        progress.show()
        
        async def run_ai():
            return await self.analysis_service.analyze_reading_passage(text)
            
        def on_finished(result):
            progress.close()
            if result.get("success"):
                data = result.get("data", {})
                self.service.update_item_analysis(
                    self.current_detail["id"],
                    vocabulary=data.get("vocabulary", []),
                    translation=data.get("translation", ""),
                    analysis=data.get("sentences", [])
                )
                toast_success("Đã phân tích xong!")
                self._on_item_clicked(self.item_list.currentItem())
            else:
                QMessageBox.critical(self, "Lỗi", f"Phân tích thất bại: {result.get('error')}")
        
        run_async(run_ai, on_finished)

    def _show_vocab_dialog(self):
        if not self.current_detail or not self.current_detail.get("vocabulary"):
            QMessageBox.warning(self, "Thông tin", "Chưa có dữ liệu phân tích. Hãy nhấn 'Phân tích AI' trước.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("📖 Hán tự")
        dialog.resize(500, 600)
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        for v in self.current_detail["vocabulary"]:
            list_widget.addItem(f"{v.get('word')} ({v.get('reading')}) - {v.get('meaning')}")
        layout.addWidget(list_widget)
        
        dialog.exec()
