"""Địa ngục tiếng Nhật AI training factory powered by provider router."""
from __future__ import annotations
from typing import Any
from frontend.models.ai_provider import AITaskType
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_router import AIRouter, get_ai_router
from frontend.services.japanese_work_memory import JapaneseWorkLearningMemory

REQUIRED_SCENARIO_FIELDS = {"scenario_id", "title", "business_context", "prompt_vi", "rubric"}

class JPBusinessHellAI:
    def __init__(self, router: AIRouter | None = None, memory: JapaneseWorkLearningMemory | None = None):
        self.router = router or get_ai_router()
        self.memory = memory or JapaneseWorkLearningMemory()
        self.attempts: list[dict[str, Any]] = []

    def generate_scenario(self, business_context: str = "deadline_report", difficulty: str = "N2-business", privacy_mode: str = "synthetic") -> dict[str, Any]:
        req=AITaskRequest(AITaskType.SCENARIO_GENERATION, "Generate a Business Japanese drill scenario", {"business_context": business_context, "difficulty": difficulty}, privacy_mode=privacy_mode, require_json=True)
        result=self.router.route(req)
        if not result.ok: raise RuntimeError(result.error_message or result.error_type)
        scenario=result.data
        self.validate_scenario_schema(scenario)
        scenario["provider_used"]=result.provider_used; scenario["provider_tier"]=result.provider_tier; scenario["fallback_used"]=result.fallback_used
        return scenario

    def validate_scenario_schema(self, scenario: dict[str, Any]) -> None:
        missing=REQUIRED_SCENARIO_FIELDS-set(scenario)
        if missing: raise ValueError(f"scenario missing fields: {sorted(missing)}")

    def grade_answer(self, scenario: dict[str, Any], user_answer: str, boss_fight: bool = False, privacy_mode: str = "redacted") -> dict[str, Any]:
        task=AITaskType.FINAL_BOSS_JUDGE if boss_fight else AITaskType.RUBRIC_GRADING
        req=AITaskRequest(task, "Grade Business Japanese answer as JSON", {"scenario": scenario, "answer": user_answer}, privacy_mode=privacy_mode, require_json=True, critical=boss_fight)
        grade=self.router.route(req)
        if not grade.ok and not boss_fight:
            req.task_type=AITaskType.JAPANESE_NUANCE_REVIEW
            grade=self.router.route(req)
        if not grade.ok: raise RuntimeError(grade.error_message or grade.error_type)
        feedback=grade.feedback_contract()
        if boss_fight:
            judge_req=AITaskRequest(AITaskType.FINAL_BOSS_JUDGE, "Judge final boss answer with independent reviewer", {"scenario": scenario, "answer": user_answer, "first_feedback": feedback}, privacy_mode=privacy_mode, require_json=True, critical=True)
            judge=self.router.route(judge_req)
            feedback["judge_provider"] = judge.provider_used if judge.ok else grade.provider_used
        else:
            feedback["judge_provider"] = ""
        feedback["provider_used"] = grade.provider_used
        feedback["provider_tier"] = grade.provider_tier
        feedback["fallback_used"] = grade.fallback_used
        self.attempts.append({"scenario_id": scenario.get('scenario_id'), "score_total": feedback['score_total'], "weakness_tags": feedback['weakness_tags'], "feedback": feedback})
        self.memory.update_from_feedback(scenario.get('business_context','unknown'), user_answer, feedback)
        feedback["srs_items"] = self.generate_srs_items(feedback["weakness_tags"])
        return feedback

    def generate_srs_items(self, weakness_tags: list[str]) -> list[dict[str, Any]]:
        return [{"tag": tag, "prompt": f"Review and drill: {tag}", "interval_days": 1} for tag in weakness_tags]
