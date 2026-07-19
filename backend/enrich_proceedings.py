"""Backfill missing CVF proceedings metadata from paper detail pages."""
import json
import logging

from database import SessionLocal, init_db
from models import Paper
from scrapers.base import tag_by_keywords
from scrapers.proceedings import ProceedingsScraper
from sqlalchemy import or_

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    init_db()
    db = SessionLocal()
    scraper = ProceedingsScraper()
    updated = 0
    failed = 0
    try:
        papers = (
            db.query(Paper)
            .filter(
                Paper.source == "proceedings",
                or_(Paper.authors == "[]", Paper.abstract == "", Paper.pdf_url.is_(None)),
            )
            .all()
        )
        for index, paper in enumerate(papers, start=1):
            if not paper.abs_url:
                continue
            try:
                detail = scraper.fetch_detail(paper.abs_url)
                if detail["authors"]:
                    paper.authors = json.dumps(detail["authors"], ensure_ascii=False)
                if detail["abstract"]:
                    paper.abstract = detail["abstract"]
                if detail["pdf_url"]:
                    paper.pdf_url = detail["pdf_url"]
                paper.tags = json.dumps(
                    tag_by_keywords(f"{paper.title} {paper.abstract or ''}"),
                    ensure_ascii=False,
                )
                updated += 1
                if index % 10 == 0:
                    db.commit()
                    logger.info("Processed %d/%d", index, len(papers))
            except Exception as exc:  # noqa: BLE001
                failed += 1
                logger.warning("Failed to enrich paper %s: %s", paper.id, exc)
        db.commit()
    finally:
        db.close()
    logger.info("Enrichment complete: %d updated, %d failed", updated, failed)


if __name__ == "__main__":
    main()
