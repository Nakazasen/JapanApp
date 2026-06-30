from pathlib import Path
import re, sys, json
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harness.report_writer import write_report
ROOT=Path(__file__).resolve().parents[1]
SECRET_PATTERNS=[
    re.compile(r'(?i)(api[_-]?key|token|secret)\s*[:=]\s*[A-Za-z0-9_\-]{16,}'),
    re.compile(r'(?i)(api[_-]?key|token|secret|GEMINI_API_KEY).*\[:\d+\]'),
    re.compile(r'(?i)\[:\d+\].*(api[_-]?key|token|secret|GEMINI_API_KEY)'),
]
ALLOW={'credential_safety_check.py','test_ai_router.py'}
def main():
    findings=[]
    for p in list((ROOT/'frontend').rglob('*.py'))+list((ROOT/'data/ai').rglob('*'))+list((ROOT/'docs').rglob('*.md')):
        if p.name in ALLOW: continue
        txt=p.read_text(encoding='utf-8', errors='ignore')
        for pat in SECRET_PATTERNS:
            if pat.search(txt): findings.append(str(p.relative_to(ROOT)))
    ok=not findings; write_report('credential_safety_check', {'ok': ok, 'findings': findings})
    print('PASS' if ok else 'FAIL'); return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
