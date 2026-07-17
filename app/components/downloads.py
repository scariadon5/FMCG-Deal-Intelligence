import streamlit as st


def render(newsletter_content, latest_file, articles_df):
    st.html("""
    <div class="downloads-shell">
        <div class="downloads-header">
            <div class="section-title">Exports</div>
            <div class="downloads-subtitle">Download the generated newsletter or the underlying article set</div>
        </div>
    </div>
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="downloads-card">
                <div class="download-item">
                    <div class="download-label">Newsletter draft</div>
                    <div class="download-meta">Markdown export for sharing and review</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if newsletter_content and latest_file:
            st.download_button(
                label="Download Newsletter (.md)",
                data=newsletter_content,
                file_name=latest_file,
                mime="text/markdown",
                width="stretch",
            )
        else:
            st.button("Newsletter unavailable", width="stretch", disabled=True)

    with col2:
        st.markdown(
            """
            <div class="downloads-card">
                <div class="download-item">
                    <div class="download-label">Article dataset</div>
                    <div class="download-meta">CSV export of the filtered article list</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not articles_df.empty:
            st.download_button(
                label="Download Raw Articles (.csv)",
                data=articles_df.to_csv(index=False),
                file_name="final_articles.csv",
                mime="text/csv",
                width="stretch",
            )
        else:
            st.button("Dataset unavailable", width="stretch", disabled=True)
