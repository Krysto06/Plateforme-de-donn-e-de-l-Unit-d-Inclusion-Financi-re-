"""Point d'entrée de l'API FastAPI de la PDIF. Documentation automatique : /docs."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import admin, auth, chargements, depots, exports, kpi, sources
from app.config import get_settings
from app.db import engine

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s : %(message)s")


@asynccontextmanager
async def cycle_de_vie(_: FastAPI):
    planificateur = None
    if settings.planification_active:
        from app.scheduler import creer_planificateur

        planificateur = creer_planificateur()
        planificateur.start()
        logging.getLogger("pdif").info("Planification active : %s", [j.id for j in planificateur.get_jobs()])
    yield
    if planificateur:
        planificateur.shutdown(wait=False)


app = FastAPI(
    title="PDIF — Plateforme de Données de l'Inclusion Financière",
    description="API interne de l'Unité d'Inclusion Financière (BRH). Données agrégées uniquement.",
    version="0.2.0",
    lifespan=cycle_de_vie,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (auth, kpi, sources, chargements, depots, exports, admin):
    app.include_router(module.router)


@app.get("/api/sante", tags=["système"])
def sante() -> dict:
    """Vérifie que l'API répond et que la base est joignable."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"statut": "ok", "application": settings.app_name, "environnement": settings.environment, "base": "joignable",
            "planification": settings.planification_active, "depots_ouverts": settings.depots_directions_ouverts}
