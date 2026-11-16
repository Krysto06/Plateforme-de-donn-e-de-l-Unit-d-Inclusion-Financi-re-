"""Étape 6 : import d'un fichier de population IHSI (FICTIF : valeurs inventées pour les tests)."""
import pandas as pd
import pytest

from app.connectors.base import lire_tableau
from app.connectors.ihsi import ConnecteurIHSI
from app.services.chargement import traiter_envoi
from tests.conftest import FIXTURES, valeur

FICHIER = FIXTURES / "ihsi" / "population_FICTIVE_2024.csv"


def importer(session, df):
    con = ConnecteurIHSI()
    return traiter_envoi(session, source_code="IHSI", df_brut=df, modele=con.modele, normaliser=con.normaliser,
                         declencheur="manuel", auteur="test", fichier_nom=FICHIER.name)


def test_import_population_par_departement(session):
    brut = lire_tableau(FICHIER.read_bytes(), FICHIER.name)
    c = importer(session, brut)
    assert c.statut == "chargé", c.message
    assert {k.resultat for k in c.controles} == {"réussi"}
    df = pd.read_csv(FICHIER, sep=";")
    ouest = df[df["departement"] == "HT-OU"]
    adultes = ouest[ouest["groupe_age"].map(lambda g: int(g.split("-")[0].rstrip("+")) >= 15)]
    from sqlalchemy import select

    from app.models import Departement, Indicateur, Observation

    def pop(code, dep, sexe="Total"):
        return session.scalar(select(Observation.valeur).join(Indicateur).join(Departement).where(
            Indicateur.code == code, Departement.code == dep, Observation.sexe == sexe, Observation.est_courante))

    assert pop("POP-TOT", "HT-OU") == ouest["population"].sum()
    assert pop("POP-ADU", "HT-OU") == adultes["population"].sum()
    assert pop("POP-TOT", "HT-OU", "F") == ouest[ouest["sexe"] == "F"]["population"].sum()
    # total national (10 départements présents)
    assert valeur(session, "POP-TOT", "IHSI", 2024) == df["population"].sum()


def test_pas_de_total_national_si_un_departement_manque(session):
    brut = lire_tableau(FICHIER.read_bytes(), FICHIER.name)
    c = importer(session, brut[brut["departement"] != "HT-NI"].reset_index(drop=True))
    assert c.statut == "chargé"
    assert valeur(session, "POP-TOT", "IHSI", 2024) is None


def test_fichier_ihsi_mal_forme_rejete(session):
    brut = lire_tableau(FICHIER.read_bytes(), FICHIER.name).rename(columns={"groupe_age": "age"})
    c = importer(session, brut)
    assert c.statut == "rejeté"
    assert any(k.regle.startswith("1.") and k.resultat == "échec" for k in c.controles)


def test_import_ihsi_par_l_api(client, comptes):
    from tests.conftest import entetes

    with FICHIER.open("rb") as f:
        r = client.post("/api/sources/IHSI/import", files={"fichier": (FICHIER.name, f, "text/csv")},
                        headers=entetes(client, comptes["admin"]))
    assert r.status_code == 201 and r.json()["statut"] == "chargé"
