"""
UI Components — all HTML/CSS components for the app.
Uses xp- prefixed CSS classes defined in ui/theme.py.
Count-up cards use self-contained HTML with inline styles (no CSS var dependency)
so they work correctly inside st.components.v1.html iframes.
"""
import streamlit as st
import streamlit.components.v1 as components
from ui.theme import CATEGORY_COLORS


def inject_all_css():
    """No-op — theme is injected directly in app.py before anything else."""
    pass


# ─── Section Header ───────────────────────────────────────────────────────────

def section_header(title: str, subtitle: str = "", delay_ms: int = 0) -> str:
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    return f"""
<div class="xp-section-header" style="animation-delay:{delay_ms}ms">
  <h2>{title}</h2>
  {sub_html}
</div>
"""


# ─── Metric Card (static HTML, rendered via st.markdown) ─────────────────────

def metric_card(
    label: str,
    value: str,
    icon: str,
    color: str = "#6c63ff",
    sub: str = "",
    delay_ms: int = 0,
) -> str:
    return f"""
<div class="xp-card" style="animation-delay:{delay_ms}ms">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;
              background:linear-gradient(90deg,{color},{color}88);
              border-radius:18px 18px 0 0"></div>
  <div class="xp-icon" style="background:{color}18;color:{color}">{icon}</div>
  <div class="xp-label">{label}</div>
  <div class="xp-value">{value}</div>
  {"<div class='xp-sub'>" + sub + "</div>" if sub else ""}
</div>
"""


# ─── Count-Up Card (self-contained iframe via components.html) ────────────────

def count_up_card(
    label: str,
    numeric_value: float,
    prefix: str = "₹",
    icon: str = "💰",
    color: str = "#6c63ff",
    sub: str = "",
    delay_ms: int = 0,
) -> None:
    """
    Renders a glass metric card with count-up animation.
    Self-contained HTML with no dependency on parent CSS variables.
    """
    card_id = f"cu_{abs(hash(label+str(delay_ms))) % 99999}"
    sub_html = f'<div style="font-size:12px;color:#64748b;margin-top:5px;font-family:Poppins,sans-serif">{sub}</div>' if sub else ""

    html = f"""
<!DOCTYPE html>
<html>
<head>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; padding:0; margin:0; overflow:hidden; }}
  .card {{
    background:#ffffff;
    border:1px solid #e8eaf6;
    border-radius:18px;
    padding:20px 22px 18px;
    box-shadow:0 2px 16px rgba(108,99,255,0.07),0 1px 4px rgba(0,0,0,0.05);
    position:relative;
    overflow:hidden;
    transition:transform 0.22s ease,box-shadow 0.22s ease;
    animation:fadeInUp 0.5s ease both;
    animation-delay:{delay_ms}ms;
    font-family:'Poppins',sans-serif;
    height:120px;
  }}
  .card:hover {{
    transform:translateY(-4px);
    box-shadow:0 8px 32px rgba(108,99,255,0.14),0 2px 8px rgba(0,0,0,0.08);
  }}
  .top-bar {{
    position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,{color},{color}88);
    border-radius:18px 18px 0 0;
  }}
  .icon {{
    width:40px;height:40px;border-radius:11px;
    background:{color}18;color:{color};
    display:inline-flex;align-items:center;justify-content:center;
    font-size:18px;margin-bottom:10px;
  }}
  .lbl {{
    font-size:10px;font-weight:600;text-transform:uppercase;
    letter-spacing:0.08em;color:#64748b;margin-bottom:3px;
  }}
  .val {{
    font-size:26px;font-weight:700;color:#1a1d2e;
    letter-spacing:-0.03em;line-height:1.1;
  }}
  @keyframes fadeInUp {{
    from {{ opacity:0; transform:translateY(18px); }}
    to   {{ opacity:1; transform:translateY(0); }}
  }}
</style>
</head>
<body>
<div class="card">
  <div class="top-bar"></div>
  <div class="icon">{icon}</div>
  <div class="lbl">{label}</div>
  <div class="val" id="{card_id}">0</div>
  {sub_html}
</div>
<script>
(function() {{
  var el = document.getElementById('{card_id}');
  if (!el) return;
  var target = {float(numeric_value)};
  var isInt = (target % 1 === 0);
  var duration = 1000;
  var start = null;
  function easeOut(t) {{ return 1 - Math.pow(1-t, 3); }}
  function fmt(n) {{
    if (isInt) return '{prefix}' + Math.round(n).toLocaleString('en-IN');
    return '{prefix}' + n.toFixed(1);
  }}
  function step(ts) {{
    if (!start) start = ts;
    var prog = Math.min((ts - start) / duration, 1);
    el.textContent = fmt(easeOut(prog) * target);
    if (prog < 1) requestAnimationFrame(step);
    else el.textContent = fmt(target);
  }}
  setTimeout(function() {{ requestAnimationFrame(step); }}, {delay_ms});
}})();
</script>
</body>
</html>
"""
    components.html(html, height=132, scrolling=False)


