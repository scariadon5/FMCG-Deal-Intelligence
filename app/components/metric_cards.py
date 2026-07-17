import streamlit as st
def render(df, latest_file):
    if not df.empty:
        st.subheader("Pipeline Results")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Final Articles", len(df))
        with col2:
            tier1_count = len(df[df.get("credibility_tier", "") == "tier_1"])
            st.metric("Tier 1 Sources", tier1_count)
        with col3:
            unique_sources = df["source"].nunique() if "source" in df.columns else 0
            st.metric("Unique Sources", unique_sources)
        with col4:
            newsletter_date = latest_file.replace("newsletter_", "").replace(".md", "") if latest_file else "N/A"
            st.metric("Last Generated", newsletter_date)

        st.markdown("---")
    else:
        st.warning("No pipeline results found yet. Click 'Run Live Pipeline' in the sidebar to generate results.")
