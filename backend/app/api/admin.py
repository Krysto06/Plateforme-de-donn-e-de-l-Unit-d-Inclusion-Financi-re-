"""Administration : référentiels (directions, institutions), utilisateurs, journal."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, ESPACE_UIF, exiger
from app.db import get_session
from app.models import Departement, Direction, Institution, Journal, Pays, TypeInstitution, Utilisateur
from app.services.journal import tracer

router = APIRouter(prefix="/api", tags=["administration"])
lecture = exiger(*ESPACE_UIF)
admin = exiger(ADMIN)


@router.get("/referentiels")
def referentiels(session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> dict:
    return {
        "pays": [{"code": p.code_iso3, "nom": p.nom, "region": p.region} for p in session.scalars(select(Pays))],
        "departements": [{"code": d.code, "nom": d.nom} for d in session.scalars(select(Departement).order_by(Departement.nom))],
        "directions": [{"id": d.id, "code": d.code, "nom": d.nom, "actif": d.actif} for d in session.scalars(select(Direction))],
        "types_institution": [{"id": t.id, "code": t.code, "libelle": t.libelle} for t in session.scalars(select(TypeInstitution))],
        "institutions": [{"id": i.id, "nom": i.nom, "type": i.type_institution.code, "actif": i.actif}
                         for i in session.scalars(select(Institution))],
    }


class DirectionEntree(BaseModel):
    code: str = Field(min_length=2, max_length=20)
    nom: str = Field(min_length=3)


class InstitutionEntree(BaseModel):
    nom: str = Field(min_length=2)
    type_institution: str


@router.post("/directions", status_code=201)
def creer_direction(d: DirectionEntree, session: Session = Depends(get_session), u: Utilisateur = Depends(admin)) -> dict:
    if session.scalar(select(Direction).where(Direction.code == d.code)):
        raise HTTPException(409, "Ce code de direction existe déjà.")
    direction = Direction(code=d.code, nom=d.nom)
    session.add(direction)
    tracer(session, u.identifiant, "direction:création", d.code)
    session.commit()
    return {"id": direction.id, "code": direction.code, "nom": direction.nom}


@router.post("/institutions", status_code=201)
def creer_institution(d: InstitutionEntree, session: Session = Depends(get_session), u: Utilisateur = Depends(admin)) -> dict:
    t = session.scalar(select(TypeInstitution).where(TypeInstitution.code == d.type_institution))
    if t is None:
        raise HTTPException(422, "Type d'institution inconnu.")
    if session.scalar(select(Institution).where(Institution.nom == d.nom)):
        raise HTTPException(409, "Cette institution existe déjà.")
    inst = Institution(nom=d.nom, type_institution=t)
    session.add(inst)
    tracer(session, u.identifiant, "institution:création", d.nom)
    session.commit()
    return {"id": inst.id, "nom": inst.nom, "type": t.code}


class UtilisateurEntree(BaseModel):
    identifiant: str = Field(min_length=3)
    nom: str
    role: str = Field(pattern="^(admin_uif|cadre_uif|point_focal)$")
    mot_de_passe: str
    direction_code: str | None = None


@router.get("/utilisateurs")
def lister_utilisateurs(session: Session = Depends(get_session), u: Utilisateur = Depends(admin)) -> list[dict]:
    return [{"identifiant": x.identifiant, "nom": x.nom, "role": x.role.code, "actif": x.actif,
             "direction": x.direction.nom if x.direction else None} for x in session.scalars(select(Utilisateur))]


@router.post("/utilisateurs", status_code=201)
def creer_utilisateur(d: UtilisateurEntree, session: Session = Depends(get_session), u: Utilisateur = Depends(admin)) -> dict:
    from app.services.comptes import creer_compte

    try:
        compte = creer_compte(session, d.identifiant, d.nom, d.role, d.mot_de_passe, d.direction_code, auteur=u.identifiant)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"identifiant": compte.identifiant, "role": compte.role.code}


@router.get("/journal")
def journal(limite: int = 200, session: Session = Depends(get_session), u: Utilisateur = Depends(admin)) -> list[dict]:
    return [{"horodatage": j.horodatage.isoformat(), "utilisateur": j.utilisateur, "action": j.action,
             "objet": j.objet, "detail": j.detail}
            for j in session.scalars(select(Journal).order_by(Journal.id.desc()).limit(min(limite, 1000)))]
