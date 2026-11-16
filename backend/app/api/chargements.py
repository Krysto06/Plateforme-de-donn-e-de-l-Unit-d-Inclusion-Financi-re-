"""Chargements et contrôle qualité : liste, détail (résultat de chaque règle), décision humaine."""
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, ESPACE_UIF, exiger
from app.db import get_session
from app.models import Chargement, Depot, Source, Utilisateur
from app.services.chargement import decider

router = APIRouter(prefix="/api/chargements", tags=["contrôle qualité"])
lecture = exiger(*ESPACE_UIF)
admin = exiger(ADMIN)


def resume_chargement(c: Chargement, avec_controles: bool = False, apercu: int = 0) -> dict:
    d = {
        "id": c.id, "source": c.source.code, "source_nom": c.source.nom, "cree_le": c.cree_le.isoformat(),
        "termine_le": c.termine_le.isoformat() if c.termine_le else None, "declencheur": c.declencheur,
        "auteur": c.auteur, "fichier_nom": c.fichier_nom, "nb_lignes": c.nb_lignes, "nb_nouvelles": c.nb_nouvelles,
        "nb_modifiees": c.nb_modifiees, "nb_inchangees": c.nb_inchangees, "statut": c.statut, "message": c.message,
        "decision_par": c.decision_par, "decision_le": c.decision_le.isoformat() if c.decision_le else None,
        "decision_commentaire": c.decision_commentaire,
        "attend_validation": c.statut == "en contrôle" and bool(c.donnees_json),
    }
    if avec_controles:
        d["controles"] = [{"regle": k.regle, "resultat": k.resultat, "detail": k.detail} for k in c.controles]
    if apercu and c.donnees_json:
        lignes = json.loads(c.donnees_json)
        d["apercu"] = lignes[:apercu]
        d["nb_valeurs_en_attente"] = len(lignes)
    return d


class Decision(BaseModel):
    decision: Literal["accepter", "renvoyer"]
    commentaire: str | None = None


@router.get("")
def lister(statut: str | None = None, source: str | None = None, session: Session = Depends(get_session),
           u: Utilisateur = Depends(lecture)) -> list[dict]:
    requete = select(Chargement).order_by(Chargement.id.desc()).limit(200)
    if statut:
        requete = requete.where(Chargement.statut == statut)
    if source:
        requete = requete.join(Source).where(Source.code == source.upper())
    return [resume_chargement(c) for c in session.scalars(requete)]


@router.get("/{chargement_id}")
def detail(chargement_id: int, session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> dict:
    c = session.get(Chargement, chargement_id)
    if c is None:
        raise HTTPException(404, "Chargement introuvable.")
    d = resume_chargement(c, avec_controles=True, apercu=50)
    depot = session.scalar(select(Depot).where(Depot.chargement_id == c.id))
    if depot:
        d["depot"] = {"id": depot.id, "direction": depot.direction.nom, "type_donnees": depot.type_donnees,
                      "periode": depot.periode, "institution": depot.institution.nom if depot.institution else None,
                      "commentaire": depot.commentaire}
    return d


@router.post("/{chargement_id}/decision")
def prendre_decision(chargement_id: int, donnees: Decision, session: Session = Depends(get_session),
                     u: Utilisateur = Depends(admin)) -> dict:
    c = session.get(Chargement, chargement_id)
    if c is None:
        raise HTTPException(404, "Chargement introuvable.")
    try:
        decider(session, c, donnees.decision, donnees.commentaire, u.identifiant)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    depot = session.scalar(select(Depot).where(Depot.chargement_id == c.id))
    if depot:
        depot.statut = c.statut
        session.commit()
    return resume_chargement(c, avec_controles=True)
