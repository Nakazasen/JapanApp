"""JapanApp AI Resource Layer provider router.

Gemini is supported as one provider; routing is capability/tier based and can run
fully offline with synthetic data for demo drills.
"""
from __future__ import annotations
import json, os, re, time
from pathlib import Path
from typing import Any
from frontend.models.ai_provider import ProviderHealth, ProviderProfile, ProviderRuntimeState
from frontend.models.ai_task_result import AITaskRequest, AITaskResult
from frontend.services.ai_task_policy import AITaskPolicy
from frontend.services.ai_providers import OfflineDemoProvider, GeminiProvider, OpenAICompatibleProvider, CloudflareProvider, HuggingFaceProvider

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "data" / "ai" / "provider_profiles.yaml"
SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|secret)[=:]\s*['\"]?([A-Za-z0-9_\-]{8,})")

AUTH_HINTS=("401","403","unauthorized","auth","invalid api key","forbidden")
QUOTA_HINTS=("429","quota","rate limit","too many requests","resource exhausted")
TIMEOUT_HINTS=("timeout","timed out")

def mask_secret(value: str) -> str:
    if not value: return ""
    return "***MASKED***"

def sanitize_text(text: str) -> str:
    return SECRET_RE.sub(lambda m: f"{m.group(1)}={mask_secret(m.group(2))}", str(text))

def classify_error(message: str) -> str:
    low = str(message).lower()
    if any(h in low for h in AUTH_HINTS): return "auth_failure"
    if any(h in low for h in QUOTA_HINTS): return "quota_exhausted"
    if any(h in low for h in TIMEOUT_HINTS): return "timeout"
    if "invalid_json" in low or "json" in low: return "invalid_json"
    return "provider_error"

def parse_json_repair(text: str) -> tuple[dict[str, Any], bool]:
    try: return json.loads(text), False
    except Exception: pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try: return json.loads(m.group(0)), True
        except Exception: pass
    return {}, True

def _parse_profiles(path: Path=PROFILE_PATH) -> dict[str, ProviderProfile]:
    # Prefer PyYAML, fallback to built-in defaults to avoid mandatory dependency.
    if path.exists():
        try:
            import yaml  # type: ignore
            raw = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
            out = {}
            for pid, cfg in (raw.get('providers') or {}).items():
                out[pid] = ProviderProfile(provider_id=pid, display_name=cfg.get('display_name', pid), enabled=cfg.get('enabled', True), default_model=cfg.get('default_model',''), env_key=cfg.get('env_key',''), base_url=cfg.get('base_url',''), priority=int(cfg.get('priority',100)), max_tier=int(cfg.get('max_tier',1)), cost_class=cfg.get('cost_class','free'), privacy_modes=cfg.get('privacy_modes') or ['redacted'], capabilities=cfg.get('capabilities') or [], notes=cfg.get('notes',''))
            if out: return out
        except Exception:
            pass
    return {"offline_demo": ProviderProfile("offline_demo", "Offline Demo Provider", True, "synthetic-jp-business-v1", priority=1, max_tier=3, privacy_modes=["redacted","synthetic","local_only"], capabilities=["scenario_generation","drill_variation","rubric_grading","japanese_nuance_review","keigo_correction","business_mail_rewrite","meeting_roleplay","final_boss_judge"]),
            "gemini": ProviderProfile("gemini", "Gemini", True, "gemini-2.5-flash", "GEMINI_API_KEY", priority=30, max_tier=4, capabilities=["code_generation","architecture_review","audit_review","japanese_nuance_review"])}

class AIRouter:
    def __init__(self, policy: AITaskPolicy | None = None, profiles: dict[str, ProviderProfile] | None = None, cooldown_seconds: int = 60):
        self.policy = policy or AITaskPolicy()
        self.profiles = profiles or _parse_profiles()
        self.cooldown_seconds = cooldown_seconds
        self.states = {pid: ProviderRuntimeState(pid) for pid in self.profiles}
        self.providers = {pid: self._adapter(profile) for pid, profile in self.profiles.items()}

    def _adapter(self, profile: ProviderProfile):
        if profile.provider_id == "offline_demo": return OfflineDemoProvider(profile)
        if profile.provider_id == "gemini": return GeminiProvider(profile)
        if profile.provider_id == "cloudflare": return CloudflareProvider(profile)
        if profile.provider_id == "huggingface": return HuggingFaceProvider(profile)
        return OpenAICompatibleProvider(profile)

    def provider_health(self) -> dict[str, dict[str, Any]]:
        self._refresh_cooldowns()
        return {pid: st.public_dict() for pid, st in self.states.items()}

    def _refresh_cooldowns(self) -> None:
        now=time.time()
        for st in self.states.values():
            if st.health == ProviderHealth.COOLDOWN and st.cooldown_until <= now and not st.auth_failed:
                st.health = ProviderHealth.DEGRADED if st.failure_count else ProviderHealth.HEALTHY

    def _eligible(self, request: AITaskRequest) -> list[str]:
        self.policy.assert_allowed(request.task_type)
        task = self.policy.normalize_task(request.task_type)
        tier = int(self.policy.tier_for(task))
        ordered = [request.preferred_provider] if request.preferred_provider else self.policy.providers_for(task)
        result=[]; self._refresh_cooldowns()
        for pid in ordered:
            if not pid or pid not in self.profiles: continue
            prof=self.profiles[pid]; st=self.states[pid]
            if not prof.enabled or st.health in {ProviderHealth.DISABLED, ProviderHealth.COOLDOWN}: continue
            if task not in prof.capabilities: continue
            if int(prof.max_tier) < tier: continue
            if request.privacy_mode not in prof.privacy_modes: continue
            result.append(pid)
        return sorted(result, key=lambda p: self.profiles[p].priority)

    def route(self, request: AITaskRequest) -> AITaskResult:
        attempts=[]; tier=int(self.policy.tier_for(request.task_type)); providers=self._eligible(request)
        if not providers:
            return AITaskResult(False, provider_tier=tier, error_type="no_provider_available", error_message="No provider matched task, privacy mode, health, and tier policy")
        first = providers[0]
        for pid in providers:
            adapter=self.providers[pid]; prof=self.profiles[pid]; st=self.states[pid]
            resp=adapter.generate(request)
            attempt={"provider": pid, "model": prof.default_model, "ok": resp.ok, "error_type": resp.error_type}
            attempts.append(attempt)
            if resp.ok:
                data=resp.data
                repaired=False
                if request.require_json and not data:
                    data, repaired = parse_json_repair(resp.text)
                    if not data:
                        self._record_failure(pid, "invalid_json")
                        continue
                st.success_count += 1; st.consecutive_failures=0; st.timeout_failures=0; st.health=ProviderHealth.HEALTHY
                return AITaskResult(True, content=resp.text, data=data, provider_used=pid, provider_tier=tier, fallback_used=(pid != first or len(attempts)>1), model=resp.model or prof.default_model, attempts=attempts)
            self._record_failure(pid, resp.error_type or classify_error(resp.error_message))
        return AITaskResult(False, provider_tier=tier, fallback_used=len(attempts)>1, attempts=attempts, error_type="all_providers_failed", error_message=sanitize_text("All eligible providers failed"))

    def _record_failure(self, pid: str, error_type: str) -> None:
        st=self.states[pid]; st.failure_count += 1; st.consecutive_failures += 1; st.last_error_type=error_type
        if error_type == "auth_failure": st.auth_failed=True; st.health=ProviderHealth.DISABLED
        elif error_type == "quota_exhausted": st.quota_exhausted=True; st.health=ProviderHealth.COOLDOWN; st.cooldown_until=time.time()+self.cooldown_seconds
        elif error_type == "timeout":
            st.timeout_failures += 1
            if st.timeout_failures >= 2: st.health=ProviderHealth.COOLDOWN; st.cooldown_until=time.time()+self.cooldown_seconds
            else: st.health=ProviderHealth.DEGRADED
        elif error_type == "invalid_json":
            st.invalid_json_failures += 1; st.invalid_json_total += 1
            if st.invalid_json_failures >= 2: st.health=ProviderHealth.COOLDOWN; st.cooldown_until=time.time()+self.cooldown_seconds
            else: st.health=ProviderHealth.DEGRADED
        elif st.consecutive_failures >= 3:
            st.health=ProviderHealth.COOLDOWN; st.cooldown_until=time.time()+self.cooldown_seconds
        else: st.health=ProviderHealth.DEGRADED

_default_router: AIRouter | None = None
def get_ai_router() -> AIRouter:
    global _default_router
    if _default_router is None: _default_router = AIRouter()
    return _default_router
