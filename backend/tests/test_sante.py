def test_sante_repond_ok(client):
    reponse = client.get("/api/sante")
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "ok"
