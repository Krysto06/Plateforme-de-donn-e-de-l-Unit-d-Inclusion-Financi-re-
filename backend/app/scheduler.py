"""Mises à jour planifiées (étape 14) : chaque source API se relance selon son calendrier (colonne calendrier_cron).

Activé par PLANIFICATION_ACTIVE=true dans .env. Sur le serveur BRH, on peut aussi utiliser cron avec
la commande « python -m app.cli maj WB ». Les retards sont visibles sur l'écran Connexions (statut « en retard »).
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Source
from app.services.mises_a_jour import CONNECTEURS_API, etat_source, mettre_a_jour

log = logging.getLogger("pdif.planification")


def tache_mise_a_jour(code: str) -> None:
    with SessionLocal() as session:
        chargement = mettre_a_jour(session, code, declencheur="automatique", auteur="planificateur")
        log.info("Mise à jour planifiée %s : %s — %s", code, chargement.statut, chargement.message)


def tache_verifier_retards() -> None:
    with SessionLocal() as session:
        for source in session.scalars(select(Source).where(Source.actif)):
            etat = etat_source(session, source)
            if etat["en_retard"]:
                log.warning("Source %s en retard (dernière mise à jour réussie : %s)", source.code,
                            etat["derniere_maj_reussie"] or "jamais")


def creer_planificateur() -> BackgroundScheduler:
    planificateur = BackgroundScheduler(timezone="America/Port-au-Prince")
    with SessionLocal() as session:
        for source in session.scalars(select(Source).where(Source.actif, Source.calendrier_cron.is_not(None))):
            if source.code in CONNECTEURS_API and source.calendrier_cron:
                planificateur.add_job(tache_mise_a_jour, CronTrigger.from_crontab(source.calendrier_cron),
                                      args=[source.code], id=f"maj-{source.code}", replace_existing=True,
                                      max_instances=1, coalesce=True)
    planificateur.add_job(tache_verifier_retards, CronTrigger(hour=7, minute=0), id="retards", replace_existing=True)
    return planificateur
