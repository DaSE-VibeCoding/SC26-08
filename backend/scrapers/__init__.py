"""Scraper package: multi-source diffusion paper collectors."""
from .base import ScraperBase, tag_by_keywords
from .arxiv import ArxivScraper
from .paperswithcode import PapersWithCodeScraper
from .proceedings import ProceedingsScraper
from .papernotes import PaperNotesScraper
from .semanticscholar import SemanticScholarScraper
from .official import OfficialProceedingsScraper

__all__ = [
    "ScraperBase",
    "tag_by_keywords",
    "ArxivScraper",
    "PapersWithCodeScraper",
    "ProceedingsScraper",
    "PaperNotesScraper",
    "SemanticScholarScraper",
    "OfficialProceedingsScraper",
]
