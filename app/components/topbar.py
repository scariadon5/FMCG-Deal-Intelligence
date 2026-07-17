import streamlit as st


def render():
    st.html(f"""
    <div class="topbar">
        <div class="topbar-left">
            <div class="topbar-title">FMCG Deal Intelligence</div>
            <div class="topbar-subtitle">Executive monitoring workspace</div>
        </div>
        <div class="topbar-right">
            <div class="topbar-chip">Live dashboard</div>
            <div class="topbar-section">Scrollable workspace</div>
        </div>
    </div>
    """)
