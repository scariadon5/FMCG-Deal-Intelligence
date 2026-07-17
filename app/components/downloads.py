import streamlit as st
def render(newsletter_content, latest_file, articles_df):
            col1,col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Download Newsletter (.md)",
                    data=newsletter_content,
                    file_name=latest_file,
                    mime="text/markdown",
                    width="stretch",
                )
            with col2:
                st.download_button(
                    label="⬇️ Download Raw Articles (.csv)",
                    data=articles_df.to_csv(index=False),
                    file_name="final_articles.csv",
                    mime="text/csv",
                    width="stretch",
                )