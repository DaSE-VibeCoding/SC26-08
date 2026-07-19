"""Reclassify existing papers into the configured research directions."""
import json
import logging

from database import SessionLocal, init_db
from models import Paper
from scrapers.base import tag_by_keywords

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    init_db()
    db = SessionLocal()
    try:
        papers = db.query(Paper).all()
        for paper in papers:
            tags = tag_by_keywords(f"{paper.title} {paper.abstract or ''}")
            paper.tags = json.dumps(tags, ensure_ascii=False)
        db.commit()
        logger.info("Reclassified %d papers.", len(papers))
    finally:
        db.close()


if __name__ == "__main__":
    main()
