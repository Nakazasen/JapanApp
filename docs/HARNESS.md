# Harnesses

JapanApp harness scripts are executable QA gates. They write runtime reports under `quarantine_reports/`, which is ignored by git.

## Mock-only live adapter harness

```powershell
py -3 harness/provider_live_adapter_mock_eval.py
```

This harness performs no live API calls. It verifies adapter contracts, fallback behavior, credential masking, provider health persistence, and `local_only` blocking through mocked tests.

## Key loader and provider parity harness

```powershell
py -3 harness/provider_key_loader_eval.py
```

This harness verifies the local key loader parses alternate label-key and json files safely without leakage, verifies boolean-only presence reporting, validates `JAPANAPP_AI_MODE` routing policies, and checks provider name/model alignment with `translation_app`.

## Existing gates

```powershell
py -3 harness/provider_live_adapter_mock_eval.py
py -3 harness/provider_router_eval.py
py -3 harness/model_tier_policy_check.py
py -3 harness/credential_safety_check.py
py -3 harness/provider_health_smoke.py
py -3 harness/jp_hell_product_eval.py
```

Do not claim PASS unless the command actually passes.
