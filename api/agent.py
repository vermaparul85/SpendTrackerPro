import json
import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from agents.spend_agent import stream_agent_response

router = APIRouter()

@router.post("/chat")
async def chat(body: dict):
    message = body.get("message", "").strip()
    session_id = body.get("session_id", "default")
    model_name = body.get("model_name") or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    api_key = os.getenv("API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not message:
        return JSONResponse(status_code=400, content={"error": "message is required"})
    if not api_key:
        return JSONResponse(status_code=401,
            content={"error": "API key required. Set API_KEY in the server .env file."})

    def generate():
        try:
            for chunk in stream_agent_response(message, session_id, api_key, model_name=model_name):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
