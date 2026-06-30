'''Minimal command guard: keep harness commands read-only unless explicitly approved.'''
ALLOWED_PREFIXES = ['python -m pytest', 'python harness/provider_router_eval.py', 'python harness/model_tier_policy_check.py', 'python harness/credential_safety_check.py', 'python harness/provider_health_smoke.py']
