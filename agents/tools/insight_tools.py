"""
ADK Tools — Financial insight generation.
Pulls summary data from the DB and generates a structured, AI-enhanced
financial insights report for the household.
"""
import json
from datetime import datetime, timedelta


def generate_financial_insights() -> str:
    """
    Generates a comprehensive AI financial insight report for the household.
    Analyses spending patterns, flags unusual activity, compares month-over-month
    trends, and suggests actionable savings tips — all in Markdown format.
    """
    import pandas as pd
    from config import ENV_API_KEY, ENV_GEMINI_MODEL, format_inr
    from db import db

    # ── Gather data ──────────────────────────────────────────────────────────
    today = datetime.today()
    start_3m = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    start_6m = (today - timedelta(days=180)).strftime("%Y-%m-%d")
    end_dt = today.strftime("%Y-%m-%d")

    df_3m = db.get_transactions(filters={"start_date": start_3m, "end_date": end_dt})
    df_6m = db.get_transactions(filters={"start_date": start_6m, "end_date": end_dt})

    if df_3m.empty:
        return "📭 **No transaction data found.** Please upload bank statements first using the *Upload Statements* tab or click *Load Sample Statements*."

    df_deb = df_3m[df_3m["transaction_type"] == "Debit"]
    total_spend = float(df_deb["amount"].sum())
    tx_count = len(df_deb)

    # Top categories
    top_cats = (
        df_deb.groupby("category_name")["amount"]
        .sum().sort_values(ascending=False).head(5)
    )

    # Top merchants
    top_merchants = (
        df_deb.groupby("clean_merchant")["amount"]
        .sum().sort_values(ascending=False).head(5)
    )

    # High-value transactions
    hv = df_deb[df_deb["amount"] >= 10000].sort_values("amount", ascending=False).head(5)

    # Month-over-month trend (last 6 months)
    if not df_6m.empty:
        df_6m_deb = df_6m[df_6m["transaction_type"] == "Debit"].copy()
        df_6m_deb["month"] = pd.to_datetime(df_6m_deb["transaction_date"]).dt.to_period("M").astype(str)
        monthly = df_6m_deb.groupby("month")["amount"].sum().sort_index()
        months_list = monthly.index.tolist()
        amounts_list = [format_inr(v) for v in monthly.values]
        mom_trend = ", ".join(f"{m}: {a}" for m, a in zip(months_list, amounts_list))
    else:
        mom_trend = "Insufficient data for trend analysis."

    # ── Build structured context for Gemini ─────────────────────────────────
    context = {
        "period": "Last 3 months",
        "total_spend": format_inr(total_spend),
        "transaction_count": tx_count,
        "top_categories": {k: format_inr(v) for k, v in top_cats.items()},
        "top_merchants": {k: format_inr(v) for k, v in top_merchants.items()},
        "high_value_transactions": [
            {"date": row["transaction_date"], "merchant": row["clean_merchant"], "amount": format_inr(row["amount"])}
            for _, row in hv.iterrows()
        ],
        "monthly_trend": mom_trend,
    }

    # ── AI-enhanced report (if API key available) ────────────────────────────
    if ENV_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=ENV_API_KEY)

            prompt = f"""You are SpendTracker Pro's personal finance advisor for an Indian household.
Below is spending data for the last 3 months. Write a detailed, friendly, and actionable
financial insights report in **Markdown** format.

DATA:
{json.dumps(context, ensure_ascii=False, indent=2)}

Your report MUST include these sections using Markdown headers:
## 📊 Spending Overview
## 🏆 Top Spending Categories
## 🛒 Top Merchants
## ⚠️ Notable / High-Value Purchases
## 📈 Month-over-Month Trend
## 💡 Personalised Savings Tips (at least 3 specific, actionable tips based on the data)
## ✅ Quick Wins (2-3 immediate actions)

Be specific, use the actual rupee amounts from the data, and make the tone friendly and encouraging.
Keep each section concise. Use bullet points where appropriate."""

            response = client.models.generate_content(
                model=ENV_GEMINI_MODEL,
                contents=prompt,
            )
            return response.text

        except Exception:
            pass

    # ── Fallback: structured Markdown report (no AI) ─────────────────────────
    lines = [
        "## 📊 Spending Overview",
        f"- **Total spend (last 3 months):** {format_inr(total_spend)}",
        f"- **Total transactions:** {tx_count}",
        "",
        "## 🏆 Top Spending Categories",
    ]
    for cat, amt in top_cats.items():
        lines.append(f"- **{cat}:** {format_inr(amt)}")

    lines += ["", "## 🛒 Top Merchants"]
    for merchant, amt in top_merchants.items():
        lines.append(f"- **{merchant}:** {format_inr(amt)}")

    if not hv.empty:
        lines += ["", "## ⚠️ High-Value Purchases (≥ ₹10,000)"]
        for _, row in hv.iterrows():
            lines.append(f"- {row['transaction_date']} — **{row['clean_merchant']}** — {format_inr(row['amount'])}")

    lines += [
        "",
        "## 📈 Month-over-Month Trend",
        mom_trend,
        "",
        "## 💡 Tips & Recommendations",
        "- Configure a **Gemini API key** in Settings to unlock personalized AI insights and suggestions.",
        f"- Your top spending category is **{top_cats.index[0] if not top_cats.empty else 'N/A'}** — set a monthly budget for this.",
        f"- Review your recurring transactions at **{top_merchants.index[0] if not top_merchants.empty else 'N/A'}**.",
    ]

    return "\n".join(lines)
