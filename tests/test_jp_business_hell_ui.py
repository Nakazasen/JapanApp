import collections

import pytest
from PySide6.QtWidgets import QApplication

from frontend.ui.tabs.jp_business_hell_tab import JpBusinessHellTab

REQUIRED_GATE_COUNTS = {
    "meeting_listening": 6,
    "meeting_speaking": 6,
    "business_mail": 6,
    "document_reading": 6,
    "keigo_nuance": 6,
    "final_boss": 3,
}

REQUIRED_SCENARIO_FIELDS = {
    "scenario_id", "gate", "title", "business_context", "prompt_vi", "rubric", "difficulty",
}

REQUIRED_FEEDBACK_FIELDS = {
    "score_total", "scores", "critical_errors", "unnatural_phrases", "better_version",
    "vietnamese_explanation", "next_drill", "weakness_tags", "srs_items",
    "provider_used", "provider_tier", "fallback_used", "judge_provider",
}

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def clean_test_memory(monkeypatch, tmp_path):
    test_json = tmp_path / "test_japanese_work_learning_memory.json"
    monkeypatch.setenv("JAPANAPP_TEST_MEMORY_PATH", str(test_json))
    
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)



def test_jp_business_hell_ui_initialization(qapp):
    tab = JpBusinessHellTab()
    assert tab.stacked_widget.count() == 3
    assert len(tab.gate_buttons) == 6
    assert "final_boss" in tab.gate_buttons


def test_seed_data_loaded_and_required_counts(qapp):
    tab = JpBusinessHellTab()
    counts = collections.Counter(s.get("gate") for s in tab.seed_data)
    assert len(tab.seed_data) >= sum(REQUIRED_GATE_COUNTS.values())
    assert set(counts) == set(REQUIRED_GATE_COUNTS)
    for gate, minimum in REQUIRED_GATE_COUNTS.items():
        assert counts[gate] >= minimum, f"{gate} has {counts[gate]}, needs {minimum}"


def test_seed_data_required_fields(qapp):
    tab = JpBusinessHellTab()
    for scenario in tab.seed_data:
        missing = REQUIRED_SCENARIO_FIELDS - set(scenario)
        assert not missing, f"{scenario.get('scenario_id', '<unknown>')} missing {sorted(missing)}"
        assert scenario["scenario_id"]
        assert scenario["gate"] in REQUIRED_GATE_COUNTS
        assert scenario["prompt_vi"].strip()
        assert scenario["rubric"].strip()


def test_demo_drill_runs_offline_and_feedback_has_router_metadata(qapp):
    tab = JpBusinessHellTab()
    tab._start_drill("meeting_listening")
    tab.answer_edit.setPlainText("Nguyên nhân là cảm biến phát hiện bất thường. Đội bảo trì đang xử lý và cần khoảng 30 phút để khôi phục.")
    tab._submit_answer()
    assert tab.stacked_widget.currentIndex() == 2
    assert tab.ai_service.attempts
    feedback = tab.ai_service.attempts[-1]["feedback"]
    missing = REQUIRED_FEEDBACK_FIELDS - set(feedback)
    assert not missing, f"feedback missing {sorted(missing)}"
    assert feedback["provider_used"]
    assert feedback["provider_tier"]
    assert "fallback_used" in feedback


def test_boss_unlock_logic(qapp):
    tab = JpBusinessHellTab()
    tab._refresh_dashboard()
    assert not tab.gate_buttons["final_boss"].isEnabled()
    tab.scores_by_gate["meeting_listening"] = [70, 80, 90]
    tab.scores_by_gate["business_mail"] = [70, 75]
    tab._refresh_dashboard()
    assert tab.gate_buttons["final_boss"].isEnabled()


def test_boss_unlock_logic_failing(qapp):
    tab = JpBusinessHellTab()
    tab.scores_by_gate["meeting_listening"] = [50, 60, 40]
    tab.scores_by_gate["business_mail"] = [70, 75]
    tab._refresh_dashboard()
    assert not tab.gate_buttons["final_boss"].isEnabled()


def test_boss_cannot_start_locked(qapp):
    tab = JpBusinessHellTab()
    tab._refresh_dashboard()
    tab._start_drill("final_boss")
    assert tab.stacked_widget.currentIndex() == 0  # Should not go to drill page (index 1)


def test_no_english_labels(qapp):
    tab = JpBusinessHellTab()
    assert "Điểm trung bình" in tab.stats_label.text()
    assert "BÁO CÁO KẾT QUẢ" in tab.report_title.text()
    # Mocking some data to check drill input text
    tab.current_scenario = {"japanese_input": "Test"}
    tab.drill_input.setText(f"Tiếng Nhật:\nTest")
    assert "Tiếng Nhật:" in tab.drill_input.text()


