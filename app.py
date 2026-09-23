"""
AI Invoice & Expense Analyzer — Main Streamlit Application
Multi-Agent Architecture: Extraction → Classification → Analysis → Anomaly → Budget
"""
import os
import json
import time
import io
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Internal imports ──────────────────────────────────────────────────────────
from ui.theme import inject_theme, CATEGORY_COLORS
from ui.components import (
    inject_all_css, metric_card, count_up_card, render_pipeline,
    anomaly_card, category_badge, budget_progress_bar, section_header,
    PRIVACY_NOTICE, calculated_tag, ai_tag, thinking_dots,
    build_sidebar_nav, empty_state_html,
)
from ui.charts import (
    spending_donut, spending_timeline, budget_vs_actual,
    anomaly_scatter, monthly_bar, category_horizontal_bars,
)
from utils.data_loader import load_sample_data, load_from_csv_bytes, merge_expenses
from utils.file_parser import parse_uploaded_file
from utils.calculations import (
    compute_summary_stats, spending_by_category, daily_spending,
    monthly_spending, detect_anomalies, compute_budget_comparison,
)
from agents.extraction_agent import extract_expenses
from agents.classification_agent import classify_expenses
from agents.analysis_agent import analyse_spending
from agents.anomaly_agent import detect_and_explain_anomalies
from agents.budget_agent import analyse_budget
from prompts.agent_prompts import ASSISTANT_SYSTEM, ASSISTANT_USER
from utils.groq_client import stream_groq

# ── Session state defaults ────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "expenses": None,
        "budgets": {
            "Food": 5000.0, "Travel": 3000.0, "Shopping": 4000.0,
            "Utilities": 3500.0, "Healthcare": 2000.0, "Education": 3000.0,
            "Entertainment": 2000.0, "Office": 15000.0, "Rent": 20000.0,
            "Transportation": 2000.0, "Other": 1000.0,
        },
        "chat_history": [],
        "dark_mode": False,
        "agent_results": {},
        "pipeline_ran": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Inject theme + CSS ────────────────────────────────────────────────────────
# This runs on EVERY rerun (Streamlit re-executes the full script on each
# interaction), so styles are always present regardless of which nav item
# was clicked.
st.markdown(inject_theme(st.session_state.dark_mode), unsafe_allow_html=True)

# ── Navigation visibility safeguard ─────────────────────────────────────────
# The theme can hide Streamlit's default header. Keep it visible so the
# sidebar expand/collapse control remains available, while the custom sidebar
# below provides the complete project navigation and dark/light mode toggle.
st.markdown("""
<style>
header[data-testid="stHeader"] {
    display: flex !important;
    visibility: visible !important;
}
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
}
[data-testid="stSidebar"] .stButton > button {
    min-height: 42px !important;
    line-height: 1.35 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}
[data-testid="stSidebar"] {
    min-width: 285px !important;
    max-width: 320px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helper: get expense DF ────────────────────────────────────────────────────

def get_df() -> pd.DataFrame:
    if st.session_state.expenses is None or st.session_state.expenses.empty:
        return pd.DataFrame()
    return st.session_state.expenses.copy()


def has_data() -> bool:
    df = get_df()
    return not df.empty


def currency_fmt(v: float) -> str:
    return f"₹{v:,.0f}"


# ── Run full agent pipeline ───────────────────────────────────────────────────

def run_pipeline(df: pd.DataFrame, pipeline_placeholder, log_placeholder):
    """Execute all 5 agents sequentially with live UI updates."""
    states = ["waiting"] * 5
    logs = []

    def update_ui():
        pipeline_placeholder.markdown(
            render_pipeline(states, logs), unsafe_allow_html=True
        )

    # Stage 0: Extraction (already done if coming from CSV/manual)
    states[0] = "running"
    update_ui()
    time.sleep(0.3)
    states[0] = "done"
    logs.append(f"✅ Extraction Agent: {len(df)} transaction(s) loaded")
    update_ui()

    # Stage 1: Classification
    states[1] = "running"
    logs.append("⏳ Classification Agent: classifying transactions...")
    update_ui()
    time.sleep(0.2)

    rows_needing_class = df[df["category"].isin(["Uncategorized", ""])]
    if not rows_needing_class.empty:
        tx_list = rows_needing_class.to_dict("records")
        classified, err = classify_expenses(tx_list)
        if not err:
            for i, orig_idx in enumerate(rows_needing_class.index):
                if i < len(classified):
                    df.at[orig_idx, "category"] = classified[i].get("category", "Other")
    states[1] = "done"
    logs.append(f"✅ Classification Agent: {df['category'].value_counts().to_dict()}")
    update_ui()

    # Stage 2: Analysis
    states[2] = "running"
    logs.append("⏳ Analysis Agent: computing spending statistics...")
    update_ui()
    stats, explanation, err = analyse_spending(df)
    states[2] = "done"
    summary = stats.get("summary", {})
    logs.append(f"✅ Analysis Agent: total ₹{summary.get('total_spending', 0):,.0f} across {summary.get('transaction_count', 0)} transactions")
    st.session_state.agent_results["stats"] = stats
    st.session_state.agent_results["analysis_explanation"] = explanation
    update_ui()

    # Stage 3: Anomaly Detection
    states[3] = "running"
    logs.append("⏳ Anomaly Agent: scanning for unusual transactions...")
    update_ui()
    anomalies, err = detect_and_explain_anomalies(df)
    states[3] = "done"
    logs.append(f"{'⚠️' if anomalies else '✅'} Anomaly Agent: {len(anomalies)} potential anomal{'y' if len(anomalies)==1 else 'ies'} detected")
    st.session_state.agent_results["anomalies"] = anomalies
    update_ui()

    # Stage 4: Budget Advisory
    states[4] = "running"
    logs.append("⏳ Budget Agent: comparing against defined budgets...")
    update_ui()
    budgets = st.session_state.budgets
    budget_comp, budget_text, err = analyse_budget(df, budgets)
    states[4] = "done"
    over = sum(1 for b in budget_comp if b["status"] == "Over Budget")
    logs.append(f"✅ Budget Agent: {over} categor{'y' if over==1 else 'ies'} over budget")
    st.session_state.agent_results["budget_comparison"] = budget_comp
    st.session_state.agent_results["budget_text"] = budget_text
    update_ui()

    st.session_state.expenses = df
    st.session_state.pipeline_ran = True
    time.sleep(0.3)
    return df


# ── Page definitions ─────────────────────────────────────────────────────────

PAGES = {
    "🏠  Dashboard":              "dashboard",
    "➕  Add Expenses":           "add",
    "📁  Upload Expenses":        "upload",
    "🏷️  Expense Classification": "classification",
    "📊  Spending Analysis":      "analysis",
    "⚠️  Anomaly Detection":      "anomaly",
    "💰  Budget Analysis":        "budget",
    "🤖  AI Expense Assistant":   "assistant",
    "📄  Reports":                "reports",
    "ℹ️  About Project":          "about",
}

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# ── Per-rerun sidebar nav CSS ─────────────────────────────────────────────────
# Injected on EVERY rerun so active-page highlight is always correct.
# Strategy: find the 1-based position of the active page in PAGES, then use
# nth-child CSS to highlight only that button. This is 100% reliable.
_page_keys = list(PAGES.values())
_cur = st.session_state.page
_active_pos = _page_keys.index(_cur) + 1 if _cur in _page_keys else 1

# The sidebar vertical block contains: 1 markdown (logo), then 10 button divs.
# Each button div is a direct child; the logo markdown is the first child.
# So button N is at position N+1 (1-indexed), or we can target .stButton nth-of-type.
_nav_dark = st.session_state.dark_mode
_nav_bg = "#161b27" if _nav_dark else "#ffffff"
_nav_surface2 = "#252d3d" if _nav_dark else "#f4f6fb"
_nav_text = "#8b95a8" if _nav_dark else "#64748b"
_nav_primary = "#7c6fff" if _nav_dark else "#6c63ff"
_nav_border = "#30384d" if _nav_dark else "#e8eaf6"
_nav_logo_text = "#e8eaf6" if _nav_dark else "#1a1d2e"
_nav_muted = "#8b95a8" if _nav_dark else "#94a3b8"

_active_nth_css = f"""
<style>
/* ── Sidebar background ── */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
  background-color: {_nav_bg} !important;
}}

