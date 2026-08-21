"""
SpendTracker AI — Root ADK Agent (ADK 2.x compatible)
Orchestrates all financial tools with a Gemini-powered conversational assistant.

Streaming: exposes `stream_agent_response(user_message, session_id, api_key)` which
yields text chunks incrementally — compatible with Streamlit's st.write_stream.
"""
import asyncio
import os
from typing import Generator

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agents.tools.categorize_tools import ai_categorize_transaction
from agents.tools.insight_tools import generate_financial_insights
from agents.tools.query_tools import (
    get_category_breakdown,
    get_high_value_transactions,
    get_member_spends,
    get_merchant_history,
    get_monthly_trend,
    get_spending_summary,
)

# ── Configuration ─────────────────────────────────────────────────────────────
_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
_APP_NAME = "spend_tracker_ai"

_SYSTEM_PROMPT = """You are **SpendTracker AI**, a friendly and knowledgeable personal finance
assistant for an Indian household. You have access to the household's complete bank transaction
history across multiple accounts and family members.

Your capabilities:
- Summarise spending across time periods, categories, and merchants
- Identify high-value or unusual purchases
- Categorise transactions intelligently
- Generate personalised financial insights and savings recommendations
- Show month-over-month spending trends
- Break down spending by household member

Guidelines:
- Always use Indian Rupee (₹) formatting
- Be warm, encouraging, and non-judgmental
- When presenting numbers, also provide brief context (e.g., "That's about ₹5,000/month")
- Proactively suggest relevant follow-up questions
- If no data exists, guide the user to upload bank statements first
- Keep responses concise unless asked for a full report

You have access to these tools — use them when the user asks about their spending:
• get_spending_summary — overall spend for a period
• get_category_breakdown — drill into a specific category
• get_merchant_history — look up a specific merchant
• get_high_value_transactions — find large purchases
• get_member_spends — per-member breakdown
• get_monthly_trend — month-over-month chart data
• ai_categorize_transaction — categorize a transaction description
• generate_financial_insights — full AI insight report
"""

# ── Singletons (created once per process) ────────────────────────────────────
_session_service = InMemorySessionService()

_agent = Agent(
    name="spend_tracker_agent",
    model=_GEMINI_MODEL,
    description="SpendTracker AI — household financial assistant",
    instruction=_SYSTEM_PROMPT,
    tools=[
        get_spending_summary,
        get_category_breakdown,
        get_merchant_history,
        get_high_value_transactions,
        get_member_spends,
        get_monthly_trend,
        ai_categorize_transaction,
        generate_financial_insights,
    ],
)


def _make_runner(api_key: str) -> Runner:
    """Creates a Runner with the Gemini API key set in the environment."""
    os.environ["GOOGLE_API_KEY"] = api_key
    return Runner(
        agent=_agent,
        app_name=_APP_NAME,
        session_service=_session_service,
        auto_create_session=True,
    )


async def _collect_chunks(runner: Runner, session_id: str, user_message: str) -> list[str]:
    """
    Runs the agent asynchronously and collects final response text chunks.
    Returns a list of string chunks in order.
    """
    message = Content(role="user", parts=[Part(text=user_message)])
    chunks: list[str] = []

    async for event in runner.run_async(
        user_id="household",
        session_id=session_id,
        new_message=message,
    ):
        # Only capture the final model response (not tool call events)
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        chunks.append(part.text)

    return chunks


def stream_agent_response(user_message: str, session_id: str, api_key: str) -> Generator[str, None, None]:
    """
    Public API for Streamlit.
    Yields text chunks so st.write_stream can render them incrementally.

    Args:
        user_message: The user's natural-language query.
        session_id: A unique string per Streamlit session.
        api_key: Gemini API key (reuses the app's existing API_KEY session state).

    Yields:
        str chunks of the agent's response.
    """
    runner = _make_runner(api_key)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        chunks = loop.run_until_complete(_collect_chunks(runner, session_id, user_message))
        loop.close()
    except Exception as e:
        yield f"\n\n⚠️ Agent error: {e}"
        return

    if not chunks:
        yield "I couldn't generate a response. Please try rephrasing your question."
        return

    for chunk in chunks:
        yield chunk
