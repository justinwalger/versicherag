"""Module for API dependencies.

Currently simple dependency injection for the chat agent, but can be expanded
in the future to include other dependencies as needed.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.config import get_settings
from src.llm.agent import ChatAgent
from src.llm.judge import AnswerJudge
from src.llm.prompts import CHAT_SYSTEM_PROMPT
from src.llm.tools import get_all_tools

_password_header = APIKeyHeader(name="X-API-Password", auto_error=False)


def verify_password(password: str | None = Depends(_password_header)) -> None:
    """Gate access with the shared password the Streamlit UI prompts users for."""
    if password != get_settings().app_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")


def build_chat_agent(
    checkpointer: BaseCheckpointSaver, model: BaseChatModel, judge: AnswerJudge
) -> ChatAgent:
    """Build the chat agent once at startup, so it shares the same checkpointer and models
    across requests."""
    return ChatAgent(
        model=model,
        tools=get_all_tools(),
        system_prompt=CHAT_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        judge=judge,
    )
