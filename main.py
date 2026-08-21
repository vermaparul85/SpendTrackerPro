from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from api import dashboard, transactions, upload, members, rules, insights, agent, settings

app = FastAPI(title="SpendTracker Pro API", version="1.0.0")

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(dashboard,     prefix="/api/dashboard",     tags=["Dashboard"])
app.include_router(transactions,  prefix="/api/transactions",  tags=["Transactions"])
app.include_router(upload,        prefix="/api/upload",        tags=["Upload"])
app.include_router(members,       prefix="/api/members",       tags=["Members"])
app.include_router(rules,         prefix="/api/rules",         tags=["Rules"])
app.include_router(insights,      prefix="/api/insights",      tags=["Insights"])
app.include_router(agent,         prefix="/api/agent",         tags=["AI Agent"])
app.include_router(settings,      prefix="/api/settings",      tags=["Settings"])

# ── Disable browser caching for live development ────────────────────────────
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ── Static SPA ────────────────────────────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
async def serve_spa():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/{full_path:path}", include_in_schema=False)
async def catch_all(full_path: str):
    """Catch-all: return index.html for any non-API route (SPA routing)."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"), headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
