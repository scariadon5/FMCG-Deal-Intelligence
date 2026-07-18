import streamlit as st
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "pipeline"))
from stage2 import STRONG_FMCG_COMPANIES, normalize

FUNNEL_PATH = "data/processed/funnel_summary.json"


def _detect_company(text):
    text_norm = normalize(text)
    for company in STRONG_FMCG_COMPANIES:
        if company in text_norm:
            return company.title()
    return None


def _load_funnel():
    if os.path.exists(FUNNEL_PATH):
        with open(FUNNEL_PATH) as f:
            return json.load(f)
    return {}


def render(df):
    if df.empty:
        return

    funnel = _load_funnel()
    ingested = funnel.get("ingested")
    final = funnel.get("final", len(df))
    conversion_pct = round((final / ingested) * 100, 1) if ingested else None

    df = df.copy()
    df["detected_company"] = df["text"].apply(_detect_company)
    known = df[df["detected_company"].notna()]

    if not known.empty:
        top_company_row = known["detected_company"].value_counts().reset_index().iloc[0]
        top_company, top_count = top_company_row["detected_company"], top_company_row["count"]
    else:
        top_company, top_count = None, 0

    tier1_pct = (
        round(len(df[df.get("credibility_tier", "") == "tier_1"]) / len(df) * 100, 1)
        if len(df) else None
    )

    narrative_parts = [f"{final} deals surfaced"]
    if ingested:
        narrative_parts.append(f"from {ingested} raw articles ({conversion_pct}% conversion)")
    if top_company:
        narrative_parts.append(f"led by {top_company} with {top_count} deal{'s' if top_count != 1 else ''}")
    narrative = ", ".join(narrative_parts) + "."

    stats_html = f"""
    <div class="exec-stat">
        <div class="exec-stat-value">{conversion_pct if conversion_pct is not None else '—'}%</div>
        <div class="exec-stat-label">Funnel conversion</div>
    </div>
    <div class="exec-stat">
        <div class="exec-stat-value">{top_company or '—'}</div>
        <div class="exec-stat-label">Leading company</div>
    </div>
    <div class="exec-stat">
        <div class="exec-stat-value">{tier1_pct if tier1_pct is not None else '—'}%</div>
        <div class="exec-stat-label">Tier-1 coverage</div>
    </div>
    """

    st.html(f"""
    <div class="card exec-summary-card">
        <h3>Executive summary</h3>
        <p class="exec-narrative">{narrative}</p>
        <div class="exec-stat-row">{stats_html}</div>
    </div>
    """)
