from pydantic import BaseModel


class ChatRequest(BaseModel):
    """ChatRequest model for the chat API endpoint.
    Takes a thread_id to identify the conversation and a message to send to the chat agent.
    """

    message: str
    thread_id: str
