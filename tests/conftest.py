"""
Fixtures Playwright compartilhadas.

Strategy: intercepta as chamadas de API com respostas mock para que Vue renderize
o template completo sem precisar do backend rodando.  Isso permite testar CSS
(tooltips, z-index, navegação) de forma determinística e offline.
"""
import json
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext, Route

HTML_PATH = Path(__file__).parent.parent / "static-html" / "painel_mcmv_rural.html"
FILE_URL = "file:///" + HTML_PATH.as_posix()

VIEWPORT = {"width": 1440, "height": 900}

# ── Dados mock mínimos para Vue renderizar o template completo ───────────────

MOCK_STATS = {
    "total_propostas": 6, "total_unidades": 600,
    "total_ufs": 3, "total_municipios": 5,
    "cnpj_validos": 5, "cnpj_invalidos": 1,
    "cnpj_unicos": 5, "cnpj_unicos_validos": 5,
    "avancos_7d": 3,
    "por_etapa": [
        {"etapa": "Selecionado",             "cor": "#3b82f6", "propostas": 2, "unidades": 200},
        {"etapa": "Habilitação da Entidade", "cor": "#8b5cf6", "propostas": 1, "unidades": 100},
        {"etapa": "Contratação",             "cor": "#f59e0b", "propostas": 1, "unidades": 100},
        {"etapa": "Início das Obras",        "cor": "#f97316", "propostas": 1, "unidades": 100},
        {"etapa": "Em Execução",             "cor": "#06b6d4", "propostas": 0, "unidades": 0},
        {"etapa": "Entrega das Chaves",      "cor": "#16a34a", "propostas": 1, "unidades": 100},
    ],
    "por_uf": [
        {"uf": "SP", "propostas": 4, "unidades": 400},
        {"uf": "MG", "propostas": 2, "unidades": 200},
    ],
}

MOCK_PROPOSTAS = {
    "total": 2, "pagina": 1, "por_pagina": 20, "total_paginas": 1,
    "items": [
        {
            "num_proposta": "UUID-001", "uf": "SP", "municipio": "Campinas",
            "entidade": "Coop Campinas", "cnpj": "12.345.678/0001-90",
            "unidades": 200, "etapa_atual": "Selecionado",
            "atualizado_em": "2026-01-01T00:00:00", "tags": [], "responsavel": None,
        },
        {
            "num_proposta": "UUID-002", "uf": "MG", "municipio": "Belo Horizonte",
            "entidade": "Coop BH", "cnpj": "99.999.999/0001-00",
            "unidades": 100, "etapa_atual": "Contratação",
            "atualizado_em": "2026-01-10T00:00:00", "tags": ["urgente"], "responsavel": "João",
        },
    ],
}

MOCK_TEMPO_MEDIO = [
    {"etapa": e, "cor": "#999", "avg_dias": 30.0, "propostas": 1}
    for e in ["Selecionado","Habilitação da Entidade","Contratação",
              "Início das Obras","Em Execução","Entrega das Chaves"]
]

MOCK_TOP_MUNS = [
    {"municipio": "Campinas", "uf": "SP", "propostas": 2, "unidades": 200},
    {"municipio": "Belo Horizonte", "uf": "MG", "propostas": 1, "unidades": 100},
]

MOCK_ETAPAS = [
    {"nome": e} for e in ["Selecionado","Habilitação da Entidade","Contratação",
                           "Início das Obras","Em Execução","Entrega das Chaves"]
]


def _json_ok(route: Route, data) -> None:
    route.fulfill(status=200, content_type="application/json", body=json.dumps(data))


def _setup_mocks(pg: Page) -> None:
    """Registra interceptores antes de carregar a página."""
    pg.route("**/api/propostas/stats",        lambda r, _=None: _json_ok(r, MOCK_STATS))
    pg.route("**/api/propostas/tempo-medio",  lambda r, _=None: _json_ok(r, MOCK_TEMPO_MEDIO))
    pg.route("**/api/propostas/top-municipios*", lambda r, _=None: _json_ok(r, MOCK_TOP_MUNS))
    pg.route("**/api/propostas*",             lambda r, _=None: _json_ok(r, MOCK_PROPOSTAS))
    pg.route("**/api/etapas*",                lambda r, _=None: _json_ok(r, MOCK_ETAPAS))
    pg.route("**/api/historico*",             lambda r, _=None: _json_ok(r, []))


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser() -> Browser:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def ctx(browser: Browser) -> BrowserContext:
    context = browser.new_context(viewport=VIEWPORT)
    yield context
    context.close()


@pytest.fixture
def page(ctx: BrowserContext) -> Page:
    pg = ctx.new_page()
    _setup_mocks(pg)
    pg.goto(FILE_URL)
    pg.wait_for_load_state("load")
    # Aguarda Vue renderizar o template principal (gateado por stats && !carregando)
    pg.wait_for_function(
        "() => document.querySelector('.tab-nav') !== null",
        timeout=15_000,
    )
    pg.wait_for_timeout(400)
    return pg
