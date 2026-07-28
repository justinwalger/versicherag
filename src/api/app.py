"""Entry point for the API."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from google import genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from src.api.dependencies import build_chat_agent
from src.api.routes import chat
from src.config import get_settings
from src.llm.judge import AnswerJudge


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # TODO: Replace InMemorySaver with a persistent checkpointer (e.g., database-backed)
    # for production use (probably overkill)

    settings = get_settings()
    checkpointer = InMemorySaver()
    chat_model = ChatGoogleGenerativeAI(
        model=settings.gemini_chat_model, api_key=settings.gemini_api_key
    )
    judge = AnswerJudge(
        client=genai.Client(api_key=settings.gemini_api_key),
        model_name=settings.gemini_judge_model,
    )

    app.state.agent = build_chat_agent(checkpointer=checkpointer, model=chat_model, judge=judge)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(chat.router, prefix="/api")
