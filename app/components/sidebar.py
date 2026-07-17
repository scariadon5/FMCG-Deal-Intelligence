import streamlit as st
def render():
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
        
    return run_live
