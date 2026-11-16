"""Préparation commune des tests : base en mémoire, référentiel chargé, faux réseau servant les vraies réponses
enregistrées dans tests/fixtures/ (aucun appel réel aux API pendant les tests)."""
import json
import os
import re
from pathlib import Path

# Réglages de test, posés AVANT d'importer l'application
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "cle-de-test-uniquement-pour-pytest-0123456789"
os.environ["HTTP_ATTENTE_SECONDES"] = "0"
os.environ["HTTP_ESSAIS"] = "3"
os.environ["DEPOTS_DIRECTIONS_OUVERTS"] = "true"
os.environ["PLANIFICATION_ACTIVE"] = "false"

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Direction, Institution, TypeInstitution  # noqa: E402
from app.services.comptes import creer_compte  # noqa: E402
from app.services.referentiel import charger_referentiel  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
MOT_DE_PASSE = "mot-de-passe-de-test-123"


@pytest.fixture()
def session():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        charger_referentiel(s, auteur="test")
        yield s


def repondre_fixtures(requete: httpx.Request) -> httpx.Response:
    """Faux serveur : rend le fichier enregistré correspondant à l'URL demandée."""
    url = str(requete.url)
    if "api.worldbank.org" in url:
        code = re.search(r"/indicator/([^/?]+)", url).group(1)
        chemin = FIXTURES / "worldbank" / f"{code}.json"
        if "/country/" not in url:  # métadonnées d'un indicateur (test de connexion)
            if not chemin.exists():
                return httpx.Response(200, json=[{"message": [{"id": "120", "key": "Invalid value",
                                                               "value": "The provided parameter value is not valid"}]}])
            return httpx.Response(200, json=[{"page": 1}, [{"id": code, "name": f"Indicateur {code}"}]])
        return httpx.Response(200, content=chemin.read_bytes(), headers={"content-type": "application/json"})
    if "api.imf.org" in url:
        if "/structure/dataflow/" in url:
            return httpx.Response(200, json={"data": {"dataflows": [
                {"agencyID": "IMF.STA", "id": "FAS", "version": "9.0.0", "name": "Financial Access Survey (FAS)"}]}})
        return httpx.Response(200, content=(FIXTURES / "imf" / "fas_comparateurs.json").read_bytes(),
                              headers={"content-type": "application/json"})
    return httpx.Response(404)


@pytest.fixture()
def faux_reseau():
    return httpx.Client(transport=httpx.MockTransport(repondre_fixtures))


@pytest.fixture()
def comptes(session):
    banque = session.query(TypeInstitution).filter_by(code="BANQUE").one()
    direction = Direction(code="DSF", nom="Direction de test (fictive)")
    session.add_all([direction, Institution(nom="Banque fictive A", type_institution=banque)])
    session.commit()
    creer_compte(session, "admin@test", "Admin Test", "admin_uif", MOT_DE_PASSE)
    creer_compte(session, "cadre@test", "Cadre Test", "cadre_uif", MOT_DE_PASSE)
    creer_compte(session, "focal@test", "Point focal Test", "point_focal", MOT_DE_PASSE, "DSF")
    return {"admin": "admin@test", "cadre": "cadre@test", "focal": "focal@test"}


@pytest.fixture()
def client(session):
    return TestClient(app)


def entetes(client: TestClient, identifiant: str) -> dict:
    r = client.post("/api/auth/connexion", json={"identifiant": identifiant, "mot_de_passe": MOT_DE_PASSE})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['jeton']}"}


def valeur(session, code: str, source: str, annee: int, pays: str = "HTI", sexe: str = "Total"):
    from sqlalchemy import select

    from app.models import Indicateur, Observation, Pays, Periode, Source

    return session.scalar(select(Observation.valeur).join(Indicateur).join(Pays).join(Periode).join(Source).where(
        Indicateur.code == code, Source.code == source, Periode.annee == annee, Pays.code_iso3 == pays,
        Observation.sexe == sexe, Observation.est_courante, Observation.departement_id.is_(None),
        Observation.institution_id.is_(None)))
