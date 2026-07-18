"""Base scraper: shared request helpers, keyword tagging and normalization."""
import logging
from typing import List

import requests

from config import DIFFUSION_KEYWORDS, REQUEST_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def tag_by_keywords(text: str) -> List[str]:
    """Return diffusion-related tags present in the given text."""
    tags = []
    lowered = (text or "").lower()
    for kw in DIFFUSION_KEYWORDS:
        if kw.lower() in lowered:
            tags.append(kw)
    return tags


def is_diffusion_related(text: str) -> bool:
    return len(tag_by_keywords(text)) > 0


class ScraperBase:
    """Base class for all data-source scrapers.

    Subclasses implement ``fetch()`` returning a list of normalized paper
    dicts matching the unified schema (see models.PaperBase).
    """

    name = "base"
    source = "base"

    def __init__(self, max_results: int = 100):
        self.max_results = max_results
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)

    def get(self, url: str, **kwargs):
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        return self.session.get(url, **kwargs)

    def normalize(self, raw: dict) -> dict:
        """Ensure a raw record conforms to the unified paper schema."""
        title = raw.get("title", "").strip()
        abstract = raw.get("abstract", "") or ""
        tags = raw.get("tags") or tag_by_keywords(f"{title} {abstract}")
        return {
            "title": title,
            "authors": raw.get("authors", []),
            "conference": raw.get("conference", "arXiv"),
            "year": raw.get("year"),
            "pdf_url": raw.get("pdf_url"),
            "abs_url": raw.get("abs_url"),
            "abstract": abstract.strip(),
            "abstract_zh": raw.get("abstract_zh"),
            "tags": tags,
            "source": self.source,
        }

    def fetch(self) -> List[dict]:  # pragma: no cover - interface
        raise NotImplementedError
