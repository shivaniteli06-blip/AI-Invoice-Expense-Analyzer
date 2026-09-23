"""
Agent 4 — Anomaly Detection Agent
Uses Python statistics to flag anomalies and Groq to explain them.
"""
import json
import re
from typing import Any
import pandas as pd
from utils.groq_client import call_groq
from utils.calculations import detect_anomalies
from prompts.agent_prompts import ANOMALY_SYSTEM, ANOMALY_USER


def detect_and_explain_anomalies(
    df: pd.DataFrame, z_threshold: float = 2.0
) -> tuple[list[dict[str, Any]], str]:
    """
    Detect statistically unusual transactions and explain them.

    Returns:
        (anomaly_results, error_message)
        Each item in anomaly_results contains the original transaction data
        plus 'explanation' and 'recommendation' from Groq.
    """
    if df.empty:
        return [], "No expense data available for anomaly detection."

    # Python-based detection
    anomalies = detect_anomalies(df, z_threshold=z_threshold)

    if not anomalies:
        return [], ""

    # Ask Groq for cautious plain-language explanations
    prompt = ANOMALY_USER.format(
        anomalies_json=json.dumps(anomalies, indent=2, default=str)
    )

    try:
        response = call_groq(
            system_prompt=ANOMALY_SYSTEM,
            user_prompt=prompt,
            temperature=0.2,
            max_tokens=1024,
        )
    except Exception as e:
        # Still return anomalies without explanations
        for a in anomalies:
            a["explanation"] = "Explanation unavailable."
            a["recommendation"] = "Please review this transaction manually."
        return anomalies, f"API error during anomaly explanation: {e}"

    cleaned = re.sub(r"```(?:json)?", "", response).replace("```", "").strip()

    try:
        explanations = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                explanations = json.loads(match.group())
            except json.JSONDecodeError:
                explanations = []
        else:
            explanations = []

    # Merge explanations into anomaly records
    exp_map = {}
    if isinstance(explanations, list):
        for item in explanations:
            if isinstance(item, dict):
                idx = item.get("transaction_index")
                if idx is not None:
                    exp_map[int(idx)] = item

    for anomaly in anomalies:
        matched = exp_map.get(anomaly["index"], {})
        anomaly["explanation"] = matched.get(
            "explanation",
            f"This {anomaly['category']} transaction of ₹{anomaly['amount']:,.0f} is significantly "
            f"higher than the category average of ₹{anomaly['category_mean']:,.0f}. It may require verification."
        )
        anomaly["recommendation"] = matched.get(
            "recommendation",
            "Please verify this transaction and compare with receipts or invoices."
        )

    return anomalies, ""
