"""Mocked router fallback tests for live provider adapter phase."""
from __future__ import annotations

import os

from frontend.models.ai_provider import ProviderProfile
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_router import AIRouter
from frontend.services.ai_providers.base import ProviderResponse


class StaticProvider:
    def __init__(self, response, available=True): self.response=response; self.calls=0; self.available=available
    def is_available(self): return self.available
    def generate(self, request): self.calls += 1; return self.response


def profiles():
    caps=['scenario_generation']
    return {
        'offline_demo': ProviderProfile('offline_demo','Offline',priority=1,max_tier=3,privacy_modes=['redacted','synthetic','local_only'],capabilities=caps),
        'groq': ProviderProfile('groq','Groq',priority=2,max_tier=2,env_key='GROQ_API_KEY',base_url='https://x',default_model='m',privacy_modes=['redacted','synthetic'],capabilities=caps),
        'gemini': ProviderProfile('gemini','Gemini',priority=3,max_tier=4,env_key='GEMINI_API_KEY',base_url='https://x',default_model='m',privacy_modes=['redacted','synthetic'],capabilities=caps),
    }


def test_invalid_json_falls_back_to_next_provider(tmp_path):
    router = AIRouter(profiles=profiles(), health_path=None)
    router.health_path = tmp_path/'health.json'
    router.policy.policy['routing']['scenario_generation']['providers'] = ['groq','gemini']
    router.providers['groq'] = StaticProvider(ProviderResponse(True, text='not json'))
    router.providers['gemini'] = StaticProvider(ProviderResponse(True, text='{"ok": true}', data={'ok': True}))
    result = router.route(AITaskRequest('scenario_generation','x',require_json=True))
    assert result.ok and result.provider_used == 'gemini'
    assert result.fallback_used


def test_auth_failure_disables_provider(tmp_path):
    router = AIRouter(profiles=profiles(), health_path=None)
    router.health_path = tmp_path/'health.json'
    router.policy.policy['routing']['scenario_generation']['providers'] = ['groq']
    router.providers['groq'] = StaticProvider(ProviderResponse(False, error_type='auth_failure', error_message='bad key'))
    result = router.route(AITaskRequest('scenario_generation','x'))
    assert not result.ok
    assert router.states['groq'].auth_failed


def test_timeout_cooldown_after_two_failures(tmp_path):
    router = AIRouter(profiles=profiles(), cooldown_seconds=10, health_path=None)
    router.health_path = tmp_path/'health.json'
    router._record_failure('groq','timeout')
    router._record_failure('groq','timeout')
    assert router.states['groq'].health.value == 'cooldown'


def test_local_only_never_calls_external_provider(tmp_path):
    router = AIRouter(profiles=profiles(), health_path=None)
    router.health_path = tmp_path/'health.json'
    external = StaticProvider(ProviderResponse(True, text='{"bad": true}', data={'bad': True}))
    router.providers['groq'] = external
    result = router.route(AITaskRequest('scenario_generation','x',privacy_mode='local_only'))
    assert result.ok
    assert result.provider_used == 'offline_demo'
    assert external.calls == 0


def test_offline_demo_works_without_keys():
    for key in ['GROQ_API_KEY','GEMINI_API_KEY']:
        os.environ.pop(key, None)
    router = AIRouter(profiles=profiles(), health_path=None)
    result = router.route(AITaskRequest('scenario_generation','x',privacy_mode='synthetic'))
    assert result.ok
    assert result.provider_used == 'offline_demo'
