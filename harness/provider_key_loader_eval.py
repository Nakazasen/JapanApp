"""Harness to evaluate the local key loader and provider profiles parity."""
import os
import tempfile
import sys
import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from frontend.services.ai_providers.local_key_loader import (
    get_provider_secret,
    get_key_presence_report,
    clear_loader_cache,
)
from frontend.services.ai_router import AIRouter
from frontend.models.ai_provider import AITaskType, ProviderProfile
from frontend.models.ai_task_result import AITaskRequest
from harness.report_writer import write_report


def run_eval() -> bool:
    checks = []
    
    # 1. API Key.txt parser with temp fake file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Groq API Key\n")
        f.write("groq_secret_val\n")
        f.write("Open Router:\n")
        f.write("openrouter_secret_val\n")
        f.write("export GEMINI_API_KEY=gemini_secret_val\n")
        f.write('{"CEREBRAS_API_KEY": "cerebras_secret_val"}\n')  # Note: parser does JSON first, but since it falls back if not JSON, it won't crash
        temp_path = f.name

    # Clear environment variables to isolate parsing tests
    old_env = {}
    test_keys = [
        "GEMINI_API_KEY", "GROQ_API_KEY", "CEREBRAS_API_KEY", "OPENROUTER_API_KEY",
        "MISTRAL_API_KEY", "SAMBANOVA_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID",
        "HUGGINGFACE_API_KEY", "GITHUB_TOKEN", "AI21_API_KEY", "DEEPSEEK_API_KEY",
        "NVIDIA_API_KEY", "CHATANYWHERE_API_KEY"
    ]
    for k in test_keys:
        if k in os.environ:
            old_env[k] = os.environ[k]
            del os.environ[k]

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        clear_loader_cache()
        
        groq_val = get_provider_secret("GROQ_API_KEY")
        openrouter_val = get_provider_secret("OPENROUTER_API_KEY")
        gemini_val = get_provider_secret("GEMINI_API_KEY")
        
        checks.append(("parse_alternating_groq", groq_val == "groq_secret_val"))
        checks.append(("parse_alternating_openrouter", openrouter_val == "openrouter_secret_val"))
        checks.append(("parse_export_gemini", gemini_val == "gemini_secret_val"))
        
        # 2. Key presence report is boolean-only
        presence = get_key_presence_report()
        checks.append(("presence_is_dict", isinstance(presence, dict)))
        checks.append(("presence_is_boolean", all(isinstance(v, bool) for v in presence.values())))
        checks.append(("presence_groq_true", presence.get("GROQ_API_KEY") is True))
        checks.append(("presence_non_existent_false", presence.get("CEREBRAS_API_KEY") is False))
        
        # 3. No secret leakage check
        # Convert presence to string, ensure no secrets are leaked
        presence_str = json.dumps(presence)
        checks.append(("no_secret_leakage", "groq_secret_val" not in presence_str and "gemini_secret_val" not in presence_str))
        
        # 4. AI Mode routing behavior
        r = AIRouter(health_path=None)
        
        # Test offline mode
        os.environ["JAPANAPP_AI_MODE"] = "offline"
        eligible_offline = r._eligible(AITaskRequest(AITaskType.SCENARIO_GENERATION, "x", privacy_mode="redacted"))
        checks.append(("mode_offline_only_demo", eligible_offline == ["offline_demo"]))
        
        # Test live mode
        os.environ["JAPANAPP_AI_MODE"] = "live"
        eligible_live = r._eligible(AITaskRequest(AITaskType.SCENARIO_GENERATION, "x", privacy_mode="redacted"))
        if "offline_demo" in eligible_live:
            checks.append(("mode_live_fallback_demo_last", eligible_live[-1] == "offline_demo"))
        else:
            checks.append(("mode_live_fallback_demo_last", True))
            
    finally:
        os.remove(temp_path)
        os.environ.pop("JAPANAPP_API_KEY_FILE", None)
        os.environ.pop("JAPANAPP_AI_MODE", None)
        # Restore environment variables
        for k, v in old_env.items():
            os.environ[k] = v
        clear_loader_cache()

    # 5. translation_app provider parity check
    # Check that github is in profiles, and its default model is gpt-4o-mini
    r_parity = AIRouter(health_path=None)
    checks.append(("parity_github_rename", "github" in r_parity.profiles))
    checks.append(("parity_github_models_deprecated", "github_models" not in r_parity.profiles))
    checks.append(("parity_github_default_model", r_parity.profiles["github"].default_model == "gpt-4o-mini"))
    checks.append(("parity_openrouter_free_model", r_parity.profiles["openrouter"].default_model == "meta-llama/llama-3.3-70b-instruct:free"))
    checks.append(("parity_deepseek_added", "deepseek" in r_parity.profiles))

    ok = all(v for _, v in checks)
    write_report("provider_key_loader_eval", {"ok": ok, "checks": checks})
    print("PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_eval() else 1)
