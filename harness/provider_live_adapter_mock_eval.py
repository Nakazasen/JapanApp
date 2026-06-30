"""Mock-only Phase 2B live adapter harness.

This harness performs no live API calls. It relies on pytest coverage for adapter
contracts and writes a quarantine report summarizing the mocked checks.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / 'quarantine_reports'


def main() -> int:
    REPORT_DIR.mkdir(exist_ok=True)
    command = ['py','-3','-m','pytest','tests/test_ai_provider_http_client.py','tests/test_live_provider_adapters_mocked.py','tests/test_provider_health_persistence.py','tests/test_ai_router_live_fallback_mocked.py','tests/test_ai_key_loader.py','-q']
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    git = subprocess.run(['git','status','--short'], cwd=ROOT, text=True, capture_output=True)
    report = {
        'harness': 'provider_live_adapter_mock_eval',
        'timestamp': int(time.time()),
        'live_api_calls_performed': False,
        'command': ' '.join(command),
        'returncode': proc.returncode,
        'stdout_tail': proc.stdout[-4000:],
        'stderr_tail': proc.stderr[-2000:],
        'git_state': git.stdout.strip(),
        'checked': [
            'adapter contracts with mocked HTTP',
            'fallback behavior',
            'credential masking',
            'provider health persistence',
            'local_only external-provider block',
        ],
        'not_tested': ['real provider credentials', 'live API latency', 'provider account quota'],
        'verdict': 'PASS' if proc.returncode == 0 else 'FAIL',
    }
    path = REPORT_DIR / f"provider_live_adapter_mock_eval_{report['timestamp']}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(path)
    print(report['verdict'])
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    return proc.returncode


if __name__ == '__main__':
    raise SystemExit(main())
