"""Cleaning step of the ingestion pipeline: remove unwanted characters and whitespace from a document."""

import re

from langchain_core.documents import Document


class PDFCleaner:
    def clean(self, document: Document) -> Document:

        text = document.page_content
        text = text.replace("<!-- image -->", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        return Document(page_content=text, metadata=document.metadata)
