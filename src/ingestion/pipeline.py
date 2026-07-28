"""ZEN ML pipeline orchestration"""

from pathlib import Path

from google import genai
from loguru import logger
from qdrant_client import QdrantClient
from zenml import pipeline, step

from src.config import get_settings
from src.ingestion.models import (
    NOT_INSURANCE_MARKER,
    ChunkedDocument,
    EnrichedFile,
    LoadedFile,
    ParsedProduct,
)
from src.ingestion.steps.chunk import MIN_CHUNK_CHARS, PDFChunker, header_path
from src.ingestion.steps.clean import PDFCleaner
from src.ingestion.steps.embed import Embedder, Embeddings
from src.ingestion.steps.enricher import Enricher
from src.ingestion.steps.index import QdrantIndexer
from src.ingestion.steps.load import WebsiteLoader
from src.ingestion.steps.parse import parse_many

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@step
def load_step() -> list[LoadedFile]:
    """First step of the ingestion pipeline: download PDFs from the configured source URLs and return their filename and paths."""
    settings = get_settings()
    loader = WebsiteLoader(settings.source_urls)
    links = loader.retrieve_links()
    paths = loader.download_pdfs(links, DATA_DIR)

    return [LoadedFile(filename=path.name, path=path) for path in paths]


@step
def parse_step(pdf_files: list[LoadedFile]) -> list[ParsedProduct]:
    """Second step of the ingestion pipeline: parse each PDF and split it into its individual bundled products
    (a single PDF may contain multiple independently numbered policy documents)."""
    return parse_many([str(f.path) for f in pdf_files])


@step
def enrich_step(parsed_products: list[ParsedProduct]) -> list[EnrichedFile]:
    """Third step of the ingestion pipeline: extract document metadata (provider, date, policy, category) for each
    product and skip products that are not insurance conditions."""
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)
    enricher = Enricher(llm=client, model_name=settings.gemini_metadata_model)

    enriched_files = []
    for p in parsed_products:
        document = enricher.enrich(p.markdown)
        if document.anbieter == NOT_INSURANCE_MARKER:
            logger.info(f"skipping {p.filename} ({p.product_title}): not insurance conditions.")
            continue
        enriched_files.append(
            EnrichedFile(
                filename=p.filename,
                product_title=p.product_title,
                page_start=p.page_start,
                page_end=p.page_end,
                document=document,
            )
        )
    return enriched_files


@step
def chunk_step(enriched_docs: list[EnrichedFile]) -> list[ChunkedDocument]:
    """Fourth step of the ingestion pipeline: split each enriched product into chunks, clean them, and return a list of dicts containing the chunk text and metadata."""
    chunker = PDFChunker()
    cleaner = PDFCleaner()

    chunks: list[ChunkedDocument] = []
    for f in enriched_docs:
        for chunk in chunker.chunk(f.document.content, source=f.filename):
            chunk.metadata["anbieter"] = f.document.anbieter
            chunk.metadata["datum"] = f.document.datum
            chunk.metadata["police"] = f.document.police
            chunk.metadata["kategorie"] = f.document.kategorie
            chunk.metadata["product_title"] = f.product_title
            chunk.metadata["page_start"] = f.page_start
            chunk.metadata["page_end"] = f.page_end
            cleaned = cleaner.clean(chunk)
            if len(cleaned.page_content) < MIN_CHUNK_CHARS:
                # e.g. a section that was only an image (stripped to nothing by
                # PDFCleaner) or a leftover page-number/"Seite X" artifact from
                # parsing - too short to add retrieval value, and an empty
                # string would be rejected by the embedding API anyway.
                logger.info(
                    f"skipping short chunk {f.filename} "
                    f"({header_path(cleaned) or 'no Header'}): {cleaned.page_content!r}"
                )
                continue
            for piece in chunker.cap(cleaned):
                enriched = chunker.enrich(piece)
                chunks.append(
                    ChunkedDocument(text=enriched.page_content, metadata=enriched.metadata)
                )
    return chunks


@step
def embed_step(chunks: list[ChunkedDocument]) -> Embeddings:
    """Fifth step of the ingestion pipeline: create embeddings for all chunks."""
    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)
    embedder = Embedder(client=client, model_name=settings.gemini_embedding_model)
    texts = [chunk.text for chunk in chunks]
    return embedder.embed_batch(texts)


@step
def index_step(chunks: list[ChunkedDocument], embeddings: Embeddings) -> None:
    """Sixth step of the ingestion pipeline: index chunks and their corresponding embeddings in Qdrant."""
    settings = get_settings()
    client = QdrantClient(
        url=settings.qdrant_host, api_key=settings.qdrant_api_key, port=settings.qdrant_port
    )
    indexer = QdrantIndexer(
        client,
        collection_name=settings.qdrant_collection_name,
        vector_size=settings.qdrant_vector_size,
    )
    indexer.index(chunks, embeddings)


@pipeline
def ingestion_pipeline() -> None:
    """RAG-Ingestion-Pipeline: load, parse, enrich, chunk, embed, and index insurance product PDFs."""
    pdf_paths = load_step()
    markdown_docs = parse_step(pdf_paths)
    enriched_docs = enrich_step(markdown_docs)
    chunks = chunk_step(enriched_docs)
    embeddings = embed_step(chunks)
    index_step(chunks, embeddings)


if __name__ == "__main__":
    ingestion_pipeline()
