import streamlit as st
def render(newsletter_content):
    st.subheader("📄 Latest Newsletter Draft")
    if newsletter_content:
        st.markdown(newsletter_content)
    else:
        st.info("No newsletter generated yet. Run the pipeline to create one.")
