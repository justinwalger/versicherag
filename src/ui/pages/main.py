"""Main page of the app, used for interacting with the llm."""

import streamlit as st

from src.ui.backend_connector import BackendConnector
from src.ui.components.chat import display_message, write_ai_response, write_human_message
from src.ui.constants import DISCLAIMER, SUGGESTIONS

_connector = BackendConnector()


def handle_suggestion_change() -> None:
    st.session_state.pending_suggestion = st.session_state.selected_suggestion


def _prompt_for_password() -> str | None:
    """Ask for the shared password once per session; returns None until entered."""
    if st.session_state.get("api_password"):
        return st.session_state.api_password

    st.title("VersicherungsAssist", anchor=False)
    password = st.text_input("Passwort", type="password", key="password_input")
    if st.button("Anmelden") and password:
        match _connector.check_password(password):
            case True:
                st.session_state.api_password = password
                st.rerun()
            case False:
                st.error("Falsches Passwort.")
            case None:
                st.error("Server nicht erreichbar.")
    return None


def _ask_and_render(question: str, password: str) -> None:
    write_human_message(question)
    llm_generator = _connector.ask_backend(
        message=question,
        thread_id=st.session_state.thread_id,
        password=password,
    )
    if write_ai_response(llm_generator):
        st.session_state.api_password = None
        st.rerun()


def create_main_page():
    """Create main page."""
    st.warning(DISCLAIMER)

    password = _prompt_for_password()
    if password is None:
        return

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
        _ask_and_render(suggested_question, password)

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
        _ask_and_render(human_input, password)
