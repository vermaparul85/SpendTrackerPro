import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

APP_TITLE = "SpendTracker Pro"
APP_SUBTITLE = "Industry-Grade Household Financial Intelligence Platform"

# Cloud & Environment Variables
ENV_API_KEY = os.getenv("API_KEY", "")
ENV_GCP_PROJECT = os.getenv("GCP_PROJECT", "")
ENV_DATASET_ID = os.getenv("DATASET_ID", "spend_tracker")
ENV_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Color Palette
COLORS = {
    "bg_dark": "#0A0F1E",
    "card_bg": "rgba(15, 23, 42, 0.8)",
    "card_border": "rgba(255, 255, 255, 0.07)",
    "accent_blue": "#4F8EFF",
    "accent_emerald": "#00D18C",
    "accent_purple": "#A78BFA",
    "accent_amber": "#FFBA3B",
    "accent_rose": "#FF5B7F",
    "text_primary": "#F0F4FF",
    "text_secondary": "#8B9DC3"
}

DEFAULT_MEMBERS = [
    {"id": 1, "name": "Rahul (Self)", "role": "Primary Earner", "color": "#4F8EFF"},
]

DEFAULT_BANKS = [
    {"id": 1, "name": "HDFC Bank", "code": "HDFC", "icon": "💳"},
    {"id": 2, "name": "ICICI Bank", "code": "ICICI", "icon": "🟧"},
    {"id": 3, "name": "State Bank of India (SBI)", "code": "SBI", "icon": "🔷"},
    {"id": 4, "name": "Axis Bank", "code": "AXIS", "icon": "🔺"},
    {"id": 5, "name": "American Express (AMEX)", "code": "AMEX", "icon": "✈️"},
    {"id": 6, "name": "Kotak Mahindra Bank", "code": "KOTAK", "icon": "🔴"},
    {"id": 7, "name": "CRED Consolidated", "code": "CRED", "icon": "⚡"},
    {"id": 8, "name": "Bank of Baroda (BOB)", "code": "BOB", "icon": "🔶"}
]

DEFAULT_CATEGORIES = [
    {"id": 1, "name": "Groceries & Quick Commerce", "group": "Essentials", "icon": "🛒"},
    {"id": 2, "name": "Dining & Food Delivery", "group": "Lifestyle", "icon": "🍔"},
    {"id": 3, "name": "Shopping & E-Commerce", "group": "Lifestyle", "icon": "🛍️"},
    {"id": 4, "name": "Utilities, Bills & Rent", "group": "Essentials", "icon": "⚡"},
    {"id": 5, "name": "Fuel & Transport", "group": "Essentials", "icon": "⛽"},
    {"id": 6, "name": "Travel & Holidays", "group": "Lifestyle", "icon": "✈️"},
    {"id": 7, "name": "Entertainment & Subscriptions", "group": "Lifestyle", "icon": "🎬"},
    {"id": 8, "name": "Healthcare & Wellness", "group": "Essentials", "icon": "🏥"},
    {"id": 9, "name": "Financials, EMI & Investments", "group": "Financial", "icon": "📈"},
    {"id": 10, "name": "Uncategorized / Other", "group": "Other", "icon": "📦"},
    {"id": 11, "name": "Credit Card Payments", "group": "Financial", "icon": "💳"}
]

DEFAULT_CARDS = [
    {"id": "hdfc_regalia_1", "name": "HDFC Regalia Gold", "bank_id": 1, "member_id": 1, "type": "Credit Card", "last4": "4812", "limit": 400000.0},
    {"id": "icici_amazon_2", "name": "ICICI Amazon Pay", "bank_id": 2, "member_id": 1, "type": "Credit Card", "last4": "9102", "limit": 300000.0},
    {"id": "sbi_cashback_1", "name": "SBI Cashback Card", "bank_id": 3, "member_id": 1, "type": "Credit Card", "last4": "3341", "limit": 200000.0},
    {"id": "axis_ace_3", "name": "Axis ACE Card", "bank_id": 4, "member_id": 1, "type": "Debit Card", "last4": "7710", "limit": 50000.0},
    {"id": "hdfc_savings_joint", "name": "HDFC Salary & Savings", "bank_id": 1, "member_id": 1, "type": "Savings Account", "last4": "0049", "limit": 0.0}
]

def format_inr(amount: float) -> str:
    if amount is None:
        return "₹0.00"
    is_negative = amount < 0
    amount = abs(amount)
    s, *d = f"{amount:.2f}".split(".")
    r = []
    if len(s) > 3:
        r.append(s[-3:])
        s = s[:-3]
        while len(s) > 2:
            r.append(s[-2:])
            s = s[:-2]
        if s:
            r.append(s)
        formatted_int = ",".join(reversed(r))
    else:
        formatted_int = s
    formatted_str = f"₹{formatted_int}.{d[0]}"
    return f"-{formatted_str}" if is_negative else formatted_str

def format_lakhs(amount: float) -> str:
    if amount >= 10000000:
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:
        return f"₹{amount/100000:.2f} Lakhs"
    else:
        return format_inr(amount)
