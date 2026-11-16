"""Import des fichiers de l'IHSI (pas d'API publique à ce jour).

Premier besoin : population par département, sexe et tranche d'âge (modèle ihsi_population, voir templates/).
Le connecteur calcule deux séries auxiliaires, dénominateurs des taux par département :
- POP-TOT : population totale ;
- POP-ADU : population de 15 ans et plus.
Si l'IHSI ouvre une API, il suffira d'écrire un ConnecteurAPI qui rend les mêmes colonnes.
"""
import re

import pandas as pd

from app.connectors.base import Connecteur
from app.quality.modeles import IHSI_POPULATION

AGE_ADULTE = 15


def borne_basse(groupe: str) -> int:
    return int(re.match(r"\d+", str(groupe).strip()).group())


class ConnecteurIHSI(Connecteur):
    code_source = "IHSI"
    modele = IHSI_POPULATION

    def __init__(self, nb_departements: int = 10, pays: str = "HTI"):
        self.nb_departements = nb_departements
        self.pays = pays

    def normaliser(self, df_brut: pd.DataFrame) -> pd.DataFrame:
        df = df_brut.copy()
        for col in ("departement", "sexe", "groupe_age"):
            df[col] = df[col].astype("string").str.strip()
        df["population"] = pd.to_numeric(df["population"], errors="coerce")
        df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
        df = df.dropna(subset=["departement", "sexe", "groupe_age", "annee", "population"])
        df["adulte"] = df["groupe_age"].map(borne_basse) >= AGE_ADULTE

        tot = df.groupby(["departement", "sexe", "annee"], as_index=False)["population"].sum()
        adu = df[df["adulte"]].groupby(["departement", "sexe", "annee"], as_index=False)["population"].sum()
        lignes = pd.concat([tot.assign(indicateur="POP-TOT"), adu.assign(indicateur="POP-ADU")])

        # Total = F + H quand le fichier ne donne pas la ligne Total
        sans_total = []
        for (ind, dep, annee), g in lignes.groupby(["indicateur", "departement", "annee"]):
            sexes = set(g["sexe"])
            if "Total" not in sexes and {"F", "H"} <= sexes:
                sans_total.append({"indicateur": ind, "departement": dep, "annee": annee, "sexe": "Total",
                                   "population": g[g["sexe"].isin(["F", "H"])]["population"].sum()})
        lignes = pd.concat([lignes, pd.DataFrame(sans_total)], ignore_index=True)

        # Total national seulement si les 10 départements sont présents (sinon il serait faux)
        nationales = []
        for (ind, sexe, annee), g in lignes.groupby(["indicateur", "sexe", "annee"]):
            if g["departement"].nunique() == self.nb_departements:
                nationales.append({"indicateur": ind, "departement": "", "sexe": sexe, "annee": annee,
                                   "population": g["population"].sum()})
        lignes = pd.concat([lignes, pd.DataFrame(nationales)], ignore_index=True)

        return pd.DataFrame({
            "indicateur": lignes["indicateur"], "pays": self.pays, "departement": lignes["departement"],
            "sexe": lignes["sexe"], "annee": lignes["annee"].astype(int), "trimestre": 0, "institution": "",
            "valeur": lignes["population"], "source": self.code_source,
        })
