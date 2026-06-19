"""Testes dos endpoints /api/propostas."""
import pytest


# ─── GET /api/propostas/stats ──────────────────────────────────────────────────

class TestStats:
    def test_stats_retorna_200(self, client):
        r = client.get("/api/propostas/stats")
        assert r.status_code == 200

    def test_stats_campos_obrigatorios(self, client):
        data = client.get("/api/propostas/stats").json()
        assert "total_propostas"  in data
        assert "total_unidades"   in data
        assert "total_ufs"        in data
        assert "total_municipios" in data
        assert "por_etapa"        in data
        assert "por_uf"           in data

    def test_stats_totais_consistentes(self, client):
        data = client.get("/api/propostas/stats").json()
        assert data["total_propostas"] == 5
        assert data["total_unidades"]  == 240  # 50+30+20+100+40
        assert data["total_ufs"]       == 4    # AC, BA, SP, MG
        assert data["total_municipios"] == 5

    def test_stats_por_etapa_cobre_todas(self, client):
        from app.models import ETAPAS
        data = client.get("/api/propostas/stats").json()
        nomes = [e["etapa"] for e in data["por_etapa"]]
        for etapa in ETAPAS:
            assert etapa in nomes

    def test_stats_por_etapa_soma_total(self, client):
        data = client.get("/api/propostas/stats").json()
        soma = sum(e["propostas"] for e in data["por_etapa"])
        assert soma == data["total_propostas"]

    def test_stats_por_uf_ordenado_desc(self, client):
        data = client.get("/api/propostas/stats").json()
        qtds = [u["propostas"] for u in data["por_uf"]]
        assert qtds == sorted(qtds, reverse=True)


# ─── GET /api/propostas ────────────────────────────────────────────────────────

class TestListar:
    def test_listar_retorna_200(self, client):
        r = client.get("/api/propostas")
        assert r.status_code == 200

    def test_listar_estrutura_paginada(self, client):
        data = client.get("/api/propostas").json()
        assert "total"        in data
        assert "pagina"       in data
        assert "por_pagina"   in data
        assert "total_paginas" in data
        assert "items"        in data

    def test_listar_total_correto(self, client):
        data = client.get("/api/propostas").json()
        assert data["total"] == 5

    def test_listar_paginacao(self, client):
        r = client.get("/api/propostas?pagina=1&por_pagina=2")
        data = r.json()
        assert len(data["items"])  == 2
        assert data["total_paginas"] == 3

    def test_listar_pagina_alem_do_total(self, client):
        data = client.get("/api/propostas?pagina=99&por_pagina=20").json()
        assert data["items"] == []

    def test_filtro_por_uf(self, client):
        data = client.get("/api/propostas?uf=BA").json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["uf"] == "BA"

    def test_filtro_por_etapa(self, client):
        data = client.get("/api/propostas?etapa=Selecionado").json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["etapa_atual"] == "Selecionado"

    def test_filtro_por_uf_inexistente(self, client):
        data = client.get("/api/propostas?uf=ZZ").json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_busca_por_municipio(self, client):
        data = client.get("/api/propostas?busca=Salvador").json()
        assert data["total"] == 1
        assert data["items"][0]["municipio"] == "Salvador"

    def test_busca_por_entidade_parcial(self, client):
        data = client.get("/api/propostas?busca=Assoc").json()
        assert data["total"] >= 2

    def test_busca_sem_resultado(self, client):
        data = client.get("/api/propostas?busca=xyzinexistente").json()
        assert data["total"] == 0

    def test_filtro_uf_e_etapa_combinados(self, client):
        data = client.get("/api/propostas?uf=BA&etapa=Selecionado").json()
        assert data["total"] == 1
        assert data["items"][0]["uf"] == "BA"
        assert data["items"][0]["etapa_atual"] == "Selecionado"

    def test_por_pagina_limite_200(self, client):
        r = client.get("/api/propostas?por_pagina=999")
        assert r.status_code == 422  # FastAPI valida le=200

    def test_itens_tem_campos_obrigatorios(self, client):
        data = client.get("/api/propostas").json()
        for item in data["items"]:
            assert "num_proposta"  in item
            assert "uf"            in item
            assert "municipio"     in item
            assert "entidade"      in item
            assert "unidades"      in item
            assert "etapa_atual"   in item
            assert "atualizado_em" in item


# ─── GET /api/propostas/{id} ───────────────────────────────────────────────────

