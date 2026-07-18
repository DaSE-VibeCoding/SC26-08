"""Conference proceedings HTML scraper (CVF Open Access), best-effort.

Targets CVPR/ICCV/WACV open-access proceedings hosted at
https://openaccess.thecvf.com and filters diffusion-related papers.
Site structure is subject to change; failures are logged and swallowed
so they never block the primary arXiv/PWC pipelines.
"""
import logging
from typing import List

from bs4 import BeautifulSoup

from .base import ScraperBase, tag_by_keywords, is_diffusion_related

logger = logging.getLogger(__name__)

CVF_BASE = "https://openaccess.thecvf.com"

# (conference-slug, year) pairs to try — CVF Open Access covers CVPR/ICCV/ECCV.
DEFAULT_TARGETS = [
    ("CVPR", 2025),
    ("CVPR", 2024),
    ("CVPR", 2023),
    ("CVPR", 2022),
    ("CVPR", 2021),
    ("ICCV", 2025),
    ("ICCV", 2023),
    ("ICCV", 2021),
    ("ECCV", 2024),
    ("ECCV", 2022),
]


class ProceedingsScraper(ScraperBase):
    name = "Conference Proceedings"
    source = "proceedings"

    def __init__(self, max_results: int = 100, targets=None):
        super().__init__(max_results=max_results)
        self.targets = targets or DEFAULT_TARGETS

    def _fetch_target(self, conf: str, year: int) -> List[dict]:
        url = f"{CVF_BASE}/{conf}{year}?day=all"
        resp = self.get(url)
        if resp.status_code != 200:
            logger.warning("Proceedings %s%s -> HTTP %d", conf, year, resp.status_code)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        papers: List[dict] = []

        for dt in soup.find_all("dt", class_="ptitle"):
            a = dt.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            if not is_diffusion_related(title):
                continue

            abs_url = f"{CVF_BASE}/{a['href'].lstrip('/')}"
            pdf_url = None
            dd = dt.find_next_sibling("dd")
            if dd:
                for link in dd.find_all("a", href=True):
                    if link["href"].endswith(".pdf"):
                        pdf_url = f"{CVF_BASE}/{link['href'].lstrip('/')}"
                        break

            papers.append(
                {
                    "title": title,
                    "authors": [],
                    "conference": conf,
                    "year": year,
                    "pdf_url": pdf_url,
                    "abs_url": abs_url,
                    "abstract": "",
                    "tags": tag_by_keywords(title),
                    "source": self.source,
                }
            )
            if len(papers) >= self.max_results:
                break
        return papers

    def fetch(self) -> List[dict]:
        results: List[dict] = []
        for conf, year in self.targets:
            logger.info("Proceedings: fetching %s %s", conf, year)
            try:
                results.extend(self._fetch_target(conf, year))
            except Exception as exc:  # noqa: BLE001
                logger.error("Proceedings %s%s failed: %s", conf, year, exc)
            if len(results) >= self.max_results:
                break
        return results[: self.max_results]
