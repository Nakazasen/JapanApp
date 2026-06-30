"""Tests for secret-safe provider HTTP client."""
from __future__ import annotations

import io
import socket
import urllib.error

from frontend.services.ai_providers.http_client import SafeHttpClient, classify_provider_error, sanitize_text


class FakeResponse:
    status = 200
    def __init__(self, body): self.body = body.encode('utf-8')
    def read(self): return self.body
    def __enter__(self): return self
    def __exit__(self, *args): return False


def test_post_json_success():
    client = SafeHttpClient(opener=lambda req, timeout=1: FakeResponse('{"ok": true}'))
    resp = client.post_json('https://example.test', {'x': 1})
    assert resp.ok
    assert resp.data == {'ok': True}


def test_http_error_classification_and_secret_masking():
    secret = 'sk-super-secret-value'
    def opener(req, timeout=1):
        raise urllib.error.HTTPError(req.full_url, 401, 'Unauthorized', {}, io.BytesIO(f'invalid api key {secret}'.encode()))
    resp = SafeHttpClient(opener=opener).post_json('https://example.test', {}, sensitive_values=[secret])
    assert resp.error_type == 'auth_failure'
    assert secret not in resp.error_message
    assert secret[:8] not in resp.error_message


def test_quota_timeout_invalid_json():
    assert classify_provider_error('429 rate limit') == 'quota_exhausted'
    def timeout_opener(req, timeout=1): raise socket.timeout('timed out')
    assert SafeHttpClient(opener=timeout_opener, retries=0).post_json('https://x', {}).error_type == 'timeout'
    bad = SafeHttpClient(opener=lambda req, timeout=1: FakeResponse('not json')).post_json('https://x', {})
    assert bad.error_type == 'invalid_json'
    assert bad.invalid_json


def test_sanitize_text_masks_key_patterns():
    text = sanitize_text('Authorization: Bearer abcdef1234567890 and api_key=abcdef1234567890')
    assert 'abcdef1234567890' not in text
    assert '***MASKED***' in text
