"""Chargement initial des référentiels (KPI, sources, pays, départements...) depuis app/data/*.csv.

Par défaut, on n'ajoute que ce qui manque : les modifications faites ensuite dans l'interface ne sont pas écrasées.
Avec forcer=True, les valeurs des fichiers CSV remplacent celles de la base.
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Departement, Indicateur, Pays, Role, SerieSource, Source, TypeInstitution
from app.services.journal import tracer

DOSSIER = Path(__file__).resolve().parent.parent / "data"

ROLES = {
    "admin_uif": "Administratrice UIF",
    "cadre_uif": "Cadre UIF (lecture)",
    "point_focal": "Point focal de direction (dépôt)",
}


def lire_csv(nom: str) -> list[dict]:
    df = pd.read_csv(DOSSIER / nom, sep=";", dtype=str, keep_default_na=False)
    return [{k: (v if v != "" else None) for k, v in ligne.items()} for ligne in df.to_dict(orient="records")]


def _upsert(session: Session, modele, champ_cle: str, lignes: list[dict], forcer: bool, conversions=None) -> tuple[int, int]:
    ajoutes = modifies = 0
    for ligne in lignes:
        if conversions:
            ligne = {k: conversions.get(k, lambda v: v)(v) for k, v in ligne.items()}
        existant = session.scalar(select(modele).where(getattr(modele, champ_cle) == ligne[champ_cle]))
        if existant is None:
            session.add(modele(**ligne))
            ajoutes += 1
        elif forcer:
            for k, v in ligne.items():
                setattr(existant, k, v)
            modifies += 1
    session.flush()
    return ajoutes, modifies


def _bool(v):
    return str(v).strip() in ("1", "true", "True", "oui")


def charger_referentiel(session: Session, forcer: bool = False, auteur: str = "système") -> dict[str, tuple[int, int]]:
    bilan = {
        "roles": _upsert(session, Role, "code", [{"code": c, "libelle": l} for c, l in ROLES.items()], forcer),
        "pays": _upsert(session, Pays, "code_iso3", lire_csv("pays.csv"), forcer),
        "departements": _upsert(session, Departement, "code", lire_csv("departements.csv"), forcer),
        "types_institution": _upsert(session, TypeInstitution, "code", lire_csv("types_institution.csv"), forcer),
        "sources": _upsert(session, Source, "code", lire_csv("sources.csv"), forcer,
                           {"delai_alerte_jours": lambda v: int(v) if v else None}),
        "indicateurs": _upsert(session, Indicateur, "code", lire_csv("indicateurs.csv"), forcer, {
            "phase": int, "ordre": int, "seuil_variation_pct": float, "est_kpi": _bool, "additif": _bool,
        }),
    }
    # Correspondances indicateur ↔ code de série chez la source
    ajoutes = 0
    indicateurs = {i.code: i for i in session.scalars(select(Indicateur))}
    sources = {s.code: s for s in session.scalars(select(Source))}
    for l in lire_csv("series_sources.csv"):
        src = sources[l["source"]]
        existe = session.scalar(select(SerieSource).where(SerieSource.source_id == src.id,
                                                          SerieSource.code_serie == l["code_serie"]))
        if existe is None:
            session.add(SerieSource(indicateur=indicateurs[l["indicateur"]], source=src, code_serie=l["code_serie"],
                                    sexe=l["sexe"], verifie_le=l["verifie_le"]))
            ajoutes += 1
    bilan["series_sources"] = (ajoutes, 0)
    tracer(session, auteur, "referentiel:chargement", None, str(bilan))
    session.commit()
    return bilan
