"""
UI Charts — Plotly chart builders with consistent styling and animations.
All charts use the shared CATEGORY_COLORS palette.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from ui.theme import CATEGORY_COLORS

# Shared layout defaults
_FONT = dict(family="Poppins, system-ui, sans-serif", size=12)
_MARGIN = dict(l=16, r=16, t=36, b=16)
_TRANSPARENT = "rgba(0,0,0,0)"
_GRID = "#e8eaf6"


def _base_layout(**kwargs) -> dict:
    return dict(
        font=_FONT,
        paper_bgcolor=_TRANSPARENT,
        plot_bgcolor=_TRANSPARENT,
        margin=_MARGIN,
        hoverlabel=dict(
            bgcolor="#1a1d2e",
            font_color="#f1f5f9",
            font_family="Poppins, sans-serif",
            font_size=12,
            bordercolor="#30384d",
        ),
        **kwargs,
    )


def spending_donut(category_df: pd.DataFrame) -> go.Figure:
    """Donut chart of spending by category."""
    if category_df.empty:
        return _empty_fig("No category data")

    colors = [CATEGORY_COLORS.get(c, "#94a3b8") for c in category_df["category"]]

    fig = go.Figure(go.Pie(
        labels=category_df["category"],
        values=category_df["total"],
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        textinfo="label+percent",
        textfont=dict(size=12, family="Inter, sans-serif"),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>",
        pull=[0.04] * len(category_df),
    ))

    fig.update_layout(
        **_base_layout(
            title=dict(text="Spending by Category", font=dict(size=15, family="Inter, sans-serif")),
            showlegend=True,
            legend=dict(orientation="v", font=dict(size=12)),
        )
    )
    return fig


def spending_timeline(daily_df: pd.DataFrame) -> go.Figure:
    """Animated area chart of spending over time."""
    if daily_df.empty:
        return _empty_fig("No timeline data")

    col = "amount" if "amount" in daily_df.columns else "total"
    fig = go.Figure(go.Scatter(
        x=daily_df["date"],
        y=daily_df[col],
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(99,102,241,0.10)",
        line=dict(color="#6366f1", width=2.5, shape="spline"),
        marker=dict(size=6, color="#6366f1"),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>₹%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(
            title="Spending Over Time",
            xaxis=dict(showgrid=False, showline=True, linecolor="#e2e8f0"),
            yaxis=dict(showgrid=True, gridcolor=_GRID, zeroline=False),
        )
    )
    return fig


def budget_vs_actual(budget_data: list[dict]) -> go.Figure:
    """Grouped bar chart: budget vs actual spending per category."""
    if not budget_data:
        return _empty_fig("No budget data")

    categories = [d["category"] for d in budget_data]
    budgets = [d["budget"] for d in budget_data]
    spents = [d["spent"] for d in budget_data]

    bar_colors = [
        "#ef4444" if d["spent"] > d["budget"] else "#10b981"
        for d in budget_data
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Budget",
        x=categories,
        y=budgets,
        marker=dict(color="rgba(99,102,241,0.3)", line=dict(color="#6366f1", width=1)),
        hovertemplate="<b>%{x}</b><br>Budget: ₹%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Actual",
        x=categories,
        y=spents,
        marker=dict(color=bar_colors),
        hovertemplate="<b>%{x}</b><br>Spent: ₹%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(
            title="Budget vs. Actual Spending",
            barmode="group",
            bargap=0.25,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor=_GRID),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
    )
    return fig


def anomaly_scatter(df: pd.DataFrame, anomalies: list[dict]) -> go.Figure:
    """Scatter timeline of all transactions, anomalies highlighted with pulsing markers."""
    if df.empty:
        return _empty_fig("No data for anomaly chart")

    anomaly_indices = {a["index"] for a in anomalies}

    normal = df[~df.index.isin(anomaly_indices)]
    flagged = df[df.index.isin(anomaly_indices)]

    fig = go.Figure()
    if not normal.empty:
        fig.add_trace(go.Scatter(
            x=normal["date"],
            y=normal["amount"],
            mode="markers",
            name="Normal",
            marker=dict(color="#6366f1", size=7, opacity=0.7),
            hovertemplate="<b>%{customdata}</b><br>₹%{y:,.0f}<extra></extra>",
            customdata=normal["merchant"],
        ))
    if not flagged.empty:
        fig.add_trace(go.Scatter(
            x=flagged["date"],
            y=flagged["amount"],
            mode="markers",
            name="⚠️ Anomaly",
            marker=dict(
                color="#ef4444", size=14,
                symbol="star",
                line=dict(color="#ff0000", width=2),
            ),
            hovertemplate="<b>⚠️ %{customdata}</b><br>₹%{y:,.0f}<extra></extra>",
            customdata=flagged["merchant"],
        ))
    fig.update_layout(
        **_base_layout(
            title="Transaction Timeline — Anomalies Highlighted",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor=_GRID),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
    )
    return fig


def monthly_bar(monthly_df: pd.DataFrame) -> go.Figure:
    """Bar chart of monthly spending."""
    if monthly_df.empty:
        return _empty_fig("No monthly data")

    col = "amount" if "amount" in monthly_df.columns else "total"
    fig = go.Figure(go.Bar(
        x=monthly_df["month"],
        y=monthly_df[col],
        marker=dict(
            color=monthly_df[col],
            colorscale=[[0, "#818cf8"], [1, "#6366f1"]],
            showscale=False,
            line=dict(color="#6366f1", width=0.5),
        ),
        hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(
            title="Monthly Spending",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor=_GRID),
        )
    )
    return fig


def category_horizontal_bars(category_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart showing category spending share."""
    if category_df.empty:
        return _empty_fig("No category data")

    colors = [CATEGORY_COLORS.get(c, "#94a3b8") for c in category_df["category"]]

    fig = go.Figure(go.Bar(
        y=category_df["category"],
        x=category_df["percentage"],
        orientation="h",
        marker=dict(color=colors, opacity=0.85),
        text=[f"{p:.1f}%" for p in category_df["percentage"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% of total spending<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(
            title="Category Spending Share (%)",
            xaxis=dict(showgrid=True, gridcolor=_GRID, range=[0, max(category_df["percentage"]) * 1.2]),
            yaxis=dict(showgrid=False, autorange="reversed"),
            height=max(200, len(category_df) * 40 + 60),
        )
    )
    return fig


def _empty_fig(msg: str = "No data") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="#94a3b8", family="Inter, sans-serif"),
    )
    fig.update_layout(**_base_layout(height=250))
    return fig
