import os
import tempfile
import pytest
from pathlib import Path
from frontend.models.ai_provider import ProviderProfile, AITaskType, ProviderHealth
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_router import AIRouter
from frontend.services.ai_providers.local_key_loader import (
    get_provider_secret,
    get_key_presence_report,
    clear_loader_cache,
)
from frontend.services.ai_providers.gemini_provider import GeminiProvider
from frontend.services.ai_providers.openai_compatible_provider import OpenAICompatibleProvider
from frontend.services.japanese_work_memory import JapaneseWorkLearningMemory
from frontend.services.jp_business_hell_ai import JPBusinessHellAI


@pytest.fixture(autouse=True)
def clean_env_and_cache():
    # Store clean environment and clear loader cache
    old_env = dict(os.environ)
    clear_loader_cache()
    # Remove keys to isolate tests
    for k in [
        "GEMINI_API_KEY", "GROQ_API_KEY", "CEREBRAS_API_KEY", "OPENROUTER_API_KEY",
        "MISTRAL_API_KEY", "SAMBANOVA_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID",
        "HUGGINGFACE_API_KEY", "GITHUB_TOKEN", "AI21_API_KEY", "DEEPSEEK_API_KEY",
        "NVIDIA_API_KEY", "CHATANYWHERE_API_KEY", "JAPANAPP_API_KEY_FILE", "JAPANAPP_AI_MODE"
    ]:
        os.environ.pop(k, None)
    yield
    os.environ.clear()
    os.environ.update(old_env)
    clear_loader_cache()


def test_loader_parses_equals_format():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("export GROQ_API_KEY=groq_secret_123\n")
        f.write("MISTRAL_API_KEY = mistral_secret_456\n")
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        assert get_provider_secret("GROQ_API_KEY") == "groq_secret_123"
        assert get_provider_secret("MISTRAL_API_KEY") == "mistral_secret_456"
    finally:
        os.remove(temp_path)


def test_loader_parses_colon_format():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Open Router: openrouter_secret_789\n")
        f.write("Cerebras:cerebras_secret_abc\n")
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        assert get_provider_secret("OPENROUTER_API_KEY") == "openrouter_secret_789"
        assert get_provider_secret("CEREBRAS_API_KEY") == "cerebras_secret_abc"
    finally:
        os.remove(temp_path)


def test_loader_parses_json_format():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write('{"GEMINI_API_KEY": "gemini_secret_json", "SAMBANOVA_API_KEY": "samba_secret_json"}')
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        assert get_provider_secret("GEMINI_API_KEY") == "gemini_secret_json"
        assert get_provider_secret("SAMBANOVA_API_KEY") == "samba_secret_json"
    finally:
        os.remove(temp_path)


def test_loader_parses_alternating_format():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Groq API Key\n")
        f.write("groq_alt_secret\n")
        f.write("Open Router:\n")
        f.write("openrouter_alt_secret\n")
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        assert get_provider_secret("GROQ_API_KEY") == "groq_alt_secret"
        assert get_provider_secret("OPENROUTER_API_KEY") == "openrouter_alt_secret"
    finally:
        os.remove(temp_path)


def test_env_var_overrides_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("GROQ_API_KEY=file_secret\n")
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        os.environ["GROQ_API_KEY"] = "env_override_secret"
        assert get_provider_secret("GROQ_API_KEY") == "env_override_secret"
    finally:
        os.remove(temp_path)


def test_key_presence_report_contains_booleans_only():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("GROQ_API_KEY=groq_secret\n")
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        report = get_key_presence_report()
        for k, v in report.items():
            assert isinstance(v, bool)
        assert report["GROQ_API_KEY"] is True
        assert report["GEMINI_API_KEY"] is False
    finally:
        os.remove(temp_path)


