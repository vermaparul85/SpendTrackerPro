from fastapi import APIRouter
from fastapi.responses import JSONResponse
from db import db

router = APIRouter()

@router.get("")
async def get_rules():
    df = db.get_rules()
    return df.to_dict(orient="records")

@router.post("")
async def add_rule(body: dict):
    try:
        db.add_rule(
            keyword=body["keyword"],
            category_id=int(body["category_id"]),
            clean_merchant=body.get("clean_merchant", ""),
            member_id=body.get("member_id"),
        )
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@router.get("/categories")
async def get_categories():
    df = db.get_categories()
    return df.to_dict(orient="records")

@router.get("/statements")
async def get_statements():
    df = db.get_statements_log()
    return df.to_dict(orient="records")
