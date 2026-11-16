"""Journal d'audit : qui a fait quoi et quand."""
from sqlalchemy.orm import Session

from app.models import Journal


def tracer(session: Session, utilisateur: str, action: str, objet: str | None = None, detail: str | None = None) -> None:
    session.add(Journal(utilisateur=utilisateur, action=action, objet=objet, detail=detail))