/* ── ALL sidebar nav buttons: base "inactive" style ── */
[data-testid="stSidebar"] .stButton > button {{
  display: block !important;
  width: 100% !important;
  text-align: left !important;
  background: transparent !important;
  color: {_nav_text} !important;
  border: none !important;
  border-left: 3px solid transparent !important;
  border-radius: 0 10px 10px 0 !important;
  padding: 10px 16px !important;
  font-family: 'Poppins', sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  letter-spacing: 0.01em !important;
  cursor: pointer !important;
  transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease !important;
  box-shadow: none !important;
  line-height: 1.5 !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
  background: {_nav_surface2} !important;
  color: {_nav_primary} !important;
  border-left-color: {_nav_primary} !important;
  transform: translateX(2px) scale(1) !important;
  box-shadow: none !important;
}}
[data-testid="stSidebar"] .stButton > button:active {{
  transform: none !important;
}}

/* ── ACTIVE button: nth-of-type targets the Nth .stButton in the sidebar ── */
[data-testid="stSidebar"] .stButton:nth-of-type({_active_pos}) > button {{
  background: rgba(108, 99, 255, 0.10) !important;
  color: {_nav_primary} !important;
  border-left: 3px solid {_nav_primary} !important;
  font-weight: 700 !important;
}}
[data-testid="stSidebar"] .stButton:nth-of-type({_active_pos}) > button:hover {{
  background: rgba(108, 99, 255, 0.14) !important;
  transform: none !important;
}}
</style>
"""
st.markdown(_active_nth_css, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo header
    st.markdown(f"""
<div style="text-align:center;padding:22px 16px 16px;border-bottom:1px solid {_nav_border};margin-bottom:8px">
  <div style="font-size:40px;line-height:1;margin-bottom:8px">💸</div>
  <div style="font-size:15px;font-weight:700;color:{_nav_logo_text};font-family:Poppins,sans-serif;letter-spacing:-0.01em">AI Expense Analyzer</div>
  <div style="font-size:10px;font-weight:500;color:{_nav_muted};font-family:Poppins,sans-serif;text-transform:uppercase;letter-spacing:0.12em;margin-top:3px">Multi-Agent Intelligence</div>
</div>
""", unsafe_allow_html=True)

    # ── REAL st.button() nav items ────────────────────────────────────────────
    # These are actual Streamlit widgets that update session_state and trigger
    # st.rerun(). CSS above styles them to look like a custom nav.
    for label, key in PAGES.items():
        if st.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    # ── Dark mode toggle ──────────────────────────────────────────────────────
    st.markdown(f"""
<div style="height:1px;background:linear-gradient(90deg,transparent,{_nav_border},transparent);margin:12px 0 10px"></div>
<div style="padding:0 4px 6px;font-size:10px;font-weight:600;color:{_nav_muted};
            text-transform:uppercase;letter-spacing:0.1em;font-family:Poppins,sans-serif">
  Appearance
</div>
""", unsafe_allow_html=True)
    dm = st.toggle("☀️ Light / 🌙 Dark", value=st.session_state.dark_mode, help="Turn dark mode on or off")
    if dm != st.session_state.dark_mode:
        st.session_state.dark_mode = dm
        st.rerun()

    # ── Agent status ──────────────────────────────────────────────────────────
    pipeline_ran = st.session_state.pipeline_ran
    dot_on  = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#10b981;box-shadow:0 0 5px #10b981;margin-right:7px;vertical-align:middle"></span>'
    dot_off = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#64748b;margin-right:7px;vertical-align:middle"></span>'
    dot = dot_on if pipeline_ran else dot_off
    agents_html = "".join(
        f'<div style="display:flex;align-items:center;padding:3px 4px;font-size:12px;'
        f'font-family:Poppins,sans-serif;color:{_nav_text}">{dot}{name}</div>'
        for name in ["🔍 Extraction","🏷️ Classification","📊 Analysis","⚠️ Anomaly","💰 Budget"]
    )
    st.markdown(f"""
