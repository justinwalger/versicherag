from src.ui.components.chat import _citation_key, _format_citation


class TestFormatCitation:
    def test_document_section_paragraph(self):
        metadata = {
            "source": "x.pdf",
            "Header 1": "Haftpflichtversicherungsbedingungen classic (HPB 07/26)",
            "Header 2": "21. Beitragsregulierung",
        }
        assert _format_citation(metadata) == (
            "x.pdf › Haftpflichtversicherungsbedingungen classic (HPB 07/26) › "
            "21. Beitragsregulierung"
        )

    def test_shows_product_title_with_the_actual_filename(self):
        metadata = {"source": "x.pdf", "product_title": "R+V Hausratversicherung 500"}
        assert _format_citation(metadata).startswith("R+V Hausratversicherung 500 (x.pdf)")

    def test_falls_back_to_source_alone_without_product_title(self):
        metadata = {"source": "x.pdf"}
        assert _format_citation(metadata) == "x.pdf"

    def test_prefers_header_3_over_header_2_as_paragraph(self):
        metadata = {
            "source": "x.pdf",
            "Header 1": "Teil A",
            "Header 2": "1.1 Umfang",
            "Header 3": "1.1.2 Detail",
        }
        assert _format_citation(metadata).endswith("1.1.2 Detail")

    def test_does_not_repeat_section_as_paragraph(self):
        # Only Header 1 present - it must not appear twice (once as section,
        # once as a falsely-selected paragraph).
        metadata = {"source": "x.pdf", "Header 1": "Merkblatt zur Datenverarbeitung"}
        assert _format_citation(metadata) == "x.pdf › Merkblatt zur Datenverarbeitung"

    def test_includes_page_range_when_present(self):
        metadata = {"source": "x.pdf", "page_start": 9, "page_end": 9}
        assert _format_citation(metadata) == "x.pdf (Seite 9)"

        metadata = {"source": "x.pdf", "page_start": 9, "page_end": 12}
        assert _format_citation(metadata) == "x.pdf (Seite 9-12)"

    def test_falls_back_to_unknown_document_without_source_or_title(self):
        assert _format_citation({}) == "Unbekanntes Dokument"


class TestCitationKey:
    def test_same_metadata_gives_same_key(self):
        a = {"source": "x.pdf", "Header 1": "A", "Header 2": "B", "Header 3": None}
        b = {"source": "x.pdf", "Header 1": "A", "Header 2": "B", "Header 3": None}
        assert _citation_key(a) == _citation_key(b)

    def test_different_header_gives_different_key(self):
        a = {"source": "x.pdf", "Header 1": "A"}
        b = {"source": "x.pdf", "Header 1": "B"}
        assert _citation_key(a) != _citation_key(b)
