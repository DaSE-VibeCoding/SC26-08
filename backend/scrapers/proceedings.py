"""Conference proceedings HTML scraper (CVF Open Access), best-effort.

Targets CVPR/ICCV/WACV open-access proceedings hosted at
https://openaccess.thecvf.com and filters diffusion-related papers.
Site structure is subject to change; failures are logged and swallowed
so they never block the primary arXiv/PWC pipelines.
"""
import logging
import time
import argparse
import os
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bs4 import BeautifulSoup

from scrapers.base import (
    ScraperBase, tag_by_keywords, is_diffusion_related,
    existing_title_keys, normalized_title,
)

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

    def __init__(self, max_results: int = 0, targets=None):
        super().__init__(max_results=max_results)
        self.targets = targets or DEFAULT_TARGETS
        self.existing_titles = existing_title_keys()

    def fetch_detail(self, url: str) -> dict:
        """Fetch authors, abstract and PDF URL from a CVF paper page."""
        last_error = None
        for attempt in range(3):
            try:
                resp = self.get(url)
                resp.raise_for_status()
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < 2:
                    time.sleep(1 + attempt * 2)
        else:
            raise last_error
        soup = BeautifulSoup(resp.text, "html.parser")

        authors = []
        for meta in soup.select('meta[name="citation_author"]'):
            name = (meta.get("content") or "").strip()
            if name:
                # CVF uses "Family, Given" in citation metadata.
                parts = [part.strip() for part in name.split(",", 1)]
                authors.append(f"{parts[1]} {parts[0]}" if len(parts) == 2 else name)

        abstract_el = soup.select_one("#abstract")
        abstract = abstract_el.get_text(" ", strip=True) if abstract_el else ""

        pdf_meta = soup.select_one('meta[name="citation_pdf_url"]')
        pdf_url = (pdf_meta.get("content") or "").strip() if pdf_meta else None

        return {"authors": authors, "abstract": abstract, "pdf_url": pdf_url}

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
            if normalized_title(title) in self.existing_titles:
                continue

            abs_url = f"{CVF_BASE}/{a['href'].lstrip('/')}"
            detail = {"authors": [], "abstract": "", "pdf_url": None}
            try:
                detail = self.fetch_detail(abs_url)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Proceedings detail failed for %s: %s", title, exc)

            papers.append(
                {
                    "title": title,
                    "authors": detail["authors"],
                    "conference": conf,
                    "year": year,
                    "pdf_url": detail["pdf_url"],
                    "abs_url": abs_url,
                    "abstract": detail["abstract"],
                    "tags": tag_by_keywords(f"{title} {detail['abstract']}"),
                    "source": self.source,
                }
            )
            if self.max_results and len(papers) >= self.max_results:
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
        return results


def main():
    parser = argparse.ArgumentParser(description="Collect official CVF proceedings")
    parser.add_argument("--year", type=int, action="append", dest="years")
    args = parser.parse_args()
    targets = DEFAULT_TARGETS
    if args.years:
        targets = [(conf, year) for conf, year in targets if year in args.years]

    from crud import bulk_upsert
    from database import SessionLocal, init_db

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    init_db(); papers = ProceedingsScraper(max_results=0, targets=targets).fetch()
    db = SessionLocal()
    try: inserted = bulk_upsert(db, papers)
    finally: db.close()
    logger.info("CVF collection complete: %d new, %d processed", inserted, len(papers))


if __name__ == "__main__": main()