<div style="height:1px;background:linear-gradient(90deg,transparent,{_nav_border},transparent);margin:10px 0 10px"></div>
<div style="padding:0 4px 6px;font-size:10px;font-weight:600;color:{_nav_muted};
            text-transform:uppercase;letter-spacing:0.1em;font-family:Poppins,sans-serif">Agent Status</div>
{agents_html}
""", unsafe_allow_html=True)

    st.markdown(PRIVACY_NOTICE, unsafe_allow_html=True)


# ── Page router ───────────────────────────────────────────────────────────────

page = st.session_state.page

# ── Quick return to Dashboard ────────────────────────────────────────────────
# Keep a visible Home button on every page so users can return to the dashboard
# even when the Streamlit sidebar is collapsed/hidden.
if page != "dashboard":
    home_col, _ = st.columns([1, 7])
    with home_col:
        if st.button("🏠 Dashboard", use_container_width=True, key="quick_dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

if page == "dashboard":
    st.markdown(section_header("🏠 Dashboard", "Real-time spending overview powered by multi-agent AI"), unsafe_allow_html=True)

    if not has_data():
        # ── Styled empty state card ───────────────────────────────────────────
        st.markdown(empty_state_html(
            icon="💸",
            title="No Expense Data Loaded",
            subtitle="Load the built-in sample dataset to see a live demo with animated metrics, charts, and anomaly detection — or start adding your own expenses.",
        ), unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("📊 Load Sample Dataset", use_container_width=True, key="dash_load_sample"):
                df = load_sample_data()
                pipeline_ph = st.empty()
                log_ph = st.empty()
                st.session_state.expenses = df
                run_pipeline(df, pipeline_ph, log_ph)
                st.rerun()
        with col2:
            if st.button("➕ Add Expenses Manually", use_container_width=True, key="dash_add_manual"):
                st.session_state.page = "add"
                st.rerun()
        with col3:
            if st.button("📁 Upload CSV File", use_container_width=True, key="dash_upload"):
                st.session_state.page = "upload"
                st.rerun()
        st.stop()

    df = get_df()
    summary = compute_summary_stats(df)
    cat_df = spending_by_category(df)
    anomalies = st.session_state.agent_results.get("anomalies", [])
    budget_comp = st.session_state.agent_results.get("budget_comparison", [])

    # ── Metric cards row ─────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        count_up_card("Total Spending", summary.get("total_spending", 0),
                      prefix="₹", icon="💰", color="#6366f1", delay_ms=0)
    with c2:
        count_up_card("Transactions", summary.get("transaction_count", 0),
                      prefix="", icon="🧾", color="#06b6d4", delay_ms=80)
    with c3:
        count_up_card("Avg Expense", summary.get("average_transaction", 0),
                      prefix="₹", icon="📊", color="#8b5cf6", delay_ms=160)
    with c4:
        count_up_card("Highest Expense", summary.get("highest_transaction", 0),
                      prefix="₹", icon="📈", color="#f59e0b", delay_ms=240)
    with c5:
        count_up_card("Anomalies", len(anomalies),
                      prefix="", icon="⚠️", color="#ef4444", delay_ms=320)
    with c6:
        over_count = sum(1 for b in budget_comp if b["status"] == "Over Budget") if budget_comp else 0
        count_up_card("Over Budget", over_count,
                      prefix="", icon="🚨", color="#ef4444", delay_ms=400)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts row 1 ─────────────────────────────────────────────────────────
    ch1, ch2 = st.columns([1, 2])
    with ch1:
        st.plotly_chart(spending_donut(cat_df), use_container_width=True, config={"displayModeBar": False})
    with ch2:
        daily_df = daily_spending(df)
        st.plotly_chart(spending_timeline(daily_df), use_container_width=True, config={"displayModeBar": False})

    # ── Charts row 2 ─────────────────────────────────────────────────────────
    ch3, ch4 = st.columns(2)
    with ch3:
        if budget_comp:
            st.plotly_chart(budget_vs_actual(budget_comp), use_container_width=True, config={"displayModeBar": False})
        else:
            mon_df = monthly_spending(df)
            st.plotly_chart(monthly_bar(mon_df), use_container_width=True, config={"displayModeBar": False})
    with ch4:
        st.plotly_chart(anomaly_scatter(df, anomalies), use_container_width=True, config={"displayModeBar": False})

    # ── Category share bars ───────────────────────────────────────────────────
    st.markdown("#### Category Spending Share")
    st.plotly_chart(category_horizontal_bars(cat_df), use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════════════════════════
# ADD EXPENSES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "add":
    st.markdown(section_header("➕ Add Expenses", "Add expenses manually or switch to CSV upload anytime"), unsafe_allow_html=True)

    # ── Input method switch ───────────────────────────────────────────────────
    # The user can move between Manual Entry and CSV Upload at any time.
    switch_col1, switch_col2 = st.columns(2)
    with switch_col1:
        if st.button("📝 Add Manually", use_container_width=True, key="switch_to_manual"):
            st.session_state.page = "add"
            st.rerun()
    with switch_col2:
        if st.button("📁 Add CSV File", use_container_width=True, key="switch_to_csv_from_add"):
            st.session_state.page = "upload"
            st.rerun()

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    tabs = st.tabs(["📝 Manual Entry", "💬 Text Input"])

    # ── Manual Entry ─────────────────────────────────────────────────────────
    with tabs[0]:
        with st.form("manual_entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date_val = st.date_input("Date *")
                merchant = st.text_input("Merchant / Vendor *", placeholder="e.g. Swiggy, Amazon")
                amount = st.number_input("Amount (₹) *", min_value=0.0, step=10.0)
            with col2:
                description = st.text_input("Description", placeholder="e.g. Lunch order")
                category = st.selectbox("Category (optional)", [
                    "Auto-detect", "Food", "Travel", "Shopping", "Utilities",
                    "Healthcare", "Education", "Entertainment", "Office",
                    "Rent", "Transportation", "Other"
                ])
                payment = st.selectbox("Payment Method", [
                    "Not available", "UPI", "Credit Card", "Debit Card",
                    "Cash", "Net Banking", "Bank Transfer"
                ])

            submitted = st.form_submit_button("➕ Add Expense", use_container_width=True)

        if submitted:
            if not merchant.strip():
                st.error("Merchant name is required.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                new_row = pd.DataFrame([{
                    "date": pd.Timestamp(date_val),
                    "merchant": merchant.strip(),
                    "description": description.strip(),
                    "amount": float(amount),
                    "category": "Uncategorized" if category == "Auto-detect" else category,
                    "payment_method": payment,
                }])
                existing = st.session_state.expenses
                st.session_state.expenses = merge_expenses(existing, new_row)

                st.toast(f"✅ Expense added: {merchant} — ₹{amount:,.0f}", icon="✅")

                # Trigger pipeline
                st.markdown("### 🤖 Running Agent Pipeline...")
                pipeline_ph = st.empty()
                log_ph = st.empty()
                run_pipeline(st.session_state.expenses, pipeline_ph, log_ph)
                st.success("Pipeline complete! View results on the Dashboard.")

    # ── Text Input ────────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("""
