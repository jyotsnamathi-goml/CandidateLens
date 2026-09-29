from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db_and_migrate():
    """Create tables and ensure newly added columns exist in SQLite."""
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            # Auto-migrate candidates table for linkedin_url if missing
            res = conn.execute(text("PRAGMA table_info(candidates)")).fetchall()
            columns = [row[1] for row in res]
            if columns and "linkedin_url" not in columns:
                conn.execute(text("ALTER TABLE candidates ADD COLUMN linkedin_url VARCHAR(500)"))
                conn.commit()
        except Exception:
            pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
