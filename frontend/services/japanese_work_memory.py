"""Local-first Japanese Work Learning Memory.

Default mode redacts company-specific text and stores weakness evidence only.
"""
from __future__ import annotations
import json, re, time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MEMORY_PATH = ROOT / "data" / "ai" / "japanese_work_learning_memory.json"

class JapaneseWorkLearningMemory:
    def __init__(self, path: Path | str = DEFAULT_MEMORY_PATH, mode: str = "redacted"):
        if mode not in {"redacted", "synthetic", "local_only"}: raise ValueError("invalid memory mode")
        self.path=Path(path); self.mode=mode; self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data=self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            try: return json.loads(self.path.read_text(encoding='utf-8'))
            except Exception: pass
        return {"mode": self.mode, "attempts": [], "weakness_counts": {}, "confidence_by_context": {}, "email_patterns_corrected": [], "next_drill_recommendations": []}

    def _redact(self, text: str) -> str:
        if self.mode == "synthetic": return "[synthetic-example]"
        if self.mode == "local_only": return text
        text = re.sub(r"[\w.%-]+@[\w.-]+", "[email]", text or "")
        text = re.sub(r"\b\d{2,}\b", "[number]", text)
        return text[:240]

    def update_from_feedback(self, business_context: str, user_answer: str, feedback: dict[str, Any]) -> dict[str, Any]:
        tags=list(feedback.get('weakness_tags') or [])
        for tag in tags: self.data['weakness_counts'][tag]=self.data['weakness_counts'].get(tag,0)+1
        score=int(feedback.get('score_total',0)); old=self.data['confidence_by_context'].get(business_context, 50)
        self.data['confidence_by_context'][business_context]=round((old + score)/2, 1)
        rec=feedback.get('next_drill') or (tags[0] if tags else 'review_keigo_basics')
        self.data['next_drill_recommendations'].append(rec)
        if 'mail' in business_context or 'email' in business_context:
            self.data['email_patterns_corrected'].append(self._redact(feedback.get('better_version','')))
        self.data['attempts'].append({"ts": int(time.time()), "business_context": business_context, "answer_sample": self._redact(user_answer), "weakness_tags": tags, "score_total": score, "next_drill": rec, "mode": self.mode})
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')
        return self.data
