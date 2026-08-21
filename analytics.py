"""
SpendTracker Pro — Analytics (data-only, no Plotly)
Returns plain Python dicts/lists for the JS frontend to render with Chart.js.
"""
import pandas as pd
from typing import Dict, Any, List
from config import format_inr, format_lakhs
from db import db


class HouseholdAnalytics:
    """Pure-data analytics layer. All chart rendering is done in JS/Chart.js."""

    @staticmethod
    def get_summary_metrics(df_tx: pd.DataFrame) -> Dict[str, Any]:
        if df_tx.empty:
            return {
                "total_spend": 0.0,
                "total_spend_fmt": "₹0.00",
                "top_category": "N/A",
                "top_category_amt": 0.0,
                "top_category_amt_fmt": "₹0.00",
                "bank_count": 0,
                "tx_count": 0,
                "high_val_count": 0,
                "total_credit": 0.0,
                "total_credit_fmt": "₹0.00",
            }

        df_debits = df_tx[df_tx["transaction_type"] == "Debit"]
        df_credits = df_tx[df_tx["transaction_type"] == "Credit"]
        total_spend = float(df_debits["amount"].sum())
        total_credit = float(df_credits["amount"].sum())

        target_df = df_debits if not df_debits.empty else df_tx
        cat_spends = target_df.groupby("category_name")["amount"].sum()
        top_category = str(cat_spends.idxmax()) if not cat_spends.empty else "N/A"
        top_category_amt = float(cat_spends.max()) if not cat_spends.empty else 0.0

        bank_count = int(df_tx["bank_name"].nunique()) if "bank_name" in df_tx.columns else 0

        return {
            "total_spend": round(total_spend, 2),
            "total_spend_fmt": format_inr(total_spend),
            "total_credit": round(total_credit, 2),
            "total_credit_fmt": format_inr(total_credit),
            "top_category": top_category,
            "top_category_amt": round(top_category_amt, 2),
            "top_category_amt_fmt": format_inr(top_category_amt),
            "bank_count": bank_count,
            "tx_count": len(df_tx),
            "high_val_count": int(len(df_debits[df_debits["amount"] >= 10000.0])),
        }

    @staticmethod
    def get_category_chart_data(df_tx: pd.DataFrame) -> Dict[str, Any]:
        """Returns donut chart data for spending by category."""
        if df_tx.empty:
            return {"labels": [], "data": [], "formatted": [], "colors": []}

        df_debits = df_tx[df_tx["transaction_type"] == "Debit"]
        target_df = df_debits if not df_debits.empty else df_tx

        cat = target_df.groupby("category_name").agg(
            amount=("amount", "sum"),
            category_icon=("category_icon", lambda s: s.dropna().iloc[0] if not s.dropna().empty else "🏷️")
        ).reset_index()
        cat = cat.sort_values("amount", ascending=False)

        palette = [
            "#4F8EFF", "#00D18C", "#FFBA3B", "#FF5B7F", "#A78BFA",
            "#38BDF8", "#FB923C", "#4ADE80", "#F472B6", "#94A3B8"
        ]

        labels = []
        for _, row in cat.iterrows():
            icon = row.get("category_icon") or "🏷️"
            labels.append(f"{icon} {row['category_name']}")

        return {
            "labels": labels,
            "data": [round(float(row["amount"]), 2) for _, row in cat.iterrows()],
            "formatted": [format_inr(float(row["amount"])) for _, row in cat.iterrows()],
            "colors": palette[:len(cat)],
        }

    @staticmethod
    def get_monthly_trend_data(df_tx: pd.DataFrame) -> Dict[str, Any]:
        """Returns stacked bar chart data for monthly spend trend with member breakdown."""
        if df_tx.empty:
            return {"labels": [], "debit": [], "credit": [], "members": []}

        df_copy = df_tx.copy()
        df_copy["dt"] = pd.to_datetime(df_copy["transaction_date"], errors="coerce")
        df_copy = df_copy.dropna(subset=["dt"])

        if df_copy.empty:
            return {"labels": [], "debit": [], "credit": [], "members": []}

        df_copy["month"] = df_copy["dt"].dt.strftime("%b %Y")
        df_copy["sort_key"] = df_copy["dt"].dt.strftime("%Y-%m")

        months_order = df_copy.sort_values("sort_key")["month"].unique().tolist()

        df_debits = df_copy[df_copy["transaction_type"] == "Debit"]
        df_credits = df_copy[df_copy["transaction_type"] == "Credit"]

        debit_by_month = (
            df_debits.groupby("month")["amount"].sum()
        )
        credit_by_month = (
            df_credits.groupby("month")["amount"].sum()
        )

        # ── Member Breakdown By Month ───────────────────────────────────────
        members_df = db.get_members()
        member_palette = [
            "#4F8EFF", "#FF8B4D", "#EA4DFF", "#00D18C", "#FFBA3B",
            "#38BDF8", "#F472B6", "#A78BFA", "#FB923C", "#4ADE80"
        ]

        members_list = []
        if not df_debits.empty and "member_id" in df_debits.columns:
            # Active members present in debits
            active_m_ids = df_debits["member_id"].dropna().unique().tolist()
            # Also include all registered household members
            if not members_df.empty:
                for mid in members_df["member_id"].unique():
                    if mid not in active_m_ids:
                        active_m_ids.append(mid)

            for idx, m_id in enumerate(active_m_ids):
                m_match = members_df[members_df["member_id"] == m_id] if not members_df.empty else None
                if m_match is not None and not m_match.empty:
                    m_name = str(m_match.iloc[0]["member_name"])
                    m_color = str(m_match.iloc[0].get("avatar_color") or member_palette[idx % len(member_palette)])
                else:
                    m_tx = df_debits[df_debits["member_id"] == m_id]
                    m_name = str(m_tx.iloc[0]["member_name"]) if not m_tx.empty and "member_name" in m_tx.columns else f"Member {m_id}"
                    m_color = member_palette[idx % len(member_palette)]

                m_subset = df_debits[df_debits["member_id"] == m_id]
                m_debits_series = m_subset.groupby("month")["amount"].sum() if not m_subset.empty else pd.Series()
                data_vals = [round(float(m_debits_series.get(m, 0.0)), 2) for m in months_order]

                # Only include if spent > 0 in at least one month or registered member
                if sum(data_vals) > 0 or (m_match is not None and not m_match.empty):
                    members_list.append({
                        "member_id": int(m_id),
                        "member_name": m_name,
                        "color": m_color,
                        "data": data_vals,
                        "total": round(float(sum(data_vals)), 2),
                        "total_fmt": format_inr(float(sum(data_vals))),
                    })

        return {
            "labels": months_order,
            "debit": [round(float(debit_by_month.get(m, 0)), 2) for m in months_order],
            "credit": [round(float(credit_by_month.get(m, 0)), 2) for m in months_order],
            "members": members_list,
        }

    @staticmethod
    def get_top_merchants(df_tx: pd.DataFrame, n: int = 8) -> List[Dict]:
        if df_tx.empty:
            return []
        df_debits = df_tx[df_tx["transaction_type"] == "Debit"]
        target = df_debits if not df_debits.empty else df_tx
        top = (target.groupby("clean_merchant")["amount"]
               .sum().sort_values(ascending=False).head(n).reset_index())
        total = float(top["amount"].sum()) or 1.0
        return [{
            "merchant": str(row["clean_merchant"]),
            "amount": round(float(row["amount"]), 2),
            "amount_fmt": format_inr(float(row["amount"])),
            "pct": round(float(row["amount"]) / total * 100, 1)
        } for _, row in top.iterrows()]

    @staticmethod
    def get_member_breakdown(df_tx: pd.DataFrame) -> List[Dict]:
        members_df = db.get_members()
        if df_tx.empty:
            return [{
                "member_id": int(r["member_id"]),
                "member_name": r["member_name"],
                "role": r["role"],
                "avatar_color": r["avatar_color"],
                "spent": 0.0,
                "spent_fmt": "₹0.00"
            } for _, r in members_df.iterrows()]

        df_debits = df_tx[df_tx["transaction_type"] == "Debit"]
        spend_by_member = df_debits.groupby("member_id")["amount"].sum().reset_index()
        merged = pd.merge(members_df, spend_by_member, on="member_id", how="left").fillna({"amount": 0.0})
        merged = merged.rename(columns={"amount": "spent"})
        return [{
            "member_id": int(r["member_id"]),
            "member_name": r["member_name"],
            "role": r["role"],
            "avatar_color": r["avatar_color"],
            "spent": round(float(r["spent"]), 2),
            "spent_fmt": format_inr(float(r["spent"]))
        } for _, r in merged.iterrows()]

    @staticmethod
    def get_recent_transactions(df_tx: pd.DataFrame, n: int = 10) -> List[Dict]:
        if df_tx.empty:
            return []
        recent = df_tx.head(n)
        return [{
            "transaction_id": str(r["transaction_id"]),
            "transaction_date": str(r["transaction_date"]),
            "clean_merchant": str(r["clean_merchant"]),
            "amount": round(float(r["amount"]), 2),
            "amount_fmt": format_inr(float(r["amount"])),
            "transaction_type": str(r["transaction_type"]),
            "category_name": str(r.get("category_name", "Uncategorized")),
            "category_icon": str(r.get("category_icon", "🏷️")),
            "member_name": str(r.get("member_name", "Household")),
            "bank_name": str(r.get("bank_name", "Bank"))
        } for _, r in recent.iterrows()]

    @staticmethod
    def get_high_value_transactions(df_tx: pd.DataFrame, threshold: float = 10000.0) -> List[Dict]:
        if df_tx.empty:
            return []
        df_debits = df_tx[df_tx["transaction_type"] == "Debit"]
        hv = df_debits[df_debits["amount"] >= threshold].head(20)
        return [{
            "transaction_date": str(r["transaction_date"]),
            "clean_merchant": str(r["clean_merchant"]),
            "amount": round(float(r["amount"]), 2),
            "amount_fmt": format_inr(float(r["amount"])),
            "category_name": str(r.get("category_name", "Uncategorized")),
            "member_name": str(r.get("member_name", "Household"))
        } for _, r in hv.iterrows()]


analytics = HouseholdAnalytics()
