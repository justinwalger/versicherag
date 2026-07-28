import pytest
from pydantic import ValidationError

from src.ingestion.models import (
    ANBIETER_OPTIONS,
    NOT_INSURANCE_MARKER,
    ChunkedDocument,
    DocumentMetadata,
    ParsedDocument,
)


class TestAnbieterEnforcement:
    @pytest.mark.parametrize("anbieter", ANBIETER_OPTIONS)
    def test_accepts_every_declared_option(self, anbieter):
        metadata = DocumentMetadata(anbieter=anbieter, datum="2021-07", police=[], kategorie="x")
        assert metadata.anbieter == anbieter

    def test_accepts_not_insurance_marker(self):
        metadata = DocumentMetadata(
            anbieter=NOT_INSURANCE_MARKER, datum=NOT_INSURANCE_MARKER, police=[], kategorie="x"
        )
        assert metadata.anbieter == NOT_INSURANCE_MARKER

    def test_rejects_unnormalized_variant(self):

        with pytest.raises(ValidationError):
            DocumentMetadata(anbieter="RV", datum="2021-07", police=[], kategorie="x")

    def test_rejects_arbitrary_string(self):
        with pytest.raises(ValidationError):
            DocumentMetadata(anbieter="Allianz", datum="2021-07", police=[], kategorie="x")

    def test_parsed_document_enforces_the_same_values(self):
        with pytest.raises(ValidationError):
            ParsedDocument(content="x", anbieter="RV", datum="2021-07", police=[], kategorie="x")


class TestChunkedDocument:
    def test_metadata_accepts_a_full_flat_dict(self):
        # Regression test: metadata must stay a plain dict, not the narrower
        # DocumentMetadata - chunk_step adds several fields (Header path,
        # source, page range, parent_id, ...) beyond DocumentMetadata's four,
        # and a stricter type would silently drop them.
        chunk = ChunkedDocument(
            text="Ist eine Selbstbeteiligung vereinbart...",
            metadata={
                "Header 2": "Selbstbeteiligung",
                "source": "x.pdf",
                "anbieter": "R+V",
                "datum": "2021-07",
                "police": ["Hausratversicherung 500"],
                "kategorie": "Haus + Wohnen",
                "page_start": 1,
                "page_end": 3,
                "parent_id": "abc123",
                "chunk_index": 0,
                "chunk_count": 2,
            },
        )
        assert chunk.metadata["source"] == "x.pdf"
        assert chunk.metadata["page_start"] == 1
        assert chunk.metadata["chunk_index"] == 0
