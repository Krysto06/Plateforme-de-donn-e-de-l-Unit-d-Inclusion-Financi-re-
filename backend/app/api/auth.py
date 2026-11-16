"""Connexion et profil de l'utilisateur connecté."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import utilisateur_courant
from app.db import get_session
from app.models import Utilisateur
from app.services.journal import tracer
from app.services.securite import creer_jeton, verifier_mot_de_passe

router = APIRouter(prefix="/api/auth", tags=["authentification"])


class Identifiants(BaseModel):
    identifiant: str
    mot_de_passe: str


def profil(u: Utilisateur) -> dict:
    return {
        "identifiant": u.identifiant, "nom": u.nom, "role": u.role.code, "role_libelle": u.role.libelle,
        "espace": "direction" if u.role.code == "point_focal" else "uif",
        "direction": {"id": u.direction.id, "nom": u.direction.nom} if u.direction else None,
    }


@router.post("/connexion")
def connexion(donnees: Identifiants, session: Session = Depends(get_session)) -> dict:
    u = session.scalar(select(Utilisateur).where(Utilisateur.identifiant == donnees.identifiant.strip().lower()))
    if u is None or not u.actif or not verifier_mot_de_passe(donnees.mot_de_passe, u.mot_de_passe_hash):
        tracer(session, donnees.identifiant[:120], "connexion:échec")
        session.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiant ou mot de passe incorrect.")
    tracer(session, u.identifiant, "connexion")
    session.commit()
    return {"jeton": creer_jeton(u.identifiant, u.role.code), "utilisateur": profil(u)}


@router.get("/moi")
def moi(u: Utilisateur = Depends(utilisateur_courant)) -> dict:
    return profil(u)
