from fastapi import APIRouter
from fastapi.responses import JSONResponse
from db import db

router = APIRouter()

# ── Members ───────────────────────────────────────────────────────────────────
@router.get("")
async def get_members():
    df = db.get_members()
    return df.to_dict(orient="records")

@router.post("")
async def add_member(body: dict):
    name = body.get("name", "").strip()
    role = body.get("role", "Member").strip()
    color = body.get("color", "#4F8EFF")
    if not name:
        return JSONResponse(status_code=400, content={"error": "Name is required"})
    db.add_member(name, role, color)
    return {"success": True}

@router.patch("/{member_id}")
async def update_member(member_id: int, body: dict):
    name = (body.get("name") or "").strip()
    role = (body.get("role") or "Member").strip()
    color = body.get("color")

    if not name:
        return JSONResponse(status_code=400, content={"error": "Name is required"})

    try:
        db.update_member(member_id, name, role, color)
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@router.delete("/{member_id}")
async def delete_member(member_id: int):
    try:
        db.delete_member(member_id)
        return {"success": True}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

# ── Banks ─────────────────────────────────────────────────────────────────────
@router.get("/banks")
async def get_banks():
    df = db.get_banks()
    return df.to_dict(orient="records")

# ── Cards ─────────────────────────────────────────────────────────────────────
@router.get("/cards")
async def get_cards():
    df = db.get_cards()
    return df.to_dict(orient="records")

@router.post("/cards")
async def add_card(body: dict):
    try:
        db.add_card(
            account_id=body["account_id"],
            name=body["name"],
            bank_id=int(body["bank_id"]),
            member_id=int(body["member_id"]),
            acc_type=body["account_type"],
            last4=body.get("last4", ""),
            limit=float(body.get("credit_limit", 0)),
        )
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@router.patch("/cards/{account_id}")
async def update_card(account_id: str, body: dict):
    try:
        updates = {}
        if "name" in body or "account_name" in body:
            updates["account_name"] = body.get("name") or body.get("account_name")
        if "last4" in body:
            # Clean last4 to 4 digits
            raw_last4 = str(body["last4"]).replace("•", "").replace("*", "").strip()
            updates["last4"] = raw_last4[-4:] if len(raw_last4) >= 4 else raw_last4
        if "member_id" in body and body["member_id"] is not None:
            updates["member_id"] = int(body["member_id"])
        if "bank_id" in body and body["bank_id"] is not None:
            updates["bank_id"] = int(body["bank_id"])
        if "account_type" in body:
            updates["account_type"] = body["account_type"]
        if "credit_limit" in body and body["credit_limit"] is not None:
            updates["credit_limit"] = float(body["credit_limit"])

        success = db.update_card(account_id, updates)
        if not success:
            return JSONResponse(status_code=400, content={"error": "No valid fields provided to update"})
        return {"success": True, "message": "Card updated successfully"}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@router.delete("/cards/{account_id}")
async def delete_card(account_id: str):
    success, msg = db.delete_card(account_id)
    if not success:
        return JSONResponse(status_code=400, content={"error": msg})
    return {"success": True, "message": msg}

