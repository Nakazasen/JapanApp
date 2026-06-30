from frontend.models.ai_provider import AITaskType, ProviderHealth, ProviderProfile
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_router import AIRouter, mask_secret, sanitize_text
from frontend.services.ai_providers.base import AIProviderAdapter, ProviderResponse

class FailingProvider(AIProviderAdapter):
    def generate(self, request): return ProviderResponse(False, error_type='quota_exhausted', error_message='429 quota')
class InvalidProvider(AIProviderAdapter):
    def generate(self, request): return ProviderResponse(True, text='not json', model='bad')

def router_with(extra=None):
    r=AIRouter(cooldown_seconds=1, health_path=None)
    if extra:
        for pid, adapter in extra.items():
            r.providers[pid]=adapter
    return r

def test_router_selects_offline_demo_for_scenario_generation():
    r=AIRouter(health_path=None)
    res=r.route(AITaskRequest(AITaskType.SCENARIO_GENERATION, 'make scenario', privacy_mode='synthetic'))
    assert res.ok
    assert res.provider_used == 'offline_demo'
    assert res.provider_tier == 1
    assert res.data['scenario_id']

def test_fallback_when_preferred_provider_fails():
    r=AIRouter(cooldown_seconds=1, health_path=None)
    prof=r.profiles['groq']
    r.providers['groq']=FailingProvider(prof)
    res=r.route(AITaskRequest(AITaskType.SCENARIO_GENERATION, 'x', privacy_mode='redacted', preferred_provider='groq'))
    assert not res.ok
    assert r.states['groq'].health == ProviderHealth.COOLDOWN
    res2=r.route(AITaskRequest(AITaskType.SCENARIO_GENERATION, 'x', privacy_mode='redacted'))
    assert res2.ok
    assert res2.provider_used == 'offline_demo'

def test_invalid_json_degrades_then_cooldowns_provider():
    r=AIRouter(cooldown_seconds=1, health_path=None)
    r.providers['groq']=InvalidProvider(r.profiles['groq'])
    req=AITaskRequest(AITaskType.RUBRIC_GRADING, 'grade', privacy_mode='redacted', preferred_provider='groq')
    assert not r.route(req).ok
    assert r.states['groq'].health == ProviderHealth.DEGRADED
    assert not r.route(req).ok
    assert r.states['groq'].health == ProviderHealth.COOLDOWN

def test_credential_masking_never_prints_key_or_prefix():
    key='sk-test-SECRETKEY123456'
    assert mask_secret(key) == '***MASKED***'
    clean=sanitize_text(f'api_key={key}')
    assert key not in clean and 'sk-test' not in clean
