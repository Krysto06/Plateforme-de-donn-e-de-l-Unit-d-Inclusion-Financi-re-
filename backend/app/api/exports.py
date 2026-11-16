"""Rapports et exports (CSV et Excel) des valeurs courantes, avec leur traçabilité."""
import io
from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ESPACE_UIF, exiger
from app.db import get_session
from app.models import Chargement, Departement, Indicateur, Observation, Pays, Periode, Source, Utilisateur

router = APIRouter(prefix="/api/exports", tags=["exports"])
lecture = exiger(*ESPACE_UIF)


def tableau_observations(session: Session, indicateurs: list[str] | None, pays: list[str] | None,
                         annee_debut: int | None, annee_fin: int | None, avec_auxiliaires: bool) -> pd.DataFrame:
    requete = (
        select(Indicateur.code.label("code_kpi"), Indicateur.libelle.label("indicateur"), Indicateur.unite,
               Pays.code_iso3.label("pays"), Departement.code.label("departement"), Observation.sexe,
               Periode.annee, Periode.trimestre, Observation.valeur, Source.code.label("source"),
               Observation.version, Observation.chargement_id, Chargement.termine_le.label("charge_le"))
        .join(Indicateur, Observation.indicateur_id == Indicateur.id)
        .join(Pays, Observation.pays_id == Pays.id)
        .join(Periode, Observation.periode_id == Periode.id)
        .join(Source, Observation.source_id == Source.id)
        .join(Chargement, Observation.chargement_id == Chargement.id)
        .outerjoin(Departement, Observation.departement_id == Departement.id)
        .where(Observation.est_courante)
        .order_by(Indicateur.ordre, Pays.code_iso3, Periode.annee, Source.code)
    )
    if indicateurs:
        requete = requete.where(Indicateur.code.in_(indicateurs))
    if not avec_auxiliaires:
        requete = requete.where(Indicateur.est_kpi)
    if pays:
        requete = requete.where(Pays.code_iso3.in_(pays))
    if annee_debut:
        requete = requete.where(Periode.annee >= annee_debut)
    if annee_fin:
        requete = requete.where(Periode.annee <= annee_fin)
    df = pd.DataFrame(session.execute(requete).mappings().all())
    if df.empty:
        df = pd.DataFrame(columns=["code_kpi", "indicateur", "unite", "pays", "departement", "sexe", "annee", "trimestre",
                                   "valeur", "source", "version", "chargement_id", "charge_le"])
    if "charge_le" in df and not df.empty:
        df["charge_le"] = pd.to_datetime(df["charge_le"]).dt.strftime("%Y-%m-%d %H:%M")
    return df


@router.get("/observations")
def exporter(
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    indicateurs: list[str] | None = Query(None),
    pays: list[str] | None = Query(None),
    annee_debut: int | None = None,
    annee_fin: int | None = None,
    avec_auxiliaires: bool = False,
    session: Session = Depends(get_session),
    u: Utilisateur = Depends(lecture),
) -> Response:
    df = tableau_observations(session, indicateurs, pays, annee_debut, annee_fin, avec_auxiliaires)
    nom = f"pdif_observations_{date.today().isoformat()}"
    if format == "csv":
        contenu = df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")  # lisible directement dans Excel
        return Response(contenu, media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{nom}.csv"'})
    flux = io.BytesIO()
    with pd.ExcelWriter(flux, engine="openpyxl") as ecrivain:
        df.to_excel(ecrivain, sheet_name="Observations", index=False)
        pd.DataFrame({"Note": [
            "Export de la PDIF (UIF, BRH). Valeurs courantes uniquement ; les versions précédentes restent en base.",
            "Colonne chargement_id : numéro du chargement d'origine (traçabilité, écran Contrôle qualité).",
            f"Exporté par {u.identifiant} le {date.today().isoformat()}.",
        ]}).to_excel(ecrivain, sheet_name="À lire", index=False)
    return Response(flux.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{nom}.xlsx"'})
