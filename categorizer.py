import pandas as pd
from typing import List, Dict, Any, Tuple
from db import db

class ExpenseCategorizer:
    """Auto-categorization engine matching clean merchant strings against rules database."""

    def __init__(self):
        self.rules_df = None
        self.refresh_rules()

    def refresh_rules(self):
        """Loads latest categorization rules from DB."""
        self.rules_df = db.get_rules()

    def categorize_transaction(self, merchant_description: str, clean_merchant: str) -> Tuple[int, str]:
        """
        Returns (category_id, clean_merchant_name).
        Matches against DB rules (keywords sorted by priority).
        """
        if self.rules_df is None or self.rules_df.empty:
            self.refresh_rules()

        desc_upper = str(merchant_description).upper()
        clean_upper = str(clean_merchant).upper()

        if self.rules_df is not None and not self.rules_df.empty:
            for _, rule in self.rules_df.iterrows():
                kw = str(rule["keyword"]).upper()
                if kw in clean_upper or kw in desc_upper:
                    category_id = int(rule["category_id"])
                    rule_clean = rule.get("clean_merchant")
                    final_clean = rule_clean if rule_clean else clean_merchant
                    return category_id, final_clean

        # Default Fallback: Uncategorized (Category 10)
        return 10, clean_merchant

    def categorize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categorizes all rows in a parsed statement DataFrame."""
        if df.empty:
            return df

        categories = []
        clean_merchants = []

        for _, row in df.iterrows():
            cat_id, clean_m = self.categorize_transaction(
                row.get("merchant_description", ""),
                row.get("clean_merchant", "")
            )
            categories.append(cat_id)
            clean_merchants.append(clean_m)

        df["category_id"] = categories
        df["clean_merchant"] = clean_merchants
        return df

# Singleton Categorizer Instance
categorizer = ExpenseCategorizer()
