from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, date, timedelta
import pandas as pd
from db import db
from analytics import analytics

router = APIRouter()

def _get_filtered_df(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    member_id: Optional[int] = None,
    bank_id: Optional[int] = None,
):
    filters = {}
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if member_id:
        filters["member_id"] = member_id
    if bank_id:
        filters["bank_id"] = bank_id

    df_filtered = db.get_transactions(filters=filters if filters else None)
    df_all = db.get_transactions()

    # Determine date range from actual data
    if not df_filtered.empty and "transaction_date" in df_filtered.columns:
        dt_series = pd.to_datetime(df_filtered["transaction_date"], errors="coerce").dropna()
        if not dt_series.empty:
            start_str = dt_series.min().strftime("%Y-%m-%d")
            end_str = dt_series.max().strftime("%Y-%m-%d")
        else:
            start_str = start_date or ""
            end_str = end_date or ""
    elif not df_all.empty and "transaction_date" in df_all.columns:
        dt_series = pd.to_datetime(df_all["transaction_date"], errors="coerce").dropna()
        if not dt_series.empty:
            start_str = dt_series.min().strftime("%Y-%m-%d")
            end_str = dt_series.max().strftime("%Y-%m-%d")
        else:
            start_str = ""
            end_str = ""
    else:
        start_str = ""
        end_str = ""

    return df_filtered, df_all, start_str, end_str


@router.get("/summary")
async def get_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    member_id: Optional[int] = None,
    bank_id: Optional[int] = None,
):
    df_filtered, df_all, start, end = _get_filtered_df(start_date, end_date, member_id, bank_id)
    metrics = analytics.get_summary_metrics(df_filtered)
    members = analytics.get_member_breakdown(df_filtered)
    top_merchants = analytics.get_top_merchants(df_filtered)
    recent = analytics.get_recent_transactions(df_all if df_filtered.empty else df_filtered, n=8)

    return {
        "metrics": metrics,
        "members": members,
        "top_merchants": top_merchants,
        "recent_transactions": recent,
        "date_range": {"start": start, "end": end},
        "total_transactions": len(df_all)
    }


@router.get("/charts")
async def get_charts(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    member_id: Optional[int] = None,
    bank_id: Optional[int] = None,
):
    df_filtered, df_all, start, end = _get_filtered_df(start_date, end_date, member_id, bank_id)
    return {
        "category_donut": analytics.get_category_chart_data(df_filtered),
        "monthly_trend": analytics.get_monthly_trend_data(df_all if not (start_date or end_date) else df_filtered),
        "high_value": analytics.get_high_value_transactions(df_filtered),
        "date_range": {"start": start, "end": end}
    }
