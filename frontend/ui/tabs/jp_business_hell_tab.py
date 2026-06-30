import json
import os
import random
from typing import Any, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QStackedWidget, QScrollArea, QFrame, QPlainTextEdit, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from frontend.ui.styles.theme import ThemeColors
from frontend.services.jp_business_hell_ai import JPBusinessHellAI

class JpBusinessHellTab(QWidget):
    """Địa ngục tiếng Nhật MVP UI."""
    
    GATES = [
        ("meeting_listening", "Nghe họp địa ngục"),
        ("meeting_speaking", "Phát biểu địa ngục"),
        ("business_mail", "Mail địa ngục"),
        ("document_reading", "Đọc tài liệu địa ngục"),
        ("keigo_nuance", "Kính ngữ & sắc thái địa ngục"),
        ("final_boss", "Final Boss họp Nhật")
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ai_service = JPBusinessHellAI()
        self.seed_data = self._load_seed_data()
        self.current_scenario = None
        self.scores_by_gate = {gate_id: [] for gate_id, _ in self.GATES}
        
        self._setup_ui()
        self._refresh_dashboard()

    def _load_seed_data(self) -> list[Dict[str, Any]]:
        path = os.path.join("data", "japanese", "business_hell_seed.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading seed data: {e}")
        return []

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # 1. Dashboard Page
        self.dashboard_page = QWidget()
        self._setup_dashboard_page()
        self.stacked_widget.addWidget(self.dashboard_page)
        
        # 2. Drill Page
        self.drill_page = QWidget()
        self._setup_drill_page()
        self.stacked_widget.addWidget(self.drill_page)
        
        # 3. Report Page
        self.report_page = QWidget()
        self._setup_report_page()
        self.stacked_widget.addWidget(self.report_page)

    def _setup_dashboard_page(self):
        layout = QVBoxLayout(self.dashboard_page)
        layout.setSpacing(20)
        
        title = QLabel("🔥 ĐỊA NGỤC TIẾNG NHẬT (日本語地獄)")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Stats
        self.stats_label = QLabel("Đang tải dữ liệu...")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(self.stats_label)
        
        # Gates Container
        gates_container = QFrame()
        gates_layout = QVBoxLayout(gates_container)
        
        self.gate_buttons = {}
        for gate_id, gate_name in self.GATES:
            btn = QPushButton(gate_name)
            btn.setFixedHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, gid=gate_id: self._start_drill(gid))
            gates_layout.addWidget(btn)
            self.gate_buttons[gate_id] = btn
            
        scroll = QScrollArea()
        scroll.setWidget(gates_container)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

    def _setup_drill_page(self):
        layout = QVBoxLayout(self.drill_page)
        layout.setSpacing(15)
        
        self.drill_title = QLabel()
        self.drill_title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(self.drill_title)
        
        self.drill_context = QLabel()
        self.drill_context.setWordWrap(True)
        self.drill_context.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY};")
        layout.addWidget(self.drill_context)
        
        self.drill_prompt = QLabel()
        self.drill_prompt.setWordWrap(True)
        self.drill_prompt.setFont(QFont("Arial", 14))
        layout.addWidget(self.drill_prompt)
        
        self.drill_input = QLabel()
        self.drill_input.setWordWrap(True)
        self.drill_input.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.drill_input)
        
        self.answer_edit = QPlainTextEdit()
        self.answer_edit.setPlaceholderText("Nhập câu trả lời của bạn vào đây...")
        layout.addWidget(self.answer_edit)
        
        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton("Gửi đáp án")
        self.submit_btn.setFixedHeight(40)
        self.submit_btn.clicked.connect(self._submit_answer)
        btn_layout.addWidget(self.submit_btn)
        
        back_btn = QPushButton("Quay lại")
        back_btn.setFixedHeight(40)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        btn_layout.addWidget(back_btn)
        
        layout.addLayout(btn_layout)

    def _setup_report_page(self):
        layout = QVBoxLayout(self.report_page)
        layout.setSpacing(10)
        
        self.report_title = QLabel("📝 BÁO CÁO KẾT QUẢ")
        self.report_title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(self.report_title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.report_content = QLabel()
        self.report_content.setWordWrap(True)
        self.report_content.setStyleSheet("font-size: 14px;")
        scroll.setWidget(self.report_content)
        layout.addWidget(scroll)
        
        back_btn = QPushButton("Quay lại Bảng điều khiển")
        back_btn.setFixedHeight(40)
        back_btn.clicked.connect(lambda: [self._refresh_dashboard(), self.stacked_widget.setCurrentIndex(0)])
        layout.addWidget(back_btn)

    def _is_final_boss_unlocked(self) -> bool:
        total_score = 0
        total_drills = 0
        for scores in self.scores_by_gate.values():
            if scores:
                total_score += sum(scores)
                total_drills += len(scores)
        overall_avg = total_score / total_drills if total_drills > 0 else 0
        return total_drills >= 5 and overall_avg >= 70

    def _refresh_dashboard(self):
        # Calculate stats and unlock logic
        total_score = 0
        total_drills = 0
        weakest = None
        min_score = 100
        
        for gate_id, scores in self.scores_by_gate.items():
            if scores:
                avg = sum(scores) / len(scores)
                total_score += sum(scores)
                total_drills += len(scores)
                if avg < min_score:
                    min_score = avg
                    weakest = gate_id
                    
        overall_avg = total_score / total_drills if total_drills > 0 else 0
        can_unlock_boss = self._is_final_boss_unlocked()
        
        self.stats_label.setText(
            f"Điểm trung bình: {overall_avg:.1f}/100 | Điểm yếu: {weakest or 'Chưa rõ'}\n"
            f"Tiến trình unlock Final Boss: {'Đã mở khóa' if can_unlock_boss else 'Cần đạt TB 70đ qua ít nhất 5 bài'}"
        )
        
        # Unlock Final Boss
        boss_btn = self.gate_buttons["final_boss"]
        boss_btn.setEnabled(can_unlock_boss)
        if can_unlock_boss:
            boss_btn.setText("Final Boss họp Nhật (ĐÃ MỞ KHÓA)")
            boss_btn.setStyleSheet(f"background-color: {ThemeColors.ERROR}; color: white; font-weight: bold;")
        else:
            boss_btn.setText("Final Boss họp Nhật (CHƯA MỞ KHÓA - Cần TB 70đ & 5 bài)")
            boss_btn.setStyleSheet("")

    def _start_drill(self, gate_id: str):
        if gate_id == "final_boss" and not self._is_final_boss_unlocked():
            QMessageBox.warning(self, "Chưa mở khóa", "Bạn chưa đủ điều kiện để mở khóa Final Boss.")
            return
            
        candidates = [s for s in self.seed_data if s.get("gate") == gate_id]
        if not candidates:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy dữ liệu cho cổng này.")
            return
            
        self.current_scenario = random.choice(candidates)
        
        self.drill_title.setText(self.current_scenario.get("title", "Drill"))
        self.drill_context.setText(f"Ngữ cảnh: {self.current_scenario.get('business_context', '')}")
        self.drill_prompt.setText(f"Nhiệm vụ: {self.current_scenario.get('prompt_vi', '')}")
        
        jp_input = self.current_scenario.get("japanese_input")
        if jp_input:
            self.drill_input.setText(f"Tiếng Nhật:\n{jp_input}")
            self.drill_input.setVisible(True)
        else:
            self.drill_input.setVisible(False)
            
        self.answer_edit.clear()
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("Gửi đáp án")
        self.stacked_widget.setCurrentIndex(1)

    def _submit_answer(self):
        answer = self.answer_edit.toPlainText().strip()
        if not answer:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập câu trả lời.")
            return
            
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Đang chấm điểm...")
        
        # Use offline mode for demo without API keys
        # We explicitly set privacy_mode="offline" or something similar if the app is configured without keys, 
        # but the AI router fallback logic handles it automatically if keys are missing.
        # Let's pass redacted as required by AI service.
        try:
            is_boss = self.current_scenario.get("gate") == "final_boss"
            feedback = self.ai_service.grade_answer(
                scenario=self.current_scenario, 
                user_answer=answer, 
                boss_fight=is_boss
            )
            self._show_report(feedback)
            
            # Save score
            score = feedback.get("score_total", 0)
            self.scores_by_gate[self.current_scenario.get("gate")].append(score)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi chấm điểm", str(e))
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Gửi đáp án")

    def _show_report(self, feedback: Dict[str, Any]):
        html = f"""
        <h3>Điểm: {feedback.get('score_total', 0)}/100</h3>
        <b>Lỗi nghiêm trọng:</b><br/>
        <ul>
        """
        for err in feedback.get('critical_errors', []):
            html += f"<li>{err}</li>"
        html += "</ul><br/><b>Câu không tự nhiên:</b><br/><ul>"
        for unnat in feedback.get('unnatural_phrases', []):
            html += f"<li>{unnat}</li>"
        html += f"""
        </ul><br/>
        <b>Phiên bản tốt hơn:</b><br/>{feedback.get('better_version', '')}<br/><br/>
        <b>Giải thích (VI):</b><br/>{feedback.get('vietnamese_explanation', '')}<br/><br/>
        <b>Điểm yếu:</b> {', '.join(feedback.get('weakness_tags', []))}<br/><br/>
        <hr/>
        <b>Metadata Router:</b><br/>
        Provider: {feedback.get('provider_used')}<br/>
        Tier: {feedback.get('provider_tier')}<br/>
        Fallback: {feedback.get('fallback_used')}<br/>
        Judge Provider (Boss): {feedback.get('judge_provider')}
        """
        self.report_content.setText(html)
        self.stacked_widget.setCurrentIndex(2)
