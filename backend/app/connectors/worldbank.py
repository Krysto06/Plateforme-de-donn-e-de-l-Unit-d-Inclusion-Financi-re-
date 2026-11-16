"""Connecteur Banque mondiale — API Indicators v2 (sans clé).

Adresse vérifiée le 16/11/2026 : https://api.worldbank.org/v2/country/{pays;...}/indicator/{code}?format=json
Les codes de séries utilisés sont ceux de la table serie_source (vérifiés, voir docs/sources.md).
"""
from datetime import date

import httpx
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.connectors.base import ConnecteurAPI, ErreurSource, ResultatTest, obtenir_json
from app.models import SerieSource, Source
from app.quality.modeles import STANDARD


class ConnecteurBanqueMondiale(ConnecteurAPI):
    code_source = "WB"
    modele = STANDARD

    def __init__(self, session: Session, client: httpx.Client | None = None):
        self.session = session
        self.client = client or httpx.Client()
        self.reglages = get_settings()

    def _series(self) -> list[SerieSource]:
        return list(self.session.scalars(
            select(SerieSource).join(Source).where(Source.code == self.code_source, SerieSource.actif)))

    def _pages(self, url: str, params: dict) -> list[dict]:
        lignes, page, pages = [], 1, 1
        while page <= pages:
            donnees = obtenir_json(self.client, url, params={**params, "page": page})
            if not isinstance(donnees, list) or not donnees:
                raise ErreurSource(f"Réponse inattendue de la Banque mondiale pour {url}")
            if "message" in donnees[0]:  # l'API signale une erreur (ex. code d'indicateur inconnu)
                messages = "; ".join(m.get("value", "") for m in donnees[0]["message"])
                raise ErreurSource(f"Banque mondiale : {messages} ({url})")
            pages = int(donnees[0].get("pages") or 1)
            lignes.extend((donnees[1] or []) if len(donnees) > 1 else [])
            page += 1
        return lignes

    def tester(self) -> ResultatTest:
        details, ok = [], True
        for serie in self._series():
            try:
                rep = obtenir_json(self.client, f"{self.reglages.wb_base_url}/indicator/{serie.code_serie}",
                                   params={"format": "json"})
                if isinstance(rep, list) and len(rep) > 1 and rep[1]:
                    details.append(f"{serie.code_serie} : trouvé — {rep[1][0]['name']}")
                else:
                    ok = False
                    details.append(f"{serie.code_serie} : INCONNU de l'API")
            except ErreurSource as exc:
                return ResultatTest(False, f"Banque mondiale injoignable : {exc}", details)
        return ResultatTest(ok, "Connexion réussie, codes vérifiés." if ok else "Connexion réussie, mais des codes sont inconnus.", details)

    def extraire(self) -> pd.DataFrame:
        pays = ";".join(self.reglages.tous_les_pays)
        params = {"format": "json", "per_page": 1000, "date": f"{self.reglages.annee_debut}:{date.today().year}"}
        lignes = []
        for serie in self._series():
            url = f"{self.reglages.wb_base_url}/country/{pays}/indicator/{serie.code_serie}"
            for r in self._pages(url, params):
                if r.get("value") is None:  # année sans donnée publiée
                    continue
                lignes.append({
                    "indicateur": serie.indicateur.code, "pays": r["countryiso3code"], "departement": "",
                    "sexe": serie.sexe, "annee": r["date"], "trimestre": "", "institution": "",
                    "valeur": r["value"],
                })
        return pd.DataFrame(lignes, columns=STANDARD.noms_colonnes)

    def normaliser(self, df_brut: pd.DataFrame) -> pd.DataFrame:
        return df_brut.assign(source=self.code_source)
