# Địa ngục tiếng Nhật (日本語地獄) - Technical Design

## Architecture

The feature is built on top of the **AI Resource Layer**.

1. **UI Layer (`frontend/ui/tabs/jp_business_hell_tab.py`)**:
   - `QStackedWidget` manages 3 main states: Dashboard (Gates), Drill Screen, and Report Screen.
   - UI is integrated into the main application via `frontend/ui/main_window.py` and `frontend/config/menu_config.json`.
   - Distinct task fields are rendered dynamically based on the active gate.
   - Final Boss implements a nested 3-step wizard workflow (Pre-material Notes -> Meeting Question Speech -> Follow-up Email Response) before allowing submission.

2. **Service Layer (`frontend/services/jp_business_hell_ai.py`)**:
   - Acts as the orchestrator. It receives UI inputs and formats them into `AITaskRequest` objects.
   - The requests are sent to the `AIRouter`, which decides the optimal AI provider based on `task_routing_policy.yaml`.
   - The service integrates with `JapaneseWorkLearningMemory` to persist feedback and generate Spaced Repetition (SRS) items.

3. **Data Layer (`data/japanese/business_hell_seed.json`)**:
   - Seed data containing 33 MVP scenarios across all 6 gates.
   - Each scenario has a `scenario_id`, `gate`, `title`, `business_context`, `prompt_vi`, `rubric`, and `difficulty`.

## Boss Unlock Logic
- Computed dynamically in the UI Dashboard based on loaded learning memory.
- Unlocks the "Final Boss" gate only if `overall_avg >= 70` and `total_drills >= 5`.

## Safe Evaluation & Test Isolation
- Checking `PYTEST_CURRENT_TEST` or `JAPANAPP_USE_TEST_MEMORY` env variables on initialization redirects database persistence to `data/ai/test_japanese_work_learning_memory.json` to prevent real memory pollution.
- Harness script `harness/jp_hell_product_eval.py` simulates UI interactions without requiring API keys using `offline_provider` for safe, deterministic testing.
