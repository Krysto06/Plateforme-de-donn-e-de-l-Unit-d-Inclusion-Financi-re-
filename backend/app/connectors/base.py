"""Interface commune à tous les connecteurs et outils partagés (appels réseau, lecture de fichiers)."""
import io
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx
import pandas as pd

from app.config import get_settings
from app.quality.modeles import Modele

log = logging.getLogger("pdif.connecteurs")


class ErreurSource(RuntimeError):
    """La source n'a pas pu être lue (réseau, réponse inattendue, code inconnu...)."""


@dataclass
class ResultatTest:
    ok: bool
    message: str
    details: list[str]


class Connecteur(ABC):
    """Un connecteur sait lire une source et ramener ses données au format normalisé de la PDIF."""

    code_source: str
    modele: Modele

    @abstractmethod
    def normaliser(self, df_brut: pd.DataFrame) -> pd.DataFrame:
        """Transforme les données brutes (colonnes du modèle) en lignes au format standard."""


class ConnecteurAPI(Connecteur):
    @abstractmethod
    def tester(self) -> ResultatTest: ...

    @abstractmethod
    def extraire(self) -> pd.DataFrame:
        """Interroge l'API et rend les données brutes (déjà au format standard pour les API)."""


def obtenir_json(client: httpx.Client, url: str, *, params: dict | None = None, headers: dict | None = None):
    """GET avec plusieurs essais et une attente qui double à chaque fois (erreurs réseau, 429, 5xx)."""
    reglages = get_settings()
    attente = reglages.http_attente_secondes
    derniere_erreur = ""
    for essai in range(1, reglages.http_essais + 1):
        try:
            reponse = client.get(url, params=params, headers=headers, timeout=reglages.http_timeout_secondes)
            if reponse.status_code == 429 or reponse.status_code >= 500:
                derniere_erreur = f"code HTTP {reponse.status_code}"
            elif reponse.status_code >= 400:
                raise ErreurSource(f"{url} a répondu {reponse.status_code} : {reponse.text[:300]}")
            else:
                return reponse.json()
        except httpx.HTTPError as exc:  # délai dépassé, connexion coupée, refus du proxy...
            derniere_erreur = f"{type(exc).__name__} : {exc}"
        except ValueError as exc:
            raise ErreurSource(f"Réponse illisible (JSON attendu) de {url}") from exc
        log.warning("Essai %s/%s échoué pour %s (%s)", essai, reglages.http_essais, url, derniere_erreur)
        if essai < reglages.http_essais:
            time.sleep(attente)
            attente *= 2
    raise ErreurSource(f"{url} injoignable après {reglages.http_essais} essais ({derniere_erreur}).")


def lire_tableau(contenu: bytes, nom_fichier: str) -> pd.DataFrame:
    """Lit un fichier Excel (.xlsx) ou CSV (séparateur ; ou ,) en gardant tout en texte, en-têtes en minuscules."""
    nom = nom_fichier.lower()
    try:
        if nom.endswith((".xlsx", ".xlsm")):
            with pd.ExcelFile(io.BytesIO(contenu), engine="openpyxl") as classeur:
                feuille = "Données" if "Données" in classeur.sheet_names else classeur.sheet_names[0]
            df = pd.read_excel(io.BytesIO(contenu), sheet_name=feuille, dtype=str, engine="openpyxl")
        elif nom.endswith((".csv", ".txt")):
            texte = contenu.decode("utf-8-sig", errors="replace")
            separateur = ";" if texte.split("\n", 1)[0].count(";") >= texte.split("\n", 1)[0].count(",") else ","
            df = pd.read_csv(io.StringIO(texte), sep=separateur, dtype=str)
        else:
            raise ErreurSource("Format de fichier non pris en charge : utiliser .xlsx ou .csv.")
    except ErreurSource:
        raise
    except Exception as exc:  # fichier abîmé, mauvais format...
        raise ErreurSource(f"Fichier illisible : {exc}") from exc
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.dropna(how="all")
    return df.reset_index(drop=True)
