"""Lancement d'une mise à jour d'une source API (depuis l'écran Connexions ou le planificateur)."""
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.connectors.base import ConnecteurAPI, ErreurSource
from app.connectors.imf import ConnecteurFMI
from app.connectors.worldbank import ConnecteurBanqueMondiale
from app.models import Chargement, Observation, Source
from app.services.chargement import traiter_envoi
from app.services.journal import tracer

log = logging.getLogger("pdif.maj")

CONNECTEURS_API = {"WB": ConnecteurBanqueMondiale, "FMI": ConnecteurFMI}


def connecteur_api(code: str, session: Session, client: httpx.Client | None = None) -> ConnecteurAPI:
    if code not in CONNECTEURS_API:
        raise ValueError(f"La source {code} n'a pas de connecteur API.")
    return CONNECTEURS_API[code](session, client=client)


def preparer_chargement(session: Session, code: str, declencheur: str, auteur: str) -> Chargement:
    source = session.scalar(select(Source).where(Source.code == code))
    chargement = Chargement(source=source, declencheur=declencheur, auteur=auteur, statut="reçu",
                            message="Interrogation de l'API en cours…")
    session.add(chargement)
    session.commit()
    return chargement


def executer(session: Session, chargement_id: int, client: httpx.Client | None = None) -> Chargement:
    chargement = session.get(Chargement, chargement_id)
    code = chargement.source.code
    connecteur = connecteur_api(code, session, client)
    try:
        brut = connecteur.extraire()
    except ErreurSource as exc:
        chargement.statut = "erreur"
        chargement.message = str(exc)
        chargement.termine_le = datetime.now(timezone.utc)
        tracer(session, chargement.auteur, "chargement", f"chargement #{chargement.id}", f"{code} — erreur — {exc}")
        session.commit()
        log.error("Mise à jour %s en erreur : %s", code, exc)
        return chargement
    return traiter_envoi(session, source_code=code, df_brut=brut, modele=connecteur.modele,
                         normaliser=connecteur.normaliser, declencheur=chargement.declencheur,
                         auteur=chargement.auteur, chargement=chargement)


def mettre_a_jour(session: Session, code: str, declencheur: str, auteur: str, client: httpx.Client | None = None) -> Chargement:
    chargement = preparer_chargement(session, code, declencheur, auteur)
    return executer(session, chargement.id, client)


def etat_source(session: Session, source: Source) -> dict:
    """Résumé affiché sur l'écran Connexions : dernière mise à jour réussie, retard éventuel."""
    dernier = session.scalar(select(Chargement).where(Chargement.source_id == source.id)
                             .order_by(Chargement.id.desc()).limit(1))
    dernier_ok = session.scalar(select(Chargement).where(Chargement.source_id == source.id, Chargement.statut == "chargé")
                                .order_by(Chargement.id.desc()).limit(1))
    nb_obs = session.scalar(select(func.count()).select_from(Observation)
                            .where(Observation.source_id == source.id, Observation.est_courante)) or 0
    en_retard = False
    if source.delai_alerte_jours and source.actif:
        reference = dernier_ok.termine_le if dernier_ok and dernier_ok.termine_le else None
        if reference is not None and reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        en_retard = reference is None or datetime.now(timezone.utc) - reference > timedelta(days=source.delai_alerte_jours)
    if dernier is None:
        statut = "jamais chargée"
    elif dernier.statut == "erreur":
        statut = "en erreur"
    elif dernier.statut in ("reçu", "en contrôle"):
        statut = "en attente" if dernier.statut == "en contrôle" else "en cours"
    elif en_retard:
        statut = "en retard"
    else:
        statut = "à jour"
    return {
        "code": source.code, "nom": source.nom, "mode": source.mode, "url": source.url, "actif": source.actif,
        "calendrier_cron": source.calendrier_cron, "delai_alerte_jours": source.delai_alerte_jours,
        "statut": statut, "en_retard": en_retard, "nb_observations": nb_obs,
        "derniere_maj_reussie": dernier_ok.termine_le.isoformat() if dernier_ok and dernier_ok.termine_le else None,
        "dernier_chargement": {"id": dernier.id, "statut": dernier.statut, "cree_le": dernier.cree_le.isoformat(),
                               "message": dernier.message} if dernier else None,
    }
