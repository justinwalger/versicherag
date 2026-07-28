"""Main page of the app, used for interacting with the llm."""

import streamlit as st

from src.ui.backend_connector import BackendConnector
from src.ui.components.chat import display_message, write_ai_response, write_human_message
from src.ui.constants import DISCLAIMER, SUGGESTIONS

_connector = BackendConnector()


def handle_suggestion_change() -> None:
    st.session_state.pending_suggestion = st.session_state.selected_suggestion


def create_main_page():
    """Create main page."""
    st.warning(DISCLAIMER)

    title_row = st.container(
        horizontal=True,
        vertical_alignment="bottom",
    )

    with title_row:
        st.title(
            "VersicherungsAssist",
            anchor=False,
            width="stretch",
        )
    st.caption(
        "Beantwortet Fragen zu deinen Versicherungsbedingungen auf Basis der "
        "hinterlegten Vertragsdokumente. Keine individuelle Rechts- oder Steuerberatung."
    )
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Ask for suggestions
    st.pills(
        label="Schnelleinstiege",
        label_visibility="collapsed",
        options=SUGGESTIONS.keys(),
        key="selected_suggestion",
        on_change=handle_suggestion_change,
    )

    # Container for chat history
    with st.container():
        for message in st.session_state.messages:
            display_message(message)

    # Flow for suggested questions
    pending_suggestion = st.session_state.get("pending_suggestion")
    if pending_suggestion:
        suggested_question = SUGGESTIONS[pending_suggestion]
        st.session_state.pending_suggestion = None
        write_human_message(suggested_question)
        llm_generator = _connector.ask_backend(
            message=suggested_question,
            thread_id=st.session_state.thread_id,
        )
        write_ai_response(llm_generator)

    # footer
    with title_row:

        def clear_conversation():
            st.session_state.messages = []

        st.button(
            "Neues Gespräch",
            icon=":material/refresh:",
            on_click=clear_conversation,
        )

    # Flow for human input
    if human_input := st.chat_input("Stelle eine Frage...", key="initial_question"):
        write_human_message(human_input)
        llm_generator = _connector.ask_backend(
            message=human_input,
            thread_id=st.session_state.thread_id,
        )
        write_ai_response(llm_generator)
