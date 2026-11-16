"""Moteur SQLAlchemy et session. Le même code sert pour SQLite et PostgreSQL."""
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

settings = get_settings()

_est_sqlite = settings.database_url.startswith("sqlite")
_options: dict = {}
if _est_sqlite:
    # SQLite a besoin de ce paramètre pour être utilisé par le serveur web
    _options["connect_args"] = {"check_same_thread": False}
    if ":memory:" in settings.database_url:  # base de test en mémoire, partagée par toutes les connexions
        _options["poolclass"] = StaticPool

engine = create_engine(settings.database_url, **_options)

if _est_sqlite:

    @event.listens_for(engine, "connect")
    def _activer_cles_etrangeres(conn, _):
        # SQLite ne vérifie les liens entre tables que si on le lui demande
        conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe mère de toutes les tables (voir app/models)."""


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
