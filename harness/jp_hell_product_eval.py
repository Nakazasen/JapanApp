"""
Harness script to evaluate the Business Japanese Hell (Địa ngục tiếng Nhật) MVP.
"""
import collections
import sys
from pathlib import Path

import os
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

os.environ["JAPANAPP_USE_TEST_MEMORY"] = "1"
os.environ["JAPANAPP_USE_TEST_MEMORY_PATH"] = str(project_root / "data" / "ai" / "test_japanese_work_learning_memory.json")

import yaml
from PySide6.QtWidgets import QApplication
from frontend.ui.tabs.jp_business_hell_tab import JpBusinessHellTab
from harness.report_writer import write_report


def _validate_seed_data(tab: JpBusinessHellTab, config: dict, case: dict) -> tuple[bool, str]:
    required_counts = config.get("required_seed_counts", {})
    required_fields = set(config.get("required_scenario_fields", []))
    counts = collections.Counter(s.get("gate") for s in tab.seed_data)
    expected_total_min = case.get("expected_total_min", sum(required_counts.values()))

    if len(tab.seed_data) < expected_total_min:
        return False, f"Expected at least {expected_total_min} scenarios, found {len(tab.seed_data)}."
    if len(counts) != case.get("expected_gates", len(required_counts)):
        return False, f"Expected {case.get('expected_gates')} gates, found {len(counts)}: {dict(counts)}."
    for gate, minimum in required_counts.items():
        if counts.get(gate, 0) < minimum:
            return False, f"Gate {gate} has {counts.get(gate, 0)} scenarios, needs {minimum}."
    for scenario in tab.seed_data:
        missing = required_fields - set(scenario)
        if missing:
            return False, f"Scenario {scenario.get('scenario_id', '<unknown>')} missing fields: {sorted(missing)}."
        if scenario.get("gate") not in required_counts:
            return False, f"Scenario {scenario.get('scenario_id')} has unknown gate {scenario.get('gate')}."
    return True, ""


def run_eval():
    cases_path = project_root / "evals" / "jp_hell" / "product_cases.yaml"
    if not cases_path.exists():
        print(f"Error: Cases file not found at {cases_path}")
        return False

    with open(cases_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    app = QApplication.instance() or QApplication(sys.argv)
    results = []
    all_passed = True

    print(f"Running {config['name']}...\n")

    for case in config["cases"]:
        case_id = case["id"]
        action = case["action"]
        print(f"Evaluating {case_id}...")

        # Clean up test memory before each case to avoid state contamination
        test_mem_path = Path(os.environ["JAPANAPP_USE_TEST_MEMORY_PATH"])
        if test_mem_path.exists():
            try:
                test_mem_path.unlink()
            except Exception:
                pass

        tab = JpBusinessHellTab()
        passed = False
        error_msg = ""

        try:
            if action == "check_seed_data":
                passed, error_msg = _validate_seed_data(tab, config, case)

            elif action == "check_boss_lock":
                scores = case.get("simulate_scores", [])
                tab.scores_by_gate["meeting_listening"] = scores
                tab._refresh_dashboard()
                is_locked = not tab.gate_buttons["final_boss"].isEnabled()
                if is_locked == case.get("expected_locked"):
                    passed = True
                else:
                    error_msg = f"Expected locked={case.get('expected_locked')}, but was {is_locked}."

            elif action == "simulate_drill":
                passed = True
                for gate_id, _ in tab.GATES:
                    if gate_id == "final_boss":
                        # Unlock final boss first
                        tab.scores_by_gate["meeting_listening"] = [80, 80, 80, 80, 80]
                        tab._refresh_dashboard()
                    
                    tab._start_drill(gate_id)
                    
                    if gate_id == "final_boss":
                        # Simulate the 3-step boss interaction
                        tab.boss_notes.setPlainText("Step 1 pre-material notes text")
                        tab.boss_next_btn1.click()
                        tab.boss_speech.setPlainText("Step 2 speaking question response")
                        tab.boss_next_btn2.click()
                        tab.boss_email.setPlainText("Step 3 follow-up email response")
                    else:
                        tab.answer_edit.setPlainText(f"Offline response for {gate_id}")
                        
                    tab._submit_answer()
                    
                    if tab.stacked_widget.currentIndex() != 2 or not tab.ai_service.attempts:
                        passed = False
                        error_msg = f"Gate {gate_id} did not transition to report screen or no attempt was recorded."
                        break
                        
                    feedback = tab.ai_service.attempts[-1]["feedback"]
                    missing = [f for f in case["expected_feedback_fields"] if f not in feedback]
                    metadata_missing = [f for f in ["provider_used", "provider_tier", "fallback_used"] if f not in feedback]
                    report_text = tab.report_content.text()
                    
                    if missing:
                        passed = False
                        error_msg = f"Gate {gate_id} feedback missing fields: {missing}"
                        break
                    elif metadata_missing:
                        passed = False
                        error_msg = f"Gate {gate_id} missing router metadata: {metadata_missing}"
                        break
                    elif not feedback.get("provider_used") or not feedback.get("provider_tier"):
                        passed = False
                        error_msg = f"Gate {gate_id} router metadata values are empty."
                        break
                    elif "Điểm theo tiêu chí" not in report_text or "Lỗi chí mạng" not in report_text or "Câu chưa tự nhiên" not in report_text or "Bản tiếng Nhật tốt hơn" not in report_text or "Giải thích chi tiết" not in report_text or "Thẻ điểm yếu" not in report_text or "Mục cần ôn lại bằng SRS" not in report_text:
                        passed = False
                        error_msg = f"Gate {gate_id} report is missing required Vietnamese labels/fields."
                        break
            else:
                error_msg = f"Unknown action: {action}"

        except Exception as e:
            error_msg = str(e)

        if not passed:
            all_passed = False

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        if error_msg:
            print(f"  Error: {error_msg}")

        results.append({"case_id": case_id, "passed": passed, "error": error_msg})

    report = {"eval_name": config["name"], "all_passed": all_passed, "results": results}
    write_report("jp_hell_product_eval", report)
    return all_passed


if __name__ == "__main__":
    success = run_eval()
    sys.exit(0 if success else 1)
