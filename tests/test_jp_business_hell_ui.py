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
    assert "Điểm trung bình:" in tab.stats_label.text()
    assert "BÁO CÁO KẾT QUẢ" in tab.report_title.text()
    # Mocking some data to check drill input text
    tab.current_scenario = {"japanese_input": "Test"}
    tab.drill_input.setText(f"Tiếng Nhật:\nTest")
    assert "Tiếng Nhật:" in tab.drill_input.text()
