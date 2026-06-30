"""Safe local API key loader for JapanApp AI Resource Layer.

Supports loading keys from D:\\Sandbox\\AIOS_habbit\\API Key.txt or an environment-configured file path.
"""
from __future__ import annotations
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache of loaded keys to avoid re-reading the file continuously
_cached_keys: dict[str, str] | None = None

ENV_TO_KEYWORDS = {
    "GEMINI_API_KEY": ["gemini"],
    "GROQ_API_KEY": ["groq"],
    "CEREBRAS_API_KEY": ["cerebras"],
    "OPENROUTER_API_KEY": ["openrouter", "open router"],
    "MISTRAL_API_KEY": ["mistral"],
    "SAMBANOVA_API_KEY": ["sambanova", "samba"],
    "CLOUDFLARE_API_TOKEN": ["cloudflare"],
    "CLOUDFLARE_ACCOUNT_ID": ["cloudflare_account", "cloudflare account"],
    "HUGGINGFACE_API_KEY": ["huggingface", "hugging face", "hugging"],
    "GITHUB_TOKEN": ["github"],
    "AI21_API_KEY": ["ai21"],
    "DEEPSEEK_API_KEY": ["deepseek"],
    "NVIDIA_API_KEY": ["nvidia"],
    "CHATANYWHERE_API_KEY": ["chatanywhere"]
}


def _load_keys_from_file() -> dict[str, str]:
    global _cached_keys
    if _cached_keys is not None:
        return _cached_keys

    _cached_keys = {}
    
    file_path_env = os.getenv("JAPANAPP_API_KEY_FILE")
    if file_path_env:
        path = Path(file_path_env)
    else:
        path = Path(r"D:\Sandbox\AIOS_habbit\API Key.txt")

    if not path.exists():
        logger.info(f"Local key file not found at {path}. Continuing gracefully.")
        return _cached_keys

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Failed to read key file at {path}: {e}")
        return _cached_keys

    # Try parsing as JSON first
    stripped = content.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, str):
                        _cached_keys[k.strip()] = v.strip()
                logger.info(f"Loaded {len(_cached_keys)} keys from JSON file {path}")
                return _cached_keys
        except Exception:
            pass

    # Fallback to line-by-line parsing
    lines = []
    for line in content.splitlines():
        line_str = line.strip()
        if line_str and not line_str.startswith("#"):
            lines.append(line_str)

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        matched = False
        
        # Check standard KEY=value or KEY:value assignments
        for sep in ["=", ":"]:
            if sep in line:
                parts = line.split(sep, 1)
                key_part = parts[0].strip()
                val_part = parts[1].strip()

                if key_part.startswith("export "):
                    key_part = key_part[7:].strip()

                if len(val_part) >= 2 and ((val_part.startswith('"') and val_part.endswith('"')) or (val_part.startswith("'") and val_part.endswith("'"))):
                    val_part = val_part[1:-1].strip()

                # If trailing separator with empty value, try using next line as the value (e.g. "Open Router:")
                if not val_part and idx + 1 < len(lines):
                    next_line = lines[idx+1].strip()
                    if "=" not in next_line and ":" not in next_line:
                        val_part = next_line
                        idx += 1  # consume next line

                # Try mapping key_part to standard keys
                mapped_key = None
                key_part_lower = key_part.lower()
                for env_key, keywords in ENV_TO_KEYWORDS.items():
                    if key_part == env_key or any(kw == key_part_lower for kw in keywords):
                        mapped_key = env_key
                        break

                if mapped_key:
                    _cached_keys[mapped_key] = val_part
                    matched = True
                    break
                elif key_part.isupper():
                    _cached_keys[key_part] = val_part
                    matched = True
                    break

        if matched:
            idx += 1
            continue

        # Alternating label/key lines format (without separators)
        if idx + 1 < len(lines):
            label = line.lower()
            val_part = lines[idx+1].strip()

            if "=" not in val_part and ":" not in val_part:
                mapped_key = None
                for env_key, keywords in ENV_TO_KEYWORDS.items():
                    if any(kw in label for kw in keywords):
                        mapped_key = env_key
                        break
                
                if mapped_key:
                    _cached_keys[mapped_key] = val_part
                    idx += 2  # consume both lines
                    continue

        idx += 1

    # Log only the key names to prevent secret leakage
    logger.info(f"Parsed keys from file {path}. Found: {list(_cached_keys.keys())}")
    return _cached_keys


def get_provider_secret(env_key: str) -> str:
    """Get secret value, checking os.environ first, then local key file fallback."""
    if not env_key:
        return ""
    val = os.getenv(env_key)
    if val:
        return val.strip()
    keys = _load_keys_from_file()
    return keys.get(env_key, "").strip()


def get_key_presence_report() -> dict[str, bool]:
    """Return presence status of keys (boolean only, no secret values)."""
    keys = _load_keys_from_file()
    all_keys = [
        "GEMINI_API_KEY", "GROQ_API_KEY", "CEREBRAS_API_KEY", "OPENROUTER_API_KEY",
        "MISTRAL_API_KEY", "SAMBANOVA_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID",
        "HUGGINGFACE_API_KEY", "GITHUB_TOKEN", "AI21_API_KEY", "DEEPSEEK_API_KEY",
        "NVIDIA_API_KEY", "CHATANYWHERE_API_KEY"
    ]
    report = {}
    for k in all_keys:
        report[k] = bool(os.getenv(k) or keys.get(k))
    return report


def clear_loader_cache() -> None:
    """Clear cached keys to force re-reading (mainly for testing)."""
    global _cached_keys
    _cached_keys = None