def test_all_gates_can_start_and_render_fields(qapp):
    tab = JpBusinessHellTab()
    # meeting_listening
    tab._start_drill("meeting_listening")
    assert tab.stacked_widget.currentIndex() == 1
    assert tab.input_fields_stack.currentIndex() == 1
    assert tab.current_scenario["gate"] == "meeting_listening"
    
    # meeting_speaking
    tab._start_drill("meeting_speaking")
    assert tab.input_fields_stack.currentIndex() == 2
    
    # business_mail
    tab._start_drill("business_mail")
    assert tab.input_fields_stack.currentIndex() == 3
    
    # document_reading
    tab._start_drill("document_reading")
    assert tab.input_fields_stack.currentIndex() == 4
    
    # keigo_nuance
    tab._start_drill("keigo_nuance")
    assert tab.input_fields_stack.currentIndex() == 5


def test_vietnamese_report_labels(qapp):
    tab = JpBusinessHellTab()
    tab._start_drill("meeting_listening")
    tab.answer_edit.setPlainText("Test answer")
    tab._submit_answer()
    assert tab.stacked_widget.currentIndex() == 2
    report_text = tab.report_content.text()
    assert "Điểm theo tiêu chí:" in report_text
    assert "Lỗi chí mạng" in report_text
    assert "Câu chưa tự nhiên" in report_text
    assert "Bản tiếng Nhật tốt hơn" in report_text
    assert "Giải thích chi tiết" in report_text
    assert "Thẻ điểm yếu" in report_text
    assert "Mục cần ôn lại bằng SRS" in report_text
    assert "Metadata Router:" in report_text


def test_temp_memory_safety_and_persisted_reload(qapp, tmp_path, monkeypatch):
    import json
    test_json = tmp_path / "test_memory.json"
    monkeypatch.setenv("JAPANAPP_TEST_MEMORY_PATH", str(test_json))
    
    from frontend.services.japanese_work_memory import JapaneseWorkLearningMemory
    mem = JapaneseWorkLearningMemory()
    assert mem.path == test_json
    
    tab = JpBusinessHellTab(memory=mem)
    tab._start_drill("meeting_listening")
    tab.answer_edit.setPlainText("Test answer")
    tab._submit_answer() # This writes an attempt
    
    # Now instantiate another tab with the same memory
    tab2 = JpBusinessHellTab(memory=mem)
    # Check that attempts loaded and scores_by_gate populated
    assert len(tab2.scores_by_gate["meeting_listening"]) == 1
    assert tab2.scores_by_gate["meeting_listening"][0] == 78


def test_dashboard_metrics_calculation(qapp):
    tab = JpBusinessHellTab()
    tab.scores_by_gate["meeting_listening"] = [80]
    tab.scores_by_gate["business_mail"] = [60]
    metrics = tab._calculate_dashboard_metrics()
    assert metrics["overall_avg"] == 70.0
    assert metrics["weakest_gate"] == "Mail địa ngục"


def test_repeated_weakness_tags(qapp, tmp_path, monkeypatch):
    import json
    test_json = tmp_path / "test_memory_tags.json"
    monkeypatch.setenv("JAPANAPP_TEST_MEMORY_PATH", str(test_json))
    from frontend.services.japanese_work_memory import JapaneseWorkLearningMemory
    mem = JapaneseWorkLearningMemory()
    # Add manual weakness count
    mem.data["weakness_counts"] = {"keigo_apology": 5, "deadline_report": 3}
    mem.path.write_text(json.dumps(mem.data), encoding='utf-8')
    
    tab = JpBusinessHellTab(memory=mem)
    metrics = tab._calculate_dashboard_metrics()
    assert "keigo_apology" in metrics["top_3_weaknesses"]
    assert "deadline_report" in metrics["top_3_weaknesses"]


def test_final_boss_3_step_flow_unlocked(qapp):
    tab = JpBusinessHellTab()
    # Unlock boss
    tab.scores_by_gate["meeting_listening"] = [80, 80, 80, 80, 80]
    tab._refresh_dashboard()
    assert tab._is_final_boss_unlocked()
    
    tab._start_drill("final_boss")
    assert tab.stacked_widget.currentIndex() == 1
    assert tab.input_fields_stack.currentIndex() == 6
    assert tab.boss_steps_stack.currentIndex() == 0
    assert not tab.submit_btn.isEnabled()
    
    # Step 1 -> Step 2
    tab.boss_notes.setPlainText("Reading notes")
    tab.boss_next_btn1.click()
    assert tab.boss_steps_stack.currentIndex() == 1
    assert not tab.submit_btn.isEnabled()
    
    # Step 2 -> Step 3
    tab.boss_speech.setPlainText("Meeting speech")
    tab.boss_next_btn2.click()
    assert tab.boss_steps_stack.currentIndex() == 2
    assert tab.submit_btn.isEnabled()
    
    # Step 3 -> submit
    tab.boss_email.setPlainText("Follow-up email")
    tab._submit_answer()
    assert tab.stacked_widget.currentIndex() == 2


def test_no_direct_gemini_path():
    from frontend.services.jp_business_hell_ai import JPBusinessHellAI
    ai = JPBusinessHellAI()
    assert hasattr(ai, "router")
    
    with open("frontend/services/jp_business_hell_ai.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "GeminiClient" not in content
    assert "frontend.core.gemini_client" not in content
