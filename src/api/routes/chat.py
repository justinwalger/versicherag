"""Module for chat-related API routes."""

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from src.api.dependencies import verify_password
from src.api.schemas.chat import ChatRequest

router = APIRouter(dependencies=[Depends(verify_password)])


@router.get("/auth/check")
async def check_password() -> dict[str, bool]:
    """Cheap endpoint the UI calls to validate a password right after entry,
    without running the full chat pipeline. 401s via the router's dependency
    if the password is wrong or missing."""
    return {"ok": True}


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
