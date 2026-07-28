"""Splits a parsed PDF's DoclingDocument into its individual bundled products.

Some R+V PDFs bundle multiple, independently-numbered products into one file
(e.g. a 327-page "PrivatPolice" Verbraucherinformation covering ~13 separate
AVBs). Docling's own heading levels don't reflect this - every header comes
back at the same level regardless of true depth - so product boundaries are
detected from the title text itself (AVB code patterns, canonical part
names) rather than from any parser's heading hierarchy.

Each product's title banner shows up twice in the raw header list before its
real content starts: once right before its own "Inhaltsverzeichnis", and
again immediately after it. The same bare product code can also resurface
later under different wording (e.g. a part-divider mid-product). Both
patterns were verified against real multi-product PDFs (327 and 581 pages)
before simplifying this file - see _find_boundaries.
"""

import re
from collections import defaultdict
from typing import NamedTuple

from docling_core.types.doc import DocItemLabel

from src.ingestion.models import ParsedProduct

TITLE_RE = re.compile(
    r"\([A-ZÄÖÜ]{2,8}[\s\-]?[A-Z]?\s?\d{2}[./]\d{2,4}\)"
    r"|bedingungen\b"
    r"|^merkblatt\b"
    r"|^verbraucherinformationen?\b"
    r"|^widerrufsbelehrung\b",
    re.IGNORECASE,
)
NUM_START_RE = re.compile(r"^\d+(\.\d+)*[.\s]")
CODE_RE = re.compile(r"\(([A-ZÄÖÜ]{2,8}[\s\-]?[A-Z]?\s?\d{2}[./]\d{2,4})\)")
CODE_LETTERS_RE = re.compile(r"\(([A-ZÄÖÜ]{2,8}(?:[\s\-][A-Z])?)(?:\s?[\d./]+)?\)")


class _Header(NamedTuple):
    """A section header with a resolved page number - headers without any
    provenance (page location) are filtered out where this is built, since
    they can't participate in page-range boundary detection anyway."""

    page: int
    text: str


def _extract_code_letters(title: str) -> str | None:
    """Bare product code without version, e.g. "HPB" from "(HPB 07/26)" or "(HPB)".

    Whitespace is normalized because Docling sometimes emits a non-breaking
    space between code and version instead of a regular one, which would
    otherwise make two occurrences of the same code compare unequal."""
    match = CODE_LETTERS_RE.search(title)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _find_boundaries(headers: list[_Header]) -> list[int]:
    """Finds the header index where each bundled product's real content starts."""
    candidates = [
        i
        for i, h in enumerate(headers)
        if TITLE_RE.search(h.text) and not NUM_START_RE.match(h.text)
    ]

    # Same exact banner text repeats around its own ToC (title -> ToC ->
    # title again -> content) - the later occurrence is always where the
    # real content starts.
    by_text: dict[str, list[int]] = defaultdict(list)
    for i in candidates:
        by_text[headers[i].text.strip()].append(i)
    boundaries = sorted(idxs[-1] for idxs in by_text.values())

    # Same bare product code can resurface later under different wording -
    # keep only the first (real) boundary per code, drop the rest so one
    # product doesn't get fragmented into two segments.
    seen_codes: set[str] = set()
    final = []
    for i in boundaries:
        code = _extract_code_letters(headers[i].text)
        if code and code in seen_codes:
            continue
        final.append(i)
        if code:
            seen_codes.add(code)

    return final


def split_into_products(doc, filename: str) -> list[ParsedProduct]:
    """Segments a parsed PDF into its bundled products, one ParsedProduct per
    detected boundary. Falls back to a single product covering the whole
    document when no boundary is detected."""
    headers = [
        _Header(page=item.prov[0].page_no, text=item.text)
        for item, _ in doc.iterate_items()
        if getattr(item, "label", None) == DocItemLabel.SECTION_HEADER and item.prov
    ]

    last_page = max(doc.pages.keys())
    boundary_idxs = _find_boundaries(headers)
    starts = (
        boundary_idxs
        if boundary_idxs and headers[boundary_idxs[0]].page == 1
        else [0] + boundary_idxs
    )

    products = []
    for seg_i, header_idx in enumerate(starts):
        title = headers[header_idx].text if header_idx < len(headers) else filename
        page_start = headers[header_idx].page if header_idx < len(headers) else 1
        page_end = headers[starts[seg_i + 1]].page - 1 if seg_i + 1 < len(starts) else last_page
        page_end = max(page_end, page_start)

        markdown = "\n\n".join(
            doc.export_to_markdown(page_no=p) for p in range(page_start, page_end + 1)
        )
        products.append(
            ParsedProduct(
                filename=filename,
                product_title=title,
                page_start=page_start,
                page_end=page_end,
                markdown=markdown,
            )
        )
    return products
