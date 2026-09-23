"""
Agent 2 — Expense Classification Agent
Classifies extracted transactions into spending categories using Groq.
"""
import json
import re
from typing import Any
from utils.groq_client import call_groq
from prompts.agent_prompts import CLASSIFICATION_SYSTEM, CLASSIFICATION_USER

VALID_CATEGORIES = {
    "Food", "Travel", "Shopping", "Utilities", "Healthcare",
    "Education", "Entertainment", "Office", "Rent", "Transportation", "Other"
}


def classify_expenses(transactions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """
    Classify a list of extracted transactions.

    Returns:
        (classified_transactions, error_message)
        Each transaction gets 'category', 'classification_reason', 'confidence' added.
    """
    if not transactions:
        return [], "No transactions to classify."

    # Build a clean summary for the LLM — avoid sending unnecessary data
    tx_list = [
        {
            "index": i,
            "merchant": t.get("merchant", "Unknown"),
            "description": t.get("description", ""),
            "amount": t.get("amount", 0),
            "currency": t.get("currency", "INR"),
        }
        for i, t in enumerate(transactions)
    ]

    prompt = CLASSIFICATION_USER.format(
        transactions_json=json.dumps(tx_list, indent=2)
    )

    try:
        response = call_groq(
            system_prompt=CLASSIFICATION_SYSTEM,
            user_prompt=prompt,
            temperature=0.05,
            max_tokens=2048,
        )
    except Exception as e:
        return transactions, f"API error during classification: {e}"

    cleaned = re.sub(r"```(?:json)?", "", response).replace("```", "").strip()

    try:
        classifications = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                classifications = json.loads(match.group())
            except json.JSONDecodeError:
                # Fallback: tag all as Other
                for tx in transactions:
                    tx["category"] = "Other"
                    tx["classification_reason"] = "Classification failed"
                    tx["confidence"] = "Low"
                return transactions, "Classification response could not be parsed; defaulted to 'Other'."
        else:
            for tx in transactions:
                tx["category"] = "Other"
                tx["classification_reason"] = "Classification failed"
                tx["confidence"] = "Low"
            return transactions, "Classification response could not be parsed; defaulted to 'Other'."

    if not isinstance(classifications, list):
        classifications = [classifications]

    # Merge classification results back into transactions
    result = []
    for i, tx in enumerate(transactions):
        tx = dict(tx)
        if i < len(classifications):
            c = classifications[i]
            if isinstance(c, dict):
                cat = c.get("category", "Other")
                tx["category"] = cat if cat in VALID_CATEGORIES else "Other"
                tx["classification_reason"] = c.get("reason", "")
                tx["confidence"] = c.get("confidence", "Medium")
            else:
                tx["category"] = "Other"
                tx["classification_reason"] = ""
                tx["confidence"] = "Low"
        else:
            tx["category"] = "Other"
            tx["classification_reason"] = ""
            tx["confidence"] = "Low"
        result.append(tx)

    return result, ""
