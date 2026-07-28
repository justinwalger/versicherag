import time

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from loguru import logger

from src.ingestion.models import DocumentMetadata, ParsedDocument
from src.llm.prompts import METADATA_PROMPT

MAX_RETRIES = 5


class Enricher:
    """Enriches documents with additional metadata or context."""

    def __init__(self, llm: genai.Client, model_name: str) -> None:
        self.llm = llm
        self.model_name = model_name

    def _generate_content(self, prompt: str) -> types.GenerateContentResponse:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self.llm.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=DocumentMetadata,
                    ),
                )
            except ClientError as e:
                if e.code != 429 or attempt == MAX_RETRIES:
                    raise
                wait = 60
                logger.warning(
                    f"Rate limit readed (try {attempt}/{MAX_RETRIES}), waiting {wait}s: {e}"
                )
                time.sleep(wait)
        raise RuntimeError("Metadata generation retries exhausted without a response or error.")

    def enrich(self, markdown: str) -> ParsedDocument:
        """Enriches the document by extracting metadata using a language model."""
        prompt = METADATA_PROMPT.format(content=markdown)
        response = self._generate_content(prompt)
        metadata = response.parsed
        if not isinstance(metadata, DocumentMetadata):
            raise TypeError(
                f"Expected DocumentMetadata from structured output, got {type(metadata)!r}."
            )
        return ParsedDocument(
            content=markdown,
            anbieter=metadata.anbieter,
            datum=metadata.datum,
            police=metadata.police,
            kategorie=metadata.kategorie,
        )
