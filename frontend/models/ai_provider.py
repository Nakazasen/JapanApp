"""AI provider metadata for JapanApp provider routing."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


class ProviderHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"


class AITaskType(str, Enum):
    SCENARIO_GENERATION = "scenario_generation"
    DRILL_VARIATION = "drill_variation"
    RUBRIC_GRADING = "rubric_grading"
    JAPANESE_NUANCE_REVIEW = "japanese_nuance_review"
    KEIGO_CORRECTION = "keigo_correction"
    BUSINESS_MAIL_REWRITE = "business_mail_rewrite"
    MEETING_ROLEPLAY = "meeting_roleplay"
    FINAL_BOSS_JUDGE = "final_boss_judge"
    CODE_GENERATION = "code_generation"
    ARCHITECTURE_REVIEW = "architecture_review"
    AUDIT_REVIEW = "audit_review"


class ModelTier(IntEnum):
    LOCAL_DETERMINISTIC = 0
    CHEAP_FREE_POOL = 1
    STRONG_LANGUAGE = 2
    JUDGE_CONSENSUS = 3
    DEVELOPMENT_AUDIT = 4


@dataclass
class ProviderProfile:
    provider_id: str
    display_name: str
    enabled: bool = True
    default_model: str = ""
    env_key: str = ""
    base_url: str = ""
    priority: int = 100
    max_tier: int = 1
    cost_class: str = "free"
    privacy_modes: list[str] = field(default_factory=lambda: ["redacted", "synthetic"])
    capabilities: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ProviderRuntimeState:
    provider_id: str
    health: ProviderHealth = ProviderHealth.HEALTHY
    cooldown_until: float = 0.0
    consecutive_failures: int = 0
    timeout_failures: int = 0
    invalid_json_failures: int = 0
    invalid_json_total: int = 0
    auth_failed: bool = False
    quota_exhausted: bool = False
    last_error_type: str = ""
    success_count: int = 0
    failure_count: int = 0

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "health": self.health.value,
            "cooldown_until": self.cooldown_until,
            "consecutive_failures": self.consecutive_failures,
            "timeout_failures": self.timeout_failures,
            "invalid_json_failures": self.invalid_json_failures,
            "auth_failed": self.auth_failed,
            "quota_exhausted": self.quota_exhausted,
            "last_error_type": self.last_error_type,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }
