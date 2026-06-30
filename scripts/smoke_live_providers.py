"""Opt-in live provider smoke checks.

Not used by pytest. Requires RUN_LIVE_PROVIDER_SMOKE=1. Prints provider status
only and never prints API keys, key prefixes, prompts, or raw responses.
"""
from __future__ import annotations

import os

from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_router import AIRouter


def main() -> int:
    if os.getenv('RUN_LIVE_PROVIDER_SMOKE') != '1':
        print('SKIP: set RUN_LIVE_PROVIDER_SMOKE=1 to run opt-in live provider smoke.')
        return 0
    router = AIRouter()
    providers = [p for p in router.profiles if p != 'offline_demo']
    for provider_id in providers:
        req = AITaskRequest('scenario_generation', 'Return JSON: {"ok": true}', preferred_provider=provider_id, require_json=True)
        result = router.route(req)
        status = 'ok' if result.ok else (result.error_type or 'failed')
        print(f'{provider_id}: {status}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
