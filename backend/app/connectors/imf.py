"""Connecteur FMI — Financial Access Survey, API SDMX 3.0.

Vérifié le 16/11/2026 (voir docs/sources.md) :
- jeu de données : IMF.STA / FAS (structure DSD_FAS) ;
- clé de série : PAYS.INDICATEUR.SECTEUR.CONTREPARTIE.SEXE.TRANSFORMATION.FRÉQUENCE ;
- requête : {base}/data/dataflow/IMF.STA/FAS/+/HTI+DOM+....*.*.*.*.*.A (en-tête Accept: application/json).
"""
import time

import httpx
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.connectors.base import ConnecteurAPI, ErreurSource, ResultatTest, obtenir_json
from app.models import SerieSource, Source
from app.quality.modeles import STANDARD

ENTETES = {"Accept": "application/json"}
PAUSE_ENTRE_APPELS = 1.0  # secondes, pour respecter les limites de requêtes de l'API


def decoder_sdmx(donnees: dict) -> list[dict]:
    """Transforme une réponse SDMX-JSON en lignes {pays, code_serie, annee, valeur}."""
    try:
        bloc = donnees["data"]
        dims = bloc["structures"][0]["dimensions"]
        dims_serie = dims["series"]
        temps = [v["value"] for v in dims["observation"][0]["values"]]
        series = bloc["dataSets"][0].get("series", {})
    except (KeyError, IndexError, TypeError) as exc:
        raise ErreurSource("Réponse SDMX du FMI dans un format inattendu.") from exc
    ids = [d["id"] for d in dims_serie]
    lignes = []
    for cle, serie in series.items():
        codes = {ids[i]: dims_serie[i]["values"][int(j)]["id"] for i, j in enumerate(cle.split(":"))}
        code_serie = ".".join(codes[d] for d in ("INDICATOR", "SECTOR", "COUNTERPARTY_SECTOR", "SEX", "TYPE_OF_TRANSFORMATION"))
        for position, obs in serie.get("observations", {}).items():
            if not obs or obs[0] in (None, ""):
                continue
            lignes.append({"pays": codes["COUNTRY"], "code_serie": code_serie, "frequence": codes.get("FREQUENCY"),
                           "annee": temps[int(position)], "valeur": obs[0]})
    return lignes


class ConnecteurFMI(ConnecteurAPI):
    code_source = "FMI"
    modele = STANDARD

    def __init__(self, session: Session, client: httpx.Client | None = None, pause: float = PAUSE_ENTRE_APPELS):
        self.session = session
        self.client = client or httpx.Client()
        self.reglages = get_settings()
        self.pause = pause

    def _series(self) -> dict[str, SerieSource]:
        return {s.code_serie: s for s in self.session.scalars(
            select(SerieSource).join(Source).where(Source.code == self.code_source, SerieSource.actif))}

    def tester(self) -> ResultatTest:
        r = self.reglages
        try:
            rep = obtenir_json(self.client, f"{r.imf_base_url}/structure/dataflow/{r.imf_agence}/{r.imf_jeu_fas}/+",
                               headers=ENTETES)
            flux = rep["data"]["dataflows"][0]
        except (ErreurSource, KeyError, IndexError, TypeError) as exc:
            return ResultatTest(False, f"FMI injoignable ou jeu FAS introuvable : {exc}", [])
        return ResultatTest(True, "Connexion réussie.", [
            f"Jeu de données : {flux['agencyID']}:{flux['id']} version {flux['version']} — {flux.get('name')}",
            f"{len(self._series())} séries suivies dans le référentiel.",
        ])

    def extraire(self) -> pd.DataFrame:
        r = self.reglages
        cle = "+".join(r.tous_les_pays) + ".*.*.*.*.*.A"
        url = f"{r.imf_base_url}/data/dataflow/{r.imf_agence}/{r.imf_jeu_fas}/+/{cle}"
        donnees = obtenir_json(self.client, url, headers=ENTETES)
        time.sleep(self.pause)
        series = self._series()
        lignes = []
        for l in decoder_sdmx(donnees):
            serie = series.get(l["code_serie"])
            if serie is None or int(l["annee"]) < r.annee_debut:
                continue
            lignes.append({
                "indicateur": serie.indicateur.code, "pays": l["pays"], "departement": "", "sexe": serie.sexe,
                "annee": l["annee"], "trimestre": "", "institution": "", "valeur": l["valeur"],
            })
        return pd.DataFrame(lignes, columns=STANDARD.noms_colonnes)

    def normaliser(self, df_brut: pd.DataFrame) -> pd.DataFrame:
        return df_brut.assign(source=self.code_source)
