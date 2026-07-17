import streamlit as st
import json, os

FUNNEL_PATH = "data/processed/funnel_summary.json"

ICONS = {"ingested": "📡", "stage1": "🧠", "stage2": "⏚", "dedup": "⧉", "credibility": "🛡", "final": "📄"}

STAGES = [
    ("1. Ingestion", "RSS feed", "var(--accent-blue)", "ingested"),
    ("2. Stage 1", "ML classifier", "var(--accent-purple)", "stage1"),
    ("3. Stage 2", "Rule gate", "var(--accent-amber)", "stage2"),
    ("4. Deduplication", "TF-IDF similarity", "var(--accent-teal)", "dedup"),
    ("5. Credibility", "Source scoring", "var(--accent-green)", "final"),
    ("6. Newsletter", "LLM generation", "var(--accent-purple)", "final"),
]

def load_funnel():
    if os.path.exists(FUNNEL_PATH):
        with open(FUNNEL_PATH) as f:
            return json.load(f)
    return {}

def render():
    funnel = load_funnel()
    stages_html = ""
    for i, (label, sub, color, key) in enumerate(STAGES):
        count = funnel.get(key, "—")
        icon = list(ICONS.values())[i]
        stages_html += f"""
        <div class="pipeline-stage">
            <div class="stage-circle" style="background:{color}">{icon}</div>
            <div class="stage-label">{label}</div>
            <div class="stage-sub">{sub}</div>
            <div class="stage-count">{count}<br><span style="font-weight:400;color:var(--muted);font-size:0.75rem">Articles</span></div>
        </div>"""
        if i < len(STAGES) - 1:
            stages_html += '<div class="pipeline-connector"></div>'

    st.html(f"""
    <div class="card">
        <h3>Pipeline overview</h3>
        <p>From raw news to intelligence</p>
        <div class="pipeline-row">{stages_html}</div>
    </div>
    """)