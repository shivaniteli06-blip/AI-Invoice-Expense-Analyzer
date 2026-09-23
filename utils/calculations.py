"""
Pure Python/pandas numerical calculations — no LLM involvement.
All financial arithmetic happens here for accuracy.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple


def compute_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Return high-level summary statistics for the expense dataframe."""
    if df.empty:
        return {}

    amounts = df["amount"].dropna().astype(float)
    return {
        "total_spending": round(float(amounts.sum()), 2),
        "transaction_count": int(len(df)),
        "average_transaction": round(float(amounts.mean()), 2),
        "highest_transaction": round(float(amounts.max()), 2),
        "lowest_transaction": round(float(amounts.min()), 2),
        "highest_merchant": df.loc[amounts.idxmax(), "merchant"] if not amounts.empty else "N/A",
        "lowest_merchant": df.loc[amounts.idxmin(), "merchant"] if not amounts.empty else "N/A",
    }


def spending_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Return spending totals and percentage breakdown by category."""
    if df.empty or "category" not in df.columns:
        return pd.DataFrame()

    grouped = (
        df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total"})
        .sort_values("total", ascending=False)
    )
    total = grouped["total"].sum()
    grouped["percentage"] = (grouped["total"] / total * 100).round(2) if total > 0 else 0.0
    grouped["total"] = grouped["total"].round(2)
    return grouped


def daily_spending(df: pd.DataFrame) -> pd.DataFrame:
    """Return spending aggregated by date."""
    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    daily = (
        df.dropna(subset=["date"])
        .groupby("date")["amount"]
        .sum()
        .reset_index()
        .sort_values("date")
    )
    daily["amount"] = daily["amount"].round(2)
    return daily


def monthly_spending(df: pd.DataFrame) -> pd.DataFrame:
    """Return spending aggregated by month."""
    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = (
        df.dropna(subset=["date"])
        .groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )
    monthly["amount"] = monthly["amount"].round(2)
    return monthly


def detect_anomalies(df: pd.DataFrame, z_threshold: float = 2.0) -> List[Dict[str, Any]]:
    """
    Detect anomalies using Z-score within each category.
    A transaction is flagged if its amount deviates > z_threshold standard deviations
    from the category mean.
    Returns list of anomaly dicts.
    """
    if df.empty or "category" not in df.columns:
        return []

    anomalies = []
    for category, group in df.groupby("category"):
        amounts = group["amount"].astype(float)
        if len(amounts) < 2:
            continue
        mean = amounts.mean()
        std = amounts.std()
        if std == 0:
            continue
        for idx, row in group.iterrows():
            z = (float(row["amount"]) - mean) / std
            if z > z_threshold:
                anomalies.append({
                    "index": int(idx),
                    "merchant": row.get("merchant", "N/A"),
                    "date": str(row.get("date", "N/A")),
                    "amount": float(row["amount"]),
                    "category": category,
                    "category_mean": round(float(mean), 2),
                    "category_std": round(float(std), 2),
                    "z_score": round(float(z), 2),
                    "description": row.get("description", "N/A"),
                    "times_above_mean": round(float(row["amount"]) / mean, 1) if mean > 0 else None,
                })
    return anomalies


def compute_budget_comparison(
    df: pd.DataFrame, budgets: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Compare actual spending per category against user-defined budgets.
    Returns list of comparison dicts for every budgeted category.
    """
    cat_spending = spending_by_category(df)
    actual_map = dict(zip(cat_spending["category"], cat_spending["total"])) if not cat_spending.empty else {}

    results = []
    for category, budget_amount in budgets.items():
        spent = actual_map.get(category, 0.0)
        remaining = budget_amount - spent
        pct_used = round((spent / budget_amount * 100), 2) if budget_amount > 0 else 0.0
        exceeded = max(0.0, spent - budget_amount)
        results.append({
            "category": category,
            "budget": round(float(budget_amount), 2),
            "spent": round(float(spent), 2),
            "remaining": round(float(remaining), 2),
            "pct_used": pct_used,
            "exceeded_by": round(float(exceeded), 2),
            "status": (
                "Over Budget" if exceeded > 0
                else "On Track" if pct_used >= 80
                else "Under Budget"
            ),
        })
    return results


def build_statistics_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Combine all computed stats into one dict to pass to the Analysis Agent."""
    return {
        "summary": compute_summary_stats(df),
        "by_category": spending_by_category(df).to_dict("records") if not df.empty else [],
        "monthly": monthly_spending(df).to_dict("records") if not df.empty else [],
    }
