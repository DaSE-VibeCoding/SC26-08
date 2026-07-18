"""Import existing papers.json (arXiv diffusion seed data) into SQLite."""
import json
import logging
import os
import re

from config import SEED_JSON
from database import SessionLocal, init_db
from crud import bulk_upsert

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _extract_year(paper: dict) -> int | None:
    """Best-effort year extraction from arXiv id embedded in URLs."""
    for key in ("abs_url", "pdf_url"):
        url = paper.get(key) or ""
        m = re.search(r"/(\d{2})(\d{2})\.\d{4,5}", url)
        if m:
            return 2000 + int(m.group(1))
    return None


def load_seed():
    if not os.path.exists(SEED_JSON):
        logger.warning("Seed file not found: %s", SEED_JSON)
        return []

    with open(SEED_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)

    papers = []
    for p in raw:
        papers.append(
            {
                "title": p.get("title", ""),
                "authors": p.get("authors", []),
                "conference": p.get("conference", "arXiv"),
                "year": _extract_year(p),
                "pdf_url": p.get("pdf_url"),
                "abs_url": p.get("abs_url"),
                "abstract": p.get("abstract", ""),
                "abstract_zh": p.get("abstract_zh"),
                "tags": p.get("tags", []),
                "source": "arxiv",
            }
        )
    return papers


def main():
    init_db()
    papers = load_seed()
    if not papers:
        logger.info("No seed papers to import.")
        return
    db = SessionLocal()
    new_count = bulk_upsert(db, papers)
    db.close()
    logger.info("Seed import complete: %d new, %d total processed", new_count, len(papers))


if __name__ == "__main__":
    main()
