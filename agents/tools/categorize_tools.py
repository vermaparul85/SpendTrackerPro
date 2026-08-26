"""
ADK Tools — AI-powered transaction categorization.
Uses Gemini directly (via google.genai) to classify a transaction description
into one of the app's defined categories. Falls back to rule-based categorizer
if no API key is available.
"""
import json

_CATEGORY_LIST = """
1. Groceries & Quick Commerce (Essentials)
2. Dining & Food Delivery (Lifestyle)
3. Shopping & E-Commerce (Lifestyle)
4. Utilities, Bills & Rent (Essentials)
5. Fuel & Transport (Essentials)
6. Travel & Holidays (Lifestyle)
7. Entertainment & Subscriptions (Lifestyle)
8. Healthcare & Wellness (Essentials)
9. Financials, EMI & Investments (Financial)
10. Uncategorized / Other
"""


def ai_categorize_transaction(description: str, merchant: str = "") -> str:
    """
    Uses AI to categorize a bank transaction into one of the SpendTracker categories.
    Ideal for transactions that the rule-based system cannot match.
    """
    from config import ENV_API_KEY, ENV_GEMINI_MODEL
    from categorizer import categorizer

    # --- Rule-based first pass ---
    cat_id, clean_m = categorizer.categorize_transaction(description, merchant or description)
    rule_based = cat_id != 10  # 10 = Uncategorized

    # --- AI enhancement when API key present ---
    if ENV_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=ENV_API_KEY)

            prompt = f"""You are a financial transaction categorizer for Indian households.
Given the transaction below, pick the SINGLE best category from this list:
{_CATEGORY_LIST}

Transaction description: "{description}"
Merchant name (if known): "{merchant}"

Respond ONLY as valid JSON with these fields:
{{
  "category_id": <number 1-10>,
  "category_name": "<name>",
  "confidence": "<high|medium|low>",
  "reasoning": "<one sentence>"
}}"""

            response = client.models.generate_content(
                model=ENV_GEMINI_MODEL,
                contents=prompt,
            )
            text = response.text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            result = json.loads(text)
            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "category_id": cat_id,
                "category_name": f"(rule-based fallback — AI error: {str(e)[:80]})",
                "confidence": "medium" if rule_based else "low",
                "reasoning": f"Matched via rule: '{clean_m}'" if rule_based else "No rule match found.",
            })

    from config import DEFAULT_CATEGORIES
    cat_name = next((c["name"] for c in DEFAULT_CATEGORIES if c["id"] == cat_id), "Uncategorized / Other")
    return json.dumps({
        "category_id": cat_id,
        "category_name": cat_name,
        "confidence": "medium" if rule_based else "low",
        "reasoning": f"Matched via keyword rule: '{clean_m}'" if rule_based else "No matching rule. Add an API key for AI categorization.",
    })
