"""Semantic Scholar conference scraper (requires a free API key).

Fetches diffusion-related papers from the major venues
(ACL, CVPR, ICLR, AAAI, NeurIPS, ICCV, ICML, ECCV) for the configured year
range via the Semantic Scholar Graph API.

A free API key is required and must be provided through the
``SEMANTIC_SCHOLAR_API_KEY`` environment variable (or a ``.env`` file).
Without a key the source is skipped gracefully — S2 rate-limits anonymous
requests to the point of being unusable. Any failure is swallowed so it never
blocks the other collection sources.
"""
import logging
import re
import time
from typing import Dict, List, Optional

import requests

from config import (
    CONFERENCE_YEARS,
    REQUEST_DELAY,
    SEMANTIC_SCHOLAR_API_KEY,
    SEMANTIC_SCHOLAR_CONFERENCES,
    SEMANTIC_SCHOLAR_MAX_PAGES,
)
from .base import ScraperBase, is_diffusion_related, tag_by_keywords

logger = logging.getLogger(__name__)

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_FIELDS = "title,year,venue,abstract,authors,externalIds,openAccessPdf,url"
S2_RATE_LIMIT_BACKOFF = 10  # seconds to wait after a 429


class SemanticScholarScraper(ScraperBase):
    name = "Semantic Scholar"
    source = "semanticscholar"

    def __init__(
        self,
        max_results: int = 300,
        conferences: Optional[Dict[str, List[str]]] = None,
        years: Optional[List[int]] = None,
        max_pages: int = SEMANTIC_SCHOLAR_MAX_PAGES,
    ):
        super().__init__(max_results=max_results)
        self.conferences = conferences or SEMANTIC_SCHOLAR_CONFERENCES
        self.years = years or CONFERENCE_YEARS
        self.max_pages = max_pages
        if SEMANTIC_SCHOLAR_API_KEY:
            self.session.headers.update({"x-api-key": SEMANTIC_SCHOLAR_API_KEY})

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #
    def fetch(self) -> List[dict]:
        if not SEMANTIC_SCHOLAR_API_KEY:
            logger.warning(
                "SemanticScholar: no API key (SEMANTIC_SCHOLAR_API_KEY); skipping. "
                "Get a free key at https://www.semanticscholar.org/product/api"
            )
            return []

        results: List[dict] = []
        seen = set()
        for year in self.years:
            logger.info("SemanticScholar: collecting year %s", year)
            try:
                papers = self._fetch_year(year)
            except Exception as exc:  # noqa: BLE001
                logger.error("SemanticScholar year %s failed: %s", year, exc)
                continue

            added = 0
            for p in papers:
                key = self._title_key(p["title"])
                if key not in seen:
                    seen.add(key)
                    results.append(p)
                    added += 1
                if len(results) >= self.max_results:
                    break

            logger.info("SemanticScholar %s: %d venue papers (%d added)", year, len(papers), added)
            if len(results) >= self.max_results:
                break
            time.sleep(REQUEST_DELAY)

        return results[: self.max_results]

    # ------------------------------------------------------------------ #
    # Per-year collection
    # ------------------------------------------------------------------ #
    def _fetch_year(self, year: int) -> List[dict]:
        out: List[dict] = []
        offset = 0
        for _ in range(self.max_pages):
            params = {
                "query": "diffusion",
                "year": year,
                "fields": S2_FIELDS,
                "limit": 100,
                "offset": offset,
            }
            resp = self._safe_get(params)
            if resp is None:
                break

            try:
                data = resp.json()
            except ValueError:
                logger.warning("SemanticScholar: non-JSON response for %s", year)
                break

            items = data.get("data") or []
            if not items:
                break

            for item in items:
                paper = self._parse(item)
                if paper:
                    out.append(paper)

            if len(items) < 100:
                break
            offset += 100
            time.sleep(REQUEST_DELAY)

        return out

    # ------------------------------------------------------------------ #
    # HTTP helper (handles rate-limiting / errors gracefully)
    # ------------------------------------------------------------------ #
    def _safe_get(self, params: dict) -> Optional[requests.Response]:
        try:
            resp = self.get(S2_API, params=params)
        except requests.RequestException as exc:
            logger.error("SemanticScholar request error: %s", exc)
            return None

        if resp.status_code == 429:
            logger.warning(
                "SemanticScholar rate limited (429); backing off %ss",
                S2_RATE_LIMIT_BACKOFF,
            )
            time.sleep(S2_RATE_LIMIT_BACKOFF)
            return None
        if resp.status_code != 200:
            logger.warning("SemanticScholar HTTP %d", resp.status_code)
            return None
        return resp

    # ------------------------------------------------------------------ #
    # Parse a single S2 record into the unified schema
    # ------------------------------------------------------------------ #
    def _parse(self, item: dict) -> Optional[dict]:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        abstract = (item.get("abstract") or "").strip()
        if not is_diffusion_related(f"{title} {abstract}"):
            return None

        conference = self._match_conference(item.get("venue"))
        if not conference:
            return None

        authors = [
            a.get("name", "") for a in item.get("authors", []) or [] if a.get("name")
        ]

        pdf_url = None
        oa = item.get("openAccessPdf")
        if isinstance(oa, dict) and oa.get("url"):
            pdf_url = oa["url"]

        external_ids = item.get("externalIds") or {}
        arxiv_id = external_ids.get("ArXiv")
        abs_url = item.get("url")
        if not abs_url and arxiv_id:
            abs_url = f"https://arxiv.org/abs/{arxiv_id}"

        return {
            "title": title,
            "authors": authors,
            "conference": conference,
            "year": item.get("year"),
            "pdf_url": pdf_url,
            "abs_url": abs_url,
            "abstract": abstract,
            "tags": tag_by_keywords(f"{title} {abstract}"),
            "source": self.source,
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _match_conference(self, venue: Optional[str]) -> Optional[str]:
        if not venue:
            return None
        lowered = venue.lower()
        for conf, patterns in self.conferences.items():
            for pat in patterns:
                if pat in lowered:
                    return conf
        return None

    @staticmethod
    def _title_key(title: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (title or "").lower())
