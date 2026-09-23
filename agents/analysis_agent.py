"""
Agent 3 — Spending Analysis Agent
Computes statistics in Python and asks Groq to explain them in plain language.
"""
import json
from typing import Any
import pandas as pd
from utils.groq_client import call_groq
from utils.calculations import build_statistics_report
from prompts.agent_prompts import ANALYSIS_SYSTEM, ANALYSIS_USER


def analyse_spending(df: pd.DataFrame) -> tuple[dict[str, Any], str, str]:
    """
    Analyse a DataFrame of classified expenses.

    Returns:
        (statistics_dict, ai_explanation, error_message)
        statistics_dict — all Python-computed numbers
        ai_explanation  — Groq's plain-language explanation
        error_message   — empty on success
    """
    if df.empty:
        return {}, "", "No expense data available for analysis."

    # All arithmetic done in Python
    stats = build_statistics_report(df)

    # Ask Groq to explain (not recalculate)
    prompt = ANALYSIS_USER.format(
        statistics_json=json.dumps(stats, indent=2, default=str)
    )

    try:
        explanation = call_groq(
            system_prompt=ANALYSIS_SYSTEM,
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
        )
    except Exception as e:
        explanation = "AI explanation unavailable."
        return stats, explanation, f"API error during analysis: {e}"

    return stats, explanation, ""
