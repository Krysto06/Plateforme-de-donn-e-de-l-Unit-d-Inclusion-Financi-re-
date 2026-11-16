"""Espace direction : modèles Excel et dépôt de fichiers (phase 2, ouvert seulement sur le serveur BRH)."""
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.chargements import resume_chargement
from app.api.deps import ADMIN, CADRE, POINT_FOCAL, exiger
from app.config import get_settings
from app.connectors.base import ErreurSource, lire_tableau
from app.connectors.depot import ConnecteurDepot
from app.db import get_session
from app.models import Depot, Direction, Institution, TypeInstitution, Utilisateur
from app.quality.modeles import MODELES_DEPOT
from app.services import modeles_excel
from app.services.chargement import traiter_envoi
from app.services.journal import tracer

router = APIRouter(prefix="/api/depots", tags=["dépôts"])
deposant = exiger(POINT_FOCAL, ADMIN)
tous = exiger(POINT_FOCAL, ADMIN, CADRE)
TAILLE_MAX = 10 * 1024 * 1024
RE_PERIODE = re.compile(r"^(\d{4})(-T[1-4])?$")


def depot_dict(d: Depot) -> dict:
    return {
        "id": d.id, "direction": d.direction.nom, "type_institution": d.type_institution.libelle,
        "institution": d.institution.nom if d.institution else None, "type_donnees": d.type_donnees,
        "type_donnees_libelle": MODELES_DEPOT[d.type_donnees].libelle if d.type_donnees in MODELES_DEPOT else d.type_donnees,
        "version_modele": d.version_modele, "periode": d.periode, "fichier_nom": d.fichier_nom,
        "commentaire": d.commentaire, "statut": d.chargement.statut if d.chargement else d.statut,
        "auteur": d.auteur, "cree_le": d.cree_le.isoformat(), "chargement_id": d.chargement_id,
    }


@router.get("/parametres")
def parametres(session: Session = Depends(get_session), u: Utilisateur = Depends(tous)) -> dict:
    """Listes du formulaire de dépôt. Un point focal ne voit que sa direction."""
    directions = session.scalars(select(Direction).where(Direction.actif).order_by(Direction.nom))
    if u.role.code == POINT_FOCAL:
        directions = [u.direction] if u.direction else []
    return {
        "depots_ouverts": get_settings().depots_directions_ouverts,
        "directions": [{"id": d.id, "nom": d.nom} for d in directions],
        "types_institution": [{"id": t.id, "libelle": t.libelle} for t in session.scalars(select(TypeInstitution))],
        "institutions": [{"id": i.id, "nom": i.nom, "type_institution_id": i.type_institution_id}
                         for i in session.scalars(select(Institution).where(Institution.actif).order_by(Institution.nom))],
        "types_donnees": [{"code": m.code, "libelle": m.libelle, "version": m.version,
                           "indicateurs": list(m.indicateurs_autorises), "fichier": modeles_excel.nom_fichier(m)}
                          for m in MODELES_DEPOT.values()],
    }


@router.get("/modeles/{code}")
def telecharger_modele(code: str, session: Session = Depends(get_session), u: Utilisateur = Depends(tous)) -> Response:
    from app.quality.modeles import TOUS_LES_MODELES

    modele = TOUS_LES_MODELES.get(code)
    if modele is None or code == "standard":
        raise HTTPException(404, "Modèle inconnu.")
    return Response(modeles_excel.generer(modele, session),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{modeles_excel.nom_fichier(modele)}"'})


@router.get("")
def lister(session: Session = Depends(get_session), u: Utilisateur = Depends(tous)) -> list[dict]:
    requete = select(Depot).order_by(Depot.id.desc()).limit(200)
    if u.role.code == POINT_FOCAL:
        requete = requete.where(Depot.direction_id == u.direction_id)
    return [depot_dict(d) for d in session.scalars(requete)]


@router.post("", status_code=201)
async def deposer(
    direction_id: int = Form(...),
    type_institution_id: int = Form(...),
    institution_id: int | None = Form(None),
    type_donnees: str = Form(...),
    periode: str = Form(...),
    commentaire: str | None = Form(None),
    certifie_agrege: bool = Form(False),
    fichier: UploadFile = File(...),
    session: Session = Depends(get_session),
    u: Utilisateur = Depends(deposant),
) -> dict:
    if not get_settings().depots_directions_ouverts:
        raise HTTPException(403, "Le dépôt des directions n'est ouvert qu'une fois la plateforme hébergée "
                                 "sur un serveur de la BRH (DEPOTS_DIRECTIONS_OUVERTS=false).")
    if not certifie_agrege:
        raise HTTPException(422, "Cochez la case « données agrégées uniquement » pour déposer.")
    if u.role.code == POINT_FOCAL and direction_id != u.direction_id:
        raise HTTPException(403, "Vous ne pouvez déposer que pour votre direction.")
    if type_donnees not in MODELES_DEPOT:
        raise HTTPException(422, "Type de données inconnu.")
    if not RE_PERIODE.match(periode.strip()):
        raise HTTPException(422, "Période attendue : AAAA ou AAAA-T1 à AAAA-T4.")
    direction = session.get(Direction, direction_id)
    type_inst = session.get(TypeInstitution, type_institution_id)
    institution = session.get(Institution, institution_id) if institution_id else None
    if direction is None or type_inst is None or (institution_id and institution is None):
        raise HTTPException(422, "Direction, type d'institution ou institution inconnu.")
    if institution and institution.type_institution_id != type_inst.id:
        raise HTTPException(422, "L'institution choisie n'est pas de ce type.")

    contenu = await fichier.read()
    if len(contenu) > TAILLE_MAX:
        raise HTTPException(413, "Fichier trop volumineux (10 Mo au plus).")
    try:
        brut = lire_tableau(contenu, fichier.filename or "")
    except ErreurSource as exc:
        raise HTTPException(422, str(exc)) from exc

    connecteur = ConnecteurDepot(type_donnees, institution.nom if institution else None, periode.strip())
    depot = Depot(direction=direction, type_institution=type_inst, institution=institution, type_donnees=type_donnees,
                  version_modele=connecteur.modele.version, periode=periode.strip(), fichier_nom=fichier.filename or "",
                  commentaire=commentaire, certifie_agrege=True, auteur=u.identifiant)
    session.add(depot)
    session.flush()
    chargement = traiter_envoi(session, source_code=connecteur.code_source, df_brut=brut, modele=connecteur.modele,
                               normaliser=connecteur.normaliser, declencheur="manuel", auteur=u.identifiant,
                               fichier_nom=fichier.filename)
    depot.chargement_id = chargement.id
    depot.statut = chargement.statut
    tracer(session, u.identifiant, "dépôt", f"dépôt #{depot.id}", f"{direction.nom} — {type_donnees} — {periode}")
    session.commit()
    return {"depot": depot_dict(depot), "chargement": resume_chargement(chargement, avec_controles=True)}
