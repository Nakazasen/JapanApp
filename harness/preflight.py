from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
cmds=[[sys.executable,'-m','pytest','tests/test_ai_router.py','tests/test_ai_task_policy.py','tests/test_jp_business_hell_ai_router.py','-q'], [sys.executable,'harness/provider_router_eval.py'], [sys.executable,'harness/model_tier_policy_check.py'], [sys.executable,'harness/credential_safety_check.py'], [sys.executable,'harness/provider_health_smoke.py']]
for cmd in cmds:
    print('RUN', ' '.join(cmd)); r=subprocess.run(cmd, cwd=ROOT); 
    if r.returncode: raise SystemExit(r.returncode)
