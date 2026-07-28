"""Indexing step of the ingestion pipeline: store vectorized chunks in a Qdrant collection."""

import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.ingestion.models import ChunkedDocument
from src.ingestion.steps.embed import Embeddings


def _make_id(chunk: ChunkedDocument) -> str:
    """Get a unique identifier for a chunk based on its source, section, and text content.
    Used to ensure that the same chunk is not indexed multiple times in Qdrant.
    """
    source = chunk.metadata.get("source", "")
    section = chunk.metadata.get("Header 2") or chunk.metadata.get("Header 1") or ""
    raw = f"{source}::{section}::{chunk.text}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


class QdrantIndexer:
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        vector_size: int,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def index(
        self,
        chunks: list[ChunkedDocument],
        embeddings: Embeddings,
        batch_size: int = 100,
    ) -> None:
        points = [
            PointStruct(
                id=_make_id(chunk),
                vector=embedding,
                payload={"text": chunk.text, **chunk.metadata},
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        for i in range(0, len(points), batch_size):
            self.client.upsert(
                collection_name=self.collection_name,
                points=points[i : i + batch_size],
            )
