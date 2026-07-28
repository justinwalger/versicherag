from langchain_core.documents import Document

from src.ingestion.steps.chunk import PDFChunker, header_path


class TestHeaderPath:
    def test_joins_header_levels_in_order(self):
        doc = Document(page_content="x", metadata={"Header 1": "A", "Header 2": "B"})
        assert header_path(doc) == "A > B"

    def test_no_headers_returns_empty_string(self):
        doc = Document(page_content="x", metadata={"source": "x.pdf"})
        assert header_path(doc) == ""


class TestChunk:
    def test_splits_on_header_hierarchy_and_attaches_source(self):
        markdown = "# Titel\n\ntext a\n\n## Abschnitt\n\ntext b\n"
        chunks = PDFChunker().chunk(markdown, source="x.pdf")
        assert len(chunks) == 2
        assert all(c.metadata["source"] == "x.pdf" for c in chunks)
        assert chunks[0].metadata["Header 1"] == "Titel"
        assert chunks[1].metadata["Header 2"] == "Abschnitt"


class TestCap:
    def test_document_within_limit_is_returned_unchanged(self):
        chunker = PDFChunker(max_chars=1000)
        doc = Document(page_content="short text", metadata={"source": "x.pdf"})
        pieces = chunker.cap(doc)
        assert pieces == [doc]
        assert "parent_id" not in pieces[0].metadata

    def test_oversized_document_is_split_with_linking_metadata(self):
        chunker = PDFChunker(max_chars=50, overlap=10)
        doc = Document(
            page_content="x" * 200,
            metadata={"source": "x.pdf", "Header 1": "21. Beitragsregulierung"},
        )
        pieces = chunker.cap(doc)
        assert len(pieces) > 1
        parent_ids = {p.metadata["parent_id"] for p in pieces}
        assert len(parent_ids) == 1
        assert [p.metadata["chunk_index"] for p in pieces] == list(range(len(pieces)))
        assert all(p.metadata["chunk_count"] == len(pieces) for p in pieces)

    def test_same_header_in_different_products_gets_different_parent_id(self):

        chunker = PDFChunker(max_chars=50, overlap=10)
        base_metadata = {"source": "x.pdf", "Header 1": "21. Beitragsregulierung"}

        doc_a = Document(
            page_content="a" * 200,
            metadata={**base_metadata},
        )
        doc_b = Document(
            page_content="b" * 200,
            metadata={**base_metadata},
        )

        parent_id_a = chunker.cap(doc_a)[0].metadata["parent_id"]
        parent_id_b = chunker.cap(doc_b)[0].metadata["parent_id"]
        assert parent_id_a != parent_id_b


class TestEnrich:
    def test_prefixes_header_path_to_text(self):
        doc = Document(page_content="Inhalt", metadata={"Header 1": "Titel"})
        enriched = PDFChunker().enrich(doc)
        assert enriched.page_content == "Titel\n\nInhalt"

    def test_no_header_leaves_text_unchanged(self):
        doc = Document(page_content="Inhalt", metadata={})
        enriched = PDFChunker().enrich(doc)
        assert enriched.page_content == "Inhalt"
