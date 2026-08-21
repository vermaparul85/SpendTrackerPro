from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from db import db
from parsers import parser
from categorizer import categorizer
from sample_generator import generate_sample_statements_bundle

router = APIRouter()

@router.post("/inspect")
async def inspect_statement(
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
):
    """
    Pre-scans an uploaded statement to automatically detect:
    1. Whether the statement is password-protected (encrypted)
    2. Bank Name & Bank Code (HDFC, ICICI, SBI, Axis, AMEX, Kotak, CRED, BOB, etc.)
    3. Household Member Name & ID
    4. Account / Card details & Last 4 digits
    """
    try:
        file_bytes = await file.read()
        members_df = db.get_members()
        banks_df = db.get_banks()
        cards_df = db.get_cards()

        detection = parser.detect_bank_and_member(
            file_bytes=file_bytes,
            filename=file.filename,
            members_df=members_df,
            banks_df=banks_df,
            cards_df=cards_df,
            password=password
        )

        file_hash = parser.calculate_file_hash(file_bytes)
        already_uploaded = db.is_statement_uploaded(file_hash)
        detection["already_uploaded"] = already_uploaded
        detection["file_size_kb"] = round(len(file_bytes) / 1024, 1)
        detection["filename"] = file.filename

        return detection
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to inspect statement: {e}"})


@router.post("")
async def upload_statement(
    file: UploadFile = File(...),
    account_id: Optional[str] = Form(None),
    card_name: Optional[str] = Form(None),
    last4: Optional[str] = Form(None),
    bank_code: Optional[str] = Form(None),
    member_id: Optional[int] = Form(None),
    password: Optional[str] = Form(None),
):
    """
    Ingests statement with automated Bank & Member recognition and PDF password decryption.
    """
    try:
        pdf_bytes = await file.read()
        file_hash = parser.calculate_file_hash(pdf_bytes)

        if db.is_statement_uploaded(file_hash):
            return JSONResponse(
                status_code=409,
                content={"error": "DUPLICATE_STATEMENT", "message": "This statement has already been uploaded (duplicate detected)."}
            )

        members_df = db.get_members()
        banks_df = db.get_banks()
        cards_df = db.get_cards()

        # ── 1. Auto-Detect if bank_code / member_id / account_id not provided ──
        detection = parser.detect_bank_and_member(
            file_bytes=pdf_bytes,
            filename=file.filename,
            members_df=members_df,
            banks_df=banks_df,
            cards_df=cards_df,
            password=password
        )

        # Check if PDF is encrypted and requires password
        if detection["status"] == "PASSWORD_REQUIRED":
            return JSONResponse(
                status_code=422,
                content={
                    "error": "PASSWORD_REQUIRED",
                    "message": "This statement is password-protected. Please provide the statement password to decrypt it.",
                    "detected_bank": detection["bank_name"],
                    "detected_bank_code": detection["bank_code"]
                }
            )
        elif detection["status"] == "INCORRECT_PASSWORD":
            return JSONResponse(
                status_code=422,
                content={
                    "error": "INCORRECT_PASSWORD",
                    "message": "The password provided is incorrect for this PDF statement. Please verify and try again."
                }
            )

        # Apply auto-detected values if not explicitly provided
        final_bank_code = bank_code or detection["bank_code"]
        final_member_id = int(member_id) if member_id is not None else detection["member_id"]
        final_bank_id = detection["bank_id"]
        final_account_id = account_id or detection["account_id"]

        # Ensure matching card/account exists & is updated in database
        acc_name = card_name or detection["account_name"] or f"{final_bank_code} Card"
        raw_last4 = last4 or detection.get("last4") or "0000"
        clean_last4 = str(raw_last4).replace("•", "").replace("*", "").strip()
        final_last4 = clean_last4[-4:] if len(clean_last4) >= 4 else clean_last4

        db.add_card(
            account_id=final_account_id,
            name=acc_name,
            bank_id=final_bank_id,
            member_id=final_member_id,
            acc_type="Credit Card",
            last4=final_last4,
            limit=100000.0
        )

        # ── 2. Parse Statement Transactions ─────────────────────────────────
        if file.filename.lower().endswith(".csv"):
            df_parsed, status = parser.parse_csv(pdf_bytes, file.filename, final_account_id)
        else:
            df_parsed, status = parser.parse_pdf(pdf_bytes, file.filename, final_account_id, final_bank_code, password)

        if df_parsed.empty:
            if status == "LOCKED_PDF_PASSWORD_REQUIRED":
                return JSONResponse(
                    status_code=422,
                    content={"error": "PASSWORD_REQUIRED", "message": "Statement is password-protected. Please enter password."}
                )
            elif status == "INCORRECT_PASSWORD":
                return JSONResponse(
                    status_code=422,
                    content={"error": "INCORRECT_PASSWORD", "message": "Incorrect statement password."}
                )
            else:
                return JSONResponse(
                    status_code=422,
                    content={"error": "PARSER_ERROR", "message": f"Could not extract transactions. Parser status: {status}"}
                )

        # ── 3. Auto-Categorize & Ingest ─────────────────────────────────────
        df_cat = categorizer.categorize_dataframe(df_parsed)
        df_cat["upload_id"] = file_hash
        df_cat["member_id"] = final_member_id
        df_cat["bank_id"] = final_bank_id

        records = df_cat.to_dict(orient="records")
        inserted = db.insert_transactions(records)
        total_debit = float(df_cat[df_cat["transaction_type"] == "Debit"]["amount"].sum())
        total_credit = float(df_cat[df_cat["transaction_type"] == "Credit"]["amount"].sum())

        db.log_statement_upload(
            file_hash, file.filename, "PDF" if file.filename.lower().endswith(".pdf") else "CSV",
            final_bank_code, final_member_id, len(records), total_debit, total_credit
        )

        return {
            "success": True,
            "inserted": inserted,
            "total_parsed": len(records),
            "total_debit": total_debit,
            "total_credit": total_credit,
            "status": status,
            "auto_detected": {
                "bank_code": final_bank_code,
                "bank_name": detection["bank_name"],
                "bank_icon": detection["bank_icon"],
                "member_name": detection["member_name"],
                "member_id": final_member_id,
                "account_name": detection["account_name"],
                "last4": detection.get("last4")
            },
            "preview": records[:5]
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "SERVER_ERROR", "message": str(e)})


