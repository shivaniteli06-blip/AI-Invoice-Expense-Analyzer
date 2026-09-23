"""
Agent 1 — Expense Extraction Agent
Extracts structured transaction data from raw text using Groq.
"""
import json
import re
from typing import Any
from utils.groq_client import call_groq
from prompts.agent_prompts import EXTRACTION_SYSTEM, EXTRACTION_USER


def extract_expenses(raw_text: str) -> tuple[list[dict[str, Any]], str]:
    """
    Extract structured expense data from raw text.

    Returns:
        (transactions, error_message)
        transactions — list of dicts with keys: merchant, date, invoice_number,
                       description, amount, currency, payment_method
        error_message — empty string on success
    """
    if not raw_text or not raw_text.strip():
        return [], "Input text is empty. Please provide expense information."

    prompt = EXTRACTION_USER.format(raw_text=raw_text.strip())

    try:
        response = call_groq(
            system_prompt=EXTRACTION_SYSTEM,
            user_prompt=prompt,
            temperature=0.05,
            max_tokens=2048,
        )
    except Exception as e:
        return [], f"API error during extraction: {e}"

    # Strip markdown fences if model wrapped JSON
    cleaned = re.sub(r"```(?:json)?", "", response).replace("```", "").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to extract JSON array from response
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return [], f"Could not parse extraction response as JSON. Raw: {cleaned[:300]}"
        else:
            return [], f"No JSON array found in extraction response. Raw: {cleaned[:300]}"

    if not isinstance(data, list):
        data = [data]

    # Normalise each transaction
    normalised = []
    for item in data:
        if not isinstance(item, dict):
            continue
        tx = {
            "merchant": item.get("merchant", "Not available"),
            "date": item.get("date", "Not available"),
            "invoice_number": item.get("invoice_number", "Not available"),
            "description": item.get("description", "Not available"),
            "amount": _parse_amount(item.get("amount")),
            "currency": item.get("currency", "INR"),
            "payment_method": item.get("payment_method", "Not available"),
        }
        normalised.append(tx)

    if not normalised:
        return [], "Extraction Agent found no transactions in the provided text."

    return normalised, ""


def _parse_amount(value: Any) -> float:
    """Safely convert an extracted amount to float."""
    if value is None:
        return 0.0
    try:
        return float(str(value).replace(",", "").replace("₹", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return 0.0
