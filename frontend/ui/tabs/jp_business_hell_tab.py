import json
import os
import random
from typing import Any, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QStackedWidget, QScrollArea, QFrame, QPlainTextEdit, QMessageBox,
    QLineEdit, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from frontend.ui.styles.theme import ThemeColors
from frontend.services.japanese_work_memory import JapaneseWorkLearningMemory
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

    def __init__(self, parent=None, memory: JapaneseWorkLearningMemory | None = None):
        super().__init__(parent)
        self.ai_service = JPBusinessHellAI(memory=memory)
        self.seed_data = self._load_seed_data()
        self.scores_by_gate = {gate_id: [] for gate_id, _ in self.GATES}
        self._load_scores_from_memory()
        
        self._setup_ui()
        self._refresh_dashboard()

    def _load_scores_from_memory(self):
        self.scores_by_gate = {gate_id: [] for gate_id, _ in self.GATES}
        attempts = self.ai_service.memory.data.get("attempts", [])
        for attempt in attempts:
            gate = attempt.get("gate")
            score = attempt.get("score_total")
            if gate in self.scores_by_gate and score is not None:
                self.scores_by_gate[gate].append(score)

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
        self.stats_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.stats_label.setTextFormat(Qt.RichText)
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet(f"font-size: 14px;")
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
        
        # Stacked inputs container
        self.input_fields_stack = QStackedWidget()
        layout.addWidget(self.input_fields_stack)
        
        # 0. Generic answer_edit
        self.answer_edit = QPlainTextEdit()
        self.answer_edit.setPlaceholderText("Nhập câu trả lời của bạn vào đây...")
        self.input_fields_stack.addWidget(self.answer_edit)
        
        # 1. meeting_listening container
        self.listening_widget = QWidget()
        listen_layout = QVBoxLayout(self.listening_widget)
        self.listen_topic = QPlainTextEdit()
        self.listen_topic.setPlaceholderText("Topic (Chủ đề họp)")
        self.listen_topic.setMaximumHeight(60)
        self.listen_decision = QPlainTextEdit()
        self.listen_decision.setPlaceholderText("Decision (Quyết định được đưa ra)")
        self.listen_decision.setMaximumHeight(60)
        self.listen_issue = QPlainTextEdit()
        self.listen_issue.setPlaceholderText("Issue (Vấn đề phát sinh)")
        self.listen_issue.setMaximumHeight(60)
        self.listen_pic = QPlainTextEdit()
        self.listen_pic.setPlaceholderText("PIC (Người chịu trách nhiệm)")
        self.listen_pic.setMaximumHeight(40)
        self.listen_deadline = QPlainTextEdit()
        self.listen_deadline.setPlaceholderText("Deadline (Hạn chót)")
        self.listen_deadline.setMaximumHeight(40)
        self.listen_risk = QPlainTextEdit()
        self.listen_risk.setPlaceholderText("Risk (Rủi ro tiềm ẩn)")
        self.listen_risk.setMaximumHeight(60)
        
        listen_layout.addWidget(QLabel("<b>Chủ đề họp (Topic):</b>"))
        listen_layout.addWidget(self.listen_topic)
        listen_layout.addWidget(QLabel("<b>Quyết định (Decision):</b>"))
        listen_layout.addWidget(self.listen_decision)
        listen_layout.addWidget(QLabel("<b>Vấn đề (Issue):</b>"))
        listen_layout.addWidget(self.listen_issue)
        listen_layout.addWidget(QLabel("<b>Người phụ trách (PIC):</b>"))
        listen_layout.addWidget(self.listen_pic)
        listen_layout.addWidget(QLabel("<b>Hạn chót (Deadline):</b>"))
        listen_layout.addWidget(self.listen_deadline)
        listen_layout.addWidget(QLabel("<b>Rủi ro (Risk):</b>"))
        listen_layout.addWidget(self.listen_risk)
        self.input_fields_stack.addWidget(self.listening_widget)
        
        # 2. meeting_speaking container
        self.speaking_widget = QWidget()
        speak_layout = QVBoxLayout(self.speaking_widget)
        self.speak_duration = QComboBox()
        self.speak_duration.addItems(["30 giây", "60 giây", "90 giây"])
        self.speak_pattern = QComboBox()
        self.speak_pattern.addItems(["Báo cáo (Report)", "Đề xuất (Proposal)", "Xác nhận (Confirmation)", "Phản đối (Disagreement)", "Xin lỗi (Apology)"])
        self.speak_response = QPlainTextEdit()
        self.speak_response.setPlaceholderText("Nhập câu phát biểu tiếng Nhật của bạn...")
        
        speak_layout.addWidget(QLabel("<b>Thời lượng phát biểu:</b>"))
        speak_layout.addWidget(self.speak_duration)
        speak_layout.addWidget(QLabel("<b>Mẫu cấu trúc / Mục đích:</b>"))
        speak_layout.addWidget(self.speak_pattern)
        speak_layout.addWidget(QLabel("<b>Nội dung phát biểu:</b>"))
        speak_layout.addWidget(self.speak_response)
        self.input_fields_stack.addWidget(self.speaking_widget)
        
        # 3. business_mail container
        self.mail_widget = QWidget()
        mail_layout = QVBoxLayout(self.mail_widget)
        self.mail_subject = QLineEdit()
        self.mail_subject.setPlaceholderText("Tiêu đề email (Subject)")
        self.mail_opening = QPlainTextEdit()
        self.mail_opening.setPlaceholderText("Lời chào & mở đầu (Opening)")
        self.mail_opening.setMaximumHeight(60)
        self.mail_context = QPlainTextEdit()
        self.mail_context.setPlaceholderText("Ngữ cảnh / Nội dung chi tiết (Context)")
        self.mail_context.setMaximumHeight(80)
        self.mail_request = QPlainTextEdit()
        self.mail_request.setPlaceholderText("Yêu cầu / Hành động cần thiết (Request/Action)")
        self.mail_request.setMaximumHeight(80)
        self.mail_deadline = QLineEdit()
        self.mail_deadline.setPlaceholderText("Hạn chót phản hồi (Deadline)")
        self.mail_closing = QPlainTextEdit()
        self.mail_closing.setPlaceholderText("Lời kết (Closing)")
        self.mail_closing.setMaximumHeight(60)
        
        mail_layout.addWidget(QLabel("<b>Tiêu đề (Subject):</b>"))
        mail_layout.addWidget(self.mail_subject)
        mail_layout.addWidget(QLabel("<b>Mở đầu (Opening):</b>"))
        mail_layout.addWidget(self.mail_opening)
        mail_layout.addWidget(QLabel("<b>Bối cảnh (Context):</b>"))
        mail_layout.addWidget(self.mail_context)
        mail_layout.addWidget(QLabel("<b>Yêu cầu hành động (Request/Action):</b>"))
        mail_layout.addWidget(self.mail_request)
        mail_layout.addWidget(QLabel("<b>Hạn chót (Deadline):</b>"))
        mail_layout.addWidget(self.mail_deadline)
        mail_layout.addWidget(QLabel("<b>Lời kết (Closing):</b>"))
        mail_layout.addWidget(self.mail_closing)
        self.input_fields_stack.addWidget(self.mail_widget)
        
        # 4. document_reading container
        self.reading_widget = QWidget()
        reading_layout = QVBoxLayout(self.reading_widget)
        self.doc_summary = QPlainTextEdit()
        self.doc_summary.setPlaceholderText("Tóm tắt tài liệu (Summary)")
        self.doc_summary.setMaximumHeight(60)
        self.doc_actions = QPlainTextEdit()
        self.doc_actions.setPlaceholderText("Các hành động cần làm (Action Items)")
        self.doc_actions.setMaximumHeight(60)
        self.doc_risks = QPlainTextEdit()
        self.doc_risks.setPlaceholderText("Các rủi ro / Điểm cần lưu ý (Risks)")
        self.doc_risks.setMaximumHeight(60)
        self.doc_terms = QPlainTextEdit()
        self.doc_terms.setPlaceholderText("Thuật ngữ kinh doanh chưa rõ (Unknown business terms)")
        self.doc_terms.setMaximumHeight(60)
        
        reading_layout.addWidget(QLabel("<b>Tóm tắt tài liệu:</b>"))
        reading_layout.addWidget(self.doc_summary)
        reading_layout.addWidget(QLabel("<b>Action Items:</b>"))
        reading_layout.addWidget(self.doc_actions)
        reading_layout.addWidget(QLabel("<b>Rủi ro tiềm ẩn:</b>"))
        reading_layout.addWidget(self.doc_risks)
        reading_layout.addWidget(QLabel("<b>Thuật ngữ chuyên ngành/chưa rõ:</b>"))
        reading_layout.addWidget(self.doc_terms)
        self.input_fields_stack.addWidget(self.reading_widget)
        
        # 5. keigo_nuance container
        self.keigo_widget = QWidget()
        keigo_layout = QVBoxLayout(self.keigo_widget)
        self.keigo_rewritten = QPlainTextEdit()
        self.keigo_rewritten.setPlaceholderText("Viết lại câu tiếng Nhật tự nhiên hơn...")
        self.keigo_explanation = QPlainTextEdit()
        self.keigo_explanation.setPlaceholderText("Giải thích vì sao câu cũ chưa tự nhiên theo góc nhìn của người Nhật...")
        
        keigo_layout.addWidget(QLabel("<b>Câu tiếng Nhật tự nhiên (Rewritten):</b>"))
        keigo_layout.addWidget(self.keigo_rewritten)
        keigo_layout.addWidget(QLabel("<b>Lý do câu cũ chưa ổn (Explanation):</b>"))
        keigo_layout.addWidget(self.keigo_explanation)
        self.input_fields_stack.addWidget(self.keigo_widget)
        
        # 6. final_boss container
        self.boss_widget = QWidget()
        boss_layout = QVBoxLayout(self.boss_widget)
        self.boss_steps_stack = QStackedWidget()
        boss_layout.addWidget(self.boss_steps_stack)
        
        # Step 1
        self.boss_step1_page = QWidget()
        step1_layout = QVBoxLayout(self.boss_step1_page)
        self.boss_step1_lbl = QLabel()
        self.boss_step1_lbl.setWordWrap(True)
        self.boss_notes = QPlainTextEdit()
        self.boss_notes.setPlaceholderText("Ghi chú / Tóm tắt tài liệu chuẩn bị...")
        self.boss_next_btn1 = QPushButton("Tiếp theo: Chất vấn cuộc họp ➡️")
        self.boss_next_btn1.clicked.connect(lambda: self.boss_steps_stack.setCurrentIndex(1))
        step1_layout.addWidget(QLabel("<h3>Bước 1: Đọc tài liệu chuẩn bị (Pre-material)</h3>"))
        step1_layout.addWidget(self.boss_step1_lbl)
        step1_layout.addWidget(QLabel("<b>Ghi chú của bạn:</b>"))
        step1_layout.addWidget(self.boss_notes)
        step1_layout.addWidget(self.boss_next_btn1)
        self.boss_steps_stack.addWidget(self.boss_step1_page)
        
        # Step 2
        self.boss_step2_page = QWidget()
        step2_layout = QVBoxLayout(self.boss_step2_page)
        self.boss_step2_lbl = QLabel()
        self.boss_step2_lbl.setWordWrap(True)
        self.boss_speech = QPlainTextEdit()
        self.boss_speech.setPlaceholderText("Nhập câu phát biểu phản hồi chất vấn...")
        step2_nav = QHBoxLayout()
        self.boss_back_btn1 = QPushButton("⬅️ Quay lại")
        self.boss_back_btn1.clicked.connect(lambda: self.boss_steps_stack.setCurrentIndex(0))
        self.boss_next_btn2 = QPushButton("Tiếp theo: Viết email follow-up ➡️")
        self.boss_next_btn2.clicked.connect(lambda: self.boss_steps_stack.setCurrentIndex(2))
        step2_nav.addWidget(self.boss_back_btn1)
        step2_nav.addWidget(self.boss_next_btn2)
        step2_layout.addWidget(QLabel("<h3>Bước 2: Trả lời chất vấn áp lực (Pressure Meeting Question)</h3>"))
        step2_layout.addWidget(self.boss_step2_lbl)
        step2_layout.addWidget(QLabel("<b>Phát biểu tiếng Nhật của bạn:</b>"))
        step2_layout.addWidget(self.boss_speech)
        step2_layout.addLayout(step2_nav)
        self.boss_steps_stack.addWidget(self.boss_step2_page)
        
        # Step 3
        self.boss_step3_page = QWidget()
        step3_layout = QVBoxLayout(self.boss_step3_page)
        self.boss_step3_lbl = QLabel()
        self.boss_step3_lbl.setWordWrap(True)
        self.boss_email = QPlainTextEdit()
        self.boss_email.setPlaceholderText("Soạn email follow-up gửi đối tác...")
        step3_nav = QHBoxLayout()
        self.boss_back_btn2 = QPushButton("⬅️ Quay lại")
        self.boss_back_btn2.clicked.connect(lambda: self.boss_steps_stack.setCurrentIndex(1))
        step3_nav.addWidget(self.boss_back_btn2)
        step3_layout.addWidget(QLabel("<h3>Bước 3: Viết email follow-up</h3>"))
        step3_layout.addWidget(self.boss_step3_lbl)
        step3_layout.addWidget(QLabel("<b>Nội dung email tiếng Nhật:</b>"))
        step3_layout.addWidget(self.boss_email)
        step3_layout.addLayout(step3_nav)
        self.boss_steps_stack.addWidget(self.boss_step3_page)
        
        self.input_fields_stack.addWidget(self.boss_widget)
        
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
        self.boss_steps_stack.currentChanged.connect(self._on_boss_step_changed)

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
        for gate_id, _ in self.GATES:
            if gate_id == "final_boss":
                continue
            scores = self.scores_by_gate.get(gate_id, [])
            if scores:
                total_score += sum(scores)
                total_drills += len(scores)
        overall_avg = total_score / total_drills if total_drills > 0 else 0
        return total_drills >= 5 and overall_avg >= 70

    def _calculate_dashboard_metrics(self) -> Dict[str, Any]:
        total_score = 0
        total_drills = 0
        gate_averages = {}
        weakest_gate = None
        min_score = 100
        
        for gate_id, _ in self.GATES:
            if gate_id == "final_boss":
                continue
            scores = self.scores_by_gate.get(gate_id, [])
            if scores:
                avg = sum(scores) / len(scores)
                gate_averages[gate_id] = avg
                total_score += sum(scores)
                total_drills += len(scores)
                if avg < min_score:
                    min_score = avg
                    weakest_gate = gate_id
            else:
                gate_averages[gate_id] = 0.0

        overall_avg = total_score / total_drills if total_drills > 0 else 0.0

        # Include boss scores in total drills/overall avg if any
        boss_scores = self.scores_by_gate.get("final_boss", [])
        if boss_scores:
            total_score += sum(boss_scores)
            total_drills += len(boss_scores)
            overall_avg = total_score / total_drills

        # Calculate Level
        if total_drills == 0:
            level = "Chưa bắt đầu"
        elif overall_avg >= 85:
            level = "Chuyên gia (N1+)"
        elif overall_avg >= 70:
            level = "Trung cấp (N2)"
        else:
            level = "Học việc (N3)"

        # Weakest gate display name
        weakest_name = "Chưa rõ"
        if weakest_gate:
            weakest_name = next((name for gid, name in self.GATES if gid == weakest_gate), weakest_gate)

        # Get top 3 weaknesses
        weakness_counts = self.ai_service.memory.data.get("weakness_counts", {})
        sorted_weaknesses = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)
        top_3 = [f"{tag} ({count} lần)" for tag, count in sorted_weaknesses[:3]]
        top_3_str = ", ".join(top_3) if top_3 else "Không có lỗi lặp lại"

        # Today's task
        attempts = self.ai_service.memory.data.get("attempts", [])
        if attempts and attempts[-1].get("next_drill"):
            recommended_drill = attempts[-1]["next_drill"]
        else:
            recommended_drill = "meeting_listening"

        recommended_name = next((name for gid, name in self.GATES if gid == recommended_drill), recommended_drill)
        today_task = f"Luyện tập kỹ năng: {recommended_name}"

        return {
            "level": level,
            "total_drills": total_drills,
            "overall_avg": overall_avg,
            "gate_averages": gate_averages,
            "weakest_gate": weakest_name,
            "top_3_weaknesses": top_3_str,
            "today_task": today_task,
            "can_unlock_boss": self._is_final_boss_unlocked()
        }

    def _refresh_dashboard(self):
        metrics = self._calculate_dashboard_metrics()
        
        # Build gate averages string
        gate_averages_str = ""
        for gate_id, gate_name in self.GATES:
            if gate_id == "final_boss":
                continue
            avg = metrics["gate_averages"].get(gate_id, 0.0)
            avg_display = f"{avg:.1f}/100" if avg > 0 else "Chưa làm"
            gate_averages_str += f"📍 <b>{gate_name}:</b> {avg_display}<br/>"
            
        stats_html = f"""
        <div style="background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 5px; width: 45%;"><b>⭐ Cấp độ học tập:</b></td>
                    <td style="padding: 5px;"><span style="background-color: {ThemeColors.PRIMARY}; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{metrics["level"]}</span></td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>📝 Tổng số bài đã hoàn thành:</b></td>
                    <td style="padding: 5px; font-weight: bold;">{metrics["total_drills"]} bài</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>📈 Điểm trung bình tổng:</b></td>
                    <td style="padding: 5px; font-weight: bold; color: {'#2e7d32' if metrics["overall_avg"] >= 70 else '#c62828'};">{metrics["overall_avg"]:.1f} / 100</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>⚠️ Cổng yếu nhất:</b></td>
                    <td style="padding: 5px; font-weight: bold; color: #f57f17;">{metrics["weakest_gate"]}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>🚨 3 Lỗi lặp lại nhiều nhất:</b></td>
                    <td style="padding: 5px; font-style: italic;">{metrics["top_3_weaknesses"]}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><b>📅 Nhiệm vụ hôm nay:</b></td>
                    <td style="padding: 5px; font-weight: bold; color: {ThemeColors.PRIMARY};">{metrics["today_task"]}</td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #f9f9f9; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
            <h4 style="margin-top: 0; border-bottom: 1px solid #ddd; padding-bottom: 5px;">📊 Điểm trung bình từng cổng:</h4>
            {gate_averages_str}
        </div>
        
        <div style="background-color: #fffde7; border: 1px solid #fff59d; border-radius: 8px; padding: 15px;">
            <b>🚪 Trạng thái mở khóa Final Boss:</b><br/>
            {'✅ Đã mở khóa thành công!' if metrics["can_unlock_boss"] else '❌ Đang khóa (Cần hoàn thành ít nhất 5 bài và điểm TB tất cả đạt >= 70đ)'}
        </div>
        """
        self.stats_label.setText(stats_html)
        
        # Unlock Final Boss
        boss_btn = self.gate_buttons["final_boss"]
        boss_btn.setEnabled(metrics["can_unlock_boss"])
        if metrics["can_unlock_boss"]:
            boss_btn.setText("Final Boss họp Nhật (ĐÃ MỞ KHÓA)")
            boss_btn.setStyleSheet(f"background-color: {ThemeColors.SUCCESS}; color: white; font-weight: bold;")
        else:
            boss_btn.setText("Final Boss họp Nhật (CHƯA MỞ KHÓA - Cần TB 70đ & 5 bài)")
            boss_btn.setStyleSheet("")

    def _get_boss_steps(self, scenario: Dict[str, Any]) -> Dict[str, str]:
        scid = scenario.get("scenario_id", "")
        if scid == "boss_1":
            return {
                "step1_material": "TÀI LIỆU CHUẨN BỊ (Pre-material):\nBáo cáo sơ bộ về sự cố sập server phân hệ thanh toán (Payment Server Outage).\n- Thời gian xảy ra: 14:05 JST\n- Triệu chứng: Toàn bộ API thanh toán trả về lỗi 502 Bad Gateway.\n- Tác động: Khoảng 1,200 người dùng không thể hoàn tất giao dịch.\n- Biện pháp tạm thời: Chuyển hướng traffic sang server backup nhưng hiệu năng bị giảm 50%.",
                "step2_question": "CÂU HỎI CHẤT VẤN TRONG CUỘC HỌP (Pressure Meeting Question):\nTrụ sở chính Nhật Bản (HQ Department Head) chất vấn:\n「今回のシステム障害について、発生原因と暫定対応の状況、そして本社会社への具体的な支援要請内容を説明してください。」\n(Hãy trình bày nguyên nhân xảy ra sự cố, trạng thái khắc phục tạm thời và yêu cầu hỗ trợ cụ thể với trụ sở chính)",
                "step3_email": "EMAIL FOLLOW-UP:\nSau cuộc họp khẩn cấp, hãy viết email báo cáo chính thức gửi cho HQ Department Head để tóm tắt các điểm đã thống nhất và xác nhận hành động tiếp theo."
            }
        elif scid == "boss_2":
            return {
                "step1_material": "TÀI LIỆU CHUẨN BỊ (Pre-material):\nBáo cáo giao sai lô hàng (Wrong Batch Delivery).\n- Sản phẩm: Linh kiện cơ khí mã hiệu JK-900 (Thực tế đã giao nhầm JK-800).\n- Khách hàng: Công ty Toyota Tsusho (Đối tác VIP).\n- Hậu quả: Dây chuyền lắp ráp của khách hàng có nguy cơ bị dừng vào ngày mai nếu không có linh kiện JK-900 thay thế.",
                "step2_question": "CÂU HỎI CHẤT VẤN TRONG CUỘC HỌP (Pressure Meeting Question):\nKhách hàng VIP chất vấn gay gắt:\n「納品された部品の型番が異なっているため、このままでは明日のライン稼働が止まってしまいます。どのような経緯でこのミスが発生し、いつまでに正しい部品を届けてもらえるのでしょうか？」\n(Tại sao lỗi này lại xảy ra và khi nào các anh mới giao đúng linh kiện JK-900 cho chúng tôi?)",
                "step3_email": "EMAIL FOLLOW-UP:\nSau cuộc họp xin lỗi khách hàng, hãy viết email xin lỗi trang trọng gửi kèm biên bản sự việc và cam kết lịch trình giao lại hàng chính xác."
            }
        elif scid == "boss_3":
            return {
                "step1_material": "TÀI LIỆU CHUẨN BỊ (Pre-material):\nYêu cầu phát sinh từ phía PM người Nhật (Scope Creep Notification).\n- Yêu cầu mới: Bổ sung tính năng phân tích biểu đồ real-time cho dashboard.\n- Hạn chót: Vẫn giữ nguyên là cuối tháng này (không lùi lịch).\n- Đánh giá của dev team: Cần thêm ít nhất 80 man-hours (10 ngày công) để thực hiện an toàn, nếu ép làm sẽ gây rủi ro lớn về chất lượng.",
                "step2_question": "CÂU HỎI CHẤT VẤN TRONG CUỘC HỌP (Pressure Meeting Question):\nPM người Nhật thuyết phục:\n「クライアントからの強い要望なので、どうしてもこの機能を今月末のリリースに入れたいです。開発メンバーに残業してもらうなどして、なんとか対応できませんか？」\n(Yêu cầu của khách hàng rất gấp, các anh tăng ca làm thêm để kịp tiến độ cuối tháng này được không?)",
                "step3_email": "EMAIL FOLLOW-UP:\nSau khi thương lượng từ chối lịch trình phi thực tế trong cuộc họp, hãy viết email tóm tắt lại các giải pháp đề xuất thay thế (ví dụ: làm MVP đơn giản hơn hoặc chia phase 2) để PM gửi cho khách hàng."
            }
        else:
            return {
                "step1_material": f"TÀI LIỆU CHUẨN BỊ:\n{scenario.get('business_context', '')}",
                "step2_question": f"CÂU HỎI CHẤT VẤN:\n{scenario.get('prompt_vi', '')}",
                "step3_email": "EMAIL FOLLOW-UP:\nHãy viết email theo dõi và tóm tắt cuộc họp dựa trên giải pháp đã thảo luận."
            }

    def _on_boss_step_changed(self, index: int):
        is_step3 = (index == 2)
        self.submit_btn.setEnabled(is_step3)
        if is_step3:
            self.submit_btn.setText("Gửi đáp án Final Boss")
        else:
            self.submit_btn.setText("Hãy hoàn thành các bước trước")

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
            
        # Form field configuration
        if gate_id == "meeting_listening":
            self.input_fields_stack.setCurrentIndex(1)
            self.listen_topic.clear()
            self.listen_decision.clear()
            self.listen_issue.clear()
            self.listen_pic.clear()
            self.listen_deadline.clear()
            self.listen_risk.clear()
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Gửi đáp án")
        elif gate_id == "meeting_speaking":
            self.input_fields_stack.setCurrentIndex(2)
            self.speak_response.clear()
            self.speak_duration.setCurrentIndex(0)
            self.speak_pattern.setCurrentIndex(0)
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Gửi đáp án")
        elif gate_id == "business_mail":
            self.input_fields_stack.setCurrentIndex(3)
            self.mail_subject.clear()
            self.mail_opening.clear()
            self.mail_context.clear()
            self.mail_request.clear()
            self.mail_deadline.clear()
            self.mail_closing.clear()
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Gửi đáp án")
        elif gate_id == "document_reading":
            self.input_fields_stack.setCurrentIndex(4)
            self.doc_summary.clear()
            self.doc_actions.clear()
            self.doc_risks.clear()
            self.doc_terms.clear()
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Gửi đáp án")
        elif gate_id == "keigo_nuance":
            self.input_fields_stack.setCurrentIndex(5)
            self.keigo_rewritten.clear()
            self.keigo_explanation.clear()
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Gửi đáp án")
        elif gate_id == "final_boss":
            self.input_fields_stack.setCurrentIndex(6)
            self.boss_steps_stack.setCurrentIndex(0)
            self.boss_notes.clear()
            self.boss_speech.clear()
            self.boss_email.clear()
            
            steps = self._get_boss_steps(self.current_scenario)
            self.boss_step1_lbl.setText(steps["step1_material"])
            self.boss_step2_lbl.setText(steps["step2_question"])
            self.boss_step3_lbl.setText(steps["step3_email"])
            self._on_boss_step_changed(0)
        else:
            self.input_fields_stack.setCurrentIndex(0)
            self.answer_edit.clear()
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Gửi đáp án")

        self.stacked_widget.setCurrentIndex(1)

    def _submit_answer(self):
        gate = self.current_scenario.get("gate")
        
        # Package answer based on gate inputs
        if gate == "meeting_listening":
            topic = self.listen_topic.toPlainText().strip()
            decision = self.listen_decision.toPlainText().strip()
            issue = self.listen_issue.toPlainText().strip()
            pic = self.listen_pic.toPlainText().strip()
            deadline = self.listen_deadline.toPlainText().strip()
            risk = self.listen_risk.toPlainText().strip()
            
            if any([topic, decision, issue, pic, deadline, risk]):
                answer = f"Topic: {topic}\nDecision: {decision}\nIssue: {issue}\nPIC: {pic}\nDeadline: {deadline}\nRisk: {risk}"
            else:
                answer = self.answer_edit.toPlainText().strip()
                
        elif gate == "meeting_speaking":
            duration = self.speak_duration.currentText()
            pattern = self.speak_pattern.currentText()
            resp = self.speak_response.toPlainText().strip()
            
            if resp:
                answer = f"Duration: {duration}\nPattern: {pattern}\nSpeech: {resp}"
            else:
                answer = self.answer_edit.toPlainText().strip()
                
        elif gate == "business_mail":
            subject = self.mail_subject.text().strip()
            opening = self.mail_opening.toPlainText().strip()
            context = self.mail_context.toPlainText().strip()
            req_act = self.mail_request.toPlainText().strip()
            deadline = self.mail_deadline.text().strip()
            closing = self.mail_closing.toPlainText().strip()
            
            if any([subject, opening, context, req_act, deadline, closing]):
                answer = f"Subject: {subject}\nOpening: {opening}\nContext: {context}\nRequest: {req_act}\nDeadline: {deadline}\nClosing: {closing}"
            else:
                answer = self.answer_edit.toPlainText().strip()
                
        elif gate == "document_reading":
            summary = self.doc_summary.toPlainText().strip()
            actions = self.doc_actions.toPlainText().strip()
            risks = self.doc_risks.toPlainText().strip()
            terms = self.doc_terms.toPlainText().strip()
            
            if any([summary, actions, risks, terms]):
                answer = f"Summary: {summary}\nAction Items: {actions}\nRisks: {risks}\nUnknown Terms: {terms}"
            else:
                answer = self.answer_edit.toPlainText().strip()
                
        elif gate == "keigo_nuance":
            rewritten = self.keigo_rewritten.toPlainText().strip()
            explanation = self.keigo_explanation.toPlainText().strip()
            
            if any([rewritten, explanation]):
                answer = f"Rewritten natural Japanese: {rewritten}\nExplanation of unnaturalness: {explanation}"
            else:
                answer = self.answer_edit.toPlainText().strip()
                
        elif gate == "final_boss":
            notes = self.boss_notes.toPlainText().strip()
            speech = self.boss_speech.toPlainText().strip()
            email = self.boss_email.toPlainText().strip()
            
            if any([notes, speech, email]):
                answer = f"Step 1 Reading Notes: {notes}\nStep 2 Meeting Speech: {speech}\nStep 3 Follow-up Email: {email}"
            else:
                answer = self.answer_edit.toPlainText().strip()
        else:
            answer = self.answer_edit.toPlainText().strip()

        if not answer:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập câu trả lời.")
            return
            
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Đang chấm điểm...")
        
        try:
            is_boss = gate == "final_boss"
            feedback = self.ai_service.grade_answer(
                scenario=self.current_scenario, 
                user_answer=answer, 
                boss_fight=is_boss
            )
            self._show_report(feedback)
            
            # Save score
            score = feedback.get("score_total", 0)
            self.scores_by_gate[gate].append(score)
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi chấm điểm", str(e))
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("Gửi đáp án")

    def _show_report(self, feedback: Dict[str, Any]):
        scores_html = ""
        scores = feedback.get("scores", {})
        if isinstance(scores, dict) and scores:
            scores_html = "<ul>"
            for criterion, val in scores.items():
                scores_html += f"<li><b>{criterion.capitalize()}:</b> {val}</li>"
            scores_html += "</ul>"
        else:
            scores_html = "<i>Không có dữ liệu chi tiết</i>"

        crit_errors = feedback.get("critical_errors", [])
        crit_html = ""
        if crit_errors:
            crit_html = "<ul>"
            for err in crit_errors:
                crit_html += f"<li style='color: #c62828;'><b>{err}</b></li>"
            crit_html += "</ul>"
        else:
            crit_html = "<i>Không phát hiện lỗi chí mạng</i>"

        unnatural = feedback.get("unnatural_phrases", [])
        unnat_html = ""
        if unnatural:
            unnat_html = "<ul>"
            for phrase in unnatural:
                unnat_html += f"<li><span style='color: #f57f17;'>{phrase}</span></li>"
            unnat_html += "</ul>"
        else:
            unnat_html = "<i>Không có câu chưa tự nhiên</i>"

        tags = feedback.get("weakness_tags", [])
        tags_str = ", ".join(tags) if tags else "None"

        srs_items = feedback.get("srs_items", [])
        srs_html = ""
        if srs_items:
            srs_html = "<ul>"
            for item in srs_items:
                srs_html += f"<li>{item.get('prompt', '')} (Ôn lại sau {item.get('interval_days', 1)} ngày)</li>"
            srs_html += "</ul>"
        else:
            srs_html = "<i>Không có mục SRS mới</i>"

        html = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.5; color: {ThemeColors.TEXT_PRIMARY};">
            <h2 style="color: {ThemeColors.PRIMARY}; margin-bottom: 5px;">🔥 KẾT QUẢ CHẤM ĐIỂM</h2>
            <h1 style="font-size: 36px; margin: 0; color: {'#2e7d32' if feedback.get('score_total', 0) >= 70 else '#c62828'};">
                {feedback.get('score_total', 0)} / 100
            </h1>
            <hr style="border: 0; border-top: 1px solid #ccc; margin: 15px 0;"/>
            
            <h3>📊 Điểm theo tiêu chí:</h3>
            {scores_html}
            
            <h3 style="color: #c62828;">🚨 Lỗi chí mạng (Critical Errors):</h3>
            {crit_html}
            
            <h3 style="color: #f57f17;">⚠️ Câu chưa tự nhiên:</h3>
            {unnat_html}
            
            <h3>💡 Bản tiếng Nhật tốt hơn:</h3>
            <pre style="background-color: #f5f5f5; padding: 10px; border-left: 4px solid #2e7d32; font-family: Courier, monospace; white-space: pre-wrap;">{feedback.get('better_version', '')}</pre>
            
            <h3>🧐 Giải thích chi tiết (Vì sao người Nhật thấy câu cũ chưa ổn):</h3>
            <p>{feedback.get('vietnamese_explanation', 'Chưa có giải thích')}</p>
            
            <h3>🏷️ Thẻ điểm yếu:</h3>
            <p><code>{tags_str}</code></p>
            
            <h3>📅 Bài luyện tiếp theo kiến nghị:</h3>
            <p><b>{feedback.get('next_drill', 'None')}</b></p>
            
            <h3>🔁 Mục cần ôn lại bằng SRS:</h3>
            {srs_html}
            
            <hr style="border: 0; border-top: 1px solid #ccc; margin: 15px 0;"/>
            <h4 style="color: {ThemeColors.TEXT_SECONDARY}; margin-bottom: 5px;">⚙️ Metadata Router:</h4>
            <table style="font-size: 12px; color: {ThemeColors.TEXT_SECONDARY}; width: 100%;">
                <tr><td><b>Provider đã dùng:</b></td><td>{feedback.get('provider_used', 'N/A')}</td></tr>
                <tr><td><b>Phân hạng model (Tier):</b></td><td>Tier {feedback.get('provider_tier', 'N/A')}</td></tr>
                <tr><td><b>Cơ chế fallback hoạt động:</b></td><td>{'Có' if feedback.get('fallback_used') else 'Không'}</td></tr>
                <tr><td><b>Provider chấm điểm độc lập (Boss):</b></td><td>{feedback.get('judge_provider') or 'N/A'}</td></tr>
            </table>
        </div>
        """
        self.report_content.setText(html)
        self.stacked_widget.setCurrentIndex(2)
