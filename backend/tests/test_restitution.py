"""Tableau de bord, comparaison, catalogue, exports (étapes 11 et 15) et planification (étape 14)."""
import io

import pandas as pd
import pytest

from tests.conftest import entetes
from tests.test_connecteurs_api import charger


@pytest.fixture()
def donnees(session, faux_reseau):
    charger(session, "FMI", faux_reseau)
    charger(session, "WB", faux_reseau)


def test_tableau_de_bord_affiche_valeur_source_et_annee(client, comptes, donnees):
    cartes = {c["code"]: c for c in client.get("/api/tableau-de-bord", headers=entetes(client, comptes["cadre"])).json()["cartes"]}
    acc = cartes["ACC-01"]
    assert acc["source"] == "FMI" and acc["annee"] >= 2020 and acc["valeur"] > 0
    assert acc["anciennete"]["libelle"].startswith("Donnée de")
    assert cartes["EF-02"]["valeur"] is None and cartes["EF-02"]["anciennete"]["code"] == "a_collecter"
    assert len(cartes) == 19


def test_tableau_de_bord_filtre_par_annee(client, comptes, donnees):
    h = entetes(client, comptes["cadre"])
    cartes = {c["code"]: c for c in client.get("/api/tableau-de-bord?annee=2020", headers=h).json()["cartes"]}
    assert cartes["USA-01"]["annee"] == 2020 and cartes["USA-01"]["valeur"] == pytest.approx(257.05, abs=0.05)


def test_comparaison_regionale(client, comptes, donnees):
    r = client.get("/api/kpi/ACC-01/comparaison", headers=entetes(client, comptes["cadre"])).json()
    pays = {p["pays"] for p in r["pays"]}
    assert {"HTI", "DOM", "JAM", "NIC", "BRA", "FRA", "CAN"} <= pays
    assert any(p["principal"] for p in r["pays"])


def test_serie_dans_le_temps(client, comptes, donnees):
    points = client.get("/api/kpi/USA-01/serie", headers=entetes(client, comptes["cadre"])).json()["points"]
    assert len(points) >= 10 and all("chargement_id" in p for p in points)


def test_catalogue_indique_la_couverture(client, comptes, donnees):
    cat = {c["code"]: c for c in client.get("/api/catalogue", headers=entetes(client, comptes["cadre"])).json()}
    assert {c["source"] for c in cat["ACC-01"]["couverture"]} == {"FMI", "WB"}
    assert cat["VER-01"]["nb_valeurs"] == 0


def test_export_csv(client, comptes, donnees):
    r = client.get("/api/exports/observations?format=csv&indicateurs=ACC-01&pays=HTI", headers=entetes(client, comptes["cadre"]))
    df = pd.read_csv(io.StringIO(r.content.decode("utf-8-sig")), sep=";", decimal=",")
    assert set(df["code_kpi"]) == {"ACC-01"} and set(df["source"]) == {"FMI", "WB"}
    assert "chargement_id" in df.columns  # traçabilité


def test_export_excel(client, comptes, donnees):
    r = client.get("/api/exports/observations?format=xlsx", headers=entetes(client, comptes["cadre"]))
    classeur = pd.read_excel(io.BytesIO(r.content), sheet_name=None)
    assert {"Observations", "À lire"} <= set(classeur) and len(classeur["Observations"]) > 100


def test_planification_des_sources_api(session):
    from app.scheduler import creer_planificateur

    jobs = {j.id for j in creer_planificateur().get_jobs()}
    assert {"maj-WB", "maj-FMI", "retards"} <= jobs


def test_source_jamais_chargee_signalee_en_retard(client, session, comptes):
    sources = {s["code"]: s for s in client.get("/api/sources", headers=entetes(client, comptes["cadre"])).json()}
    assert sources["WB"]["en_retard"] and sources["WB"]["statut"] == "jamais chargée"


def test_source_a_jour_puis_en_retard(client, session, comptes, faux_reseau):
    from datetime import datetime, timedelta, timezone

    from app.models import Chargement

    c = charger(session, "FMI", faux_reseau)
    h = entetes(client, comptes["cadre"])
    assert client.get("/api/sources/FMI", headers=h).json()["statut"] == "à jour"
    c.termine_le = datetime.now(timezone.utc) - timedelta(days=60)  # délai d'alerte : 45 jours
    session.commit()
    etat = client.get("/api/sources/FMI", headers=h).json()
    assert etat["en_retard"] and etat["statut"] == "en retard"


def test_agregat_regional_charge_depuis_la_banque_mondiale(session, faux_reseau):
    charger(session, "WB", faux_reseau)
    from tests.conftest import valeur

    assert valeur(session, "ACC-01", "WB", 2020, pays="LCN") is not None


def test_agregat_regional_dans_la_comparaison_et_signale(client, comptes, donnees):
    r = client.get("/api/kpi/ACC-01/comparaison?source=WB", headers=entetes(client, comptes["cadre"])).json()
    lcn = next(p for p in r["pays"] if p["pays"] == "LCN")
    assert lcn["agregat"] is True and not lcn["principal"]
    assert all(not p["agregat"] for p in r["pays"] if p["pays"] != "LCN")


def test_le_fmi_ne_demande_pas_l_agregat(session):
    from app.config import get_settings

    assert "LCN" not in get_settings().tous_les_pays and "LCN" in get_settings().pays_banque_mondiale
