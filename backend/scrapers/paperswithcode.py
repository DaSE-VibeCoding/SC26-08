"""Papers With Code scraper using the public REST API."""
import logging
import time
from typing import List

from config import REQUEST_DELAY
from .base import ScraperBase, tag_by_keywords

logger = logging.getLogger(__name__)

PWC_BASE = "https://paperswithcode.com/api/v1"

# Diffusion-relevant tasks on Papers With Code
DEFAULT_TASKS = [
    "denoising",
    "image-generation",
    "text-to-image-generation",
]


class PapersWithCodeScraper(ScraperBase):
    name = "Papers With Code"
    source = "paperswithcode"

    def __init__(self, max_results: int = 100, tasks: List[str] | None = None):
        super().__init__(max_results=max_results)
        self.tasks = tasks or DEFAULT_TASKS

    def _fetch_task(self, task: str, max_results: int) -> List[dict]:
        papers: List[dict] = []
        page = 1
        while len(papers) < max_results:
            url = f"{PWC_BASE}/tasks/{task}/papers/"
            resp = self.get(url, params={"page": page, "items_per_page": 50})
            if resp.status_code != 200:
                logger.warning("PWC task '%s' page %d -> HTTP %d", task, page, resp.status_code)
                break
            data = resp.json()
            results = data.get("results", [])
            if not results:
                break
            for item in results:
                paper = self._parse_item(item)
                if paper and paper["tags"]:
                    papers.append(paper)
            if not data.get("next"):
                break
            page += 1
            time.sleep(REQUEST_DELAY)
        return papers

    def _parse_item(self, item: dict) -> dict | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None
        abstract = (item.get("abstract") or "").strip()
        year = None
        published = item.get("published")
        if published:
            year = int(str(published)[:4])
        conference = item.get("conference") or item.get("proceeding") or "Papers With Code"
        # PWC "proceeding" often looks like "neurips-2023"; extract a clean name
        if isinstance(conference, str) and "-" in conference and conference[-4:].isdigit():
            name, yr = conference.rsplit("-", 1)
            conference = name.upper()
            year = year or int(yr)

        return {
            "title": title,
            "authors": item.get("authors", []),
            "conference": conference,
            "year": year,
            "pdf_url": item.get("url_pdf"),
            "abs_url": item.get("url_abs"),
            "abstract": abstract,
            "tags": tag_by_keywords(f"{title} {abstract}"),
            "source": self.source,
        }

    def fetch(self) -> List[dict]:
        seen = set()
        results: List[dict] = []
        per_task = max(30, self.max_results // len(self.tasks))
        for task in self.tasks:
            logger.info("PWC: fetching task '%s'", task)
            try:
                papers = self._fetch_task(task, per_task)
            except Exception as exc:  # noqa: BLE001
                logger.error("PWC task '%s' failed: %s", task, exc)
                continue
            for p in papers:
                key = p["title"].lower()
                if key not in seen:
                    seen.add(key)
                    results.append(p)
            logger.info("PWC: total unique so far %d", len(results))
            if len(results) >= self.max_results:
                break
            time.sleep(REQUEST_DELAY)
        return results[: self.max_results]
