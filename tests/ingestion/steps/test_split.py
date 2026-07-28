from src.ingestion.steps.split import _extract_code_letters, _find_boundaries, _Header


class TestExtractCodeLetters:
    def test_code_with_version(self):
        assert _extract_code_letters("Haftpflichtbedingungen classic (HPB 07/26)") == "HPB"

    def test_bare_code_without_version(self):
        assert _extract_code_letters("Haftpflichtbedingungen classic (HPB)") == "HPB"

    def test_no_code_present(self):
        assert _extract_code_letters("Merkblatt zur Datenverarbeitung") is None

    def test_non_breaking_space_normalized(self):
        # Docling sometimes emits a non-breaking space between code and version.
        assert _extract_code_letters("Bedingungen (HPB\xa007/26)") == "HPB"


class TestFindBoundaries:
    def test_single_product_no_duplication(self):
        headers = [
            _Header(page=1, text="Allgemeine Versicherungsbedingungen (HPB 07/26)"),
            _Header(page=2, text="1. Vertragsgrundlagen"),
            _Header(page=2, text="2. Vertragsdauer"),
        ]
        assert _find_boundaries(headers) == [0]

    def test_toc_duplicate_keeps_later_occurrence(self):
        # Real PDFs restate a product's title banner right after its own
        # Inhaltsverzeichnis - the later occurrence is where content starts.
        headers = [
            _Header(page=2, text="Allgemeine Versicherungsbedingungen (HPB 07/26)"),
            _Header(page=2, text="Inhaltsverzeichnis"),
            _Header(page=3, text="Allgemeine Versicherungsbedingungen (HPB 07/26)"),
            _Header(page=3, text="1. Vertragsgrundlagen"),
        ]
        assert _find_boundaries(headers) == [2]

    def test_same_code_resurfacing_under_different_wording_is_dropped(self):
        # A part-divider mid-product can restate the bare code without the
        # date/version - it must not be treated as a second product boundary.
        headers = [
            _Header(page=9, text="Haftpflichtbedingungen classic (HPB 07/26)"),
            _Header(page=10, text="1. Wegfall des versicherten Interesses"),
            _Header(page=24, text="Haftpflichtbedingungen classic (HPB) Ausgabe Juli 2026"),
            _Header(page=25, text="2. Kündigung nach Versicherungsfall"),
        ]
        assert _find_boundaries(headers) == [0]

    def test_numbered_subclause_is_not_a_boundary(self):
        # Contains "Bedingungen" but starts with a clause number - not a new
        # product's title banner.
        headers = [
            _Header(page=1, text="Allgemeine Versicherungsbedingungen (HPB 07/26)"),
            _Header(page=5, text="5.2 Besondere Bedingungen für Mitversicherte"),
        ]
        assert _find_boundaries(headers) == [0]

    def test_two_distinct_products(self):
        headers = [
            _Header(page=1, text="Allgemeine Versicherungsbedingungen (HPB 07/26)"),
            _Header(page=10, text="1. Wegfall des versicherten Interesses"),
            _Header(page=20, text="Hausratversicherungsbedingungen (HRB 07/2026)"),
            _Header(page=21, text="1. Was ist versichert"),
        ]
        assert _find_boundaries(headers) == [0, 2]

    def test_no_candidates_returns_empty(self):
        headers = [_Header(page=1, text="1. Vertragsgrundlagen")]
        assert _find_boundaries(headers) == []
