"""Étapes 2 et 3 : tables créées, 19 KPI en base, modifiables sans toucher au code."""
from sqlalchemy import func, inspect, select

from app.db import engine
from app.models import Indicateur, SerieSource
from tests.conftest import entetes

TABLES = {"pays", "departement", "periode", "direction", "type_institution", "institution", "source", "indicateur",
          "serie_source", "observation", "chargement", "controle", "depot", "utilisateur", "role", "journal"}


def test_toutes_les_tables_existent(session):
    assert TABLES <= set(inspect(engine).get_table_names())


def test_les_19_kpi_sont_en_base(session):
    kpi = session.scalars(select(Indicateur.code).where(Indicateur.est_kpi)).all()
    assert len(kpi) == 19
    assert {"ACC-01", "USA-04", "GEN-02", "VER-01"} <= set(kpi)


def test_relancer_le_chargement_ne_cree_pas_de_doublon(session):
    from app.services.referentiel import charger_referentiel

    charger_referentiel(session)
    assert session.scalar(select(func.count()).select_from(Indicateur)) == 22
    assert session.scalar(select(func.count()).select_from(SerieSource)) == 18


def test_kpi_modifiable_sans_code(client, comptes):
    h = entetes(client, comptes["admin"])
    # renommer
    r = client.patch("/api/kpi/EF-03", json={"libelle": "Score de culture financière (enquête 2026)"}, headers=h)
    assert r.status_code == 200 and r.json()["libelle"].endswith("(enquête 2026)")
    # ajouter
    r = client.post("/api/kpi", json={"code": "ACC-05", "libelle": "Points de service pour 10 000 adultes",
                                      "dimension": "Accès", "unite": "pour 10 000 adultes"}, headers=h)
    assert r.status_code == 201
    # retirer (les valeurs déjà chargées restent en base)
    r = client.delete("/api/kpi/VER-01", headers=h)
    assert r.status_code == 200 and r.json()["actif"] is False
    codes = [k["code"] for k in client.get("/api/kpi", headers=h).json()]
    assert "ACC-05" in codes and "VER-01" not in codes


def test_formule_de_calcul_invalide_refusee(client, comptes):
    h = entetes(client, comptes["admin"])
    r = client.patch("/api/kpi/GEN-01", json={"calcul": "__import__('os').system('ls')"}, headers=h)
    assert r.status_code == 422


def test_un_cadre_ne_peut_pas_modifier_le_referentiel(client, comptes):
    r = client.patch("/api/kpi/EF-03", json={"libelle": "X"}, headers=entetes(client, comptes["cadre"]))
    assert r.status_code == 403