<div style="background:var(--surface2);border-radius:10px;padding:14px 18px;margin-bottom:16px;font-size:13px">
  <strong>💡 Tip:</strong> Paste any natural language expense description.<br>
  Example: <em>"Yesterday I spent ₹850 at ABC Restaurant and ₹450 on Uber."</em>
</div>
""", unsafe_allow_html=True)
        raw_text = st.text_area(
            "Paste expense text here",
            height=140,
            placeholder="e.g. ABC Restaurant, 20-09-2026, Total ₹850. Paid ₹450 for Uber ride."
        )
        if st.button("🔍 Extract & Process", use_container_width=True):
            if not raw_text.strip():
                st.error("Please enter some expense text.")
            else:
                col_raw, col_struct = st.columns(2)
                with col_raw:
                    st.markdown("**📄 Raw Input**")
                    st.code(raw_text, language=None)

                with st.spinner("Extraction Agent processing..."):
                    extracted, err = extract_expenses(raw_text)

                if err:
                    st.error(f"Extraction failed: {err}")
                elif not extracted:
                    st.warning("No transactions found in the text.")
                else:
                    with col_struct:
                        st.markdown("**✅ Extracted Transactions**")
                        for tx in extracted:
                            st.markdown(f"""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;
            padding:12px 16px;margin-bottom:8px;animation:fadeInUp 0.4s ease forwards">
  <strong>{tx['merchant']}</strong> — ₹{tx['amount']:,.0f}<br>
  <span style="color:var(--text-muted);font-size:12px">
    📅 {tx['date']} | 💳 {tx['payment_method']} | 🧾 Invoice: {tx['invoice_number']}
  </span>
</div>
""", unsafe_allow_html=True)

                    new_rows = pd.DataFrame([{
                        "date": pd.to_datetime(t.get("date"), errors="coerce"),
                        "merchant": t.get("merchant", "Unknown"),
                        "description": t.get("description", ""),
                        "amount": float(t.get("amount", 0)),
                        "category": "Uncategorized",
                        "payment_method": t.get("payment_method", "Not available"),
                    } for t in extracted])

                    st.session_state.expenses = merge_expenses(st.session_state.expenses, new_rows)

                    st.markdown("### 🤖 Running Agent Pipeline...")
                    pipeline_ph = st.empty()
                    log_ph = st.empty()
                    run_pipeline(st.session_state.expenses, pipeline_ph, log_ph)
                    st.toast(f"✅ {len(extracted)} transaction(s) extracted and processed!", icon="🤖")


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD EXPENSES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "upload":
    st.markdown(section_header("📁 Upload Expenses", "Upload CSV files or invoice documents"), unsafe_allow_html=True)

    # ── Input method switch ───────────────────────────────────────────────────
    # The user can switch back to Manual Entry without using the sidebar.
    switch_col1, switch_col2 = st.columns(2)
    with switch_col1:
        if st.button("📝 Add Manually", use_container_width=True, key="switch_to_manual_from_upload"):
            st.session_state.page = "add"
            st.rerun()
    with switch_col2:
        if st.button("📁 Add CSV File", use_container_width=True, key="switch_to_csv"):
            st.session_state.page = "upload"
            st.rerun()

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    tabs = st.tabs(["📊 CSV Upload", "📄 Invoice / Document"])

    # ── CSV Upload ────────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("""
<div style="background:var(--surface2);border-radius:10px;padding:14px 18px;margin-bottom:16px;font-size:13px">
  <strong>Expected CSV format:</strong><br>
  <code>date, merchant, description, amount, category, payment_method</code><br>
  <span style="color:var(--text-muted)">• <em>date</em>, <em>merchant</em>, and <em>amount</em> are required. Other columns are optional.</span>
</div>
""", unsafe_allow_html=True)

        uploaded = st.file_uploader("Upload CSV file", type=["csv"], label_visibility="collapsed")

        if uploaded:
            file_bytes = uploaded.read()
            df_uploaded, errors = load_from_csv_bytes(file_bytes)

            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                st.markdown(f"**Preview — {len(df_uploaded)} rows loaded**")
                st.dataframe(
                    df_uploaded.head(20),
                    use_container_width=True,
                    hide_index=True,
                )

                if st.button("✅ Confirm & Run Agent Pipeline", use_container_width=True):
                    st.session_state.expenses = merge_expenses(
                        st.session_state.expenses, df_uploaded
                    )
                    st.markdown("### 🤖 Running Agent Pipeline...")
                    pipeline_ph = st.empty()
                    log_ph = st.empty()
                    run_pipeline(st.session_state.expenses, pipeline_ph, log_ph)
                    st.toast(f"✅ {len(df_uploaded)} rows imported!", icon="📊")
                    st.success("Import complete! View results on the Dashboard.")

        st.markdown("---")
        if st.button("📦 Load Built-in Sample Data", use_container_width=True):
            df = load_sample_data()
            st.session_state.expenses = df
            pipeline_ph = st.empty()
            log_ph = st.empty()
            run_pipeline(df, pipeline_ph, log_ph)
            st.toast("✅ Sample data loaded!", icon="📊")
            st.rerun()

    # ── Invoice Upload ────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("""
<div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);
            border-radius:10px;padding:14px 18px;margin-bottom:16px;font-size:13px">
  ⚠️ <strong>Invoice parsing</strong> works with <strong>text-based PDFs and TXT files</strong> only.
  Image-based (scanned) PDFs cannot be processed without OCR services.
