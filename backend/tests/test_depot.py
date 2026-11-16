"""Étape 13 : un dépôt FICTIF fait tout le parcours, du modèle Excel au chargement."""
import io

from openpyxl import load_workbook
from sqlalchemy import select

from app.models import Direction, Institution, TypeInstitution
from tests.conftest import entetes, valeur


def ids(session):
    return (session.scalar(select(Direction.id).where(Direction.code == "DSF")),
            session.scalar(select(TypeInstitution.id).where(TypeInstitution.code == "BANQUE")),
            session.scalar(select(Institution.id).where(Institution.nom == "Banque fictive A")))


def remplir_modele(contenu: bytes, lignes: list[list]) -> bytes:
    wb = load_workbook(io.BytesIO(contenu))
    for ligne in lignes:
        wb["Données"].append(ligne)
    flux = io.BytesIO()
    wb.save(flux)
    return flux.getvalue()


def deposer(client, h, session, fichier: bytes, **extra):
    direction, type_inst, inst = ids(session)
    donnees = {"direction_id": direction, "type_institution_id": type_inst, "institution_id": inst,
               "type_donnees": "plaintes", "periode": "2025", "commentaire": "Dépôt fictif de test",
               "certifie_agrege": "true", **extra}
    return client.post("/api/depots", data=donnees, headers=h,
                       files={"fichier": ("plaintes_2025.xlsx", fichier,
                                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})


def test_parcours_complet_du_depot_au_chargement(client, session, comptes):
    h_focal = entetes(client, comptes["focal"])
    modele = client.get("/api/depots/modeles/plaintes", headers=h_focal)
    assert modele.status_code == 200
    assert load_workbook(io.BytesIO(modele.content))["Données"]["A1"].value == "indicateur"

    fichier = remplir_modele(modele.content, [["CON-01", "", "Total", 2024, "", 80], ["CON-01", "", "Total", 2025, "", 85]])
    r = deposer(client, h_focal, session, fichier)
    assert r.status_code == 201, r.text
    assert r.json()["chargement"]["statut"] == "chargé"
    assert valeur(session, "CON-01", "DIR", 2025) is None  # rattaché à l'institution, pas au total national
    depots = client.get("/api/depots", headers=h_focal).json()
    assert depots[0]["statut"] == "chargé" and depots[0]["institution"] == "Banque fictive A"


def test_depot_avec_alerte_valide_par_l_administratrice(client, session, comptes):
    h_focal, h_admin = entetes(client, comptes["focal"]), entetes(client, comptes["admin"])
    modele = client.get("/api/depots/modeles/plaintes", headers=h_focal).content
    r = deposer(client, h_focal, session, remplir_modele(modele, [["CON-01", "", "Total", 2024, "", 20],
                                                                   ["CON-01", "", "Total", 2025, "", 90]]))
    chargement = r.json()["chargement"]
    assert chargement["statut"] == "en contrôle"  # +350 % : alerte de variation
    detail = client.get(f"/api/chargements/{chargement['id']}", headers=h_admin).json()
    assert detail["depot"]["direction"].startswith("Direction de test") and detail["nb_valeurs_en_attente"] == 2
    r = client.post(f"/api/chargements/{chargement['id']}/decision",
                    json={"decision": "accepter", "commentaire": "Hausse confirmée par la direction."}, headers=h_admin)
    assert r.json()["statut"] == "chargé"
    assert client.get("/api/depots", headers=h_focal).json()[0]["statut"] == "chargé"


def test_depot_nominatif_refuse(client, session, comptes):
    h = entetes(client, comptes["focal"])
    modele = client.get("/api/depots/modeles/plaintes", headers=h).content
    wb = load_workbook(io.BytesIO(modele))
    wb["Données"]["G1"] = "nom_client"
    wb["Données"].append(["CON-01", "", "Total", 2025, "", 85, "Jean Dupont"])
    flux = io.BytesIO()
    wb.save(flux)
    r = deposer(client, h, session, flux.getvalue())
    assert r.json()["chargement"]["statut"] == "rejeté"


def test_case_donnees_agregees_obligatoire(client, session, comptes):
    h = entetes(client, comptes["focal"])
    r = deposer(client, h, session, b"x", certifie_agrege="false")
    assert r.status_code == 422


def test_point_focal_ne_depose_pas_pour_une_autre_direction(client, session, comptes):
    autre = Direction(code="AUT", nom="Autre direction fictive")
    session.add(autre)
    session.commit()
    r = deposer(client, entetes(client, comptes["focal"]), session, b"x", direction_id=str(autre.id))
    assert r.status_code == 403


def test_depot_ferme_tant_que_non_heberge_a_la_brh(client, session, comptes, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "depots_directions_ouverts", False)
    r = deposer(client, entetes(client, comptes["focal"]), session, b"x")
    assert r.status_code == 403 and "serveur de la BRH" in r.json()["detail"]
