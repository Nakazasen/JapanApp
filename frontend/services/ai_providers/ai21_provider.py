"""AI21 provider adapter.

AI21 exposes multiple API shapes across model generations. JapanApp uses a small
chat-style adapter and keeps behavior mock-tested; live smoke is opt-in.
"""
from __future__ import annotations

from frontend.services.ai_providers.openai_compatible_provider import OpenAICompatibleProvider


class AI21Provider(OpenAICompatibleProvider):
    pass
