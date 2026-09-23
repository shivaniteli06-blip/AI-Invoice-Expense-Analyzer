"""
UI Animations — CSS keyframes and reusable animation helper strings.
"""

KEYFRAMES = """
<style>
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0);     }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes pulse {
  0%, 100% { opacity: 1;   transform: scale(1);    }
  50%       { opacity: 0.7; transform: scale(1.05); }
}
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes popIn {
  0%   { opacity: 0; transform: scale(0.8); }
  70%  { transform: scale(1.05); }
  100% { opacity: 1; transform: scale(1); }
}
@keyframes fillBar {
  from { width: 0%; }
  to   { width: var(--target-width); }
}
@keyframes countUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0);   }
}
@keyframes dotBounce {
  0%, 80%, 100% { transform: translateY(0);   opacity: 0.4; }
  40%           { transform: translateY(-6px); opacity: 1;   }
}
@keyframes pipelineFill {
  from { width: 0%; }
  to   { width: 100%; }
}
@keyframes glowPulse {
  0%, 100% { box-shadow: 0 0 4px 1px rgba(99,102,241,0.3); }
  50%       { box-shadow: 0 0 12px 4px rgba(99,102,241,0.7); }
}
@keyframes slideInLog {
  from { opacity: 0; transform: translateX(-12px); }
  to   { opacity: 1; transform: translateX(0);     }
}
</style>
"""

# Staggered section entrance — apply to each section wrapper div
def stagger_style(index: int, base_delay_ms: int = 80) -> str:
    delay = index * base_delay_ms
    return (
        f"animation: fadeInUp 0.5s ease forwards; "
        f"animation-delay: {delay}ms; "
        f"opacity: 0;"
    )


SHIMMER_CARD_CSS = """
.skeleton {
  background: linear-gradient(
    90deg,
    var(--surface2) 25%,
    var(--border)   50%,
    var(--surface2) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  border-radius: 8px;
  height: 20px;
  margin: 6px 0;
}
"""

PIPELINE_CSS = """
.pipeline-wrapper {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 18px 0 10px;
  overflow-x: auto;
}
.pipeline-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 110px;
  position: relative;
  z-index: 1;
}
.pipeline-node .node-icon {
  width: 52px; height: 52px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
  font-weight: 600;
  transition: all 0.4s ease;
  position: relative;
}
.pipeline-node .node-label {
  margin-top: 8px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  max-width: 100px;
}
/* States */
.node-waiting .node-icon {
  background: var(--surface2);
  color: var(--text-muted);
  border: 2px solid var(--border);
}
.node-running .node-icon {
  background: rgba(99,102,241,0.12);
  color: var(--primary);
  border: 2px solid var(--primary);
  animation: glowPulse 1.2s ease-in-out infinite;
}
.node-done .node-icon {
  background: rgba(16,185,129,0.12);
  color: var(--success);
  border: 2px solid var(--success);
  animation: popIn 0.4s ease forwards;
}
/* Connector line */
.pipeline-connector {
  flex: 1;
  height: 3px;
  background: var(--border);
  position: relative;
  overflow: hidden;
  min-width: 20px;
  margin-top: -24px;
}
.pipeline-connector .fill {
  height: 100%;
  background: var(--success);
  width: 0%;
  transition: width 0.6s ease;
}
.pipeline-connector .fill.done {
  width: 100%;
}
/* Log lines */
.agent-log {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
  margin-top: 14px;
  max-height: 180px;
  overflow-y: auto;
  font-family: 'Inter', monospace;
  font-size: 12.5px;
}
.log-line {
  padding: 4px 0;
  color: var(--text-muted);
  animation: slideInLog 0.3s ease forwards;
  border-bottom: 1px solid var(--border);
}
.log-line:last-child { border-bottom: none; }
.log-line .log-icon { margin-right: 6px; }
.log-line.success { color: var(--success); }
.log-line.warning { color: var(--warning); }
.log-line.running { color: var(--primary); }
/* Thinking dots */
.thinking-dots { display: inline-flex; gap: 4px; align-items: center; }
.thinking-dots span {
  width: 6px; height: 6px;
  background: var(--primary);
  border-radius: 50%;
  animation: dotBounce 1.4s infinite;
}
.thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
"""

CARD_CSS = """
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px 22px;
  box-shadow: var(--card-shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  animation: fadeInUp 0.5s ease forwards;
  opacity: 0;
  cursor: default;
  position: relative;
  overflow: hidden;
}
.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--card-shadow-hover);
}
.metric-card .icon-badge {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  margin-bottom: 12px;
}
.metric-card .metric-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.metric-card .metric-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
  animation: countUp 0.4s ease forwards;
}
.metric-card .metric-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}
/* Anomaly badge */
.anomaly-card {
  background: var(--surface);
  border: 1px solid var(--danger);
  border-left: 4px solid var(--danger);
  border-radius: 12px;
  padding: 16px 20px;
  margin: 10px 0;
  animation: fadeInUp 0.4s ease forwards;
  opacity: 0;
}
/* Budget bar */
.budget-bar-wrap {
  background: var(--surface2);
  border-radius: 6px;
  height: 10px;
  overflow: hidden;
  margin: 6px 0;
}
.budget-bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 1s ease;
}
/* Chat bubble */
.chat-msg-user {
  background: var(--primary);
  color: #fff;
  border-radius: 18px 18px 4px 18px;
  padding: 10px 16px;
  max-width: 75%;
  margin-left: auto;
  margin-bottom: 10px;
  font-size: 14px;
  animation: fadeIn 0.25s ease;
}
.chat-msg-ai {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px 18px 18px 4px;
  padding: 10px 16px;
  max-width: 85%;
  margin-right: auto;
  margin-bottom: 10px;
  font-size: 14px;
  animation: fadeIn 0.25s ease;
}
"""
