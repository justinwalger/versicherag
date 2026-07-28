from enum import StrEnum

from pydantic import BaseModel


class Role(StrEnum):
    """Enum for message roles."""

    human = "human"
    ai = "ai"


class Message(BaseModel):
    """A single chat message."""

    role: Role
    content: str
