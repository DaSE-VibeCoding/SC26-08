"""FastAPI application: REST API + static frontend hosting."""
import logging
import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

import crud
from config import STATIC_DIR
from database import get_db, init_db
from models import (
    AbstractZhUpdate,
    MetaResponse,
    PaperListResponse,
    PaperOut,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Diffusion Paper Hub API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("API ready.")


# --------------------------------------------------------------------------- #
# API routes
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta", response_model=MetaResponse)
def meta(db: Session = Depends(get_db)):
    return crud.get_meta(db)


@app.get("/api/papers", response_model=PaperListResponse)
def list_papers(
    conference: str | None = Query(None),
    year: int | None = Query(None),
    tag: str | None = Query(None),
    q: str | None = Query(None),
    source: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    total, items = crud.list_papers(
        db, conference=conference, year=year, tag=tag, q=q,
        source=source, limit=limit, offset=offset,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [PaperOut(**p.to_dict()) for p in items],
    }


@app.get("/api/papers/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = crud.get_paper(db, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperOut(**paper.to_dict())


@app.patch("/api/papers/{paper_id}/abstract_zh", response_model=PaperOut)
def update_abstract_zh(
    paper_id: int, payload: AbstractZhUpdate, db: Session = Depends(get_db)
):
    paper = crud.update_abstract_zh(db, paper_id, payload.abstract_zh)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperOut(**paper.to_dict())


# --------------------------------------------------------------------------- #
# Static frontend hosting (SPA fallback)
# --------------------------------------------------------------------------- #
if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return JSONResponse({"detail": "Frontend not built"}, status_code=404)
else:
    @app.get("/")
    def root():
        return {
            "message": "Diffusion Paper Hub API is running. Build the frontend "
            "to serve the UI. See /docs for API documentation."
        }
