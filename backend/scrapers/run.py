"""Orchestrate multi-source collection, dedupe, and write into SQLite."""
import argparse
import logging
import sys

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__file__)))

from config import (  # noqa: E402
    ENABLE_ARXIV,
    ENABLE_PAPERSWITHCODE,
    ENABLE_PROCEEDINGS,
    ENABLE_PAPERNOTES,
    ENABLE_SEMANTIC_SCHOLAR,
)
from database import SessionLocal, init_db  # noqa: E402
from crud import bulk_upsert, normalize_title  # noqa: E402
from scrapers import (  # noqa: E402
    ArxivScraper,
    PapersWithCodeScraper,
    ProceedingsScraper,
    PaperNotesScraper,
    SemanticScholarScraper,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def collect(max_per_source: int = 100) -> list:
    scrapers = []
    if ENABLE_ARXIV:
        scrapers.append(ArxivScraper(max_results=max_per_source))
    if ENABLE_PAPERSWITHCODE:
        scrapers.append(PapersWithCodeScraper(max_results=max_per_source))
    if ENABLE_PROCEEDINGS:
        scrapers.append(ProceedingsScraper(max_results=max_per_source))
    if ENABLE_SEMANTIC_SCHOLAR:
        scrapers.append(SemanticScholarScraper(max_results=max_per_source))
    if ENABLE_PAPERNOTES:
        scrapers.append(PaperNotesScraper(max_results=max_per_source))

    all_papers: list = []
    seen = set()
    for scraper in scrapers:
        logger.info("=== Running source: %s ===", scraper.name)
        try:
            papers = scraper.fetch()
        except Exception as exc:  # noqa: BLE001
            logger.error("Source %s failed entirely: %s", scraper.name, exc)
            continue
        added = 0
        for p in papers:
            key = (normalize_title(p["title"]), p["source"])
            if key not in seen:
                seen.add(key)
                all_papers.append(p)
                added += 1
        logger.info("Source %s: %d fetched, %d added", scraper.name, len(papers), added)

    return all_papers


def main():
    parser = argparse.ArgumentParser(description="Collect diffusion papers from multiple sources")
    parser.add_argument("--max", type=int, default=100, help="max papers per source")
    args = parser.parse_args()

    init_db()
    papers = collect(max_per_source=args.max)
    if not papers:
        logger.warning("No papers collected.")
        return
    db = SessionLocal()
    new_count = bulk_upsert(db, papers)
    db.close()
    logger.info("Collection complete: %d new inserted, %d total processed", new_count, len(papers))


if __name__ == "__main__":
    main()
