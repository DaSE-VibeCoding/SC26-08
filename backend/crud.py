"""Database CRUD operations: query, filter, pagination, upsert, updates."""
import json
import logging
import re
from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from models import Paper

logger = logging.getLogger(__name__)


def normalize_title(title: str) -> str:
    """Lowercase and strip punctuation/whitespace for dedupe keys."""
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def upsert_paper(db: Session, data: dict) -> bool:
    """Insert or update a paper. Returns True if a new row was created."""
    title_key = normalize_title(data.get("title", ""))
    source = data.get("source", "arxiv")

    existing = (
        db.query(Paper)
        .filter(Paper.title_key == title_key, Paper.source == source)
        .first()
    )

    authors = json.dumps(data.get("authors", []), ensure_ascii=False)
    tags = json.dumps(data.get("tags", []), ensure_ascii=False)

    if existing:
        existing.title = data.get("title", existing.title)
        existing.authors = authors
        existing.conference = data.get("conference", existing.conference)
        existing.year = data.get("year", existing.year)
        existing.pdf_url = data.get("pdf_url", existing.pdf_url)
        existing.abs_url = data.get("abs_url", existing.abs_url)
        existing.abstract = data.get("abstract", existing.abstract)
        if data.get("abstract_zh"):
            existing.abstract_zh = data["abstract_zh"]
        existing.tags = tags
        db.commit()
        return False

    paper = Paper(
        title=data.get("title", ""),
        title_key=title_key,
        authors=authors,
        conference=data.get("conference", "arXiv"),
        year=data.get("year"),
        pdf_url=data.get("pdf_url"),
        abs_url=data.get("abs_url"),
        abstract=data.get("abstract", ""),
        abstract_zh=data.get("abstract_zh"),
        tags=tags,
        source=source,
    )
    db.add(paper)
    db.commit()
    return True


def bulk_upsert(db: Session, papers: List[dict]) -> int:
    """Upsert a batch of papers, returning count of newly inserted rows."""
    new_count = 0
    for data in papers:
        if upsert_paper(db, data):
            new_count += 1
    return new_count


def list_papers(
    db: Session,
    conference: Optional[str] = None,
    year: Optional[int] = None,
    tag: Optional[str] = None,
    q: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    query = db.query(Paper)

    if conference:
        query = query.filter(Paper.conference == conference)
    if year:
        query = query.filter(Paper.year == year)
    if source:
        query = query.filter(Paper.source == source)
    if tag:
        query = query.filter(Paper.tags.like(f'%"{tag}"%'))
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Paper.title.ilike(like),
                Paper.abstract.ilike(like),
                Paper.authors.ilike(like),
            )
        )

    total = query.count()
    items = (
        query.order_by(Paper.year.desc().nullslast(), Paper.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, items


def get_paper(db: Session, paper_id: int) -> Optional[Paper]:
    return db.query(Paper).filter(Paper.id == paper_id).first()


def update_abstract_zh(db: Session, paper_id: int, abstract_zh: str) -> Optional[Paper]:
    paper = get_paper(db, paper_id)
    if not paper:
        return None
    paper.abstract_zh = abstract_zh
    db.commit()
    return paper


def get_meta(db: Session) -> dict:
    total = db.query(func.count(Paper.id)).scalar() or 0

    conferences = [
        c[0] for c in db.query(Paper.conference).distinct().all() if c[0]
    ]
    years = sorted(
        {y[0] for y in db.query(Paper.year).distinct().all() if y[0]},
        reverse=True,
    )
    sources = [s[0] for s in db.query(Paper.source).distinct().all() if s[0]]

    tag_set = set()
    for row in db.query(Paper.tags).all():
        for t in json.loads(row[0] or "[]"):
            tag_set.add(t)

    return {
        "total": total,
        "conferences": sorted(conferences),
        "years": years,
        "tags": sorted(tag_set),
        "sources": sorted(sources),
    }
