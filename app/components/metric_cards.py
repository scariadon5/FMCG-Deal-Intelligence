import streamlit as st


ICONS = {
    "Final Articles": ("01", "Stories surfaced"),
    "Tier 1 Sources": ("02", "High-confidence coverage"),
    "Unique Sources": ("03", "Distinct publishers"),
    "Last Generated": ("04", "Latest pipeline output"),
}


def render(df, latest_file):
    if df.empty:
        st.html('<div class="card"><p>No pipeline results found yet. Click "Run Live Pipeline" in the sidebar.</p></div>')
        return

    tier1_count = len(df[df.get("credibility_tier", "") == "tier_1"])
    unique_sources = df["source"].nunique() if "source" in df.columns else 0
    newsletter_date = latest_file.replace("newsletter_", "").replace(".md", "") if latest_file else "N/A"

    metrics = [
        ("Final Articles", len(df)),
        ("Tier 1 Sources", tier1_count),
        ("Unique Sources", unique_sources),
        ("Last Generated", newsletter_date),
    ]

    cards_html = ""
    for label, value in metrics:
        index_label, meta = ICONS[label]
        cards_html += f"""
        <div class="kpi-card">
            <div class="kpi-card-top">
                <div class="kpi-index">{index_label}</div>
                <div class="kpi-meta">{meta}</div>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>"""

    st.html(f'<div class="kpi-grid">{cards_html}</div>')
