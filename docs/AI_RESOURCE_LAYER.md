# JapanApp AI Resource Layer

JapanApp is **not Gemini-only**. Gemini remains a valuable provider for strong language, code, architecture, and audit tasks, but the product now routes work through an AI Resource Layer so cost, privacy, quota, provider health, and quality can decide the best model path.

## Provider Router Design

The router lives in `frontend/services/ai_router.py` with provider contracts in `frontend/services/ai_providers/` and models in `frontend/models/ai_provider.py` / `frontend/models/ai_task_result.py`.

It supports these providers by profile:

- Offline Demo Provider
- Gemini
- Groq
- Cerebras
- OpenRouter
- Mistral
- SambaNova
- Cloudflare Workers AI
- HuggingFace
- GitHub Models
- AI21

Provider profiles are stored in `data/ai/provider_profiles.yaml`. The file stores **environment variable names only**, never API keys.

## Health and Circuit Breaker

Provider health states are:

- `healthy`
- `degraded`
- `cooldown`
- `disabled`

Circuit breaker triggers:

- `quota_exhausted` / HTTP 429 -> cooldown
- `auth_failure` / HTTP 401/403 -> disabled
- repeated timeout -> cooldown
- repeated invalid JSON -> cooldown or escalation

## Task-to-Tier Routing

Policy is configured in `data/ai/task_routing_policy.yaml` and loaded by `frontend/services/ai_task_policy.py`.

| Tier | Name | Use |
|---:|---|---|
| 0 | deterministic/local | schema validation, JSON repair, SRS scheduling, static rubric checks, secret/config/path scans |
| 1 | cheap/free model pool | scenarios, drill variants, simple summaries, distractors, vocabulary examples, first-pass feedback |
| 2 | strong language model | keigo nuance, naturalness, final rewrites, pressure roleplay, difficult mail correction, Vietnamese cultural explanation |
| 3 | judge/consensus | final boss judging, provider comparison, unsafe/unnatural Japanese rejection, rubric consistency |
| 4 | development/audit | code/refactor, architecture review, audit/security review |

Tier-4 calls are forbidden for simple scenario generation, drill variation, and ordinary grading.

## Privacy Modes

- `redacted`: default; removes company-specific details before storage.
- `synthetic`: demo/training mode with no real company content.
- `local_only`: stores locally and should not call external providers.

## Cost and Quality Strategy

Simple generation starts with offline/demo or cheap/free providers. Nuance and keigo work can escalate to stronger providers. Boss fights use judge/consensus tier. Development and audit tasks are reserved for tier-4 providers and are not mixed with language drills.

## Reference Inheritance

### translation_app

JapanApp inherits the architecture pattern of a free/low-cost provider pool, dynamic provider selection, waterfall fallback, health tracking, quota cooldown, authentication failure handling, provider adapters, and credential masking. The implementation is JapanApp-native and task-based rather than translation-only.

### nvidia-server

JapanApp adopts a smaller practical harness inspired by the agent runtime discipline: provider-router eval, model tier checks, credential safety scan, provider health smoke, command guard, preflight entry point, and report writer. These help Gemini/Codex/Gemini CLI/OpenCode-style agents work safely in loops.

### AIOS_habbit

JapanApp inherits local-first memory and evidence-based workflow ideas. `JapaneseWorkLearningMemory` records repeated Japanese mistakes, weak business situations, keigo/nuance errors, meeting response weaknesses, corrected email patterns, next drill recommendations, and confidence by context. It defaults to redacted/synthetic/local-only modes to avoid storing confidential company data.

### mat-the-website

JapanApp adopts practical governance: docs-first roadmap, harness scripts, quarantine reports, preflight checks, clear handover report, frontend/backend separation, and no fake PASS claims. Harness scripts write report files with actual results.
## Phase 2B live adapter layer

Phase 2B adds real provider adapter plumbing while keeping tests mock-only and offline-first.

- Gemini is supported, but it is only one provider.
- The 9-provider pool is configured: Groq, Cerebras, OpenRouter, Mistral, SambaNova, Cloudflare Workers AI, HuggingFace, GitHub Models, AI21.
- API key values must never be stored in `data/ai/provider_profiles.yaml`; only env var names are allowed.
- Runtime health is written to `data/ai/provider_health.json`, which is ignored by git.
- Tests and harnesses use mocked HTTP responses and do not perform live API calls.

### Environment variables

| Provider | Env vars |
|---|---|
| Gemini | `GEMINI_API_KEY` |
| Groq | `GROQ_API_KEY` |
| Cerebras | `CEREBRAS_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| SambaNova | `SAMBANOVA_API_KEY` |
| Cloudflare Workers AI | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` |
| HuggingFace | `HUGGINGFACE_API_KEY` |
| GitHub Models | `GITHUB_TOKEN` (configured under provider `github`) |
| AI21 | `AI21_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |

### Local Key Loader

JapanApp includes a safe local key loader at `frontend/services/ai_providers/local_key_loader.py`. It can load API keys from a key file:
1. Checked via env var `JAPANAPP_API_KEY_FILE`.
2. Defaults to `D:\Sandbox\AIOS_habbit\API Key.txt`.

Supported formats include:
- JSON key-value dictionary.
- Standard assignment patterns: `KEY=value`, `KEY: value` or `export KEY=value`.
- Alternating label-key structure where a line containing a provider name label (e.g. `Groq API Key`, `Open Router:`) is followed by the raw API key token on the next line.

Environment variables (in `os.environ`) always take precedence over the values loaded from the key file. To prevent credential leakage:
- Log messages print only the key names found (never the key values, prefixes, or suffixes).
- The key presence report `get_key_presence_report()` returns only boolean values.

### Routing Policy Config: `JAPANAPP_AI_MODE`

The environment variable `JAPANAPP_AI_MODE` controls the general behavior of the AI Resource Layer:
- `offline`: Routes all calls only to `offline_demo`.
- `auto` (default): Standard fallback chain based on priorities and availability.
- `live`: Prefers live external providers, falling back to `offline_demo` as a last resort if all live options are exhausted.

### Privacy modes

- `synthetic`: generated/demo content; external providers may be used if configured.
- `redacted`: default safe mode for sanitized content.
- `local_only`: never calls external providers; only local/offline providers are eligible.

### Manual live smoke

Live checks are opt-in only:

```powershell
$env:RUN_LIVE_PROVIDER_SMOKE="1"
py -3 scripts/smoke_live_providers.py
```

The smoke script prints provider status only and must not print keys, key prefixes, prompts, or raw responses.