class TestDetalhe:
    def test_detalhe_retorna_200(self, client):
        r = client.get("/api/propostas/aaa-001")
        assert r.status_code == 200

    def test_detalhe_campos_completos(self, client):
        data = client.get("/api/propostas/aaa-001").json()
        assert data["num_proposta"] == "aaa-001"
        assert data["uf"]           == "AC"
        assert data["municipio"]    == "Acrelândia"
        assert data["unidades"]     == 50
        assert "historico"          in data

    def test_detalhe_historico_vazio_inicial(self, client):
        data = client.get("/api/propostas/aaa-001").json()
        assert isinstance(data["historico"], list)

    def test_detalhe_nao_encontrado(self, client):
        r = client.get("/api/propostas/id-inexistente-xyz")
        assert r.status_code == 404


# ─── PUT /api/propostas/{id}/etapa ────────────────────────────────────────────

class TestAtualizarEtapa:
    def test_atualizar_etapa_retorna_200(self, client):
        r = client.put(
            "/api/propostas/bbb-002/etapa",
            json={"etapa": "Habilitação da Entidade"},
        )
        assert r.status_code == 200

    def test_atualizar_etapa_reflete_na_proposta(self, client):
        client.put("/api/propostas/bbb-002/etapa", json={"etapa": "Contratação"})
        data = client.get("/api/propostas/bbb-002").json()
        assert data["etapa_atual"] == "Contratação"

    def test_atualizar_etapa_grava_historico(self, client):
        client.put("/api/propostas/eee-005/etapa", json={"etapa": "Selecionado", "observacao": "Revisão"})
        data = client.get("/api/propostas/eee-005").json()
        assert len(data["historico"]) >= 1
        ultimo = data["historico"][-1]
        assert ultimo["etapa_para"] == "Selecionado"
        assert ultimo["observacao"] == "Revisão"

    def test_atualizar_etapa_invalida_retorna_400(self, client):
        r = client.put(
            "/api/propostas/aaa-001/etapa",
            json={"etapa": "Etapa Que Nao Existe"},
        )
        assert r.status_code == 400

    def test_atualizar_etapa_proposta_inexistente(self, client):
        r = client.put(
            "/api/propostas/nao-existe-999/etapa",
            json={"etapa": "Selecionado"},
        )
        assert r.status_code == 404

    def test_atualizar_etapa_sem_observacao(self, client):
        r = client.put("/api/propostas/ddd-004/etapa", json={"etapa": "Início das Obras"})
        assert r.status_code == 200
        assert r.json()["etapa_atual"] == "Início das Obras"

    def test_atualizar_etapa_stats_atualizam(self, client):
        client.put("/api/propostas/aaa-001/etapa", json={"etapa": "Contratação"})
        stats = client.get("/api/propostas/stats").json()
        contratacao = next(e for e in stats["por_etapa"] if e["etapa"] == "Contratação")
        assert contratacao["propostas"] >= 1


# ─── GET /api/propostas/export ────────────────────────────────────────────────

class TestExport:
    def test_export_retorna_200(self, client):
        r = client.get("/api/propostas/export")
        assert r.status_code == 200

    def test_export_content_type_csv(self, client):
        r = client.get("/api/propostas/export")
        assert "text/csv" in r.headers["content-type"]

    def test_export_tem_cabecalho(self, client):
        r = client.get("/api/propostas/export")
        linhas = r.text.lstrip("﻿").splitlines()
        cabecalho = linhas[0]
        assert "UF"          in cabecalho
        assert "Município"   in cabecalho
        assert "Entidade"    in cabecalho
        assert "Unidades"    in cabecalho
        assert "Etapa Atual" in cabecalho

    def test_export_quantidade_linhas(self, client):
        r = client.get("/api/propostas/export")
        linhas = [l for l in r.text.splitlines() if l.strip()]
        assert len(linhas) == 6  # 1 cabeçalho + 5 propostas

    def test_export_filtro_por_uf(self, client):
        r = client.get("/api/propostas/export?uf=SP")
        linhas = [l for l in r.text.splitlines() if l.strip()]
        assert len(linhas) == 2  # cabeçalho + 1 proposta SP

    def test_export_filtro_por_etapa(self, client):
        # Garante que há pelo menos 1 "Selecionado" ainda
        r = client.get("/api/propostas/export?etapa=Selecionado")
        linhas = [l for l in r.text.splitlines() if l.strip()]
        assert len(linhas) >= 2  # cabeçalho + ao menos 1
