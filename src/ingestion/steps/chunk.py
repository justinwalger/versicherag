"""Chunking step of the ingestion pipeline: split a document into smaller chunks, each with its own header hierarchy and text."""

import hashlib

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

SPLIT_HEADERS = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

MAX_CHARS = 1500
OVERLAP = 150
MIN_CHUNK_CHARS = 20


def header_path(document: Document) -> str:
    headers = [v for k, v in document.metadata.items() if k.startswith("Header")]
    return " > ".join(headers)


class PDFChunker:
    def __init__(self, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> None:
        self._splitter = MarkdownHeaderTextSplitter(SPLIT_HEADERS)
        self._capper = RecursiveCharacterTextSplitter(chunk_size=max_chars, chunk_overlap=overlap)
        self._max_chars = max_chars

    def chunk(self, markdown: str, source: str | None = None) -> list[Document]:
        """Splits a markdown document into chunks based on header hierarchy. Each chunk retains its header path in the metadata."""

        chunks = self._splitter.split_text(markdown)
        if source is not None:
            for chunk in chunks:
                chunk.metadata["source"] = source
        return chunks

    def cap(self, document: Document) -> list[Document]:
        """Splits a document into smaller pieces if it exceeds the maximum character limit, while preserving the header hierarchy and assigning a unique parent ID to each piece.

        Adds metadata fields:
        - parent_id: a unique identifier for the original document, shared by all pieces derived from it.
        - chunk_index: the index of the piece in the sequence of pieces derived from the original document.
        - chunk_count: the total number of pieces derived from the original document.
        """

        # skip splitting if the document is already within the character limit
        if len(document.page_content) <= self._max_chars:
            return [document]

        # Scoped by product, not just by source file: a single PDF can bundle
        # several products (see ParsedProduct) whose AVBs reuse identical,
        # boilerplate clause numbering/titles - hashing on source::header_path
        # alone would collide two unrelated products' "same-named" clauses
        # onto one parent_id.
        product = document.metadata.get("product_title", "")
        parent_id = hashlib.md5(
            f"{document.metadata.get('source', '')}::{product}::{header_path(document)}".encode()
        ).hexdigest()[:12]

        pieces = self._capper.split_documents([document])
        for i, piece in enumerate(pieces):
            piece.metadata["parent_id"] = parent_id
            piece.metadata["chunk_index"] = i
            piece.metadata["chunk_count"] = len(pieces)
        return pieces

    def enrich(self, document: Document) -> Document:
        """Adds header path as a prefix to the document's text, if available, and returns a new Document with the enriched text and original metadata."""

        header = header_path(document)
        if header:
            enriched_text = f"{header}\n\n{document.page_content}"
        else:
            enriched_text = document.page_content
        return Document(page_content=enriched_text, metadata=document.metadata)
