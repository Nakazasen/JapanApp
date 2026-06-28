"""Exam practice tab - Redesigned Electronic Exam Center."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QListWidget, QTextEdit, QLabel, QRadioButton, QButtonGroup,
    QTimeEdit, QSplitter, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTime, QTimer
from typing import Dict, List, Optional
import re
from frontend.utils.async_helpers import run_async
from frontend.services.exam_service import get_exam_service


class ExamTab(QWidget):
    """Exam practice tab - Redesigned Edition."""
    
    def __init__(self):
        super().__init__()
        self.exam_service = get_exam_service()
        self.current_exam_id = None
        self.current_questions = []
        self.current_question_index = 0
        self.user_answers = {}
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_timer)
        self.available_exams = []
        self.local_exams = []
        
        self._init_ui()
        self._load_local_exams()

    def _init_ui(self):
        """Initialize UI - Electronic Exam Center Edition."""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setStyleSheet("""
            QWidget#ExamTab { background-color: #f8f9fa; }
            QFrame#Sidebar { 
                background-color: #1a1a2e; 
                border-right: 1px solid #dcdde1; 
            }
            QLabel#SidebarTitle { 
                font-size: 16px; 
                font-weight: bold; 
                color: #f0a500; 
                padding: 10px 5px;
            }
            QLabel#WhiteLbl { color: #ffffff; }
            
            QListWidget {
                background-color: transparent;
                border: none;
                color: #dcdde1;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-bottom: 1px solid #2e2e42;
            }
            QListWidget::item:selected {
                background-color: #4a4e69;
                color: white;
                border-left: 4px solid #f0a500;
            }
            
            QFrame#QuestionArea {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
            
            QPushButton#ActionBtn {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px 20px;
                border: none;
            }
            QPushButton#ActionBtn:hover { background-color: #2980b9; }
            
            QPushButton#SubmitBtn {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 12px 25px;
                font-size: 15px;
            }
            QPushButton#SubmitBtn:hover { background-color: #27ae60; }
        """)
        self.setObjectName("ExamTab")

        # ========== SIDEBAR: Exam Selection ==========
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        sidebar_layout.addWidget(QLabel("📝 TRUNG TÂM LUYỆN THI", objectName="SidebarTitle"))
        
        # Filters
        filter_group = QVBoxLayout()
        filter_group.setSpacing(8)
        
        filter_group.addWidget(QLabel("Trình độ JLPT:", objectName="WhiteLbl"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["N1", "N2", "N3", "N4", "N5"])
        self.level_combo.setStyleSheet("background: #16213e; color: white; padding: 5px;")
        filter_group.addWidget(self.level_combo)
        
        filter_group.addWidget(QLabel("Nguồn đề:", objectName="WhiteLbl"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Tất cả nguồn", "Japanesetest4you", "Local DB"])
        self.source_combo.setStyleSheet("background: #16213e; color: white; padding: 5px;")
        filter_group.addWidget(self.source_combo)
        
        sidebar_layout.addLayout(filter_group)
        
        # Load Buttons
        btn_row = QHBoxLayout()
        self.load_exam_btn = QPushButton("Tìm đề")
        self.load_exam_btn.setObjectName("ActionBtn")
        self.load_exam_btn.clicked.connect(self._load_available_exams)
        btn_row.addWidget(self.load_exam_btn)
        
        self.fetch_exam_btn = QPushButton("Tải đề")
        self.fetch_exam_btn.setObjectName("ActionBtn")
        self.fetch_exam_btn.clicked.connect(self._fetch_selected_exam)
        btn_row.addWidget(self.fetch_exam_btn)

        self.refresh_local_btn = QPushButton("Máy chủ")
        self.refresh_local_btn.setObjectName("ActionBtn")
        self.refresh_local_btn.clicked.connect(self._load_local_exams)
        btn_row.addWidget(self.refresh_local_btn)
        sidebar_layout.addLayout(btn_row)
        
        sidebar_layout.addWidget(QLabel("DANH SÁCH ĐỀ THI", objectName="SidebarTitle"))
        self.exam_list = QListWidget()
        self.exam_list.itemClicked.connect(self._load_exam)
        sidebar_layout.addWidget(self.exam_list)
        
        main_layout.addWidget(sidebar)

        # ========== MAIN AREA: Exam Room ==========
        self.exam_room = QWidget()
        room_layout = QVBoxLayout(self.exam_room)
        room_layout.setContentsMargins(40, 30, 40, 30)
        room_layout.setSpacing(20)
        
        # Header: Timer and Title
        header_layout = QHBoxLayout()
        self.timer_card = QFrame()
        self.timer_card.setStyleSheet("background: #e74c3c; border-radius: 8px; padding: 8px 15px;")
        timer_layout = QHBoxLayout(self.timer_card)
        timer_layout.addWidget(QLabel("⏱️", styleSheet="font-size: 18px;"))
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet("color: white; font-weight: 900; font-size: 18px; font-family: monospace;")
        timer_layout.addWidget(self.timer_label)
        header_layout.addWidget(self.timer_card)
        
        header_layout.addStretch()
        
        self.question_stats = QLabel("Câu hỏi 0/0")
        self.question_stats.setStyleSheet("font-weight: bold; color: #7f8c8d; font-size: 14px;")
        header_layout.addWidget(self.question_stats)
        
        room_layout.addLayout(header_layout)
        
        # Question Display
        self.question_card = QFrame()
        self.question_card.setObjectName("QuestionArea")
        question_card_layout = QVBoxLayout(self.question_card)
        question_card_layout.setContentsMargins(25, 25, 25, 25)
        
        self.question_text = QTextEdit()
        self.question_text.setReadOnly(True)
        self.question_text.setFrameShape(QFrame.NoFrame)
        self.question_text.setStyleSheet("font-size: 18px; line-height: 1.6; color: #2c3e50;")
        question_card_layout.addWidget(self.question_text)
        
        room_layout.addWidget(self.question_card, 2)
        
        # Options Area
        options_label = QLabel("CHỌN ĐÁP ÁN:")
        options_label.setStyleSheet("font-weight: 900; color: #7f8c8d; letter-spacing: 1px;")
        room_layout.addWidget(options_label)
        
        self.options_widget = QWidget()
        self.options_layout = QVBoxLayout(self.options_widget)
        self.options_layout.setSpacing(10)
        self.options_group = QButtonGroup(self)
        room_layout.addWidget(self.options_widget, 1)
        
        # Bottom Navigation
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("⬅️ Câu trước")
        self.prev_btn.setObjectName("ActionBtn")
        self.prev_btn.setFixedWidth(140)
        self.prev_btn.clicked.connect(lambda: self._display_question(self.current_question_index - 1))
        
        self.next_btn = QPushButton("Câu tiếp ➡️")
        self.next_btn.setObjectName("ActionBtn")
        self.next_btn.setFixedWidth(140)
        self.next_btn.clicked.connect(lambda: self._display_question(self.current_question_index + 1))
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        
        self.submit_btn = QPushButton("🎯 NỘP BÀI THI")
        self.submit_btn.setObjectName("SubmitBtn")
        self.submit_btn.clicked.connect(self._submit_exam)
        nav_layout.addWidget(self.submit_btn)
        
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        
        room_layout.addLayout(nav_layout)
        
        main_layout.addWidget(self.exam_room, 1)
        
        self.level_combo.currentTextChanged.connect(self._on_level_changed)

    def _on_level_changed(self, level):
        self._load_available_exams()

    def _load_local_exams(self):
        """Load exams already in the database."""
        self.exam_list.clear()
        self.exam_list.addItem("Đang quét dữ liệu máy...")
        
        async def load():
            try: return self.exam_service.list_exams()
            except Exception: return []
            
        def update_ui(exams):
            self.exam_list.clear()
            self.local_exams = exams
            if exams:
                for exam in exams:
                    self.exam_list.addItem(f"🏠 {exam.get('title', 'Untitled')}")
            else:
                self.exam_list.addItem("Chưa có đề nào trên máy")
                
        run_async(load, update_ui)

    def _load_available_exams(self):
        level = self.level_combo.currentText()
        self.exam_list.clear()
        self.exam_list.addItem("Đang tải...")
        
        async def load():
            try:
                return self.exam_service.list_available_exams(level)
            except Exception as e:
                return []
        
        def update_ui(exams):
            self.exam_list.clear()
            self.available_exams = exams
            if exams:
                for exam in exams:
                    title = f"{exam.get('type', '')} - {exam.get('title', '')}"
                    self.exam_list.addItem(title)
            else:
                self.exam_list.addItem("Không tìm thấy đề thi")
        
        run_async(load, update_ui)

    def _fetch_selected_exam(self):
        current_item = self.exam_list.currentItem()
        if not current_item or current_item.text() in ["Đang tải...", "Không tìm thấy đề thi"]:
            return
        
        index = self.exam_list.currentRow()
        if index < 0 or index >= len(self.available_exams):
            return
        
        exam_info = self.available_exams[index]
        exam_url = exam_info.get('url')
        
        async def fetch():
            try:
                sources = self.exam_service.get_exam_sources()
                source_id = 1
                for source in sources:
                    if 'dethitiengnhat' in source.get('url', '').lower():
                        source_id = source['id']
                        break
                return self.exam_service.fetch_exam(source_id, exam_url)
            except Exception as e:
                return None
        
        def update_ui(result):
            if result and result.get('id'):
                self.current_exam_id = result['id']
                self.question_text.setHtml("<center><h3>Đang tải đề thi...</h3></center>")
                self._load_exam_questions(self.current_exam_id)
        
        run_async(fetch, update_ui)

    def _load_exam_questions(self, exam_id: int):
        async def load():
            try: return self.exam_service.get_exam_questions(exam_id)
            except Exception: return []
        
        def update_ui(questions):
            if not questions:
                self.question_text.setHtml("<center><h3 style='color: red;'>Không tìm thấy câu hỏi.</h3></center>")
                return
            self.current_questions = questions
            self.current_question_index = 0
            self.user_answers = {}
            self.start_time = QTime.currentTime()
            self.timer.start(1000)
            self._display_question(0)
        
        run_async(load, update_ui)

    def _load_exam(self, item):
        async def load():
            try:
                exams = self.local_exams
                if exams and self.exam_list.currentRow() < len(exams):
                    exam = exams[self.exam_list.currentRow()]
                    self.current_exam_id = exam['id']
                    return self.exam_service.get_exam_questions(exam['id'])
                return []
            except Exception: return []
        
        def update_ui(questions):
            if questions:
                self.current_questions = questions
                self.current_question_index = 0
                self.user_answers = {}
                self.start_time = QTime.currentTime()
                self.timer.start(1000)
                self._display_question(0)
        
        run_async(load, update_ui)

    def _display_question(self, index: int):
        if not self.current_questions or index < 0 or index >= len(self.current_questions):
            return
        
        self.current_question_index = index
        question = self.current_questions[index]
        question_text = question.get('question_text', '')
        options = question.get('options', {})
        
        self.question_stats.setText(f"Câu hỏi {index + 1}/{len(self.current_questions)}")
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setEnabled(index < len(self.current_questions) - 1)

        # Build HTML content
        def escape_html(t):
            return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        html = f"""
        <div style="font-family: 'Segoe UI', Arial; color: #2c3e50; font-size: 16pt;">
            {escape_html(question_text).replace('\n', '<br>')}
        </div>
        """
        self.question_text.setHtml(html)
        
        # Clear options
        while self.options_layout.count():
            it = self.options_layout.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        
        self.options_group = QButtonGroup(self)
        
        sorted_keys = sorted(options.keys())[:4]
        for key in sorted_keys:
            val = options[key]
            
            card = QFrame()
            card.setStyleSheet("QFrame { background: #f8f9fa; border: 1px solid #dcdde1; border-radius: 8px; }")
            opt_lay = QHBoxLayout(card)
            
            radio = QRadioButton(f"{key}. {val}")
            radio.setStyleSheet("font-size: 15px; padding: 5px;")
            
            # Use question_id or index as unique key
            ans_key = question.get('id') if question.get('id') else index
            if self.user_answers.get(ans_key) == key:
                radio.setChecked(True)
                card.setStyleSheet("background: #e3f2fd; border: 2px solid #3498db; border-radius: 8px;")
            
            radio.toggled.connect(lambda checked, k=key, c=card, ak=ans_key: self._on_opt_toggled(checked, k, c, ak))
            
            self.options_group.addButton(radio)
            opt_lay.addWidget(radio)
            self.options_layout.addWidget(card)
        
        self.options_layout.addStretch()

    def _on_opt_toggled(self, checked, key, card, ans_key):
        if checked:
            self.user_answers[ans_key] = key
            card.setStyleSheet("background: #e3f2fd; border: 2px solid #3498db; border-radius: 8px;")
        else:
            card.setStyleSheet("background: #f8f9fa; border: 1px solid #dcdde1; border-radius: 8px;")

    def _update_timer(self):
        if self.start_time:
            elapsed = self.start_time.msecsTo(QTime.currentTime())
            self.timer_label.setText(f"{elapsed//3600000:02d}:{(elapsed%3600000)//60000:02d}:{(elapsed%60000)//1000:02d}")

    def _submit_exam(self):
        if not self.current_exam_id: return
        
        time_taken = self.start_time.msecsTo(QTime.currentTime()) // 1000 if self.start_time else 0
        self.timer.stop()
        
        async def submit():
            return self.exam_service.submit_exam(self.current_exam_id, self.user_answers, time_taken)
        
        def show_res(res):
            if res:
                self.question_text.setHtml(f"<center><h1>KẾT QUẢ</h1><p style='font-size: 40px; color: green;'>{res.get('score', 0):.1f}%</p></center>")
        
        run_async(submit, show_res)
