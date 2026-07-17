import streamlit as st
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "pipeline"))
from stage2 import STRONG_FMCG_COMPANIES, normalize

COLORS = ["#3B82F6", "#22C55E", "#8B5CF6", "#F59E0B", "#14B8A6", "#F97066", "#EAB308"]

def detect_company(text):
    text_norm = normalize(text)
    for company in STRONG_FMCG_COMPANIES:
        if company in text_norm:
            return company.title()
    return "Other"

def render(df):
    if df.empty:
        return

    df = df.copy()
    df["detected_company"] = df["text"].apply(detect_company)
    grouped = [(c, g) for c, g in df[df["detected_company"] != "Other"].groupby("detected_company")]
    grouped.sort(key=lambda x: -len(x[1]))

    st.html('<div class="section-title">Deals this period</div>')

    company_names = ["All companies"] + [c for c, _ in grouped]
    selected = st.selectbox("Filter", company_names, label_visibility="collapsed")

    rows_html = ""
    for i, (company, group) in enumerate(grouped):
        if selected != "All companies" and selected != company:
            continue
        color = COLORS[i % len(COLORS)]
        count = len(group)
        top_headline = group.iloc[0]["text"]
        initial = company[0]
        rows_html += f"""
        <div class="deal-row">
            <div class="deal-logo" style="background:{color}22;color:{color}">{initial}</div>
            <div class="deal-row-main">
                <span class="deal-company">{company}</span>
                <span class="deal-badge" style="--badge-bg:{color}22;--badge-color:{color}">{count} deal{'s' if count != 1 else ''}</span>
                <div class="deal-headline">{top_headline}</div>
            </div>
            <div class="deal-chevron">›</div>
        </div>"""

    st.html(f'<div class="card">{rows_html}</div>')

    with st.expander("View raw article data"):
        st.dataframe(df, width="stretch")