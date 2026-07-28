"""Pydantic models shared across the retrieval module."""

from pydantic import BaseModel


class QdrantOutput(BaseModel):
    """Output model for the QdrantRetriever tool."""

    text: str
    metadata: dict | None = None
