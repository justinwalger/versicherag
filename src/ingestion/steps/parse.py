"""Parsing step of the ingestion pipeline: convert PDFs to structured products."""

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from docling.document_converter import DocumentConverter
from loguru import logger

from src.ingestion.models import ParsedProduct
from src.ingestion.steps.split import split_into_products

_worker_parser: "PDFParser | None" = None


class PDFParser:
    """Parser for PDFs that uses Docling to convert the PDF into a structured document and then splits it into individual products."""

    def __init__(self) -> None:
        self._converter = DocumentConverter()

    def parse(self, file: str) -> list[ParsedProduct]:
        doc = self._converter.convert(file).document
        products = split_into_products(doc, filename=Path(file).name)
        logger.info(f"Parsed {file} -> {len(products)} product(s)")
        [logger.debug(f"Parsed products: {product.product_title}") for product in products]
        return products


def _init_worker() -> None:
    global _worker_parser
    _worker_parser = PDFParser()


def _parse_in_worker(file: str) -> list[ParsedProduct]:
    if _worker_parser is None:
        raise RuntimeError("Worker parser was not initialized.")
    return _worker_parser.parse(file)


def parse_many(files: list[str], max_workers: int = 4) -> list[ParsedProduct]:
    """Parse multiple PDF files in parallel using a process pool. Each file is parsed into one or more products, which are returned as a flat list."""
    with ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker) as pool:
        results = pool.map(_parse_in_worker, files)
    return [product for file_products in results for product in file_products]
