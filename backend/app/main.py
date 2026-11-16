"""Point d'entrée de l'API FastAPI de la PDIF."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.db import engine

settings = get_settings()

app = FastAPI(
    title="PDIF — Plateforme de Données de l'Inclusion Financière",
    description="API interne de l'Unité d'Inclusion Financière (BRH).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/sante", tags=["système"])
def sante() -> dict:
    """Vérifie que l'API répond et que la base est joignable."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"statut": "ok", "application": settings.app_name, "environnement": settings.environment, "base": "joignable"}
