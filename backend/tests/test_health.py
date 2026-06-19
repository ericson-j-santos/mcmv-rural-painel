"""Testes do endpoint de saúde."""


def test_health_retorna_200(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_health_retorna_status_ok(client):
    data = client.get("/api/health").json()
    assert data["status"] == "ok"
    assert data["app"] == "mcmv-rural-painel"
