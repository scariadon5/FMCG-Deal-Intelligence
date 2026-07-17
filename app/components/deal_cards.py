import streamlit as st

def render(df):

    if not df.empty:

        with st.expander("🔍 View Raw Article Data"):
            st.dataframe(df, use_container_width=True)