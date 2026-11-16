"""Moteur SQLAlchemy et session. Le même code sert pour SQLite et PostgreSQL."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite a besoin de ce paramètre pour être utilisé par le serveur web
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe mère de toutes les tables (définies à l'étape 2)."""


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
