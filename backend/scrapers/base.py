"""Base scraper: shared request helpers, keyword tagging and normalization."""
import logging
import re
from typing import List

import requests

from config import DIFFUSION_KEYWORDS, REQUEST_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def normalized_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def existing_title_keys() -> set[str]:
    """Load existing titles lazily so official crawlers can run incrementally."""
    try:
        from database import SessionLocal
        from models import Paper
        db = SessionLocal()
        try:
            return {row[0] for row in db.query(Paper.title_key).all() if row[0]}
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load existing paper titles: %s", exc)
        return set()


RESEARCH_DIRECTION_RULES = {
    "Image Generation Quality": [
        "quality", "fidelity", "high-resolution", "high resolution",
        "super-resolution", "super resolution", "aesthetic", "realistic",
        "photorealistic", "artifact", "alignment", "controllable",
        "image editing", "image restoration", "reconstruction",
    ],
    "Image Generation Speed": [
        "fast", "faster", "speed", "efficient", "efficiency", "accelerat",
        "few-step", "few step", "one-step", "one step", "single-step",
        "distillation", "consistency model", "real-time", "real time",
        "lightweight", "sampling step", "inference time", "latency",
    ],
    "Image Safety": [
        "safety", "safe generation", "unsafe", "harmful", "toxic", "nsfw",
        "watermark", "deepfake", "misuse", "adversarial", "jailbreak",
        "bias", "fairness", "copyright", "content moderation",
        "concept erasure", "unlearning", "detection",
    ],
    "Image Privacy": [
        "privacy", "private", "data leakage", "information leakage",
        "membership inference", "training data extraction", "memorization",
        "data protection", "federated", "differential privacy",
    ],
}


def tag_by_keywords(text: str) -> List[str]:
    """Classify a paper into the configured Diffusion research directions."""
    lowered = (text or "").lower()
    tags = [
        direction
        for direction, keywords in RESEARCH_DIRECTION_RULES.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    return tags or ["Other Directions"]


def is_diffusion_related(text: str) -> bool:
    lowered = (text or "").lower()
    return any(keyword.lower() in lowered for keyword in DIFFUSION_KEYWORDS)


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
