"""papernotes.org HTML scraper, best-effort.

papernotes.org aggregates paper notes/summaries. Its markup can change; this
scraper uses defensive selectors and never raises to the caller so it cannot
break the primary pipelines.
"""
import logging
from typing import List

from bs4 import BeautifulSoup

from .base import ScraperBase, tag_by_keywords, is_diffusion_related

logger = logging.getLogger(__name__)

PAPERNOTES_BASE = "https://papernotes.org"


class PaperNotesScraper(ScraperBase):
    name = "papernotes.org"
    source = "papernotes"

    def __init__(self, max_results: int = 50, query: str = "diffusion"):
        super().__init__(max_results=max_results)
        self.query = query

    def fetch(self) -> List[dict]:
        url = f"{PAPERNOTES_BASE}/search"
        try:
            resp = self.get(url, params={"q": self.query})
        except Exception as exc:  # noqa: BLE001
            logger.error("papernotes request failed: %s", exc)
            return []

        if resp.status_code != 200:
            logger.warning("papernotes -> HTTP %d", resp.status_code)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        papers: List[dict] = []

        # Defensive: look for anchors that reference paper pages.
        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            if "/paper" not in href and "/notes" not in href:
                continue
            if not is_diffusion_related(title):
                continue
            abs_url = href if href.startswith("http") else f"{PAPERNOTES_BASE}/{href.lstrip('/')}"
            papers.append(
                {
                    "title": title,
                    "authors": [],
                    "conference": "papernotes",
                    "year": None,
                    "pdf_url": None,
                    "abs_url": abs_url,
                    "abstract": "",
                    "tags": tag_by_keywords(title),
                    "source": self.source,
                }
            )
            if len(papers) >= self.max_results:
                break

        logger.info("papernotes: collected %d papers", len(papers))
        return papers
