"""Deterministic offline provider for demo drills and tests."""
from __future__ import annotations
import json
from frontend.models.ai_provider import AITaskType
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_providers.base import AIProviderAdapter, ProviderResponse

class OfflineDemoProvider(AIProviderAdapter):
    def generate(self, request: AITaskRequest) -> ProviderResponse:
        task = str(request.task_type.value if hasattr(request.task_type, 'value') else request.task_type)
        if task in {AITaskType.SCENARIO_GENERATION.value, AITaskType.DRILL_VARIATION.value, AITaskType.MEETING_ROLEPLAY.value}:
            data = {
                "scenario_id": "demo-ho-ren-so-001",
                "title": "Báo cáo trễ hạn cho trưởng nhóm",
                "business_context": "deadline_report",
                "difficulty": "N2-business",
                "prompt_vi": "Bạn phải báo cáo rằng tài liệu sẽ trễ 1 ngày và đề xuất cách xử lý.",
                "expected_style": "teineigo + khiêm tốn + phương án khắc phục",
                "rubric": {"keigo": 30, "clarity": 25, "accountability": 25, "next_action": 20},
            }
            return ProviderResponse(True, json.dumps(data, ensure_ascii=False), data, self.default_model)
        data = {
            "score_total": 78,
            "scores": {"keigo": 22, "clarity": 20, "accountability": 18, "next_action": 18},
            "critical_errors": [],
            "unnatural_phrases": ["ちょっと遅れます"],
            "better_version": "申し訳ございません。資料の完成が1日遅れる見込みです。本日中に不足点を整理し、明日午前中に提出いたします。",
            "vietnamese_explanation": "Cần xin lỗi rõ, nói mức trễ cụ thể và đưa hành động khắc phục.",
            "next_drill": "deadline_recovery_mail",
            "weakness_tags": ["deadline_report", "keigo_apology", "next_action_clarity"],
        }
        return ProviderResponse(True, json.dumps(data, ensure_ascii=False), data, self.default_model)
