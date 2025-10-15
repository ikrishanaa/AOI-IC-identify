from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from shared.config import get_settings

_settings = get_settings()

engine = create_engine(_settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection() -> bool:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
