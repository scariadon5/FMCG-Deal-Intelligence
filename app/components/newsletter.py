import streamlit as st
import markdown as md
import re

def render(newsletter_content):
    if not newsletter_content:
        st.html('<div class="card"><p>No newsletter generated yet. Run the pipeline to create one.</p></div>')
        return

    html_body = md.markdown(newsletter_content, extensions=["extra"])
    # Open source links in a new tab rather than navigating away from the dashboard
    html_body = re.sub(r'<a href=', '<a target="_blank" rel="noopener" href=', html_body)

    st.html(f"""
    <div class="newsletter-shell">
        <div class="newsletter-frame">
            <div class="newsletter-eyebrow">Newsletter draft</div>
            <div class="newsletter-card">{html_body}</div>
        </div>
    </div>
    """)
