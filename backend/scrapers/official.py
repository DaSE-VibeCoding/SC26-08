"""Collectors for official conference proceedings websites."""
import logging
import re
import argparse
import os
import sys
import time
from typing import List
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bs4 import BeautifulSoup

from config import CONFERENCE_YEARS
from scrapers.base import (
    ScraperBase, is_diffusion_related, tag_by_keywords,
    existing_title_keys, normalized_title,
)

logger = logging.getLogger(__name__)


def _meta_values(soup: BeautifulSoup, name: str) -> list[str]:
    return [
        (node.get("content") or "").strip()
        for node in soup.select(f'meta[name="{name}"]')
        if (node.get("content") or "").strip()
    ]


def _paper(title, authors, conference, year, pdf_url, abs_url, abstract):
    text = f"{title} {abstract}"
    if not is_diffusion_related(text):
        return None
    return {
        "title": title.strip(), "authors": authors, "conference": conference,
        "year": year, "pdf_url": pdf_url, "abs_url": abs_url,
        "abstract": (abstract or "").strip(), "tags": tag_by_keywords(text),
        "source": "official",
    }


class OfficialProceedingsScraper(ScraperBase):
    """Aggregate official ACL, ICLR, NeurIPS and ICML proceedings."""

    name = "Official Conference Proceedings"
    source = "official"

    ICML_VOLUMES = {2021: 139, 2022: 162, 2023: 202, 2024: 235, 2025: 267}

    def __init__(self, max_results: int = 0, years=None):
        # max_results is intentionally per official page, not shared globally.
        super().__init__(max_results=max_results)
        self.years = years or CONFERENCE_YEARS
        self.existing_titles = existing_title_keys()

    def _citation_detail(self, url: str, conference: str, year: int):
        last_error = None
        for attempt in range(3):
            try:
                resp = self.get(url)
                resp.raise_for_status()
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt < 2: time.sleep(1 + attempt * 2)
        else:
            raise last_error
        soup = BeautifulSoup(resp.text, "html.parser")
        title = (_meta_values(soup, "citation_title") or [""])[0]
        authors = _meta_values(soup, "citation_author")
        pdf_url = (_meta_values(soup, "citation_pdf_url") or [None])[0]
        abstract_el = soup.select_one("#abstract, .abstract, div.abstract")
        abstract = abstract_el.get_text(" ", strip=True) if abstract_el else ""
        description = (_meta_values(soup, "description") or [""])[0]
        return _paper(title, authors, conference, year, pdf_url, url, abstract or description)

    def _acl(self, year: int) -> list[dict]:
        base = f"https://aclanthology.org/events/acl-{year}/"
        resp = self.get(base); resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []
        pattern = re.compile(rf"^/{year}\.acl-(?:long|short|main|demo|industry)\.\d+/$")
        for a in soup.find_all("a", href=pattern):
            url = urljoin(base, a["href"])
            title = a.get_text(" ", strip=True)
            if (url not in urls and is_diffusion_related(title)
                    and normalized_title(title) not in self.existing_titles):
                urls.append(url)
        results = []
        for url in urls:
            try:
                paper = self._citation_detail(url, "ACL", year)
                if paper: results.append(paper)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ACL detail skipped %s: %s", url, exc)
        return results

    def _neurips(self, year: int) -> list[dict]:
        base = f"https://proceedings.neurips.cc/paper_files/paper/{year}"
        resp = self.get(base); resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []
        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            if ("Abstract" in a["href"] and is_diffusion_related(title)
                    and normalized_title(title) not in self.existing_titles):
                url = urljoin(base, a["href"])
                if url not in urls:
                    urls.append(url)
        results = []
        for url in urls:
            try:
                paper = self._citation_detail(url, "NeurIPS", year)
                if paper: results.append(paper)
            except Exception as exc:  # noqa: BLE001
                logger.warning("NeurIPS detail skipped %s: %s", url, exc)
        return results

    @staticmethod
    def _openreview_value(content: dict, key: str, default=None):
        value = content.get(key, default)
        return value.get("value", default) if isinstance(value, dict) else value

    def _iclr(self, year: int) -> list[dict]:
        api = "https://api2.openreview.net/notes"
        results, offset = [], 0
        while True:
            resp = self.get(api, params={
                "content.venueid": f"ICLR.cc/{year}/Conference",
                "limit": 1000, "offset": offset,
            })
            resp.raise_for_status(); notes = (resp.json().get("notes") or [])
            if not notes: break
            for note in notes:
                content = note.get("content") or {}
                title = self._openreview_value(content, "title", "") or ""
                if normalized_title(title) in self.existing_titles: continue
                abstract = self._openreview_value(content, "abstract", "") or ""
                venue = self._openreview_value(content, "venue", "") or ""
                if "Withdrawn" in venue or "Rejected" in venue: continue
                authors = self._openreview_value(content, "authors", []) or []
                paper = _paper(title, authors, "ICLR", year, None,
                               f"https://openreview.net/forum?id={note.get('forum') or note.get('id')}", abstract)
                if paper: results.append(paper)
            if len(notes) < 1000: break
            offset += 1000
        return results

    def _iclr_html(self, year: int) -> list[dict]:
        """Fallback when the public OpenReview notes API is blocked."""
        base = f"https://openreview.net/group?id=ICLR.cc/{year}/Conference"
        resp = self.get(base); resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []
        for a in soup.find_all("a", href=True):
            if "/forum?id=" in a["href"] and is_diffusion_related(a.get_text(" ", strip=True)):
                url = urljoin(base, a["href"])
                if url not in urls: urls.append(url)
        results = []
        for url in urls:
            try:
                paper = self._citation_detail(url, "ICLR", year)
                if paper: results.append(paper)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ICLR detail skipped %s: %s", url, exc)
        return results

    def _icml(self, year: int) -> list[dict]:
        volume = self.ICML_VOLUMES.get(year)
        if not volume: return []
        base = f"https://proceedings.mlr.press/v{volume}/"
        resp = self.get(base); resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for block in soup.select("div.paper"):
            title_el = block.select_one("p.title")
            if not title_el: continue
            title = title_el.get_text(" ", strip=True)
            if not is_diffusion_related(title): continue
            if normalized_title(title) in self.existing_titles: continue
            link = block.select_one('a[href$=".html"]')
            if not link: continue
            paper = self._citation_detail(urljoin(base, link["href"]), "ICML", year)
            if paper: results.append(paper)
        return results

    def fetch(self) -> List[dict]:
        results = []
        collectors = (("ACL", self._acl), ("ICLR", self._iclr),
                      ("NeurIPS", self._neurips), ("ICML", self._icml))
        for year in self.years:
            for name, collector in collectors:
                try:
                    papers = collector(year)
                    results.extend(papers)
                    logger.info("Official %s %s: %d diffusion papers", name, year, len(papers))
                except Exception as exc:  # noqa: BLE001
                    if name == "ICLR":
                        logger.warning("OpenReview API failed, trying HTML: %s", exc)
                        try:
                            papers = self._iclr_html(year)
                            results.extend(papers)
                            logger.info("Official ICLR %s: %d diffusion papers", year, len(papers))
                        except Exception as fallback_exc:  # noqa: BLE001
                            logger.error("Official ICLR %s failed: %s", year, fallback_exc)
                    else:
                        logger.error("Official %s %s failed: %s", name, year, exc)
        return results


def main():
    parser = argparse.ArgumentParser(description="Collect from official proceedings")
    parser.add_argument("--year", type=int, action="append", dest="years")
    args = parser.parse_args()

    from crud import bulk_upsert
    from database import SessionLocal, init_db

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    init_db()
    papers = OfficialProceedingsScraper(years=args.years).fetch()
    db = SessionLocal()
    try:
        inserted = bulk_upsert(db, papers)
    finally:
        db.close()
    logger.info("Official collection complete: %d new, %d processed", inserted, len(papers))


if __name__ == "__main__":
    main()
