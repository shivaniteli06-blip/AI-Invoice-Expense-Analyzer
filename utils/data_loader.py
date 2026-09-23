"""
Utility for loading expense DataFrames from various sources.
"""
import io
import os
import pandas as pd
from typing import Optional

REQUIRED_COLUMNS = {"date", "merchant", "amount"}
EXPECTED_COLUMNS = ["date", "merchant", "description", "amount", "category", "payment_method"]

# Resolve sample data path relative to this file so it works from any cwd
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_SAMPLE_CSV = os.path.join(_THIS_DIR, "..", "data", "sample_expenses.csv")


def load_sample_data() -> pd.DataFrame:
    """Load the bundled sample expense CSV."""
    try:
        df = pd.read_csv(_SAMPLE_CSV)
        return _normalise(df)
    except FileNotFoundError:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)


def load_from_csv_bytes(file_bytes: bytes) -> tuple[pd.DataFrame, list[str]]:
    """
    Parse uploaded CSV bytes into a normalised DataFrame.
    Returns (df, errors) — errors is an empty list on success.
    """
    errors = []
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return pd.DataFrame(), [f"Could not parse CSV file: {e}"]

    # Normalise column names
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        errors.append(f"CSV is missing required columns: {', '.join(sorted(missing))}")
        return pd.DataFrame(), errors

    return _normalise(df), errors


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure standard columns exist and types are correct."""
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["category"] = df["category"].fillna("Uncategorized").str.strip()
    df["merchant"] = df["merchant"].fillna("Unknown").str.strip()
    df["description"] = df["description"].fillna("").str.strip()
    df["payment_method"] = df["payment_method"].fillna("Not available").str.strip()

    return df[EXPECTED_COLUMNS].reset_index(drop=True)


def merge_expenses(
    existing: Optional[pd.DataFrame], new_rows: pd.DataFrame
) -> pd.DataFrame:
    """Append new_rows to existing, deduplicating by (date, merchant, amount)."""
    if existing is None or existing.empty:
        return new_rows
    combined = pd.concat([existing, new_rows], ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["date", "merchant", "amount"], keep="last"
    )
    return combined.reset_index(drop=True)
