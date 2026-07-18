import streamlit as st
import json, os

FUNNEL_PATH = "data/processed/funnel_summary.json"

STAGES = [
    ("01", "Ingestion", "RSS feed", "ingested"),
    ("02", "Recency", "Last N days", "recency_filtered"),
    ("03", "Stage 1", "ML classifier", "stage1"),
    ("04", "Stage 2", "Rule gate", "stage2"),
    ("05", "Deduplication", "TF-IDF similarity", "dedup"),
    ("06", "Credibility", "Source scoring", "final"),
    ("07", "Newsletter", "LLM generation", "final"),
]


def load_funnel():
    if os.path.exists(FUNNEL_PATH):
        with open(FUNNEL_PATH) as f:
            return json.load(f)
    return {}


def render():
    funnel = load_funnel()
    stages_html = ""
    for i, (index_label, label, sub, key) in enumerate(STAGES):
        count = funnel.get(key, "—")
        stages_html += f"""
        <div class="pipeline-stage">
            <div class="pipeline-stage-top">
                <div class="stage-index">{index_label}</div>
                <div class="stage-kicker">Articles</div>
            </div>
            <div class="stage-label">{label}</div>
            <div class="stage-sub">{sub}</div>
            <div class="stage-count">{count}</div>
        </div>"""
        if i < len(STAGES) - 1:
            stages_html += '<div class="pipeline-connector"></div>'

    st.html(f"""
    <div class="card pipeline-card">
        <div class="pipeline-header">
            <div>
                <h3>Pipeline overview</h3>
                <p>From raw news intake to executive-ready output</p>
            </div>
        </div>
        <div class="pipeline-row">{stages_html}</div>
    </div>
    """)
