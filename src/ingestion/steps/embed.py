"""Embedding step of the ingestion pipeline: create vector representations for text chunks using the Gemini Embeddings API."""

import time
from typing import TypeAlias, cast

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from loguru import logger

MAX_RETRIES = 5

# Asymmetric task types: a query and the document it should match are embedded
# differently on purpose, so search compares "this is a search query" against
# "this is a passage to be retrieved" rather than two generic embeddings.
# see https://ai.google.dev/gemini-api/docs/embeddings
TASK_TYPE_QUERY = "RETRIEVAL_QUERY"
TASK_TYPE_DOCUMENT = "RETRIEVAL_DOCUMENT"

Embedding: TypeAlias = list[float]
Embeddings: TypeAlias = list[Embedding]


class Embedder:
    def __init__(self, model_name: str, client: genai.Client) -> None:
        self.model_name = model_name
        self.client = client

    def _embed_content(
        self, contents: types.ContentListUnion, task_type: str
    ) -> types.EmbedContentResponse:
        """Embeds the given content using the Gemini Embeddings API, with retry logic for rate limiting."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self.client.models.embed_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.EmbedContentConfig(task_type=task_type),
                )
            except ClientError as e:
                if e.code != 429 or attempt == MAX_RETRIES:
                    raise
                wait = 60
                logger.warning(
                    f"Rate limit readed (try {attempt}/{MAX_RETRIES}), waiting {wait}s: {e}"
                )
                time.sleep(wait)
        raise RuntimeError("Embedding retries exhausted without a response or error.")

    def embed(self, text: str, task_type: str = TASK_TYPE_QUERY) -> Embedding:
        """Creates a vector representation for a single text chunk using the Gemini Embeddings API."""
        result = self._embed_content(text, task_type=task_type)
        if not result.embeddings or result.embeddings[0].values is None:
            raise RuntimeError("Gemini returned no embedding for the given text.")
        return result.embeddings[0].values

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
        task_type: str = TASK_TYPE_DOCUMENT,
    ) -> Embeddings:
        """Creates vector representations for multiple text chunks using the Gemini Embeddings API."""
        embeddings: Embeddings = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]

            contents = cast(
                types.ContentListUnion,
                [types.Content(parts=[types.Part(text=text)]) for text in chunk],
            )
            result = self._embed_content(contents, task_type=task_type)
            if not result.embeddings:
                raise RuntimeError("Gemini returned no embeddings for a batch.")
            for e in result.embeddings:
                if e.values is None:
                    raise RuntimeError("Gemini returned an embedding with no values.")
                embeddings.append(e.values)

        logger.info(f"Created {len(embeddings)} vectors for {len(texts)} texts.")
        return embeddings
