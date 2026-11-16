"""Référentiel des KPI (modifiable sans code), tableau de bord, séries et comparaisons."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import ADMIN, ESPACE_UIF, exiger
from app.config import get_settings
from app.db import get_session
from app.models import Departement, Indicateur, Observation, Pays, Periode, SerieSource, Source, Utilisateur
from app.services import calculs
from app.services.journal import tracer

router = APIRouter(prefix="/api", tags=["kpi"])
lecture = exiger(*ESPACE_UIF)
admin = exiger(ADMIN)


def kpi_dict(i: Indicateur) -> dict:
    return {
        "code": i.code, "libelle": i.libelle, "dimension": i.dimension, "unite": i.unite, "formule": i.formule,
        "calcul": i.calcul, "source_attendue": i.source_attendue, "source_preferee": i.source_preferee,
        "frequence": i.frequence, "phase": i.phase, "est_kpi": i.est_kpi, "additif": i.additif,
        "seuil_variation_pct": i.seuil_variation_pct, "actif": i.actif, "ordre": i.ordre,
        "series": [{"id": s.id, "source": s.source.code, "code_serie": s.code_serie, "sexe": s.sexe,
                    "verifie_le": s.verifie_le, "actif": s.actif} for s in i.series],
    }


class KpiEntree(BaseModel):
    code: str = Field(pattern=r"^[A-Z]{2,4}-[A-Z0-9]{1,4}$")
    libelle: str = Field(min_length=3)
    dimension: str
    unite: str
    formule: str | None = None
    calcul: str | None = None
    source_attendue: str | None = None
    source_preferee: str | None = None
    frequence: str = "annuelle"
    phase: int = 1
    est_kpi: bool = True
    additif: bool = False
    seuil_variation_pct: float = Field(default=50.0, gt=0)
    actif: bool = True
    ordre: int = 0


class KpiModification(BaseModel):
    libelle: str | None = None
    dimension: str | None = None
    unite: str | None = None
    formule: str | None = None
    calcul: str | None = None
    source_attendue: str | None = None
    source_preferee: str | None = None
    frequence: str | None = None
    phase: int | None = None
    est_kpi: bool | None = None
    additif: bool | None = None
    seuil_variation_pct: float | None = Field(default=None, gt=0)
    actif: bool | None = None
    ordre: int | None = None


class SerieEntree(BaseModel):
    source: str
    code_serie: str
    sexe: str = Field(default="Total", pattern="^(F|H|Total)$")
    verifie_le: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Date de vérification par l'API (règle 3)")


def _verifier_calcul(calcul: str | None) -> None:
    if calcul:
        try:
            calculs.evaluer(calcul, {ref: 1.0 for ref in calculs.references(calcul)})
        except calculs.FormuleInvalide as exc:
            raise HTTPException(422, str(exc)) from exc


def _kpi(session: Session, code: str) -> Indicateur:
    ind = session.scalar(select(Indicateur).where(Indicateur.code == code))
    if ind is None:
        raise HTTPException(404, f"KPI {code} introuvable.")
    return ind


@router.get("/kpi")
def lister_kpi(tous: bool = False, session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> list[dict]:
    requete = select(Indicateur).order_by(Indicateur.ordre, Indicateur.code)
    if not tous:
        requete = requete.where(Indicateur.actif)
    return [kpi_dict(i) for i in session.scalars(requete)]


@router.post("/kpi", status_code=201)
def creer_kpi(donnees: KpiEntree, session: Session = Depends(get_session), u: Utilisateur = Depends(admin)) -> dict:
    if session.scalar(select(Indicateur).where(Indicateur.code == donnees.code)):
        raise HTTPException(409, f"Le code {donnees.code} existe déjà.")
    _verifier_calcul(donnees.calcul)
    ind = Indicateur(**donnees.model_dump())
    session.add(ind)
    tracer(session, u.identifiant, "kpi:création", donnees.code)
    session.commit()
    return kpi_dict(ind)


@router.patch("/kpi/{code}")
def modifier_kpi(code: str, donnees: KpiModification, session: Session = Depends(get_session),
                 u: Utilisateur = Depends(admin)) -> dict:
    ind = _kpi(session, code)
    changements = donnees.model_dump(exclude_unset=True)
    _verifier_calcul(changements.get("calcul"))
    for k, v in changements.items():
        setattr(ind, k, v)
    tracer(session, u.identifiant, "kpi:modification", code, str(changements))
    session.commit()
    return kpi_dict(ind)


@router.delete("/kpi/{code}")
def retirer_kpi(code: str, session: Session = Depends(get_session), u: Utilisateur = Depends(admin)) -> dict:
    """Retire un KPI du référentiel actif. Ses valeurs restent en base (traçabilité)."""
    ind = _kpi(session, code)
    ind.actif = False
    tracer(session, u.identifiant, "kpi:retrait", code)
    session.commit()
    return kpi_dict(ind)


@router.post("/kpi/{code}/series", status_code=201)
def ajouter_serie(code: str, donnees: SerieEntree, session: Session = Depends(get_session),
                  u: Utilisateur = Depends(admin)) -> dict:
    ind = _kpi(session, code)
    source = session.scalar(select(Source).where(Source.code == donnees.source))
    if source is None:
        raise HTTPException(404, "Source inconnue.")
    ind.series.append(SerieSource(source=source, code_serie=donnees.code_serie, sexe=donnees.sexe,
                                  verifie_le=donnees.verifie_le))
    tracer(session, u.identifiant, "kpi:série", code, f"{donnees.source} {donnees.code_serie}")
    session.commit()
    return kpi_dict(ind)


# ------------------------------------------------------------------ Lecture des valeurs


def _requete_obs():
    return (select(Observation.valeur, Indicateur.code, Pays.code_iso3, Pays.nom, Periode.annee, Periode.trimestre,
                   Source.code.label("source"), Source.nom.label("source_nom"), Observation.sexe,
                   Observation.chargement_id, Departement.code.label("departement"))
            .join(Indicateur, Observation.indicateur_id == Indicateur.id)
            .join(Pays, Observation.pays_id == Pays.id)
            .join(Periode, Observation.periode_id == Periode.id)
            .join(Source, Observation.source_id == Source.id)
            .outerjoin(Departement, Observation.departement_id == Departement.id)
            .where(Observation.est_courante, Observation.institution_id.is_(None)))


def _filtrer_dep(requete, departement: str | None):
    if departement:
        return requete.where(Departement.code == departement)
    return requete.where(Observation.departement_id.is_(None))


def anciennete(annee: int | None) -> dict:
    if annee is None:
        return {"code": "a_collecter", "libelle": "À collecter"}
    ecart = date.today().year - annee
    if ecart <= 1:
        return {"code": "recente", "libelle": f"Donnée de {annee}"}
    if ecart <= 3:
        return {"code": "a_surveiller", "libelle": f"Donnée de {annee}"}
    return {"code": "ancienne", "libelle": f"Donnée de {annee} ({ecart} ans)"}


@router.get("/tableau-de-bord")
def tableau_de_bord(annee: int | None = None, departement: str | None = None,
                    sexe: str = Query("Total", pattern="^(F|H|Total)$"),
                    session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> dict:
    pays = get_settings().pays_principal
    cartes = []
    for ind in session.scalars(select(Indicateur).where(Indicateur.actif, Indicateur.est_kpi).order_by(Indicateur.ordre)):
        requete = _filtrer_dep(_requete_obs().where(Indicateur.id == ind.id, Pays.code_iso3 == pays,
                                                    Observation.sexe == sexe), departement)
        if annee:
            requete = requete.where(Periode.annee <= annee)
        lignes = session.execute(requete.order_by(Periode.annee.desc(), Periode.trimestre.desc())).all()
        if lignes:
            plus_recente = lignes[0].annee
            candidates = [l for l in lignes if l.annee == plus_recente]
            choisie = next((l for l in candidates if l.source == ind.source_preferee), candidates[0])
            autres = [{"source": l.source, "valeur": l.valeur} for l in candidates if l is not choisie]
        else:
            choisie, autres = None, []
        cartes.append({
            "code": ind.code, "libelle": ind.libelle, "dimension": ind.dimension, "unite": ind.unite,
            "phase": ind.phase, "source_attendue": ind.source_attendue,
            "valeur": choisie.valeur if choisie else None,
            "annee": choisie.annee if choisie else None,
            "source": choisie.source if choisie else None,
            "source_nom": choisie.source_nom if choisie else None,
            "chargement_id": choisie.chargement_id if choisie else None,
            "autres_sources": autres,
            "anciennete": anciennete(choisie.annee if choisie else None),
        })
    disponibles = sum(1 for c in cartes if c["valeur"] is not None)
    return {"pays": pays, "filtres": {"annee": annee, "departement": departement, "sexe": sexe},
            "resume": {"kpi_total": len(cartes), "kpi_disponibles": disponibles}, "cartes": cartes}


@router.get("/kpi/{code}/serie")
def serie(code: str, pays: str | None = None, departement: str | None = None,
          sexe: str = Query("Total", pattern="^(F|H|Total)$"),
          session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> dict:
    ind = _kpi(session, code)
    pays = pays or get_settings().pays_principal
    requete = _filtrer_dep(_requete_obs().where(Indicateur.id == ind.id, Pays.code_iso3 == pays,
                                                Observation.sexe == sexe), departement)
    lignes = session.execute(requete.order_by(Periode.annee, Periode.trimestre)).all()
    return {"code": code, "libelle": ind.libelle, "unite": ind.unite, "pays": pays,
            "points": [{"annee": l.annee, "trimestre": l.trimestre, "valeur": l.valeur, "source": l.source,
                        "chargement_id": l.chargement_id} for l in lignes]}


@router.get("/kpi/{code}/comparaison")
def comparaison(code: str, annee: int | None = None, source: str | None = None,
                session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> dict:
    """Dernière valeur de chaque pays suivi pour une même source (pour comparer ce qui est comparable)."""
    ind = _kpi(session, code)
    reglages = get_settings()
    requete = _requete_obs().where(Indicateur.id == ind.id, Observation.sexe == "Total",
                                   Observation.departement_id.is_(None), Pays.code_iso3.in_(reglages.tous_les_pays))
    lignes = session.execute(requete).all()
    sources = sorted({l.source for l in lignes})
    if not sources:
        return {"code": code, "libelle": ind.libelle, "unite": ind.unite, "source": None, "annee": None, "pays": []}
    choix = source if source in sources else ("WB" if "WB" in sources else (ind.source_preferee if ind.source_preferee in sources else sources[0]))
    lignes = [l for l in lignes if l.source == choix and (annee is None or l.annee <= annee)]
    derniere: dict[str, object] = {}
    for l in lignes:
        if l.code_iso3 not in derniere or l.annee > derniere[l.code_iso3].annee:
            derniere[l.code_iso3] = l
    pays = sorted(({"pays": l.code_iso3, "nom": l.nom, "annee": l.annee, "valeur": l.valeur,
                    "principal": l.code_iso3 == reglages.pays_principal} for l in derniere.values()),
                  key=lambda p: p["valeur"])
    return {"code": code, "libelle": ind.libelle, "unite": ind.unite, "source": choix, "sources_disponibles": sources,
            "annee": max((p["annee"] for p in pays), default=None), "pays": pays}


@router.get("/catalogue")
def catalogue(session: Session = Depends(get_session), u: Utilisateur = Depends(lecture)) -> list[dict]:
    """Ce que contient l'entrepôt : pour chaque indicateur, sources, pays, années couvertes et nombre de valeurs."""
    stats = session.execute(
        select(Indicateur.code, Source.code, func.count(), func.min(Periode.annee), func.max(Periode.annee),
               func.count(func.distinct(Observation.pays_id)))
        .join(Indicateur, Observation.indicateur_id == Indicateur.id)
        .join(Source, Observation.source_id == Source.id)
        .join(Periode, Observation.periode_id == Periode.id)
        .where(Observation.est_courante)
        .group_by(Indicateur.code, Source.code)
    ).all()
    par_code: dict[str, list] = {}
    for code, src, nb, amin, amax, npays in stats:
        par_code.setdefault(code, []).append({"source": src, "nb_valeurs": nb, "annee_min": amin, "annee_max": amax,
                                              "nb_pays": npays})
    resultat = []
    for i in session.scalars(select(Indicateur).order_by(Indicateur.ordre)):
        d = kpi_dict(i)
        d["couverture"] = par_code.get(i.code, [])
        d["nb_valeurs"] = sum(c["nb_valeurs"] for c in d["couverture"])
        resultat.append(d)
    return resultat
