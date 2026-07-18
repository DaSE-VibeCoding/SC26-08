"""arXiv diffusion paper scraper (migrated from the original scraper.py)."""
import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import List

from config import REQUEST_DELAY
from .base import ScraperBase, tag_by_keywords

logger = logging.getLogger(__name__)

ARXIV_BASE_URL = "https://export.arxiv.org/api/query"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

DEFAULT_QUERIES = [
    "diffusion",
    "diffusion model",
    "denoising diffusion",
    "stable diffusion",
    "latent diffusion",
    "score-based generative",
]


class ArxivScraper(ScraperBase):
    name = "arXiv"
    source = "arxiv"

    def __init__(self, max_results: int = 100, queries: List[str] | None = None):
        super().__init__(max_results=max_results)
        self.queries = queries or DEFAULT_QUERIES

    def _fetch_query(self, search_query: str, max_results: int) -> List[dict]:
        papers: List[dict] = []
        start = 0
        batch_size = min(50, max_results)

        while start < max_results:
            params = {
                "search_query": search_query,
                "start": start,
                "max_results": batch_size,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            response = self.get(ARXIV_BASE_URL, params=params)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 30))
                logger.warning("arXiv rate limited, retry after %ss", retry_after)
                time.sleep(retry_after)
                continue
            response.raise_for_status()

            root = ET.fromstring(response.content)
            entries = root.findall("atom:entry", NS)
            if not entries:
                break

            for entry in entries:
                paper = self._parse_entry(entry)
                if paper and paper["tags"]:
                    papers.append(paper)

            start += batch_size
            if len(entries) < batch_size:
                break
            time.sleep(REQUEST_DELAY)

        return papers

    def _parse_entry(self, entry) -> dict | None:
        title_el = entry.find("atom:title", NS)
        if title_el is None:
            return None
        title = title_el.text.strip()

        summary_el = entry.find("atom:summary", NS)
        abstract = summary_el.text.strip() if summary_el is not None else ""

        authors = [
            a.find("atom:name", NS).text.strip()
            for a in entry.findall("atom:author", NS)
            if a.find("atom:name", NS) is not None
        ]

        id_el = entry.find("atom:id", NS)
        arxiv_id = id_el.text.strip().split("/")[-1] if id_el is not None else ""

        pdf_url = abs_url = None
        for link in entry.findall("atom:link", NS):
            href = link.get("href") or ""
            if link.get("title") == "pdf" or href.endswith(".pdf"):
                pdf_url = href
            elif link.get("rel") == "alternate" or "/abs/" in href:
                abs_url = href
        pdf_url = pdf_url or f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        abs_url = abs_url or f"https://arxiv.org/abs/{arxiv_id}"

        year = None
        published = entry.find("atom:published", NS)
        if published is not None and published.text:
            year = int(published.text[:4])
        elif arxiv_id:
            m = re.match(r"(\d{2})(\d{2})", arxiv_id)
            if m:
                year = 2000 + int(m.group(1))

        return {
            "title": title,
            "authors": authors,
            "conference": "arXiv",
            "year": year,
            "pdf_url": pdf_url,
            "abs_url": abs_url,
            "abstract": abstract,
            "tags": tag_by_keywords(f"{title} {abstract}"),
            "source": self.source,
        }

    def fetch(self) -> List[dict]:
        seen = set()
        results: List[dict] = []
        per_query = max(50, self.max_results // len(self.queries))

        for query in self.queries:
            logger.info("arXiv: searching '%s'", query)
            try:
                papers = self._fetch_query(query, per_query)
            except Exception as exc:  # noqa: BLE001
                logger.error("arXiv query '%s' failed: %s", query, exc)
                continue
            for p in papers:
                key = p["title"].lower()
                if key not in seen:
                    seen.add(key)
                    results.append(p)
            logger.info("arXiv: total unique so far %d", len(results))
            if len(results) >= self.max_results:
                break
            time.sleep(REQUEST_DELAY)

        return results[: self.max_results]
