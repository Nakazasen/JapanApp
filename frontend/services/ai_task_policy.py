"""Task routing and model-tier policy for JapanApp AI Resource Layer."""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from frontend.models.ai_provider import AITaskType, ModelTier

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = ROOT / "data" / "ai" / "task_routing_policy.yaml"

def _tiny_yaml(text: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        # Fallback is intentionally small but enough for JapanApp defaults/tests.
        routing = {}
        for m in re.finditer(r"^  ([a-z_]+): \{tier: (\d+), providers: \[([^\]]*)\]([^}]*)\}", text, re.M):
            routing[m.group(1)] = {"tier": int(m.group(2)), "providers": [x.strip() for x in m.group(3).split(',') if x.strip()]}
            if "require_different_judge" in m.group(4): routing[m.group(1)]["require_different_judge"] = True
            if "language_drill_allowed: false" in m.group(4): routing[m.group(1)]["language_drill_allowed"] = False
        return {"routing": routing, "guards": {"forbid_tier4_for": ["scenario_generation", "drill_variation", "rubric_grading"], "development_tasks": ["code_generation", "architecture_review", "audit_review"]}}

class AITaskPolicy:
    def __init__(self, policy_path: Path | str = DEFAULT_POLICY_PATH):
        self.policy_path = Path(policy_path)
        self.policy = _tiny_yaml(self.policy_path.read_text(encoding='utf-8')) if self.policy_path.exists() else self._defaults()

    def _defaults(self) -> dict[str, Any]:
        return {"routing": {t.value: {"tier": 1, "providers": ["offline_demo"]} for t in AITaskType}, "guards": {"forbid_tier4_for": ["scenario_generation", "drill_variation", "rubric_grading"]}}

    def normalize_task(self, task_type: AITaskType | str) -> str:
        return task_type.value if hasattr(task_type, 'value') else str(task_type)

    def route_for(self, task_type: AITaskType | str) -> dict[str, Any]:
        task = self.normalize_task(task_type)
        return dict(self.policy.get("routing", {}).get(task, {"tier": 1, "providers": ["offline_demo"]}))

    def tier_for(self, task_type: AITaskType | str) -> ModelTier:
        return ModelTier(int(self.route_for(task_type).get("tier", 1)))

    def providers_for(self, task_type: AITaskType | str) -> list[str]:
        return list(self.route_for(task_type).get("providers", ["offline_demo"]))

    def assert_allowed(self, task_type: AITaskType | str) -> None:
        task = self.normalize_task(task_type)
        tier = int(self.tier_for(task))
        if task in self.policy.get("guards", {}).get("forbid_tier4_for", []) and tier >= 4:
            raise ValueError(f"Tier-4 provider calls are forbidden for {task}")
        if task in self.policy.get("guards", {}).get("development_tasks", []) and self.route_for(task).get("language_drill_allowed") is not False:
            raise ValueError(f"Development/audit task {task} must not be mixed with language drills")

    def tier_report(self) -> dict[str, int]:
        return {task: int(cfg.get('tier', 1)) for task, cfg in self.policy.get('routing', {}).items()}
