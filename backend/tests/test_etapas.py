"""Testes do endpoint /api/etapas."""
from app.models import ETAPAS


def test_etapas_retorna_200(client):
    r = client.get("/api/etapas")
    assert r.status_code == 200


def test_etapas_retorna_lista(client):
    data = client.get("/api/etapas").json()
    assert isinstance(data, list)
    assert len(data) == len(ETAPAS)


def test_etapas_tem_campos_obrigatorios(client):
    data = client.get("/api/etapas").json()
    for etapa in data:
        assert "nome" in etapa
        assert "cor"  in etapa


def test_etapas_ordem_correta(client):
    data = client.get("/api/etapas").json()
    nomes = [e["nome"] for e in data]
    assert nomes == ETAPAS


def test_etapas_cor_e_hex(client):
    data = client.get("/api/etapas").json()
    for etapa in data:
        assert etapa["cor"].startswith("#"), f"Cor inválida: {etapa['cor']}"
        assert len(etapa["cor"]) == 7
