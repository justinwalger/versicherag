from collections.abc import Iterator

import streamlit as st

from src.ui.constants import AVATARS
from src.ui.models import Message, Role


def write_human_message(text: str) -> None:
    """Display a human message and append it to session state."""
    avatar = AVATARS.get(Role.human)
    with st.chat_message(Role.human, avatar=avatar):
        st.markdown(text)
    st.session_state.messages.append(Message(role=Role.human, content=text))


def _format_citation(metadata: dict) -> str:
    """Renders one retrieved chunk's metadata as "Document - Section - Paragraph"."""
    product_title, source = metadata.get("product_title"), metadata.get("source")
    if product_title and source:
        document = f"{product_title} ({source})"
    else:
        document = product_title or source or "Unbekanntes Dokument"
    section = metadata.get("Header 1")
    paragraph = metadata.get("Header 3") or metadata.get("Header 2")

    location = " › ".join(
        part for part in (document, section, paragraph if paragraph != section else None) if part
    )

    page_start, page_end = metadata.get("page_start"), metadata.get("page_end")
    if page_start and page_end:
        page = f"Seite {page_start}" if page_start == page_end else f"Seite {page_start}-{page_end}"
        location += f" ({page})"

    return location


def _citation_key(metadata: dict) -> tuple:
    return (
        metadata.get("source"),
        metadata.get("Header 1"),
        metadata.get("Header 2"),
        metadata.get("Header 3"),
    )


def write_ai_response(events: Iterator[dict]) -> bool:
    """Stream an AI response from backend events, append it to session state, and
    list the retrieved chunks (Document - Section - Paragraph) it was grounded in -
    sourced directly from the search tool's results, not the model's own wording.

    Returns True if the backend rejected the request for a wrong/missing password."""
    avatar = AVATARS.get(Role.ai)
    with st.chat_message(Role.ai, avatar=avatar):
        tool_placeholder = st.empty()
        message_placeholder = st.empty()

        full_response = ""
        citations: list[dict] = []
        seen: set[tuple] = set()

        for event in events:
            event_type = event.get("type")
            content = event.get("content", "")

            if event_type == "auth_error":
                st.error(content or "Falsches Passwort.")
                return True

            if event_type == "connection_error":
                st.error(content or "Server nicht erreichbar.")
                return False

            if event_type == "tool":
                tool_placeholder.info(content)
                continue

            if event_type == "tool_result":
                for hit in event.get("artifact") or []:
                    metadata = hit.get("metadata") or {}
                    key = _citation_key(metadata)
                    if key not in seen:
                        seen.add(key)
                        citations.append(metadata)
                continue

            if event_type == "ai" and content:
                full_response += content
                message_placeholder.markdown(full_response + "▌")

        if full_response:
            message_placeholder.markdown(full_response)

        if citations:
            with st.expander(f"Quellen ({len(citations)})"):
                for metadata in citations:
                    st.markdown(f"- {_format_citation(metadata)}")

    if full_response:
        st.session_state.messages.append(Message(role=Role.ai, content=full_response))

    return False


def display_message(message: Message) -> None:
    """Display message in chat based on role."""
    role = message.role
    avatar = AVATARS.get(role)
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.content)
