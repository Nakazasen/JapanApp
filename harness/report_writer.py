from __future__ import annotations
import json, time, sys, subprocess, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def get_git_state() -> str:
    try:
        status = subprocess.check_output(["git", "status", "--short"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return "dirty" if status else "clean"
    except Exception:
        return "unknown"

def write_report(name: str, data: dict):
    out = ROOT / 'quarantine_reports' / f'{name}_{int(time.time())}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    
    # Inject metadata without leaking secrets
    metadata = {
        "timestamp_iso": datetime.datetime.now(datetime.UTC).isoformat(),
        "command": " ".join(sys.argv),
        "git_state": get_git_state(),
        "not_tested": data.get("not_tested", [])
    }
    
    # Ensure metadata is near the top
    final_data = {"metadata": metadata}
    final_data.update(data)
    
    out.write_text(json.dumps(final_data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))
    return out