# ─── Pipeline Visualizer ─────────────────────────────────────────────────────

PIPELINE_STAGES = [
    ("🔍", "Extraction"),
    ("🏷️", "Classification"),
    ("📊", "Analysis"),
    ("⚠️", "Anomaly"),
    ("💰", "Budget"),
]


def render_pipeline(stage_states: list, log_lines: list = None) -> str:
    """
    Render the 5-node animated pipeline as HTML using xp- CSS classes.
    stage_states: list of 5 "waiting" | "running" | "done" strings
    log_lines: optional list of log message strings
    """
    nodes_html = ""
    for i, (icon, label) in enumerate(PIPELINE_STAGES):
        state = stage_states[i] if i < len(stage_states) else "waiting"
        node_class = f"xp-{state}"
        # Show spinner for running, checkmark for done
        display_icon = icon
        if state == "running":
            display_icon = f'<span style="display:inline-block;animation:spin 0.8s linear infinite">⚙️</span>'
        elif state == "done":
            display_icon = "✅"

        nodes_html += f'''
<div class="xp-node {node_class}">
  <div class="xp-node-icon">{display_icon}</div>
  <div class="xp-node-label">{label}</div>
</div>'''

        if i < len(PIPELINE_STAGES) - 1:
            done_class = "done" if stage_states[i] == "done" else ""
            nodes_html += f'''
<div class="xp-connector">
  <div class="xp-connector-fill {done_class}"></div>
</div>'''

    log_html = ""
    if log_lines:
        lines_html = ""
        for line in log_lines:
            if "✅" in line:
                cls = "success"
            elif "⚠" in line:
                cls = "warning"
            elif "⏳" in line:
                cls = "running"
            else:
                cls = ""
            lines_html += f'<div class="xp-log-line {cls}">{line}</div>'
        log_html = f'<div class="xp-log">{lines_html}</div>'

    return f'<div class="xp-pipeline">{nodes_html}</div>{log_html}'


# ─── Thinking Dots ────────────────────────────────────────────────────────────

def thinking_dots() -> str:
    return '<div class="xp-thinking"><span></span><span></span><span></span></div>'


# ─── Anomaly Card ─────────────────────────────────────────────────────────────

def anomaly_card(
    merchant: str,
    amount: float,
    category: str,
    explanation: str,
    recommendation: str,
    z_score: float,
    times_above: float,
    delay_ms: int = 0,
) -> str:
    color = CATEGORY_COLORS.get(category, "#94a3b8")
    return f"""
<div class="xp-anomaly" style="animation-delay:{delay_ms}ms">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
    <div>
      <span style="font-weight:700;font-size:15px;font-family:Poppins,sans-serif">⚠️ {merchant}</span>
      <span style="background:{color}18;color:{color};font-size:11px;font-weight:600;
                   padding:2px 9px;border-radius:10px;margin-left:8px;font-family:Poppins,sans-serif">{category}</span>
    </div>
    <div style="font-size:18px;font-weight:700;color:#ef4444;font-family:Poppins,sans-serif">₹{amount:,.0f}</div>
  </div>
  <div style="font-size:13px;color:#64748b;margin-bottom:10px;line-height:1.6;font-family:Poppins,sans-serif">{explanation}</div>
  <div style="display:flex;gap:14px;font-size:12px;color:#64748b;font-family:Poppins,sans-serif">
    <span>📊 Z-score: <strong>{z_score:.1f}</strong></span>
    <span>📈 <strong>{times_above:.1f}×</strong> category avg</span>
  </div>
  <div style="margin-top:10px;padding:8px 14px;background:rgba(245,158,11,0.08);
              border-radius:8px;font-size:12px;color:#b45309;font-family:Poppins,sans-serif">
    💡 {recommendation}
  </div>
</div>
"""


# ─── Category Badge ───────────────────────────────────────────────────────────

def category_badge(category: str) -> str:
    color = CATEGORY_COLORS.get(category, "#94a3b8")
    return (
        f'<span style="background:{color}18;color:{color};font-size:11px;'
        f'font-weight:600;padding:2px 10px;border-radius:10px;'
        f'border:1px solid {color}30;font-family:Poppins,sans-serif">{category}</span>'
    )


