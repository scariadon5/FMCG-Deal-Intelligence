import streamlit as st
import markdown as md

def render(newsletter_content):
    if not newsletter_content:
        st.html('<div class="card"><p>No newsletter generated yet. Run the pipeline to create one.</p></div>')
        return

    html_body = md.markdown(newsletter_content, extensions=["extra"])
    st.html(f'<div class="newsletter-card">{html_body}</div>')