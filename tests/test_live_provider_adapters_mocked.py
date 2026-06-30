"""Mock-only live provider adapter contract tests."""
from __future__ import annotations

import os
from contextlib import contextmanager

from frontend.models.ai_provider import ProviderProfile
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_providers.base import ProviderResponse
from frontend.services.ai_providers.cloudflare_provider import CloudflareProvider
from frontend.services.ai_providers.gemini_provider import GeminiProvider
from frontend.services.ai_providers.huggingface_provider import HuggingFaceProvider
from frontend.services.ai_providers.openai_compatible_provider import OpenAICompatibleProvider
from frontend.services.ai_providers.ai21_provider import AI21Provider


class MockClient:
    def __init__(self, payload): self.payload = payload; self.calls = []
    def post_json(self, url, payload, headers=None, timeout=None, sensitive_values=None, **kwargs):
        self.calls.append((url, payload, headers or {}))
        return self.payload


class MockHttpResponse:
    ok = True; error_type = ''; error_message = ''; invalid_json = False
    def __init__(self, data): self.data = data; self.text = str(data)


@contextmanager
def env(**values):
    old = {k: os.environ.get(k) for k in values}
    try:
        for k, v in values.items(): os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def req(): return AITaskRequest('scenario_generation', 'Return {"ok": true}', require_json=True)


def profile(pid, adapter='openai_compatible', env_key='TEST_KEY'):
    return ProviderProfile(pid, pid, default_model='test-model', env_key=env_key, base_url='https://provider.test/v1', capabilities=['scenario_generation'], adapter_type=adapter)


def test_openai_compatible_success_mocked():
    client = MockClient(MockHttpResponse({'choices': [{'message': {'content': '{"ok": true}'}}]}))
    with env(TEST_KEY='secret-openai-key'):
        resp = OpenAICompatibleProvider(profile('groq'), client=client).generate(req())
    assert resp.ok and resp.data == {'ok': True}
    assert '/chat/completions' in client.calls[0][0]


def test_gemini_success_mocked():
    client = MockClient(MockHttpResponse({'candidates': [{'content': {'parts': [{'text': '{"ok": true}'}]}}]}))
    with env(GEMINI_API_KEY='secret-gemini-key'):
        resp = GeminiProvider(profile('gemini', 'gemini', 'GEMINI_API_KEY'), client=client).generate(req())
    assert resp.ok and resp.data == {'ok': True}


def test_cloudflare_success_mocked():
    client = MockClient(MockHttpResponse({'result': {'response': '{"ok": true}'}}))
    with env(CLOUDFLARE_API_TOKEN='secret-cf-token', CLOUDFLARE_ACCOUNT_ID='account123'):
        prof = profile('cloudflare', 'cloudflare', 'CLOUDFLARE_API_TOKEN')
        prof.extra = {'account_env_key': 'CLOUDFLARE_ACCOUNT_ID'}
        resp = CloudflareProvider(prof, client=client).generate(req())
    assert resp.ok and resp.data == {'ok': True}
    assert 'account123' in client.calls[0][0]


def test_huggingface_success_mocked():
    client = MockClient(MockHttpResponse([{'generated_text': '{"ok": true}'}]))
    with env(HUGGINGFACE_API_KEY='secret-hf-key'):
        resp = HuggingFaceProvider(profile('huggingface', 'huggingface', 'HUGGINGFACE_API_KEY'), client=client).generate(req())
    assert resp.ok and resp.data == {'ok': True}


def test_ai21_success_mocked():
    client = MockClient(MockHttpResponse({'choices': [{'message': {'content': '{"ok": true}'}}]}))
    with env(AI21_API_KEY='secret-ai21-key'):
        resp = AI21Provider(profile('ai21', 'ai21', 'AI21_API_KEY'), client=client).generate(req())
    assert resp.ok and resp.data == {'ok': True}


def test_missing_key_and_local_only_skip_safely():
    os.environ.pop('TEST_KEY', None)
    provider = OpenAICompatibleProvider(profile('groq'), client=MockClient(None))
    assert provider.generate(req()).error_type == 'missing_key'
    with env(TEST_KEY='secret'):
        blocked = provider.generate(AITaskRequest('scenario_generation', 'x', privacy_mode='local_only'))
    assert blocked.error_type == 'privacy_blocked'
