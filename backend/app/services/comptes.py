"""Création des comptes utilisateurs (API et ligne de commande)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Direction, Role, Utilisateur
from app.services.journal import tracer
from app.services.securite import hacher_mot_de_passe, mot_de_passe_acceptable


def creer_compte(session: Session, identifiant: str, nom: str, role: str, mot_de_passe: str,
                 direction_code: str | None = None, auteur: str = "système") -> Utilisateur:
    identifiant = identifiant.strip().lower()
    if session.scalar(select(Utilisateur).where(Utilisateur.identifiant == identifiant)):
        raise ValueError("Cet identifiant existe déjà.")
    probleme = mot_de_passe_acceptable(mot_de_passe)
    if probleme:
        raise ValueError(probleme)
    role_obj = session.scalar(select(Role).where(Role.code == role))
    if role_obj is None:
        raise ValueError(f"Rôle inconnu : {role}. Lancer d'abord « python -m app.cli init ».")
    direction = None
    if role == "point_focal":
        direction = session.scalar(select(Direction).where(Direction.code == direction_code)) if direction_code else None
        if direction is None:
            raise ValueError("Un point focal doit être rattaché à une direction existante (direction_code).")
    compte = Utilisateur(identifiant=identifiant, nom=nom, role=role_obj, direction=direction,
                         mot_de_passe_hash=hacher_mot_de_passe(mot_de_passe))
    session.add(compte)
    tracer(session, auteur, "utilisateur:création", identifiant, role)
    session.commit()
    return compte
