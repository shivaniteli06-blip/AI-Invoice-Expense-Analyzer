"""
Agent 5 — Budget Advisory Agent
Compares spending vs. user budgets in Python and generates Groq-powered feedback.
"""
import json
import re
from typing import Any
import pandas as pd
from utils.groq_client import call_groq
from utils.calculations import compute_budget_comparison
from prompts.agent_prompts import BUDGET_SYSTEM, BUDGET_USER


def analyse_budget(
    df: pd.DataFrame, budgets: dict[str, float]
) -> tuple[list[dict[str, Any]], str, str]:
    """
    Compare actual spending against user-defined budgets.

    Returns:
        (budget_comparison, ai_feedback, error_message)
        budget_comparison — list of per-category dicts with Python-computed numbers
        ai_feedback       — Groq's plain-language feedback string
        error_message     — empty on success
    """
    if not budgets:
        return [], "", "No budgets defined. Please set budgets in the Budget Analysis page."

    # Python-based budget math
    comparison = compute_budget_comparison(df, budgets)

    if not comparison:
        return [], "", "Budget comparison could not be computed."

    # Ask Groq for actionable feedback
    prompt = BUDGET_USER.format(
        budget_data_json=json.dumps(comparison, indent=2)
    )

    try:
        response = call_groq(
            system_prompt=BUDGET_SYSTEM,
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
        )
    except Exception as e:
        return comparison, "AI feedback unavailable.", f"API error during budget advisory: {e}"

    cleaned = re.sub(r"```(?:json)?", "", response).replace("```", "").strip()

    # Try to parse JSON feedback array and merge
    try:
        feedback_list = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                feedback_list = json.loads(match.group())
            except json.JSONDecodeError:
                feedback_list = []
        else:
            feedback_list = []

    # Merge AI feedback into comparison rows
    feedback_map = {}
    if isinstance(feedback_list, list):
        for item in feedback_list:
            if isinstance(item, dict) and "category" in item:
                feedback_map[item["category"]] = item

    for row in comparison:
        matched = feedback_map.get(row["category"], {})
        row["ai_feedback"] = matched.get("feedback", "")

    # Also generate a plain text summary for the page
    ai_summary_lines = []
    for row in comparison:
        fb = row.get("ai_feedback", "")
        if fb:
            ai_summary_lines.append(f"**{row['category']}**: {fb}")

    ai_summary = "\n\n".join(ai_summary_lines) if ai_summary_lines else response

    return comparison, ai_summary, ""
