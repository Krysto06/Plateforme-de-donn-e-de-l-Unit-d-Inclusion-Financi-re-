"""Sources et connexions : état, test, mise à jour, historique, import IHSI."""
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.chargements import resume_chargement
from app.api.deps import ADMIN, ESPACE_UIF, exiger
from app.connectors.base import ErreurSource, lire_tableau
from app.connectors.ihsi import ConnecteurIHSI
from app.db import SessionLocal, get_session
from app.models import Chargement, Source, Utilisateur
from app.services.chargement import traiter_envoi
from app.services.journal import tracer
from app.services.mises_a_jour import CONNECTEURS_API, connecteur_api, etat_source, executer, preparer_chargement

router = APIRouter(prefix="/api/sources", tags=["sources"])
lecture = exiger(*ESPACE_UIF)
admin = exiger(ADMIN)
TAILLE_MAX = 10 * 1024 * 1024  # 10 Mo


def _source(session: Session, code: str) -> Source:
    source = session.scalar(select(Source).where(Source.code == code.upper()))
    if source is None:
        raise HTTPException(404, f"Source {code} introuvable.")
    return source


@router.get("")
def lister(session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> list[dict]:
    return [etat_source(session, s) for s in session.scalars(select(Source).order_by(Source.id))]


@router.get("/{code}")
def detail(code: str, session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> dict:
    return etat_source(session, _source(session, code))


@router.post("/{code}/tester")
def tester(code: str, session: Session = Depends(get_session), u: Utilisateur = Depends(admin)) -> dict:
    source = _source(session, code)
    if source.code not in CONNECTEURS_API:
        raise HTTPException(400, "Cette source se charge par fichier : pas de connexion à tester.")
    resultat = connecteur_api(source.code, session).tester()
    tracer(session, u.identifiant, "source:test", source.code, resultat.message)
    session.commit()
    return {"ok": resultat.ok, "message": resultat.message, "details": resultat.details}


def _executer_en_arriere_plan(chargement_id: int) -> None:
    with SessionLocal() as session:
        executer(session, chargement_id)


@router.post("/{code}/mettre-a-jour", status_code=202)
def mettre_a_jour(code: str, taches: BackgroundTasks, session: Session = Depends(get_session),
                  u: Utilisateur = Depends(admin)) -> dict:
    """Lance la mise à jour ; elle continue en arrière-plan (l'API de la Banque mondiale peut être lente)."""
    source = _source(session, code)
    if source.code not in CONNECTEURS_API:
        raise HTTPException(400, "Cette source se charge par fichier : utiliser l'import.")
    en_cours = session.scalar(select(Chargement).where(Chargement.source_id == source.id, Chargement.statut == "reçu"))
    if en_cours:
        raise HTTPException(409, f"Une mise à jour est déjà en cours (chargement #{en_cours.id}).")
    chargement = preparer_chargement(session, source.code, "manuel", u.identifiant)
    taches.add_task(_executer_en_arriere_plan, chargement.id)
    return {"chargement_id": chargement.id, "statut": chargement.statut}


@router.get("/{code}/historique")
def historique(code: str, session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> list[dict]:
    source = _source(session, code)
    return [resume_chargement(c) for c in session.scalars(
        select(Chargement).where(Chargement.source_id == source.id).order_by(Chargement.id.desc()).limit(50))]


@router.post("/IHSI/import", status_code=201)
async def importer_ihsi(fichier: UploadFile = File(...), session: Session = Depends(get_session),
                        u: Utilisateur = Depends(admin)) -> dict:
    contenu = await fichier.read()
    if len(contenu) > TAILLE_MAX:
        raise HTTPException(413, "Fichier trop volumineux (10 Mo au plus).")
    try:
        brut = lire_tableau(contenu, fichier.filename or "")
    except ErreurSource as exc:
        raise HTTPException(422, str(exc)) from exc
    connecteur = ConnecteurIHSI()
    chargement = traiter_envoi(session, source_code="IHSI", df_brut=brut, modele=connecteur.modele,
                               normaliser=connecteur.normaliser, declencheur="manuel", auteur=u.identifiant,
                               fichier_nom=fichier.filename)
    return resume_chargement(chargement, avec_controles=True)
