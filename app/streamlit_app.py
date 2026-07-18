import streamlit as st
import importlib
from components.pipeline import render as render_pipeline
from components.hero import render as render_hero
from components.sidebar import render as render_sidebar
from components.topbar import render as render_topbar
from components.metric_cards import render as render_metrics
from components.newsletter import render as render_newsletter
from components.downloads import render as render_downloads
from components.deal_cards import render as render_deals

from src.utils.load_data import (
    load_final_articles,
    get_latest_newsletter,
)
from pathlib import Path
def load_css():
    css_path = Path(__file__).parent / "styles" / "main.css"

    with open(css_path) as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True,
        )


# ----------------------------------------------------
# Page Configuration
# ----------------------------------------------------

st.set_page_config(
    page_title="FMCG Deal Intelligence Newsletter",
    page_icon="📰",
    layout="wide",
)
load_css()

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
            import src.pipeline.run_pipeline as run_pipeline_module
            import src.pipeline.newsletter_generator as newsletter_module

            run_pipeline_module = importlib.reload(run_pipeline_module)
            newsletter_module = importlib.reload(newsletter_module)

            progress_placeholder.info(
                "Ingesting live news, then running Stage 1 → Stage 2 → Dedup → Credibility..."
            )

            run_pipeline_module.run_pipeline()

            progress_placeholder.info(
                "Generating newsletter draft..."
            )

            newsletter_module.generate_newsletter()

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

render_topbar()

st.html('<div id="overview" class="page-anchor"></div>')
render_hero()

render_metrics(
    articles_df,
    latest_file,
)

st.html('<div id="pipeline" class="page-anchor"></div>')
render_pipeline()

st.html('<div id="newsletter" class="page-anchor"></div>')
render_newsletter(
    newsletter_content,
)

st.html('<div id="sources" class="page-anchor"></div>')
render_downloads(
    newsletter_content,
    latest_file,
    articles_df,
)

st.html('<div id="deals" class="page-anchor"></div>')
render_deals(
    articles_df,
)