def test_provider_adapters_use_key_loader():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("GEMINI_API_KEY=gemini_loader_test\n")
        f.write("GROQ_API_KEY=groq_loader_test\n")
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        
        # Gemini adapter check
        gemini_prof = ProviderProfile("gemini", "Gemini", True, "gemini-2.5-flash", "GEMINI_API_KEY", priority=30)
        gemini_prov = GeminiProvider(gemini_prof)
        assert gemini_prov._api_key() == "gemini_loader_test"
        assert gemini_prov.is_available() is True
        
        # OpenAICompatible adapter check
        groq_prof = ProviderProfile("groq", "Groq", True, "llama3-8b-8192", "GROQ_API_KEY", base_url="https://api.groq.com/openai/v1")
        groq_prov = OpenAICompatibleProvider(groq_prof)
        assert groq_prov._api_key() == "groq_loader_test"
        assert groq_prov.is_available() is True
    finally:
        os.remove(temp_path)


def test_missing_key_skips_safely():
    # If key file does not exist, get_provider_secret should return "" and not crash
    os.environ["JAPANAPP_API_KEY_FILE"] = "non_existent_file_path.txt"
    assert get_provider_secret("GROQ_API_KEY") == ""
    
    prof = ProviderProfile("groq", "Groq", True, "llama3-8b-8192", "GROQ_API_KEY", base_url="https://api.groq.com/openai/v1")
    prov = OpenAICompatibleProvider(prof)
    assert prov.is_available() is False
    resp = prov.generate(AITaskRequest(AITaskType.SCENARIO_GENERATION, "x"))
    assert resp.ok is False
    assert resp.error_type == "missing_key"
    assert "groq_loader_test" not in resp.error_message


def test_ai_mode_offline_selects_offline_demo_only():
    os.environ["JAPANAPP_AI_MODE"] = "offline"
    r = AIRouter(health_path=None)
    # Ensure offline mode filters out everything except offline_demo
    eligible = r._eligible(AITaskRequest(AITaskType.SCENARIO_GENERATION, "x", privacy_mode="redacted"))
    assert eligible == ["offline_demo"]


def test_ai_mode_live_prefers_live_provider():
    os.environ["JAPANAPP_AI_MODE"] = "live"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("GROQ_API_KEY=groq_live_key\n")
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        r = AIRouter(health_path=None)
        # Ensure groq is enabled and available
        r.profiles["groq"].enabled = True
        
        eligible = r._eligible(AITaskRequest(AITaskType.SCENARIO_GENERATION, "x", privacy_mode="redacted"))
        assert "groq" in eligible
        assert "offline_demo" in eligible
        # 'offline_demo' should be the last item in the list
        assert eligible[-1] == "offline_demo"
    finally:
        os.remove(temp_path)


def test_local_only_mode_never_calls_external_providers():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("GROQ_API_KEY=groq_test_key\n")
        temp_path = f.name

    try:
        os.environ["JAPANAPP_API_KEY_FILE"] = temp_path
        prof = ProviderProfile("groq", "Groq", True, "llama3-8b-8192", "GROQ_API_KEY", base_url="https://api.groq.com/openai/v1")
        prov = OpenAICompatibleProvider(prof)
        
        req = AITaskRequest(AITaskType.SCENARIO_GENERATION, "x", privacy_mode="local_only")
        resp = prov.generate(req)
        assert resp.ok is False
        assert resp.error_type == "privacy_blocked"
    finally:
        os.remove(temp_path)


def test_jp_business_hell_works_offline_without_keys(tmp_path):
    # Make sure JPBusinessHellAI runs without keys and defaults to offline_demo.
    # Use temporary memory so this regression test never mutates real learning memory.
    memory = JapaneseWorkLearningMemory(tmp_path / "jp_hell_memory.json", mode="synthetic")
    app = JPBusinessHellAI(memory=memory)
    scenario = app.generate_scenario(privacy_mode="synthetic")
    assert scenario["provider_used"] == "offline_demo"
    
    feedback = app.grade_answer(scenario, "どうもありがとうございます", privacy_mode="synthetic")
    assert feedback["provider_used"] == "offline_demo"
