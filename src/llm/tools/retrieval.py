"""Retrieval tool: lets the chat agent search the indexed insurance conditions."""

import json
from functools import lru_cache
from typing import Literal

from google import genai
from langchain_core.tools import tool
from qdrant_client import QdrantClient

from src.config import get_settings
from src.ingestion.models import ANBIETER_OPTIONS, PRODUCT_CATEGORIES
from src.ingestion.steps.embed import Embedder
from src.llm.tools import register_tool
from src.retrieval.retriever import QdrantRetriever

AnbieterFilter = Literal[tuple(ANBIETER_OPTIONS)]  # ty: ignore[invalid-type-form]
KategorieFilter = Literal[tuple(PRODUCT_CATEGORIES)]  # ty: ignore[invalid-type-form]


@lru_cache
def _get_retriever() -> QdrantRetriever:
    """Cache the QdrantRetriever instance so that it is only created once per process, rather than on every tool invocation."""
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)
    return QdrantRetriever(
        embedder=Embedder(client=client, model_name=settings.gemini_embedding_model),
        client=QdrantClient(
            url=settings.qdrant_host, port=settings.qdrant_port, api_key=settings.qdrant_api_key
        ),
        collection_name=settings.qdrant_collection_name,
    )


@register_tool("search_versicherungsbedingungen")
@tool(
    name_or_callable="Versicherungsbedingungen-durchsuchen",
    description=(
        "Durchsucht die indizierten Versicherungsbedingungen nach zur Anfrage "
        "passenden Passagen. Nutze dieses Tool, um Fragen zu Leistungen, "
        "Ausschlüssen, Fristen oder Selbstbehalten zu beantworten.\n\n"
        "Optional kann die Suche über anbieter/kategorie/police auf ein "
        "bestimmtes Produkt eingegrenzt werden - nutze das, sobald der Nutzer "
        "(oder der bisherige Gesprächsverlauf) ein konkretes Produkt oder einen "
        "Anbieter nennt, statt die ungefilterte Suche über alle Bedingungswerke "
        "laufen zu lassen."
    ),
    response_format="content_and_artifact",
)
def search_versicherungsbedingungen(
    query: str,
    anbieter: AnbieterFilter | None = None,
    kategorie: KategorieFilter | None = None,
    police: str | None = None,
) -> tuple[str, list[dict]] | str:
    """Search the indexed insurance policy documents for passages relevant to the
    query, optionally narrowed down to a specific anbieter/kategorie/police.

    Returns (content, artifact): content is the JSON the model reads to answer
    (each hit's text plus its full metadata - source, page, header, anbieter,
    kategorie, etc. - so the model can cite it itself, no bespoke text
    formatting needed here); artifact is the same structured data, undecoded,
    for callers that want to render results themselves instead of parsing content."""
    try:
        points = _get_retriever().retrieve(
            query, anbieter=anbieter, kategorie=kategorie, police=police
        )
        results = [p.model_dump() for p in points]
        content = (
            json.dumps(results, ensure_ascii=False)
            if results
            else "Keine relevanten Passagen gefunden."
        )
        return content, results
    except Exception as e:  # noqa: BLE001 - a tool failure should read as a
        # normal (if unhelpful) tool result to the agent, not crash the turn.
        return f"Fehler bei der Suche: {e}", []


@register_tool("get_full_section")
@tool(
    name_or_callable="Vollstaendigen-Abschnitt-laden",
    description=(
        "Lädt den vollständigen, ungekürzten Text einer Klausel, falls eine "
        "Fundstelle aus 'Versicherungsbedingungen-durchsuchen' nur ein Fragment "
        "einer größeren Section war - erkennbar an 'parent_id' (zusammen mit "
        "'chunk_index'/'chunk_count') in der Metadata eines Treffers. Nutze "
        "dieses Tool nur, wenn das einzelne Fragment für eine vollständige, "
        "korrekte Antwort nicht ausreicht."
    ),
)
def get_full_section(parent_id: str) -> str:
    """Fetches and reassembles every piece of a capped section sharing parent_id."""
    try:
        text = _get_retriever().get_section(parent_id)
        if not text:
            return "Kein vollständiger Abschnitt zu dieser parent_id gefunden."
        return text
    except Exception as e:  # noqa: BLE001 - same rationale as above.
        return f"Fehler beim Laden des vollständigen Abschnitts: {e}"
