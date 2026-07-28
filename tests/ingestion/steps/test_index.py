from unittest.mock import MagicMock

from src.ingestion.models import ChunkedDocument
from src.ingestion.steps.index import QdrantIndexer, _make_id


def _chunk(**metadata) -> ChunkedDocument:
    return ChunkedDocument(text="Ist eine Selbstbeteiligung vereinbart...", metadata=metadata)


class TestMakeId:
    def test_deterministic_for_identical_input(self):
        chunk = _chunk(source="x.pdf", **{"Header 2": "Selbstbeteiligung"})
        assert _make_id(chunk) == _make_id(chunk)

    def test_different_text_gives_different_id(self):
        a = ChunkedDocument(text="text a", metadata={"source": "x.pdf"})
        b = ChunkedDocument(text="text b", metadata={"source": "x.pdf"})
        assert _make_id(a) != _make_id(b)

    def test_different_source_gives_different_id(self):
        a = ChunkedDocument(text="same text", metadata={"source": "a.pdf"})
        b = ChunkedDocument(text="same text", metadata={"source": "b.pdf"})
        assert _make_id(a) != _make_id(b)

    def test_prefers_header_2_over_header_1_for_section(self):
        with_h2 = _chunk(source="x.pdf", **{"Header 1": "Teil A", "Header 2": "1.1 Detail"})
        only_h1 = _chunk(source="x.pdf", **{"Header 1": "Teil A"})
        assert _make_id(with_h2) != _make_id(only_h1)

    def test_accepts_a_full_flat_metadata_dict_without_crashing(self):
        # Regression test: ChunkedDocument.metadata must stay a plain dict
        # (not the narrower DocumentMetadata), and _make_id must use
        # attribute access on ChunkedDocument, not dict subscripting -
        # both broke this in the past.
        chunk = _chunk(
            source="x.pdf",
            **{"Header 1": "21. Beitragsregulierung"},
            anbieter="R+V",
            datum="2021-07",
            police=["Hausratversicherung 500"],
            kategorie="Haus + Wohnen",
            product_title="Test Product",
            page_start=1,
            page_end=3,
            parent_id="abc123",
            chunk_index=0,
            chunk_count=2,
        )
        assert isinstance(_make_id(chunk), str)


class TestQdrantIndexer:
    def test_creates_collection_if_missing(self):
        client = MagicMock()
        client.collection_exists.return_value = False

        QdrantIndexer(client, collection_name="col", vector_size=8)

        client.create_collection.assert_called_once()
        assert client.create_collection.call_args.kwargs["collection_name"] == "col"

    def test_skips_collection_creation_if_it_exists(self):
        client = MagicMock()
        client.collection_exists.return_value = True

        QdrantIndexer(client, collection_name="col", vector_size=8)

        client.create_collection.assert_not_called()

    def test_index_builds_points_with_text_and_metadata_in_payload(self):
        client = MagicMock()
        client.collection_exists.return_value = True
        indexer = QdrantIndexer(client, collection_name="col", vector_size=3)

        chunk = ChunkedDocument(text="hello", metadata={"source": "x.pdf", "anbieter": "R+V"})
        indexer.index([chunk], [[0.1, 0.2, 0.3]])

        client.upsert.assert_called_once()
        points = client.upsert.call_args.kwargs["points"]
        assert len(points) == 1
        assert points[0].vector == [0.1, 0.2, 0.3]
        assert points[0].payload == {"text": "hello", "source": "x.pdf", "anbieter": "R+V"}
