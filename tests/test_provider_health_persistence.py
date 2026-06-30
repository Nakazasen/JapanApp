"""Provider health persistence tests."""
from __future__ import annotations

import json
from pathlib import Path

from frontend.models.ai_provider import ProviderHealth, ProviderProfile
from frontend.services.ai_router import AIRouter


def router_with_tmp_health(tmp_path: Path) -> AIRouter:
    profiles = {
        'offline_demo': ProviderProfile('offline_demo', 'Offline', max_tier=3, privacy_modes=['redacted','synthetic','local_only'], capabilities=['scenario_generation']),
        'groq': ProviderProfile('groq', 'Groq', env_key='GROQ_API_KEY', base_url='https://x', default_model='m', capabilities=['scenario_generation']),
    }
    return AIRouter(profiles=profiles, cooldown_seconds=10, health_path=tmp_path / 'provider_health.json', load_health=False)


def test_health_persists_auth_failure_without_secrets(tmp_path):
    router = router_with_tmp_health(tmp_path)
    router._record_failure('groq', 'auth_failure')
    raw = router.health_path.read_text(encoding='utf-8')
    assert 'secret' not in raw.lower()
    data = json.loads(raw)
    assert data['providers']['groq']['health'] == 'disabled'
    router2 = router_with_tmp_health(tmp_path)
    router2._load_health()
    assert router2.states['groq'].health == ProviderHealth.DISABLED
    assert router2.states['groq'].auth_failed


def test_quota_cooldown_persists(tmp_path):
    router = router_with_tmp_health(tmp_path)
    router._record_failure('groq', 'quota_exhausted')
    data = json.loads(router.health_path.read_text(encoding='utf-8'))
    assert data['providers']['groq']['health'] == 'cooldown'
    assert data['providers']['groq']['cooldown_until'] > 0
    assert 'prompt' not in json.dumps(data).lower()
    assert 'response' not in json.dumps(data).lower()
