"""Dépendances communes des routes : session de base, utilisateur connecté, contrôle des rôles."""
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Utilisateur
from app.services.securite import lire_jeton

_bearer = HTTPBearer(auto_error=False)

ADMIN, CADRE, POINT_FOCAL = "admin_uif", "cadre_uif", "point_focal"
ESPACE_UIF = (ADMIN, CADRE)


def utilisateur_courant(
    jeton: HTTPAuthorizationCredentials | None = Depends(_bearer), session: Session = Depends(get_session)
) -> Utilisateur:
    erreur = HTTPException(status.HTTP_401_UNAUTHORIZED, "Session absente ou expirée : reconnectez-vous.",
                           headers={"WWW-Authenticate": "Bearer"})
    if jeton is None:
        raise erreur
    contenu = lire_jeton(jeton.credentials)
    if not contenu:
        raise erreur
    utilisateur = session.scalar(select(Utilisateur).where(Utilisateur.identifiant == contenu["sub"]))
    if utilisateur is None or not utilisateur.actif:
        raise erreur
    return utilisateur


def exiger(*roles: str) -> Callable[..., Utilisateur]:
    def verifier(utilisateur: Utilisateur = Depends(utilisateur_courant)) -> Utilisateur:
        if utilisateur.role.code not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Votre rôle ne donne pas accès à cette fonction.")
        return utilisateur

    return verifier
