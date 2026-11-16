"""Étapes 8 et 9 : routes de l'API et rôles (chaque rôle ne voit que son espace)."""
import pytest

from tests.conftest import MOT_DE_PASSE, entetes

ROUTES_UIF = ["/api/kpi", "/api/tableau-de-bord", "/api/catalogue", "/api/sources", "/api/chargements",
              "/api/referentiels", "/api/exports/observations"]


def test_connexion_refusee_avec_mauvais_mot_de_passe(client, comptes):
    r = client.post("/api/auth/connexion", json={"identifiant": "admin@test", "mot_de_passe": "faux"})
    assert r.status_code == 401


def test_jeton_obligatoire(client, comptes):
    assert client.get("/api/kpi").status_code == 401
    assert client.get("/api/kpi", headers={"Authorization": "Bearer jeton-invente"}).status_code == 401


def test_profil_et_espace(client, comptes):
    assert client.get("/api/auth/moi", headers=entetes(client, comptes["admin"])).json()["espace"] == "uif"
    focal = client.get("/api/auth/moi", headers=entetes(client, comptes["focal"])).json()
    assert focal["espace"] == "direction" and focal["direction"]["nom"].startswith("Direction de test")


@pytest.mark.parametrize("route", ROUTES_UIF)
def test_espace_uif_lisible_par_admin_et_cadre(client, comptes, route):
    for role in ("admin", "cadre"):
        assert client.get(route, headers=entetes(client, comptes[role])).status_code == 200, (role, route)


@pytest.mark.parametrize("route", ROUTES_UIF)
def test_point_focal_n_a_pas_acces_a_l_espace_uif(client, comptes, route):
    assert client.get(route, headers=entetes(client, comptes["focal"])).status_code == 403


def test_actions_reservees_a_l_administratrice(client, comptes):
    h_cadre = entetes(client, comptes["cadre"])
    assert client.post("/api/sources/WB/mettre-a-jour", headers=h_cadre).status_code == 403
    assert client.post("/api/chargements/1/decision", json={"decision": "accepter"}, headers=h_cadre).status_code == 403
    assert client.get("/api/utilisateurs", headers=h_cadre).status_code == 403
    assert client.get("/api/journal", headers=entetes(client, comptes["admin"])).status_code == 200


def test_point_focal_voit_l_espace_depot(client, comptes):
    h = entetes(client, comptes["focal"])
    params = client.get("/api/depots/parametres", headers=h).json()
    assert [d["nom"] for d in params["directions"]] == ["Direction de test (fictive)"]  # sa direction seulement
    assert client.get("/api/depots", headers=h).status_code == 200


def test_mot_de_passe_trop_court_refuse(client, comptes):
    r = client.post("/api/utilisateurs", json={"identifiant": "x@test", "nom": "X", "role": "cadre_uif",
                                               "mot_de_passe": "court"}, headers=entetes(client, comptes["admin"]))
    assert r.status_code == 422


def test_connexions_tracees_dans_le_journal(client, comptes):
    entetes(client, comptes["cadre"])
    journal = client.get("/api/journal", headers=entetes(client, comptes["admin"])).json()
    assert any(j["action"] == "connexion" and j["utilisateur"] == "cadre@test" for j in journal)
