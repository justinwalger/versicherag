"""Pydantic models shared across the llm module."""

from pydantic import BaseModel


class JudgeVerdict(BaseModel):
    """Result of reviewing a draft answer."""

    passed: bool
    issues: list[str] = []
