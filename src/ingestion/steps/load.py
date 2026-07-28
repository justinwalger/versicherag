"""Website loader: Retrieve PDF links from a list of source URLs and download them to a local folder."""

from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from loguru import logger


class WebsiteLoader:
    def __init__(self, sources: list[str], timeout: int = 30) -> None:
        self.sources = sources
        self.timeout = timeout

    def retrieve_links(self) -> list[str]:
        """Check each source URL: if it's a direct PDF link, return it; if it's a webpage, scrape it for PDF links."""
        links: list[str] = []
        for source in self.sources:
            if source.lower().endswith("pdf"):
                links.append(source)
            else:
                links += self._scrape_pdf_links(source)
        return links

    def _scrape_pdf_links(self, url: str) -> list[str]:
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        pdf_links = [
            urljoin(url, href)
            for a in soup.find_all("a")
            if isinstance(href := a.get("href"), str) and href.lower().endswith("pdf")
        ]
        logger.info(f"Found {len(pdf_links)} PDF links on {url}")
        return pdf_links

    def download_pdfs(self, links: list[str], download_folder: Path) -> list[Path]:
        download_folder.mkdir(parents=True, exist_ok=True)
        saved: list[Path] = []

        for url in links:
            target = download_folder / url.split("/")[-1]
            # TODO: only skip if the file is identical (hash check), not just if it exists
            if target.exists():
                logger.info(f"Skipped {target.name}: already exists")
                saved.append(target)
                continue

            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
            except requests.RequestException as exc:
                logger.warning(f"Skipped {url}: {exc}")
                continue

            target.write_bytes(response.content)
            saved.append(target)
            logger.info(f"Downloaded {target.name}")

        return saved