@router.patch("/{upload_id}/member")
async def reassign_statement_member(upload_id: str, body: dict):
    """Reassigns a statement and ALL its transactions to a different member."""
    new_member_id = body.get("member_id")
    if not new_member_id:
        return JSONResponse(status_code=400, content={"error": "member_id is required"})
    try:
        db.reassign_statement_member(upload_id, int(new_member_id))
        members_df = db.get_members()
        m_row = members_df[members_df["member_id"] == int(new_member_id)]
        member_name = m_row.iloc[0]["member_name"] if not m_row.empty else "Unknown"
        return {"success": True, "member_name": member_name}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



@router.post("/sample")
async def load_sample_data():
    try:
        samples = generate_sample_statements_bundle()
        cards = db.get_cards()
        inserted_total = 0
        for s in samples:
            with open(s["path"], "rb") as f:
                pdf_bytes = f.read()
            file_hash = parser.calculate_file_hash(pdf_bytes)
            if db.is_statement_uploaded(file_hash):
                continue
            df_parsed, _ = parser.parse_pdf(pdf_bytes, s["filename"], s["account_id"], s["bank_code"])
            if df_parsed.empty:
                continue
            df_cat = categorizer.categorize_dataframe(df_parsed)
            df_cat["upload_id"] = file_hash
            df_cat["member_id"] = s["member_id"]
            card_info = cards[cards["account_id"] == s["account_id"]]
            if card_info.empty:
                continue
            df_cat["bank_id"] = int(card_info.iloc[0]["bank_id"])
            records = df_cat.to_dict(orient="records")
            inserted = db.insert_transactions(records)
            inserted_total += inserted
            total_debit = float(df_cat[df_cat["transaction_type"] == "Debit"]["amount"].sum())
            db.log_statement_upload(file_hash, s["filename"], "PDF", s["bank_code"],
                                    s["member_id"], len(records), total_debit, 0.0)

        return {"inserted": inserted_total, "message": f"Loaded {inserted_total} sample transactions."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "SERVER_ERROR", "message": str(e)})


@router.post("/reset")
async def reset_database():
    db.reset_database()
    return {"success": True, "message": "Database reset to clean state."}
