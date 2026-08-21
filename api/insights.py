from fastapi import APIRouter
from fastapi.responses import JSONResponse
from agents.tools.insight_tools import generate_financial_insights

router = APIRouter()

@router.get("")
async def get_insights():
    try:
        report = generate_financial_insights()
        return {"report": report, "format": "markdown"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
