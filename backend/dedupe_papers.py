"""Merge papers with the same normalized title across different sources."""
import json
import logging

from database import SessionLocal, init_db
from models import Paper

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SOURCE_PRIORITY = {"official": 0, "proceedings": 1, "semanticscholar": 2,
                   "arxiv": 3, "paperswithcode": 4, "papernotes": 5}


def richness(paper: Paper):
    return (
        -SOURCE_PRIORITY.get(paper.source, 99),
        bool(paper.abstract), bool(paper.pdf_url),
        len(json.loads(paper.authors or "[]")), len(paper.abstract or ""),
    )


def main():
    init_db(); db = SessionLocal(); removed = 0
    try:
        groups = {}
        for paper in db.query(Paper).all():
            groups.setdefault(paper.title_key, []).append(paper)
        for papers in groups.values():
            if len(papers) < 2: continue
            keeper = max(papers, key=richness)
            for duplicate in papers:
                if duplicate.id == keeper.id: continue
                if not keeper.abstract and duplicate.abstract: keeper.abstract = duplicate.abstract
                if not keeper.abstract_zh and duplicate.abstract_zh: keeper.abstract_zh = duplicate.abstract_zh
                if not keeper.pdf_url and duplicate.pdf_url: keeper.pdf_url = duplicate.pdf_url
                if not keeper.abs_url and duplicate.abs_url: keeper.abs_url = duplicate.abs_url
                if json.loads(keeper.authors or "[]") == [] and duplicate.authors:
                    keeper.authors = duplicate.authors
                db.delete(duplicate); removed += 1
        db.commit()
    finally:
        db.close()
    logger.info("Cross-source dedupe complete: %d duplicates removed", removed)


if __name__ == "__main__": main()
