"""Streamlit entry point for the application.

design is inspired by https://github.com/streamlit/demo-ai-ai/blob/main/streamlit_app.py. thanks!
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from src.ui.pages.main import create_main_page

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

st.set_page_config(page_title="VersicherungsAssist", page_icon="📄")

st.markdown(
    """
    <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

create_main_page()
