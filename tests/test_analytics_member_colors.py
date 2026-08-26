from unittest.mock import patch

import pandas as pd

from analytics import HouseholdAnalytics


@patch("analytics.db.get_members")
def test_member_share_chart_uses_avatar_color(mock_get_members):
    mock_get_members.return_value = pd.DataFrame([
        {"member_id": 1, "member_name": "Parul Verma", "avatar_color": "#123456"},
        {"member_id": 2, "member_name": "Amit Verma", "avatar_color": "#abcdef"},
    ])

    df = pd.DataFrame([
        {
            "transaction_date": "2024-01-01",
            "merchant_description": "Groceries",
            "clean_merchant": "Groceries",
            "amount": 100.0,
            "transaction_type": "Debit",
            "category_id": 1,
            "member_id": 1,
            "member_name": "Parul Verma",
            "bank_id": 1,
            "bank_name": "SBI",
            "category_name": "Groceries",
            "category_icon": "🛒",
            "account_id": "acc_1",
            "account_name": "Card 1",
            "upload_id": "upload_1",
        },
        {
            "transaction_date": "2024-01-02",
            "merchant_description": "Fuel",
            "clean_merchant": "Fuel",
            "amount": 50.0,
            "transaction_type": "Debit",
            "category_id": 2,
            "member_id": 2,
            "member_name": "Amit Verma",
            "bank_id": 2,
            "bank_name": "HDFC",
            "category_name": "Fuel",
            "category_icon": "⛽",
            "account_id": "acc_2",
            "account_name": "Card 2",
            "upload_id": "upload_2",
        },
    ])

    result = HouseholdAnalytics.get_member_share_chart_data(df)

    assert result["labels"] == ["Parul Verma", "Amit Verma"]
    assert result["colors"][0] == "#123456"
    assert result["colors"][1] == "#abcdef"
