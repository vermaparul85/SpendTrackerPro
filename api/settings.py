import os
from fastapi import APIRouter

router = APIRouter()

# In-memory settings store (persists per process; use env vars for production)
_settings = {
    "api_key": os.getenv("API_KEY", ""),
    "gcp_project": os.getenv("GCP_PROJECT", ""),
    "dataset_id": os.getenv("DATASET_ID", "spend_tracker"),
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    "db_mode": "bigquery" if os.getenv("GCP_PROJECT") else "local",
}

@router.get("")
async def get_settings():
    safe = _settings.copy()
    if safe["api_key"]:
        k = safe["api_key"]
        safe["api_key_masked"] = k[:4] + "..." + k[-4:] if len(k) > 8 else "****"
    else:
        safe["api_key_masked"] = ""
    return safe

@router.post("")
async def update_settings(body: dict):
    for key in ["api_key", "gcp_project", "dataset_id", "gemini_model", "db_mode"]:
        if key in body:
            _settings[key] = body[key]
    # Propagate API key to environment for ADK
    if "api_key" in body:
        os.environ["API_KEY"] = body["api_key"]
        os.environ["GOOGLE_API_KEY"] = body["api_key"]
    return {"success": True, "settings": {k: v for k, v in _settings.items() if k != "api_key"}}
