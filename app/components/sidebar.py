import streamlit as st


def render():
    with st.sidebar:
        st.html("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-mark">FD</div>
            <div class="sidebar-brand-copy">
                <div class="sidebar-brand-title">FMCG Deal Intelligence</div>
                <div class="sidebar-brand-subtitle">Executive dashboard</div>
            </div>
        </div>
        """)

        st.html("""
        <div class="sidebar-section">
            <div class="nav-section-label">Workspace</div>
        </div>
        <div class="sidebar-panel nav-list">
            <a class="nav-link nav-link-active" href="#overview">Overview</a>
            <a class="nav-link" href="#newsletter">Newsletter</a>
            <a class="nav-link" href="#deals">Deals</a>
            <a class="nav-link" href="#pipeline">Pipeline</a>
            <a class="nav-link" href="#sources">Sources</a>
        </div>
        """)

        st.html("""
        <div class="sidebar-section">
            <div class="nav-section-label">Pipeline stages</div>
        """)

        stages = [
            ("1", "Ingestion", "RSS feed", "var(--accent-blue)"),
            ("2", "Stage 1", "ML classifier", "var(--accent-purple)"),
            ("3", "Stage 2", "Rule gate", "var(--accent-amber)"),
            ("4", "Deduplication", "TF-IDF similarity", "var(--accent-teal)"),
            ("5", "Credibility", "Source scoring", "var(--accent-green)"),
            ("6", "Newsletter", "LLM generation", "var(--accent-purple)"),
        ]
        stage_html = ""
        for num, label, sub, color in stages:
            stage_html += f"""
            <div class="side-stage">
                <div class="side-stage-dot" style="background:{color}">{num}</div>
                <div class="side-stage-line"></div>
                <div>
                    <div class="side-stage-label">{label}</div>
                    <div class="side-stage-sub">{sub}</div>
                </div>
            </div>"""
        st.html(f'<div class="sidebar-panel side-stage-list">{stage_html}</div></div>')

        st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
        run_live = st.button("Generate Newsletter", type="primary", width="stretch")
        st.caption("Takes 2-4 minutes — fetches live news and builds this period's newsletter.")

    return run_live
