from qdrant_client.models import FieldCondition, MatchValue, ScoredPoint

from src.retrieval.retriever import _build_filter, format_context


def _point(payload: dict | None) -> ScoredPoint:
    return ScoredPoint(id=1, version=1, score=0.9, payload=payload)


class TestBuildFilter:
    def test_no_filters_returns_none(self):
        assert _build_filter(anbieter=None, kategorie=None, police=None) is None

    def test_empty_string_is_treated_as_no_filter(self):
        assert _build_filter(anbieter="", kategorie=None, police=None) is None

    def test_single_filter(self):
        result = _build_filter(anbieter="R+V", kategorie=None, police=None)
        assert result is not None
        assert result.must == [FieldCondition(key="anbieter", match=MatchValue(value="R+V"))]

    def test_multiple_filters_combine_with_must(self):
        result = _build_filter(anbieter="R+V", kategorie="Haus + Wohnen", police=None)
        assert result is not None
        assert isinstance(result.must, list)
        assert len(result.must) == 2


class TestFormatContext:
    def test_extracts_only_known_metadata_keys(self):
        point = _point(
            {
                "text": "Ist eine Selbstbeteiligung vereinbart...",
                "source": "x.pdf",
                "Header 2": "Selbstbeteiligung",
                "anbieter": "R+V",
                "unrelated_field": "should not appear",
            }
        )
        [output] = format_context([point])
        assert output.text == "Ist eine Selbstbeteiligung vereinbart..."
        assert output.metadata == {
            "source": "x.pdf",
            "Header 2": "Selbstbeteiligung",
            "anbieter": "R+V",
        }

    def test_chunk_index_zero_is_preserved(self):
        # Regression test: chunk_index=0 (the first piece of a capped
        # section) is a meaningful value - a truthy check would silently
        # drop it since 0 is falsy in Python.
        point = _point({"text": "x", "chunk_index": 0, "chunk_count": 2})
        [output] = format_context([point])
        assert output.metadata is not None
        assert output.metadata["chunk_index"] == 0

    def test_missing_payload_does_not_crash(self):
        point = _point(None)
        [output] = format_context([point])
        assert output.text == ""
        assert output.metadata == {}

    def test_missing_text_defaults_to_empty_string(self):
        point = _point({"source": "x.pdf"})
        [output] = format_context([point])
        assert output.text == ""
