"""SQLAlchemy ORM models and Pydantic schemas for papers."""
import json
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, Integer, String, Text, UniqueConstraint, Index

from database import Base


# --------------------------------------------------------------------------- #
# ORM model
# --------------------------------------------------------------------------- #
class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    title_key = Column(String, nullable=False, index=True)  # normalized dedupe key
    authors = Column(Text, default="[]")                    # JSON-encoded list
    conference = Column(String, default="arXiv", index=True)
    year = Column(Integer, nullable=True, index=True)
    pdf_url = Column(String, nullable=True)
    abs_url = Column(String, nullable=True)
    abstract = Column(Text, default="")
    abstract_zh = Column(Text, nullable=True)
    note = Column(Text, nullable=False, default="", server_default="")
    is_read = Column(Boolean, nullable=False, default=False, server_default="0", index=True)
    is_favorite = Column(Boolean, nullable=False, default=False, server_default="0", index=True)
    tags = Column(Text, default="[]")                       # JSON-encoded list
    source = Column(String, default="arxiv", index=True)

    __table_args__ = (
        UniqueConstraint("title_key", "source", name="uq_title_source"),
        Index("ix_conf_year", "conference", "year"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "authors": json.loads(self.authors or "[]"),
            "conference": self.conference,
            "year": self.year,
            "pdf_url": self.pdf_url,
            "abs_url": self.abs_url,
            "abstract": self.abstract or "",
            "abstract_zh": self.abstract_zh,
            "note": self.note or "",
            "is_read": bool(self.is_read),
            "is_favorite": bool(self.is_favorite),
            "tags": json.loads(self.tags or "[]"),
            "source": self.source,
        }


# --------------------------------------------------------------------------- #
# Pydantic schemas
# --------------------------------------------------------------------------- #
class PaperBase(BaseModel):
    title: str
    authors: List[str] = []
    conference: str = "arXiv"
    year: Optional[int] = None
    pdf_url: Optional[str] = None
    abs_url: Optional[str] = None
    abstract: str = ""
    abstract_zh: Optional[str] = None
    note: str = ""
    is_read: bool = False
    is_favorite: bool = False
    tags: List[str] = []
    source: str = "arxiv"


class PaperOut(PaperBase):
    id: int


class PaperListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[PaperOut]


class MetaResponse(BaseModel):
    total: int
    conferences: List[str]
    years: List[int]
    tags: List[str]
    sources: List[str]


class AbstractZhUpdate(BaseModel):
    abstract_zh: str = Field(..., description="Human-written Chinese abstract")


class PaperStateUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_favorite: Optional[bool] = None


class PaperNoteUpdate(BaseModel):
    note: str = Field(default="", max_length=50000)
