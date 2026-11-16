from fastapi.testclient import TestClient

from app.main import app


def test_sante_repond_ok():
    reponse = TestClient(app).get("/api/sante")
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "ok"