# ─── Budget Progress Bar ──────────────────────────────────────────────────────

def budget_progress_bar(category: str, spent: float, budget: float, pct: float) -> str:
    color = "#10b981" if pct <= 80 else ("#f59e0b" if pct <= 100 else "#ef4444")
    safe_pct = min(pct, 100)
    return f"""
<div style="margin-bottom:18px;animation:fadeInUp 0.4s ease both">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
    <span style="font-weight:600;font-size:13px;font-family:Poppins,sans-serif">
      {category_badge(category)}&nbsp; <span style="color:#1a1d2e">{category}</span>
    </span>
    <span style="font-size:13px;font-family:Poppins,sans-serif;
                 color:{'#ef4444' if pct > 100 else '#64748b'}">
      ₹{spent:,.0f} / ₹{budget:,.0f}
    </span>
  </div>
  <div class="xp-budget-bar-track">
    <div class="xp-budget-bar-fill" style="width:{safe_pct}%;background:{color}"></div>
  </div>
  <div style="font-size:11px;color:#64748b;text-align:right;margin-top:2px;
              font-family:Poppins,sans-serif">{pct:.1f}% used</div>
</div>
"""


# ─── Privacy Notice ───────────────────────────────────────────────────────────

PRIVACY_NOTICE = """
<div class="xp-privacy">
  🔒 <strong>Privacy:</strong> Financial data is processed in-session only and never stored permanently.
  Handle uploaded financial information with care.
</div>
"""


# ─── Tag Badges ───────────────────────────────────────────────────────────────

def calculated_tag() -> str:
    return '<span class="xp-tag-calc">🧮 Calculated</span>'


def ai_tag() -> str:
    return '<span class="xp-tag-ai">🤖 AI Insight</span>'


# ─── Sidebar Builder ──────────────────────────────────────────────────────────

def build_sidebar_nav(pages: dict, current_page: str, pipeline_ran: bool) -> str:
    """
    Return a fully custom HTML sidebar nav block.
    Clicking items works via Streamlit query params trick — we use st.button
    wrappers that are hidden by CSS, and render HTML nav on top as visual layer.
    The actual navigation uses st.button under the hood.
    """
    logo_html = """
<div class="xp-sidebar-logo">
  <div class="logo-icon">💸</div>
  <div class="logo-title">AI Expense Analyzer</div>
  <div class="logo-sub">Multi-Agent Intelligence</div>
</div>
<div class="xp-nav-sep"></div>
"""

    nav_html = ""
    for label, key in pages.items():
        active_class = "active" if current_page == key else ""
        # Split emoji icon from label text
        parts = label.split(" ", 1)
        icon = parts[0] if len(parts) > 1 else "•"
        text = parts[1] if len(parts) > 1 else label
        nav_html += f'''
<div class="xp-nav-item {active_class}" id="nav-{key}"
     onclick="window.parent.document.querySelectorAll('[data-testid=stSidebar] button[data-key=nav_{key}]')[0]?.click()">
  <span style="font-size:16px;width:22px;text-align:center">{icon}</span>
  <span>{text}</span>
  {"<span class='xp-sidebar-badge'>ACTIVE</span>" if active_class else ""}
</div>'''

    # Agent status dots
    dot_html = ""
    agents = ["🔍 Extraction", "🏷️ Classification", "📊 Analysis", "⚠️ Anomaly", "💰 Budget"]
    for agent in agents:
        dot_class = "active" if pipeline_ran else "idle"
        dot_html += f'''
<div style="display:flex;align-items:center;padding:4px 0;font-size:12px;
            font-family:Poppins,sans-serif;color:#64748b">
  <span class="xp-dot {dot_class}"></span>{agent}
</div>'''

    status_html = f"""
<div class="xp-nav-sep"></div>
<div style="padding:4px 4px 8px;font-size:10px;font-weight:700;text-transform:uppercase;
            letter-spacing:0.1em;color:#94a3b8;font-family:Poppins,sans-serif">
  Agent Status
</div>
{dot_html}
"""

    return logo_html + nav_html + status_html


# ─── Empty State ─────────────────────────────────────────────────────────────

def empty_state_html(
    icon: str = "📊",
    title: str = "No Data Yet",
    subtitle: str = "Load data to get started.",
) -> str:
    return f"""
<div class="xp-empty">
  <span class="xp-empty-icon">{icon}</span>
  <h3>{title}</h3>
  <p>{subtitle}</p>
</div>
"""
