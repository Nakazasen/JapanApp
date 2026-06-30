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
