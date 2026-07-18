"""Application configuration for the Diffusion Paper Hub backend."""
import os

from dotenv import load_dotenv

load_dotenv()  # read SEMANTIC_SCHOLAR_API_KEY etc. from a local .env file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# SQLite database file location
DB_PATH = os.path.join(BASE_DIR, "papers.db")

# Static frontend build output (served at "/")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Seed data (existing arXiv diffusion papers)
SEED_JSON = os.path.join(PROJECT_ROOT, "papers.json")

# Diffusion keyword filter shared by scrapers
DIFFUSION_KEYWORDS = [
    "diffusion", "denoising", "ddpm", "ddim", "score-based",
    "score matching", "flow matching", "rectified flow", "consistency model",
    "diffusion model", "diffusion probabilistic", "latent diffusion",
    "stable diffusion",
]

# Scraper networking
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 2  # seconds between paged requests

# Data source toggles
ENABLE_ARXIV = True
ENABLE_PAPERSWITHCODE = True
ENABLE_PROCEEDINGS = True    # CVF Open Access (CVPR/ICCV/ECCV), no key required
ENABLE_PAPERNOTES = False    # best-effort, disabled by default
ENABLE_SEMANTIC_SCHOLAR = True  # covers ACL/CVPR/ICLR/AAAI/NeurIPS/ICCV/ICML/ECCV

# Semantic Scholar (https://www.semanticscholar.org/product/api) — free key.
# Without a key the source is skipped gracefully (S2 rate-limits anonymous use).
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()

# Conferences we want to "connect", with the substring patterns used to
# recognise each venue in Semantic Scholar's free-text `venue` field.
SEMANTIC_SCHOLAR_CONFERENCES = {
    "ACL": ["acl", "computational linguistics"],
    "CVPR": ["cvpr", "computer vision and pattern recognition"],
    "ICCV": ["iccv", "international conference on computer vision"],
    "ECCV": ["eccv", "european conference on computer vision"],
    "NeurIPS": ["neurips", "neural information processing systems"],
    "ICML": ["icml", "machine learning"],
    "ICLR": ["iclr", "learning representations"],
    "AAAI": ["aaai", "artificial intelligence"],
}

# Year range to collect (inclusive).
CONFERENCE_YEARS = [2021, 2022, 2023, 2024, 2025]

# Max pages fetched per year from Semantic Scholar (100 results / page).
SEMANTIC_SCHOLAR_MAX_PAGES = 6
