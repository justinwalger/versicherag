"""Module for API dependencies.

Currently simple dependency injection for the chat agent, but can be expanded
in the future to include other dependencies as needed.
"""

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.llm.agent import ChatAgent
from src.llm.judge import AnswerJudge
from src.llm.prompts import CHAT_SYSTEM_PROMPT
from src.llm.tools import get_all_tools


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