</div>
""", unsafe_allow_html=True)

        inv_file = st.file_uploader("Upload invoice or receipt (PDF/TXT)", type=["pdf", "txt"])

        if inv_file:
            file_bytes = inv_file.read()
            raw_text, parse_err = parse_uploaded_file(inv_file.name, file_bytes)

            if parse_err:
                st.error(f"❌ {parse_err}")
            elif not raw_text.strip():
                st.warning("⚠️ File was empty or contained no readable text.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📄 Extracted Raw Text**")
                    st.text_area("", raw_text[:2000], height=200, disabled=True)

                if st.button("🔍 Extract & Process Invoice", use_container_width=True):
                    with st.spinner("Extraction Agent parsing invoice..."):
                        extracted, err = extract_expenses(raw_text)

                    if err:
                        st.error(f"Extraction failed: {err}")
                    elif not extracted:
                        st.warning("No transactions found in the document.")
                    else:
                        with col2:
                            st.markdown("**✅ Parsed Transactions**")
                            for tx in extracted:
                                st.markdown(f"""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;
            padding:12px 16px;margin-bottom:8px">
  <strong>{tx['merchant']}</strong> — ₹{tx['amount']:,.0f}<br>
  <span style="color:var(--text-muted);font-size:12px">
    📅 {tx['date']} | 🧾 Invoice: {tx['invoice_number']}
  </span>
</div>
""", unsafe_allow_html=True)

                        new_rows = pd.DataFrame([{
                            "date": pd.to_datetime(t.get("date"), errors="coerce"),
                            "merchant": t.get("merchant", "Unknown"),
                            "description": t.get("description", ""),
                            "amount": float(t.get("amount", 0)),
                            "category": "Uncategorized",
                            "payment_method": t.get("payment_method", "Not available"),
                        } for t in extracted])

                        st.session_state.expenses = merge_expenses(st.session_state.expenses, new_rows)
                        pipeline_ph = st.empty()
                        log_ph = st.empty()
                        run_pipeline(st.session_state.expenses, pipeline_ph, log_ph)
                        st.toast(f"✅ Invoice processed: {len(extracted)} transactions found", icon="📄")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPENSE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "classification":
    st.markdown(section_header("🏷️ Expense Classification", "AI-powered categorization of your transactions"), unsafe_allow_html=True)

    if not has_data():
        st.info("No expense data. Please add or upload expenses first.")
        st.stop()

    df = get_df()

    # Show table with category badges
    st.markdown(f"**{len(df)} transactions classified**")

    display_df = df.copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d").fillna("N/A")
    display_df["amount"] = display_df["amount"].apply(lambda x: f"₹{x:,.0f}")

    st.dataframe(
        display_df[["date", "merchant", "description", "amount", "category", "payment_method"]],
        use_container_width=True,
        hide_index=True,
    )

    # Category breakdown
    st.markdown("---")
    st.markdown("#### Category Breakdown")
    cat_df = spending_by_category(df)
    if not cat_df.empty:
        cols = st.columns(min(4, len(cat_df)))
        for i, (_, row) in enumerate(cat_df.iterrows()):
            color = CATEGORY_COLORS.get(row["category"], "#94a3b8")
            with cols[i % len(cols)]:
                st.markdown(metric_card(
                    row["category"],
                    f"₹{row['total']:,.0f}",
                    icon="📁",
                    color=color,
                    sub=f"{row['percentage']:.1f}% of total",
                    delay_ms=i * 60,
                ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.plotly_chart(spending_donut(cat_df), use_container_width=True, config={"displayModeBar": False})

    # Re-classify button
    st.markdown("---")
    if st.button("🔄 Re-classify Uncategorized Transactions", use_container_width=True):
        uncategorized = df[df["category"].isin(["Uncategorized", "Other"])]
        if uncategorized.empty:
            st.info("All transactions are already classified.")
        else:
            with st.spinner(f"Classifying {len(uncategorized)} transactions..."):
                tx_list = uncategorized.to_dict("records")
                classified, err = classify_expenses(tx_list)
                if err:
                    st.warning(f"Classification warning: {err}")
                for i, orig_idx in enumerate(uncategorized.index):
                    if i < len(classified):
                        df.at[orig_idx, "category"] = classified[i].get("category", "Other")
                st.session_state.expenses = df
            st.toast("✅ Re-classification complete!", icon="🏷️")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# SPENDING ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "analysis":
    st.markdown(section_header("📊 Spending Analysis", "Deep dive into your spending patterns"), unsafe_allow_html=True)

    if not has_data():
        st.info("No expense data available.")
        st.stop()

    df = get_df()
    stats = st.session_state.agent_results.get("stats", {})
    explanation = st.session_state.agent_results.get("analysis_explanation", "")

    if not stats:
        with st.spinner("Running analysis..."):
            stats, explanation, _ = analyse_spending(df)
            st.session_state.agent_results["stats"] = stats
            st.session_state.agent_results["analysis_explanation"] = explanation

    summary = stats.get("summary", compute_summary_stats(df))

    # Metric cards
    cols = st.columns(5)
    metrics = [
        ("Total Spending", f"₹{summary.get('total_spending', 0):,.0f}", "💰", "#6366f1"),
        ("Transactions", str(summary.get("transaction_count", 0)), "🧾", "#06b6d4"),
        ("Avg Expense", f"₹{summary.get('average_transaction', 0):,.0f}", "📊", "#8b5cf6"),
        ("Highest", f"₹{summary.get('highest_transaction', 0):,.0f}", "📈", "#f59e0b"),
        ("Lowest", f"₹{summary.get('lowest_transaction', 0):,.0f}", "📉", "#10b981"),
    ]
    for i, (label, val, icon, color) in enumerate(metrics):
        with cols[i]:
            st.markdown(metric_card(label, val, icon, color, delay_ms=i*80), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    ch1, ch2 = st.columns(2)
    with ch1:
        cat_df = spending_by_category(df)
        st.plotly_chart(spending_donut(cat_df), use_container_width=True, config={"displayModeBar": False})
    with ch2:
        mon_df = monthly_spending(df)
        st.plotly_chart(monthly_bar(mon_df), use_container_width=True, config={"displayModeBar": False})

    daily_df = daily_spending(df)
    st.plotly_chart(spending_timeline(daily_df), use_container_width=True, config={"displayModeBar": False})

    st.plotly_chart(category_horizontal_bars(cat_df), use_container_width=True, config={"displayModeBar": False})

    # AI Explanation
    st.markdown("---")
    st.markdown(f"#### {ai_tag()} AI Analysis", unsafe_allow_html=True)
    if explanation:
        st.markdown(f"""
