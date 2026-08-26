import pandas as pd

from analytics import HouseholdAnalytics


def test_get_category_chart_data_includes_member_breakdown():
    df = pd.DataFrame([
        {
            "transaction_type": "Debit",
            "amount": 1200,
            "category_name": "Groceries",
            "category_icon": "🛒",
            "member_name": "Alice",
        },
        {
            "transaction_type": "Debit",
            "amount": 500,
            "category_name": "Groceries",
            "category_icon": "🛒",
            "member_name": "Bob",
        },
        {
            "transaction_type": "Debit",
            "amount": 900,
            "category_name": "Rent",
            "category_icon": "🏠",
            "member_name": "Alice",
        },
        {
            "transaction_type": "Debit",
            "amount": 350,
            "category_name": "Rent",
            "category_icon": "🏠",
            "member_name": "Bob",
        },
    ])

    result = HouseholdAnalytics.get_category_chart_data(df)

    assert "members" in result
    assert len(result["labels"]) == 2
    assert len(result["members"]) >= 2
    assert any(member["member_name"] == "Alice" for member in result["members"])
    assert result["members"][0]["data"][0] >= 0
