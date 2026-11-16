"""Export des données PUBLIQUES de la base vers des fichiers JSON, pour le mode démonstration de l'interface
(visualisation sur StackBlitz ou Netlify, sans serveur). Refuse d'exporter si la base contient des données
de directions ou de l'UIF (règle n° 1 : rien de la BRH hors de ses serveurs)."""
import io
import json
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api import chargements as api_chargements
from app.api import kpi as api_kpi
from app.api.depots import parametres
from app.api.exports import tableau_observations
from app.models import Chargement, Indicateur, Observation, Source
from app.services.mises_a_jour import etat_source

SOURCES_PUBLIQUES = {"WB", "FMI"}


def _ecrire(dossier: Path, nom: str, contenu) -> Path:
    chemin = dossier / nom
    chemin.write_text(json.dumps(contenu, ensure_ascii=False, default=str), encoding="utf-8")
    return chemin


def exporter_demo(session: Session, dossier: Path) -> list[Path]:
    non_publiques = session.scalar(select(func.count()).select_from(Observation).join(Source)
                                   .where(Source.code.not_in(SOURCES_PUBLIQUES)))
    if non_publiques:
        raise SystemExit(f"Refus : la base contient {non_publiques} valeurs hors FMI et Banque mondiale. "
                         "Le mode démonstration ne doit contenir que des données publiques.")
    dossier.mkdir(parents=True, exist_ok=True)
    for ancien in dossier.glob("*"):
        ancien.unlink()
    ecrits = [
        _ecrire(dossier, "info.json", {"date_donnees": date.today().isoformat()}),
        _ecrire(dossier, "tableau-de-bord.json", api_kpi.tableau_de_bord(annee=None, departement=None, sexe="Total", session=session, u=None)),
        _ecrire(dossier, "kpi.json", api_kpi.lister_kpi(tous=False, session=session, u=None)),
        _ecrire(dossier, "catalogue.json", api_kpi.catalogue(session=session, u=None)),
        _ecrire(dossier, "sources.json", [etat_source(session, s) for s in session.scalars(select(Source).order_by(Source.id))]),
        _ecrire(dossier, "chargements.json", api_chargements.lister(statut=None, source=None, session=session, u=None)),
    ]
    from app.api.admin import referentiels

    ref = referentiels(session=session, u=None)
    ref["directions"], ref["institutions"] = [], []  # rien des directions dans la démonstration
    ecrits.append(_ecrire(dossier, "referentiels.json", ref))
    p = parametres(session=session, u=type("Visiteur", (), {"role": type("R", (), {"code": "cadre_uif"})()})())
    p.update({"depots_ouverts": False, "directions": [], "institutions": []})
    ecrits.append(_ecrire(dossier, "depots-parametres.json", p))
    ecrits.append(_ecrire(dossier, "depots.json", []))
    for code in session.scalars(select(Source.code)):
        ecrits.append(_ecrire(dossier, f"historique-{code}.json", [
            api_chargements.resume_chargement(c) for c in session.scalars(
                select(Chargement).join(Source).where(Source.code == code).order_by(Chargement.id.desc()))]))
    for c in session.scalars(select(Chargement)):
        ecrits.append(_ecrire(dossier, f"chargement-{c.id}.json", api_chargements.detail(c.id, session=session, u=None)))
    for code in session.scalars(select(Indicateur.code).where(Indicateur.actif)):
        ecrits.append(_ecrire(dossier, f"serie-{code}.json", api_kpi.serie(code, pays=None, departement=None, sexe="Total", session=session, u=None)))
        ecrits.append(_ecrire(dossier, f"comparaison-{code}.json", api_kpi.comparaison(code, annee=None, source=None, session=session, u=None)))
    df = tableau_observations(session, None, None, None, None, avec_auxiliaires=False)
    (dossier / "pdif_observations.csv").write_bytes(df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"))
    flux = io.BytesIO()
    df.to_excel(flux, index=False, sheet_name="Observations")
    (dossier / "pdif_observations.xlsx").write_bytes(flux.getvalue())
    ecrits += [dossier / "pdif_observations.csv", dossier / "pdif_observations.xlsx"]
    return ecrits
