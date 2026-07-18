import streamlit as st
import json
from src.utils.export_docx import markdown_to_docx


def render(newsletter_content, latest_file, articles_df):
    st.html("""
    <div class="downloads-shell">
        <div class="downloads-header">
            <div class="section-title">Exports</div>
            <div class="downloads-subtitle">Download the generated newsletter or the underlying article set</div>
        </div>
    </div>
    """)

    col1, col1b, col2, col3 = st.columns(4)
    with col1:
        st.markdown(
            """
            <div class="downloads-card">
                <div class="download-item">
                    <div class="download-label">Newsletter draft (.md)</div>
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

    with col1b:
        st.markdown(
            """
            <div class="downloads-card">
                <div class="download-item">
                    <div class="download-label">Newsletter draft (.docx)</div>
                    <div class="download-meta">Word export for business users</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if newsletter_content and latest_file:
            docx_bytes = markdown_to_docx(newsletter_content)
            docx_filename = latest_file.replace(".md", ".docx")
            st.download_button(
                label="Download Newsletter (.docx)",
                data=docx_bytes,
                file_name=docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                width="stretch",
            )
        else:
            st.button("Newsletter unavailable", width="stretch", disabled=True)

    with col2:
        st.markdown(
            """
            <div class="downloads-card">
                <div class="download-item">
                    <div class="download-label">Article dataset (CSV)</div>
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

    with col3:
        st.markdown(
            """
            <div class="downloads-card">
                <div class="download-item">
                    <div class="download-label">Article dataset (JSON)</div>
                    <div class="download-meta">JSON export of the filtered article list</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not articles_df.empty:
            st.download_button(
                label="Download Raw Articles (.json)",
                data=articles_df.to_json(orient="records", indent=2),
                file_name="final_articles.json",
                mime="application/json",
                width="stretch",
            )
        else:
            st.button("Dataset unavailable", width="stretch", disabled=True)
