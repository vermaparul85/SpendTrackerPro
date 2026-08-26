import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


def _sync_settings_from_env():
    """Refresh in-memory settings from the current environment so the UI never shows stale values."""
    global _settings
    _settings = {
        "api_key": os.getenv("API_KEY", ""),
        "gcp_project": os.getenv("GCP_PROJECT", ""),
        "dataset_id": os.getenv("DATASET_ID", "spend_tracker"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        "db_mode": "bigquery" if os.getenv("GCP_PROJECT") else "local",
    }


def _persist_env(key: str, value: str | None):
    """Persist selected non-secret settings to the local .env file so they survive app restarts."""
    if value is None:
        return

    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    updates = {
        "GEMINI_MODEL": "gemini_model",
        "GCP_PROJECT": "gcp_project",
        "DATASET_ID": "dataset_id",
    }

    current = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                env_key, env_value = line.split("=", 1)
                current[env_key.strip()] = env_value.strip()

    mapped_key = updates.get(key)
    if mapped_key is not None:
        env_key = key
    else:
        env_key = key

    if env_key in ["GEMINI_MODEL", "GCP_PROJECT", "DATASET_ID"]:
        current[env_key] = str(value)

    lines = []
    seen = set()
    for existing_key in current:
        if existing_key in seen:
            continue
        seen.add(existing_key)
        lines.append(f"{existing_key}={current[existing_key]}")

    # keep deterministic order for core settings
    ordered = []
    for prefer_key in ["API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL", "GCP_PROJECT", "DATASET_ID"]:
        if prefer_key in current:
            ordered.append(f"{prefer_key}={current[prefer_key]}")
    for key_name, value_text in current.items():
        if key_name not in ["API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL", "GCP_PROJECT", "DATASET_ID"]:
            ordered.append(f"{key_name}={value_text}")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ordered) + "\n")


# In-memory settings store (persists per process; production secrets are kept in .env)
_settings = {
    "api_key": os.getenv("API_KEY", ""),
    "gcp_project": os.getenv("GCP_PROJECT", ""),
    "dataset_id": os.getenv("DATASET_ID", "spend_tracker"),
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    "db_mode": "bigquery" if os.getenv("GCP_PROJECT") else "local",
}

@router.get("")
async def get_settings():
    _sync_settings_from_env()
    safe = _settings.copy()
    if safe["api_key"]:
        k = safe["api_key"]
        safe["api_key_masked"] = k[:4] + "..." + k[-4:] if len(k) > 8 else "****"
    else:
        safe["api_key_masked"] = ""
    safe["api_key_configured"] = bool(os.getenv("API_KEY") or os.getenv("GOOGLE_API_KEY"))
    return safe

@router.post("")
async def update_settings(body: dict):
    if "api_key" in body and body["api_key"]:
        return JSONResponse(status_code=400, content={"error": "Gemini API key must be set in the .env file on the server. It is never stored in the UI."})

    for key in ["gcp_project", "dataset_id", "gemini_model", "db_mode"]:
        if key in body:
            _settings[key] = body[key]
            if key == "gemini_model":
                os.environ["GEMINI_MODEL"] = str(body[key])
                _persist_env("GEMINI_MODEL", body[key])
            elif key == "gcp_project":
                os.environ["GCP_PROJECT"] = str(body[key])
                _persist_env("GCP_PROJECT", body[key])
            elif key == "dataset_id":
                os.environ["DATASET_ID"] = str(body[key])
                _persist_env("DATASET_ID", body[key])

    if body.get("db_mode") == "bigquery":
        _settings["db_mode"] = "bigquery"
    else:
        _settings["db_mode"] = "local"

    _sync_settings_from_env()
    return {"success": True, "settings": {k: v for k, v in _settings.items() if k != "api_key"}}