<div style="background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--primary);
            border-radius:10px;padding:18px 22px;font-size:14px;line-height:1.7">
{explanation}
</div>
""", unsafe_allow_html=True)
    else:
        if st.button("🤖 Generate AI Explanation"):
            with st.spinner("Generating AI insight..."):
                _, explanation, _ = analyse_spending(df)
                st.session_state.agent_results["analysis_explanation"] = explanation
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "anomaly":
    st.markdown(section_header("⚠️ Anomaly Detection", "Identifies potentially unusual transactions using statistical analysis"), unsafe_allow_html=True)

    if not has_data():
        st.info("No expense data available.")
        st.stop()

    df = get_df()
    anomalies = st.session_state.agent_results.get("anomalies")

    if anomalies is None:
        with st.spinner("Running anomaly detection..."):
            anomalies, err = detect_and_explain_anomalies(df)
            st.session_state.agent_results["anomalies"] = anomalies

    st.markdown(f"""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;
            padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:16px">
  <div style="font-size:32px">{'⚠️' if anomalies else '✅'}</div>
  <div>
    <div style="font-weight:700;font-size:16px">
      {'Potential Anomalies Found' if anomalies else 'No Unusual Transactions Detected'}
    </div>
    <div style="color:var(--text-muted);font-size:13px">
      {f'{len(anomalies)} transaction(s) flagged using statistical Z-score analysis' if anomalies
       else 'All transactions appear consistent with historical patterns.'}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    if anomalies:
        st.markdown(f"#### {calculated_tag()} Detected Anomalies", unsafe_allow_html=True)
        for i, a in enumerate(anomalies):
            st.markdown(
                anomaly_card(
                    merchant=a.get("merchant", "Unknown"),
                    amount=a.get("amount", 0),
                    category=a.get("category", "Other"),
                    explanation=a.get("explanation", ""),
                    recommendation=a.get("recommendation", ""),
                    z_score=a.get("z_score", 0),
                    times_above=a.get("times_above_mean", 1),
                    delay_ms=i * 100,
                ),
                unsafe_allow_html=True,
            )

    # Anomaly scatter chart
    st.markdown("---")
    st.plotly_chart(
        anomaly_scatter(df, anomalies or []),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # Re-run button
    if st.button("🔄 Re-run Anomaly Detection"):
        with st.spinner("Running..."):
            anomalies, _ = detect_and_explain_anomalies(df)
            st.session_state.agent_results["anomalies"] = anomalies
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# BUDGET ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "budget":
    st.markdown(section_header("💰 Budget Analysis", "Compare actual spending against your defined budgets"), unsafe_allow_html=True)

    # Budget editor
    with st.expander("⚙️ Configure Budgets", expanded=not has_data()):
        st.markdown("Set monthly budgets per category (₹ 0 = not tracked).")
        budgets = st.session_state.budgets.copy()
        all_cats = [
            "Food", "Travel", "Shopping", "Utilities", "Healthcare",
            "Education", "Entertainment", "Office", "Rent", "Transportation", "Other"
        ]
        cols = st.columns(3)
        for i, cat in enumerate(all_cats):
            with cols[i % 3]:
                budgets[cat] = st.number_input(
                    f"{cat}", min_value=0.0, step=500.0,
                    value=float(budgets.get(cat, 0.0)),
                    key=f"budget_{cat}"
                )
        if st.button("💾 Save Budgets"):
            st.session_state.budgets = {k: v for k, v in budgets.items() if v > 0}
            st.toast("✅ Budgets saved!", icon="💾")
            # Re-run budget agent
            if has_data():
                comp, text, _ = analyse_budget(get_df(), st.session_state.budgets)
                st.session_state.agent_results["budget_comparison"] = comp
                st.session_state.agent_results["budget_text"] = text
            st.rerun()

    if not has_data():
        st.info("Load expense data to see budget analysis.")
        st.stop()

    df = get_df()
    budget_comp = st.session_state.agent_results.get("budget_comparison")
    budget_text = st.session_state.agent_results.get("budget_text", "")

    if not budget_comp:
        with st.spinner("Running budget analysis..."):
            budget_comp, budget_text, _ = analyse_budget(df, st.session_state.budgets)
            st.session_state.agent_results["budget_comparison"] = budget_comp
            st.session_state.agent_results["budget_text"] = budget_text

    if not budget_comp:
        st.warning("No budget data. Please configure budgets above.")
        st.stop()

    # Summary cards
    total_budget = sum(b["budget"] for b in budget_comp)
    total_spent = sum(b["spent"] for b in budget_comp)
    over_budget = [b for b in budget_comp if b["status"] == "Over Budget"]
    under_budget = [b for b in budget_comp if b["status"] == "Under Budget"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("Total Budget", f"₹{total_budget:,.0f}", "📋", "#6366f1", delay_ms=0), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Total Spent", f"₹{total_spent:,.0f}", "💸", "#f59e0b", delay_ms=80), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Over Budget", str(len(over_budget)), "🔴", "#ef4444", delay_ms=160), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("Under Budget", str(len(under_budget)), "🟢", "#10b981", delay_ms=240), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Progress bars
    st.markdown(f"#### {calculated_tag()} Budget Utilization", unsafe_allow_html=True)
    for row in sorted(budget_comp, key=lambda x: x["pct_used"], reverse=True):
        st.markdown(
            budget_progress_bar(row["category"], row["spent"], row["budget"], row["pct_used"]),
            unsafe_allow_html=True,
        )

    # Budget vs Actual chart
    st.markdown("---")
    st.plotly_chart(budget_vs_actual(budget_comp), use_container_width=True, config={"displayModeBar": False})

    # AI Feedback
    if budget_text:
        st.markdown("---")
        st.markdown(f"#### {ai_tag()} AI Budget Advisory", unsafe_allow_html=True)
        st.markdown(f"""
<div style="background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--primary);
            border-radius:10px;padding:18px 22px;font-size:14px;line-height:1.7">
{budget_text}
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# AI EXPENSE ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "assistant":
    st.markdown(section_header("🤖 AI Expense Assistant", "Ask questions about your spending in natural language"), unsafe_allow_html=True)

    if not has_data():
        st.info("Please load expense data first before chatting with the assistant.")
        st.stop()

    df = get_df()
    summary = compute_summary_stats(df)
    cat_df = spending_by_category(df)
    anomalies = st.session_state.agent_results.get("anomalies", [])

    # Build a compact expense summary for context
    cat_summary = "\n".join(
        f"- {r['category']}: ₹{r['total']:,.0f} ({r['percentage']:.1f}%)"
        for _, r in cat_df.iterrows()
    ) if not cat_df.empty else "No category data"

    anomaly_summary = "\n".join(
        f"- {a['merchant']}: ₹{a['amount']:,.0f} ({a['category']}) — {a.get('explanation', '')[:80]}"
        for a in anomalies
    ) if anomalies else "None detected"

    expense_summary = f"""
Total transactions: {summary.get('transaction_count', 0)}
Total spending: ₹{summary.get('total_spending', 0):,.0f}
Average transaction: ₹{summary.get('average_transaction', 0):,.0f}
Highest expense: ₹{summary.get('highest_transaction', 0):,.0f} at {summary.get('highest_merchant', 'N/A')}

Spending by category:
{cat_summary}

Anomalies:
{anomaly_summary}
"""

    # Chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

    # Suggested questions
    if not st.session_state.chat_history:
        st.markdown("**💡 Try asking:**")
        suggestions = [
            "Where am I spending the most?",
            "What was my highest expense?",
            "Which expenses look unusual?",
            "How much have I used of my food budget?",
            "Which category increased the most?",
        ]
        s_cols = st.columns(len(suggestions))
        for i, (col, q) in enumerate(zip(s_cols, suggestions)):
            with col:
                if st.button(q, key=f"sug_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": q})
                    st.rerun()

    # Chat input
    user_input = st.chat_input("Ask about your expenses...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            thinking_ph = st.empty()
            thinking_ph.markdown(thinking_dots(), unsafe_allow_html=True)

            sys_prompt = ASSISTANT_SYSTEM
            usr_prompt = ASSISTANT_USER.format(
                expense_summary=expense_summary,
                question=user_input,
            )

            try:
                full_response = ""
                response_ph = st.empty()
                thinking_ph.empty()
                for chunk in stream_groq(sys_prompt, usr_prompt):
                    full_response += chunk
                    response_ph.markdown(full_response + "▌")
                response_ph.markdown(full_response)
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            except Exception as e:
                thinking_ph.empty()
                err_msg = f"❌ Error: {e}"
                st.error(err_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": err_msg})

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "reports":
    st.markdown(section_header("📄 Expense Analysis Report", "Full summary with AI insights and download options"), unsafe_allow_html=True)

    if not has_data():
        st.info("No expense data available for report generation.")
        st.stop()

    df = get_df()
    summary = compute_summary_stats(df)
    cat_df = spending_by_category(df)
    anomalies = st.session_state.agent_results.get("anomalies", [])
    budget_comp = st.session_state.agent_results.get("budget_comparison", [])
    analysis_exp = st.session_state.agent_results.get("analysis_explanation", "")

    # ── Section 1: Expense Summary ────────────────────────────────────────────
    with st.expander("📋 Expense Summary", expanded=True):
        st.markdown(f"{calculated_tag()} Computed using Python", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Expenses", f"₹{summary.get('total_spending', 0):,.0f}")
        with c2:
            st.metric("Transactions", summary.get("transaction_count", 0))
        with c3:
            st.metric("Average Expense", f"₹{summary.get('average_transaction', 0):,.0f}")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Highest", f"₹{summary.get('highest_transaction', 0):,.0f}", delta=summary.get("highest_merchant", ""))
        with col2:
            st.metric("Lowest", f"₹{summary.get('lowest_transaction', 0):,.0f}", delta=summary.get("lowest_merchant", ""))

    # ── Section 2: Category Analysis ─────────────────────────────────────────
    with st.expander("🏷️ Category Analysis", expanded=True):
        st.markdown(f"{calculated_tag()} Category totals computed using Python", unsafe_allow_html=True)
        if not cat_df.empty:
            st.dataframe(cat_df.rename(columns={
                "category": "Category", "total": "Total (₹)",
                "percentage": "% of Total"
            }), use_container_width=True, hide_index=True)
            st.plotly_chart(spending_donut(cat_df), use_container_width=True, config={"displayModeBar": False})

    # ── Section 3: Anomaly Report ─────────────────────────────────────────────
    with st.expander(f"⚠️ Anomaly Report ({len(anomalies)} found)", expanded=bool(anomalies)):
        st.markdown(f"{calculated_tag()} Detected via Z-score analysis &nbsp; {ai_tag()} Explanations by Groq AI", unsafe_allow_html=True)
        if anomalies:
            for a in anomalies:
                st.markdown(f"""
| Field | Value |
|-------|-------|
| **Merchant** | {a.get('merchant', 'N/A')} |
| **Date** | {a.get('date', 'N/A')} |
| **Amount** | ₹{a.get('amount', 0):,.0f} |
| **Category** | {a.get('category', 'N/A')} |
| **Category Avg** | ₹{a.get('category_mean', 0):,.0f} |
| **Z-Score** | {a.get('z_score', 0):.2f} |
| **Explanation** | {a.get('explanation', 'N/A')} |
| **Recommendation** | {a.get('recommendation', 'N/A')} |
""")
                st.markdown("---")
        else:
            st.success("✅ No anomalies detected.")

    # ── Section 4: Budget Report ──────────────────────────────────────────────
    with st.expander("💰 Budget Report", expanded=bool(budget_comp)):
        st.markdown(f"{calculated_tag()} Budget vs. actual computed in Python &nbsp; {ai_tag()} Feedback by Groq AI", unsafe_allow_html=True)
        if budget_comp:
            budget_df_report = pd.DataFrame(budget_comp)
            display_cols = ["category", "budget", "spent", "remaining", "pct_used", "status"]
            st.dataframe(
                budget_df_report[display_cols].rename(columns={
                    "category": "Category", "budget": "Budget (₹)", "spent": "Spent (₹)",
                    "remaining": "Remaining (₹)", "pct_used": "% Used", "status": "Status"
                }),
                use_container_width=True, hide_index=True,
            )
            st.plotly_chart(budget_vs_actual(budget_comp), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No budget data. Configure budgets in the Budget Analysis page.")

    # ── Section 5: AI Insights ────────────────────────────────────────────────
    with st.expander("🤖 AI Insights", expanded=True):
        st.markdown(f"{ai_tag()} Generated by Groq LLM — based on your actual data", unsafe_allow_html=True)
        if analysis_exp:
            st.markdown(analysis_exp)
        else:
            if st.button("🤖 Generate AI Insights Now"):
                with st.spinner("Generating..."):
                    _, explanation, _ = analyse_spending(df)
                    st.session_state.agent_results["analysis_explanation"] = explanation
                st.rerun()

    # ── Download options ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📥 Download Report")
    col1, col2 = st.columns(2)

    with col1:
        csv_data = df.copy()
        csv_data["date"] = csv_data["date"].dt.strftime("%Y-%m-%d")
        csv_bytes = csv_data.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Expenses CSV",
            data=csv_bytes,
            file_name="expense_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        # Plain text report
        report_lines = [
            "AI INVOICE & EXPENSE ANALYZER — REPORT",
            "=" * 50,
            f"Total Spending    : ₹{summary.get('total_spending', 0):,.0f}",
            f"Transactions      : {summary.get('transaction_count', 0)}",
            f"Average Expense   : ₹{summary.get('average_transaction', 0):,.0f}",
            f"Highest Expense   : ₹{summary.get('highest_transaction', 0):,.0f}",
            "",
            "CATEGORY BREAKDOWN",
            "-" * 30,
        ]
        for _, row in cat_df.iterrows():
            report_lines.append(f"{row['category']}: ₹{row['total']:,.0f} ({row['percentage']:.1f}%)")
        report_lines += ["", "ANOMALIES DETECTED", "-" * 30]
        if anomalies:
            for a in anomalies:
                report_lines.append(f"- {a['merchant']}: ₹{a['amount']:,.0f} | {a['explanation']}")
        else:
            report_lines.append("No anomalies detected.")
        report_lines += ["", "AI INSIGHTS", "-" * 30, analysis_exp or "Run the pipeline to generate insights."]

        report_txt = "\n".join(report_lines).encode("utf-8")
        st.download_button(
            "⬇️ Download Text Report",
            data=report_txt,
            file_name="expense_report.txt",
            mime="text/plain",
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ABOUT PROJECT
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "about":
    st.markdown(section_header("ℹ️ About Project", "AI Invoice & Expense Analyzer"), unsafe_allow_html=True)

    st.markdown("""
<div style="background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:28px 32px;margin-bottom:24px">
  <h3 style="margin-top:0">💸 AI Invoice & Expense Analyzer</h3>
  <p style="color:var(--text-muted)">
    A multi-agent AI application built with Python, Streamlit, and the Groq API that helps
    individuals and small organizations understand their spending through intelligent, 
    automated expense analysis.
  </p>
  
  <h4>🤖 Multi-Agent Architecture</h4>
  <p>Five specialized AI agents cooperate sequentially to analyze your expenses:</p>
  <ol>
    <li><strong>🔍 Extraction Agent</strong> — Parses raw text, invoices, and CSV files into structured data</li>
    <li><strong>🏷️ Classification Agent</strong> — Categorizes each transaction into 11 spending categories</li>
    <li><strong>📊 Analysis Agent</strong> — Computes statistics in Python and explains them in plain language</li>
    <li><strong>⚠️ Anomaly Detection Agent</strong> — Flags statistically unusual transactions using Z-score analysis</li>
    <li><strong>💰 Budget Advisory Agent</strong> — Compares spending against user-defined budgets and provides advice</li>
  </ol>

  <h4>🛠️ Technology Stack</h4>
  <ul>
    <li><strong>Python</strong> — Core language</li>
    <li><strong>Streamlit</strong> — Interactive web UI with custom CSS/HTML animations</li>
    <li><strong>Groq API</strong> — Fast LLM inference (llama-3.3-70b-versatile)</li>
    <li><strong>Pandas</strong> — All numerical calculations</li>
    <li><strong>Plotly</strong> — Interactive, animated charts</li>
  </ul>

  <h4>📐 Data Integrity Principles</h4>
  <ul>
    <li>All arithmetic is performed in Python — the LLM never calculates numbers</li>
    <li>The LLM only provides natural-language explanations of pre-computed results</li>
    <li>Missing information is explicitly marked "Not available" — never invented</li>
    <li>Anomalies are described with cautious language — never accused of fraud</li>
    <li>Budget advice is based only on user-provided data</li>
  </ul>

  <h4>⚙️ How to Run</h4>
  <pre style="background:var(--surface2);padding:12px;border-radius:8px;font-size:13px">
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Groq API key
cp .env.example .env
# Edit .env and add: GROQ_API_KEY=your_key_here

# 3. Run the app
streamlit run app.py
  </pre>

  <h4>🔒 Privacy</h4>
  <p style="color:var(--text-muted)">
    All financial data is processed in-session only and is never stored permanently.
    No data is sent to any service other than the Groq API for language model inference.
  </p>
</div>
""", unsafe_allow_html=True)

    # Agent pipeline demo
    st.markdown("#### 🔄 Agent Pipeline Demo")
    demo_states = ["done", "done", "done", "done", "done"]
    demo_logs = [
        "✅ Extraction Agent: 30 transactions loaded",
        "✅ Classification Agent: {Food: 10, Travel: 4, Utilities: 4, ...}",
        "✅ Analysis Agent: total ₹45,800 across 30 transactions",
        "⚠️ Anomaly Agent: 1 potential anomaly detected",
        "✅ Budget Agent: 2 categories over budget",
    ]
    st.markdown(render_pipeline(demo_states, demo_logs), unsafe_allow_html=True)
