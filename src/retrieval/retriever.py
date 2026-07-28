"""Retriver to retrieve relevant chunks from the Qdrant vector database based on a query."""

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, ScoredPoint

from src.ingestion.steps.embed import Embedder
from src.retrieval.models import QdrantOutput

METADATA_KEYS = (
    "Header 3",
    "Header 2",
    "Header 1",
    "source",
    "product_title",
    "anbieter",
    "datum",
    "police",
    "kategorie",
    "page_start",
    "page_end",
    "parent_id",
    "chunk_index",
    "chunk_count",
)


def _build_filter(**filters: str | None) -> Filter | None:
    """Builds a Qdrant filter from the given field->value pairs. `police` is a
    list in the payload - a MatchValue filter on it matches as soon as the
    value is contained anywhere in the list."""
    conditions = [
        FieldCondition(key=key, match=MatchValue(value=value))
        for key, value in filters.items()
        if value
    ]
    return Filter(must=conditions) if conditions else None


def format_context(points: list[ScoredPoint]) -> list[QdrantOutput]:
    """Formats retrieved chunks as context blocks with a §-source reference."""
    outputs = []
    for p in points:
        payload = p.payload or {}

        metadata = {key: payload[key] for key in METADATA_KEYS if payload.get(key) is not None}
        outputs.append(QdrantOutput(text=payload.get("text", ""), metadata=metadata))
    return outputs


class QdrantRetriever:
    def __init__(
        self,
        embedder: Embedder,
        client: QdrantClient,
        collection_name: str = "versicherag_collection",
    ) -> None:
        self.embedder = embedder
        self.client = client
        self.collection_name = collection_name

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        anbieter: str | None = None,
        kategorie: str | None = None,
        police: str | None = None,
    ) -> list[QdrantOutput]:
        """Retrieves the most relevant chunks from the Qdrant vector database based on
        the query, optionally narrowed down to a specific anbieter/kategorie/police."""
        if not query or not query.strip():
            logger.warning("Received an empty query; skipping retrieval.")
            return []

        query_vector = self.embedder.embed(query)
        query_filter = _build_filter(anbieter=anbieter, kategorie=kategorie, police=police)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
        )
        logger.info(f"Retrieved {len(results.points)} relevant chunks for query: {query}")
        return [QdrantOutput.model_validate(item) for item in format_context(results.points)]

    def get_section(self, parent_id: str) -> str:
        """Loads every piece of a capped section (same parent_id, see
        PDFChunker.cap) and reassembles them in their original order into the
        full clause. No vector query needed - a pure metadata filter, since
        parent_id already uniquely links the pieces."""
        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="parent_id", match=MatchValue(value=parent_id))]
            ),
            limit=200,
            with_payload=True,
        )
        if not points:
            logger.warning(f"No pieces found for parent_id={parent_id!r}.")
            return ""

        points.sort(key=lambda p: (p.payload or {}).get("chunk_index", 0))
        return "\n\n".join((p.payload or {}).get("text", "") for p in points)
