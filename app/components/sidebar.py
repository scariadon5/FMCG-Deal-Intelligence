import streamlit as st

def render():
    with st.sidebar:
        st.html("""
        <div style="padding:8px 4px 24px">
            <div style="font-weight:800;font-size:1.15rem;color:var(--text);line-height:1.3">
                FMCG<br>Deal<br>Intelligence
            </div>
        </div>
        """)

        st.html("""
        <div class="nav-list">
            <div class="nav-item nav-active">Overview</div>
            <div class="nav-item">Newsletter</div>
            <div class="nav-item">Deals</div>
            <div class="nav-item">Pipeline</div>
            <div class="nav-item">Sources</div>
        </div>
        <hr style="margin:20px 0">
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
        st.html(f'<div class="side-stage-list">{stage_html}</div>')

        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
        run_live = st.button("Run Live Pipeline", type="primary", width="stretch")
        st.caption("Takes 2-4 minutes — fetches live news and regenerates everything.")

    return run_live