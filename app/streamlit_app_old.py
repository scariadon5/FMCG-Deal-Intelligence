"""
streamlit_app.py

Demo app for the FMCG Deal Intelligence Newsletter pipeline.
Fast by default (loads pre-saved results); a "Run Live Pipeline" button
re-runs the full ingestion -> Stage 1 -> Stage 2 -> dedup -> credibility
-> newsletter chain on demand.
"""

import streamlit as st
import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "pipeline"))

st.set_page_config(
    page_title="FMCG Deal Intelligence Newsletter",
    page_icon="📰",
    layout="wide",
)

FINAL_ARTICLES_CSV = "data/processed/final_articles.csv"
NEWSLETTER_DIR = "outputs/newsletter_drafts"


def get_latest_newsletter():
    """Find the most recently generated newsletter file."""
    if not os.path.exists(NEWSLETTER_DIR):
        return None, None
    files = [f for f in os.listdir(NEWSLETTER_DIR) if f.endswith(".md")]
    if not files:
        return None, None
    files.sort(reverse=True)  # filenames include date, so this sorts newest first
    latest = files[0]
    with open(os.path.join(NEWSLETTER_DIR, latest), "r", encoding="utf-8") as f:
        content = f.read()
    return latest, content


@st.cache_data
def load_final_articles():
    if os.path.exists(FINAL_ARTICLES_CSV):
        return pd.read_csv(FINAL_ARTICLES_CSV)
    return pd.DataFrame()
# --- Sidebar ---
with st.sidebar:
    st.title("📰 FMCG Deal Intelligence")
    st.markdown("Real-time M&A and investment newsletter for the FMCG sector.")
    st.markdown("---")

    st.subheader("Pipeline Stages")
    st.markdown("""
    1. **Ingestion** — Google News RSS (real-time, no API key)
    2. **Stage 1** — ML relevance classifier (TF-IDF + Logistic Regression)
    3. **Stage 2** — FMCG entity + deal-verb rule gate
    4. **Deduplication** — TF-IDF cosine similarity
    5. **Credibility scoring** — source tier ranking
    6. **Newsletter generation** — single LLM call (Gemini)
    """)
    st.markdown("---")

    run_live = st.button("🔄 Run Live Pipeline", type="primary", width="stretch")
    st.caption("Takes 2-4 minutes — fetches live news and regenerates everything.")


# --- Run the live pipeline if requested ---
if run_live:
    with st.spinner("Running full pipeline... this takes a few minutes"):
        progress_placeholder = st.empty()
        try:
            from run_pipeline import run_pipeline
            progress_placeholder.info("Ingesting live news, then running Stage 1 → Stage 2 → dedup → credibility...")
            final_articles = run_pipeline()

            progress_placeholder.info("Generating newsletter draft...")
            from newsletter_generator import generate_newsletter
            generate_newsletter()

            progress_placeholder.success("Pipeline complete! Refreshing results below.")
            st.cache_data.clear()  # force reload of the freshly-updated CSV
        except Exception as e:
            progress_placeholder.error(f"Pipeline run failed: {e}")

# --- Main content area ---
st.title("📰 FMCG Deal Intelligence Newsletter")
st.markdown("*Automated, real-time M&A and investment tracking for the FMCG sector*")
st.markdown("---")

articles_df = load_final_articles()

# --- Funnel metrics ---
if not articles_df.empty:
    st.subheader("Pipeline Results")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Final Articles", len(articles_df))
    with col2:
        tier1_count = len(articles_df[articles_df.get("credibility_tier", "") == "tier_1"])
        st.metric("Tier 1 Sources", tier1_count)
    with col3:
        unique_sources = articles_df["source"].nunique() if "source" in articles_df.columns else 0
        st.metric("Unique Sources", unique_sources)
    with col4:
        latest_file, _ = get_latest_newsletter()
        newsletter_date = latest_file.replace("newsletter_", "").replace(".md", "") if latest_file else "N/A"
        st.metric("Last Generated", newsletter_date)

    st.markdown("---")
else:
    st.warning("No pipeline results found yet. Click 'Run Live Pipeline' in the sidebar to generate results.")

# --- Newsletter display ---
st.subheader("📄 Latest Newsletter Draft")
latest_file, newsletter_content = get_latest_newsletter()

if newsletter_content:
    st.markdown(newsletter_content)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            label="⬇️ Download Newsletter (.md)",
            data=newsletter_content,
            file_name=latest_file,
            mime="text/markdown",
            width="stretch",
        )
    with col_b:
        if not articles_df.empty:
            csv_data = articles_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Raw Articles (.csv)",
                data=csv_data,
                file_name="final_articles.csv",
                mime="text/csv",
                width="stretch",
            )
else:
    st.info("No newsletter generated yet. Run the pipeline to create one.")

# --- Raw data table (collapsible) ---
if not articles_df.empty:
    with st.expander("🔍 View Raw Article Data"):
        st.dataframe(articles_df, width="stretch")