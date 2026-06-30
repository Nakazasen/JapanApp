# Địa Ngục Tiếng Nhật AI Strategy

Địa ngục tiếng Nhật is a **Business Japanese training factory**, not a Gemini demo.

## Drill Flow

1. Generate or retrieve a scenario through the provider router.
2. Validate scenario schema locally.
3. User answers.
4. Grade through the provider router.
5. If JSON is invalid or the provider is weak, retry, repair, or escalate.
6. Boss fights use the judge/consensus tier and prefer a different reviewer path.
7. Save attempt, score, weakness tags, feedback, and next drill.
8. Generate SRS items from actual weakness tags.
9. Update Japanese Work Learning Memory.

## Cheap Scenario Generation

Routine scenarios use Tier 1: offline demo, Groq, Cerebras, Mistral, SambaNova, Cloudflare, HuggingFace, GitHub Models, AI21, or Gemini only if policy allows and cheaper paths are unsuitable. Expensive/top-tier models are not required for simple scenario generation.

## Strong Models for Nuance

Tier 2 is reserved for tasks where weak models often fail:

- keigo correction
- business Japanese naturalness
- difficult mail rewrite
- meeting pressure simulation
- cultural or organizational explanation in Vietnamese

## Boss Fights and Judge/Consensus

Tier 3 final boss judging compares or reviews outputs to reject unsafe, unnatural, or inconsistent Japanese. The feedback contract includes `judge_provider` so reports can show who judged the answer.

## Weakness Memory to Future Drills

`JapaneseWorkLearningMemory` stores:

- repeated Japanese mistakes
- weak business situations
- keigo/nuance errors
- meeting response weaknesses
- email patterns already corrected
- next drill recommendations
- confidence score by business context

The memory converts weakness tags into SRS items and future drill recommendations.

## Local-Only Protection

The default safe modes avoid confidential company storage:

- `synthetic` for demo drills
- `redacted` for normal learning memory
- `local_only` for sensitive work that must not leave the machine

Company names, emails, and numeric identifiers should be redacted before durable memory unless the user explicitly chooses local-only storage.

## Feedback Contract

Every grading result includes AI routing metadata:

```json
{
  "provider_used": "offline_demo",
  "provider_tier": 1,
  "fallback_used": false,
  "judge_provider": "offline_demo",
  "score_total": 78,
  "scores": {},
  "critical_errors": [],
  "unnatural_phrases": [],
  "better_version": "...",
  "vietnamese_explanation": "...",
  "next_drill": "...",
  "weakness_tags": []
}
```

## Final Tier Map

| Task | Tier |
|---|---:|
| scenario_generation | 1 |
| drill_variation | 1 |
| rubric_grading | 1 |
| japanese_nuance_review | 2 |
| keigo_correction | 2 |
| business_mail_rewrite | 2 |
| meeting_roleplay | 2 |
| final_boss_judge | 3 |
| code_generation | 4 |
| architecture_review | 4 |
| audit_review | 4 |

## Phase 2B provider routing update

Địa ngục tiếng Nhật continues to work in offline/demo mode with no API keys. When providers are configured, the AI Resource Layer can route non-local tasks to Gemini plus the 9-provider pool. `local_only` mode is reserved for local/offline behavior and must not call external providers.

Phase 2B does not add the Deep Training Loop and does not change the Phase 2A seed data or UI scope.
