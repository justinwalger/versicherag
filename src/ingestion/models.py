from pathlib import Path
from typing import Literal

from pydantic import BaseModel

NOT_INSURANCE_MARKER = "NICHT VORHANDEN"

# Fixed list instead of free-text extraction, since the LLM otherwise names the
# same company inconsistently (e.g. "RV" vs. "R+V" side by side in the index -
# see notebooks/metadata_analysis.ipynb).
ANBIETER_OPTIONS = [
    "R+V",
    "VTV",
    "KRAVAG",
    "Sonstige",
]

# Categories as in the Privatkunden overview at
# ruv.de/service/weitere-services/versicherungsbedingungen#privatkunden.
PRODUCT_CATEGORIES = [
    "Altersvorsorge & Lebensversicherung",
    "Berufsunfähigkeitsversicherung",
    "Haus + Wohnen",
    "Kfz-Versicherung",
    "Krankenversicherung",
    "Rechtsschutz-, Haftpflicht- und Hausratversicherung",
    "Tierversicherung",
    "Unfallversicherung",
    "Versicherungspaket für den Alltag",
    "Sonstige",
]

# Built from the lists above (single source of truth) rather than a hardcoded
# Literal[...] - static checkers can't verify a Literal derived from a runtime
# list, but the members are fixed at import time and pydantic enforces them at
# runtime regardless, which is what actually matters here.
AnbieterValue = Literal[tuple(ANBIETER_OPTIONS) + (NOT_INSURANCE_MARKER,)]  # ty: ignore[invalid-type-form]


class LoadedFile(BaseModel):
    """A downloaded PDF, before parsing."""

    filename: str
    path: Path


class ParsedProduct(BaseModel):
    """One bundled product within a PDF, before enrichment.

    A single PDF can bundle multiple, independently-numbered products end to
    end (e.g. a 327-page "PrivatPolice" Verbraucherinformation covering ~13
    separate AVBs), so parsing produces one ParsedProduct per detected
    product boundary, not one per PDF."""

    filename: str
    product_title: str
    page_start: int
    page_end: int
    markdown: str


class DocumentMetadata(BaseModel):
    """LLM extracted metadata for a parsed product, before chunking."""

    anbieter: AnbieterValue
    datum: str
    police: list[str]
    kategorie: str


class ChunkedDocument(BaseModel):
    """Represents a chunked document with its content and metadata.

    metadata is a plain dict, not DocumentMetadata: chunk_step (pipeline.py)
    starts from DocumentMetadata's four enrichment fields but adds several
    more during chunking (Header path, source, page range, product_title/
    code, parent_id/chunk_index/chunk_count) before this is constructed -
    DocumentMetadata's fixed schema would silently drop all of them."""

    text: str
    metadata: dict


class ParsedDocument(BaseModel):
    """Represents a parsed document with its content and metadata."""

    content: str
    anbieter: AnbieterValue
    datum: str
    police: list[str]
    kategorie: str


class EnrichedFile(BaseModel):
    """A parsed product with its extracted metadata, before chunking."""

    filename: str
    product_title: str
    page_start: int
    page_end: int
    document: ParsedDocument
