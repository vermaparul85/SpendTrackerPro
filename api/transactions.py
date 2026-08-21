from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from typing import Optional
from db import db
from config import format_inr

router = APIRouter()

@router.get("")
async def get_transactions(
    member_id: Optional[int] = None,
    bank_id: Optional[int] = None,
    category_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    search_text: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    filters = {}
    if member_id: filters["member_id"] = member_id
    if bank_id: filters["bank_id"] = bank_id
    if category_id: filters["category_id"] = category_id
    if transaction_type: filters["transaction_type"] = transaction_type
    if search_text: filters["search_text"] = search_text
    if start_date: filters["start_date"] = start_date
    if end_date: filters["end_date"] = end_date

    df = db.get_transactions(filters=filters if filters else None)
    total = len(df)
    start_idx = (page - 1) * page_size
    df_page = df.iloc[start_idx: start_idx + page_size]

    records = []
    for _, r in df_page.iterrows():
        records.append({
            "transaction_id": str(r["transaction_id"]),
            "transaction_date": str(r["transaction_date"]),
            "merchant_description": str(r["merchant_description"]),
            "clean_merchant": str(r["clean_merchant"]),
            "amount": round(float(r["amount"]), 2),
            "amount_fmt": format_inr(float(r["amount"])),
            "transaction_type": str(r["transaction_type"]),
            "category_id": int(r["category_id"]),
            "category_name": str(r["category_name"]),
            "category_icon": str(r["category_icon"]),
            "member_id": int(r["member_id"]),
            "member_name": str(r["member_name"]),
            "bank_id": int(r["bank_id"]),
            "bank_name": str(r["bank_name"]),
            "account_id": str(r["account_id"]),
            "account_name": str(r["account_name"]),
            "upload_id": str(r.get("upload_id") or ""),
        })

    return {"total": total, "page": page, "page_size": page_size,
            "pages": (total + page_size - 1) // page_size, "transactions": records}

@router.patch("/{transaction_id}/category")
async def update_category(transaction_id: str, body: dict):
    category_id = body.get("category_id")
    if not category_id:
        return JSONResponse(status_code=400, content={"error": "category_id required"})
    db.update_transaction_category(transaction_id, int(category_id))
    return {"success": True}

@router.patch("/{transaction_id}/member")
async def update_member(transaction_id: str, body: dict):
    member_id = body.get("member_id")
    if not member_id:
        return JSONResponse(status_code=400, content={"error": "member_id required"})
    db.update_transaction_member(transaction_id, int(member_id))
    return {"success": True}
