import streamlit as st

from components.sidebar import render as render_sidebar
from components.metric_cards import render as render_metrics
from components.newsletter import render as render_newsletter
from components.downloads import render as render_downloads
from components.deal_cards import render as render_deals

from src.utils.load_data import (
    load_final_articles,
    get_latest_newsletter,
)

# ----------------------------------------------------
# Page Configuration
# ----------------------------------------------------

st.set_page_config(
    page_title="FMCG Deal Intelligence Newsletter",
    page_icon="📰",
    layout="wide",
)

# ----------------------------------------------------
# Sidebar
# ----------------------------------------------------

run_live = render_sidebar()

# ----------------------------------------------------
# Run Pipeline
# ----------------------------------------------------

if run_live:
    with st.spinner("Running full pipeline... this takes a few minutes"):
        progress_placeholder = st.empty()

        try:
            from src.pipeline.run_pipeline import run_pipeline
            from src.pipeline.newsletter_generator import generate_newsletter

            progress_placeholder.info(
                "Ingesting live news, then running Stage 1 → Stage 2 → Dedup → Credibility..."
            )

            run_pipeline()

            progress_placeholder.info(
                "Generating newsletter draft..."
            )

            generate_newsletter()

            progress_placeholder.success(
                "Pipeline complete! Refreshing results..."
            )

            st.cache_data.clear()

        except Exception as e:
            progress_placeholder.error(
                f"Pipeline failed:\n{e}"
            )

# ----------------------------------------------------
# Load Data
# ----------------------------------------------------

articles_df = load_final_articles()
latest_file, newsletter_content = get_latest_newsletter()

# ----------------------------------------------------
# Main Page
# ----------------------------------------------------

st.title("📰 FMCG Deal Intelligence Newsletter")

st.markdown(
    "*Automated, real-time M&A and investment tracking for the FMCG sector*"
)

st.markdown("---")

# ----------------------------------------------------
# Metrics
# ----------------------------------------------------

render_metrics(
    articles_df,
    latest_file,
)

# ----------------------------------------------------
# Newsletter
# ----------------------------------------------------

render_newsletter(
    newsletter_content,
)

# ----------------------------------------------------
# Downloads
# ----------------------------------------------------

render_downloads(
    newsletter_content,
    latest_file,
    articles_df,
)

# ----------------------------------------------------
# Raw Articles
# ----------------------------------------------------

render_deals(
    articles_df,
)