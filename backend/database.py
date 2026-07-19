"""SQLite database setup, session management and schema creation."""
import logging

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DB_PATH

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db():
    """Create all tables and indexes if they do not exist."""
    import models  # noqa: F401  ensure models are registered

    Base.metadata.create_all(bind=engine)
    columns = {column["name"] for column in inspect(engine).get_columns("papers")}
    with engine.begin() as connection:
        if "is_read" not in columns:
            connection.execute(
                text("ALTER TABLE papers ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT 0")
            )
        if "is_favorite" not in columns:
            connection.execute(
                text("ALTER TABLE papers ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT 0")
            )
        if "note" not in columns:
            connection.execute(
                text("ALTER TABLE papers ADD COLUMN note TEXT NOT NULL DEFAULT ''")
            )
    logger.info("Database initialized at %s", DB_PATH)


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
