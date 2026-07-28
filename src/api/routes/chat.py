"""Module for chat-related API routes."""

import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from src.api.schemas.chat import ChatRequest

router = APIRouter()


@router.post("/chat")
async def stream_chat(
    request: ChatRequest,
    http_request: Request,
) -> StreamingResponse:
    """Main endpoint for streaming chat responses.

    It takes a ChatRequest containing the thread ID and message, and streams
    back the response from the chat agent, which retrieves grounding passages
    itself via its search tool.
    """
    agent = http_request.app.state.agent

    async def generate():
        messages = [HumanMessage(content=request.message)]
        async for event in agent.stream(messages, thread_id=request.thread_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
