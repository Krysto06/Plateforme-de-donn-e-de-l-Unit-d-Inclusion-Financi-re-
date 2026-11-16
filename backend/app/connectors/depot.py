"""Dépôt de fichiers standardisés par les directions de la BRH (phase 2) et formulaires de l'UIF.

Le point focal choisit direction, type d'institution, institution, type de données et période ;
le fichier suit le modèle Excel du type de données (templates/). Toujours contrôlé avant chargement.
"""
import pandas as pd

from app.connectors.base import Connecteur
from app.quality.modeles import MODELES_DEPOT, Modele

# Les données d'éducation financière viennent de l'UIF elle-même ; le reste, des directions
SOURCE_PAR_TYPE = {"education_financiere": "UIF"}


class ConnecteurDepot(Connecteur):
    def __init__(self, type_donnees: str, institution: str | None, periode: str, pays: str = "HTI"):
        if type_donnees not in MODELES_DEPOT:
            raise ValueError(f"Type de données inconnu : {type_donnees}")
        self.modele: Modele = MODELES_DEPOT[type_donnees]
        self.code_source = SOURCE_PAR_TYPE.get(type_donnees, "DIR")
        self.institution = institution or ""
        self.periode = periode
        self.pays = pays

    def normaliser(self, df_brut: pd.DataFrame) -> pd.DataFrame:
        df = df_brut.copy()
        for col in ("departement", "trimestre"):
            if col not in df.columns:
                df[col] = ""
        return pd.DataFrame({
            "indicateur": df["indicateur"].astype("string").str.strip(),
            "pays": self.pays,
            "departement": df["departement"].fillna(""),
            "sexe": df["sexe"].astype("string").str.strip(),
            "annee": df["annee"],
            "trimestre": df["trimestre"],
            "institution": self.institution,
            "valeur": df["valeur"],
            "source": self.code_source,
        })
