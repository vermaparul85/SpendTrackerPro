"""
ADK Tools — Query Tools
Wrap the SpendTracker DB singleton so the Gemini agent can fetch
financial data in a structured, readable format.
"""
import json
from datetime import datetime, timedelta
from typing import Optional


def _db():
    from db import db
    return db


def _fmt(amount: float) -> str:
    from config import format_inr
    return format_inr(amount)


def _date_range(months: int):
    end = datetime.today()
    start = end - timedelta(days=months * 30)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def get_spending_summary(months: int = 3) -> str:
    """
    Returns a high-level spending summary for the last N months.
    Includes total spend, top 5 categories, top 5 merchants, and credit vs debit totals.
    """
    start_date, end_date = _date_range(months)
    df = _db().get_transactions(filters={"start_date": start_date, "end_date": end_date})

    if df.empty:
        return json.dumps({"message": "No transactions found in this period.", "total_debit": 0})

    df_deb = df[df["transaction_type"] == "Debit"]
    df_cred = df[df["transaction_type"] == "Credit"]

    total_debit = float(df_deb["amount"].sum())
    total_credit = float(df_cred["amount"].sum())

    top_cats = (
        df_deb.groupby("category_name")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
        .rename(columns={"amount": "total"})
    )
    top_cats["total_fmt"] = top_cats["total"].apply(_fmt)

    top_merchants = (
        df_deb.groupby("clean_merchant")["amount"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
        .rename(columns={"amount": "total"})
    )
    top_merchants["total_fmt"] = top_merchants["total"].apply(_fmt)

    result = {
        "date_range": f"{start_date} to {end_date}",
        "total_debit": total_debit,
        "total_debit_fmt": _fmt(total_debit),
        "total_credit": total_credit,
        "total_credit_fmt": _fmt(total_credit),
        "transaction_count": len(df),
        "top_categories": top_cats[["category_name", "total_fmt"]].to_dict(orient="records"),
        "top_merchants": top_merchants[["clean_merchant", "total_fmt"]].to_dict(orient="records"),
    }
    return json.dumps(result, ensure_ascii=False)


def get_category_breakdown(category_name: str, months: int = 3) -> str:
    """
    Returns individual transactions for a specific spending category.
    """
    start_date, end_date = _date_range(months)
    df = _db().get_transactions(filters={"start_date": start_date, "end_date": end_date})

    if df.empty:
        return json.dumps({"message": "No transactions found."})

    mask = df["category_name"].str.lower().str.contains(category_name.lower(), na=False)
    df_cat = df[mask & (df["transaction_type"] == "Debit")]

    if df_cat.empty:
        return json.dumps({"message": f"No debit transactions found for category '{category_name}'."})

    records = df_cat[["transaction_date", "clean_merchant", "amount", "member_name"]].head(30).copy()
    records["amount_fmt"] = records["amount"].apply(_fmt)

    return json.dumps({
        "category": category_name,
        "total": _fmt(float(df_cat["amount"].sum())),
        "count": len(df_cat),
        "transactions": records[["transaction_date", "clean_merchant", "amount_fmt", "member_name"]].to_dict(orient="records"),
    }, ensure_ascii=False)


def get_merchant_history(merchant_name: str) -> str:
    """
    Returns all transactions for a specific merchant name.
    """
    df = _db().get_transactions(filters={"search_text": merchant_name})

    if df.empty:
        return json.dumps({"message": f"No transactions found for merchant '{merchant_name}'."})

    df_deb = df[df["transaction_type"] == "Debit"]
    records = df[["transaction_date", "clean_merchant", "amount", "transaction_type", "category_name"]].head(20).copy()
    records["amount_fmt"] = records["amount"].apply(_fmt)

    return json.dumps({
        "merchant": merchant_name,
        "total_debit": _fmt(float(df_deb["amount"].sum())),
        "count": len(df),
        "transactions": records[["transaction_date", "clean_merchant", "amount_fmt", "transaction_type", "category_name"]].to_dict(orient="records"),
    }, ensure_ascii=False)


def get_high_value_transactions(threshold: float = 10000.0, months: int = 3) -> str:
    """
    Returns large debit transactions above a rupee threshold in the last N months.
    """
    start_date, end_date = _date_range(months)
    df = _db().get_transactions(filters={
        "start_date": start_date,
        "end_date": end_date,
        "transaction_type": "Debit",
    })

    if df.empty:
        return json.dumps({"message": "No transactions found."})

    df_hv = df[df["amount"] >= threshold].sort_values("amount", ascending=False).head(20)

    if df_hv.empty:
        return json.dumps({"message": f"No transactions above {_fmt(threshold)} in this period."})

    records = df_hv[["transaction_date", "clean_merchant", "amount", "category_name", "member_name"]].copy()
    records["amount_fmt"] = records["amount"].apply(_fmt)

    return json.dumps({
        "threshold": _fmt(threshold),
        "count": len(df_hv),
        "transactions": records[["transaction_date", "clean_merchant", "amount_fmt", "category_name", "member_name"]].to_dict(orient="records"),
    }, ensure_ascii=False)


def get_member_spends(months: int = 3) -> str:
    """
    Returns total spending broken down by household member for the last N months.
    """
    start_date, end_date = _date_range(months)
    df = _db().get_transactions(filters={
        "start_date": start_date,
        "end_date": end_date,
        "transaction_type": "Debit",
    })

    if df.empty:
        return json.dumps({"message": "No transactions found."})

    breakdown = (
        df.groupby("member_name")
        .agg(total=("amount", "sum"), count=("amount", "count"))
        .reset_index()
        .sort_values("total", ascending=False)
    )
    breakdown["total_fmt"] = breakdown["total"].apply(_fmt)

    return json.dumps({
        "date_range": f"{start_date} to {end_date}",
        "members": breakdown[["member_name", "total_fmt", "count"]].to_dict(orient="records"),
    }, ensure_ascii=False)


def get_monthly_trend(months: int = 6) -> str:
    """
    Returns month-over-month spending trend for the last N months.
    """
    import pandas as pd
    start_date, end_date = _date_range(months)
    df = _db().get_transactions(filters={"start_date": start_date, "end_date": end_date})

    if df.empty:
        return json.dumps({"message": "No transactions found."})

    df["month"] = pd.to_datetime(df["transaction_date"]).dt.to_period("M").astype(str)

    debit_trend = (
        df[df["transaction_type"] == "Debit"]
        .groupby("month")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_debit"})
    )
    credit_trend = (
        df[df["transaction_type"] == "Credit"]
        .groupby("month")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_credit"})
    )
    trend = debit_trend.merge(credit_trend, on="month", how="outer").fillna(0)
    trend = trend.sort_values("month")
    trend["total_debit_fmt"] = trend["total_debit"].apply(_fmt)
    trend["total_credit_fmt"] = trend["total_credit"].apply(_fmt)

    return json.dumps({
        "months": months,
        "trend": trend[["month", "total_debit_fmt", "total_credit_fmt"]].to_dict(orient="records"),
    }, ensure_ascii=False)
