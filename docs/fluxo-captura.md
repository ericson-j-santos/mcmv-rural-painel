# Fluxo de Captura — MCMV Rural

## Origem dos dados

| Fonte | Tipo | URL / Path |
|---|---|---|
| MCID — Portaria nº 1.161/2025 | PDF (81 páginas) | https://www.gov.br/cidades/pt-br |
| Data de publicação | — | 12/06/2026 |
| Tabela do PDF | Colunas: UF · Município · Nº Proposta (UUID) · Entidade · CNPJ · Unidades |  |

---

## Pipeline completo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FONTE                                                                      │
│  Portal MCID (gov.br)                                                       │
│  Portaria MCID nº 1.161/2025 — Resultado da Seleção HIS Rural               │
│  PDF de 81 páginas com tabela de propostas selecionadas                     │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │ download manual
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ETAPA 1 — Extração do PDF                                                  │
│  scripts: static-html/extrai_mcmv.py                                        │
│  lib    : pdfplumber                                                         │
│                                                                              │
│  Para cada página do PDF:                                                    │
│    page.extract_tables() → lista de linhas                                   │
│    Detecta UF (2 letras maiúsculas) e propaga para linhas seguintes          │
│    Extrai: uf, municipio, num_proposta (UUID), entidade, cnpj, unidades      │
│                                                                              │
│  Saída: mcmv_rural_lista.json (~1.450 linhas brutas)                        │
│                                                                              │
│  PROBLEMA IDENTIFICADO: pdfplumber divide células multi-linha em            │
│  linhas separadas → ~390 registros fragmentados (UUID e CNPJ cortados)      │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ETAPA 2 — Limpeza inicial                                                  │
│  script: static-html/limpa_mcmv.py                                          │
│                                                                              │
│  • Remove cabeçalhos capturados (uf='UF', municipio='Município')             │
│  • Adiciona campos de controle: etapa_atual='Selecionado', historico=[]     │
│                                                                              │
│  Saída: mcmv_rural_lista.json limpo (~1.412 linhas)                         │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ETAPA 3 — Correção de IDs e CNPJ                                           │
│  script: scripts/fix_proposta_ids.py  (UUIDs)                               │
│  script: scripts/fix_html_helpers.py  (CNPJ)                                │
│                                                                              │
│  UUID: re.sub(r'\s+', '', num_proposta)                                     │
│    → Corrige espaços inseridos pelo pdfplumber no meio dos UUIDs            │
│    → Ex: "05dc7967-bbd1- 466f" → "05dc7967-bbd1-466f-..."                  │
│                                                                              │
│  CNPJ: normaliza para XX.XXX.XXX/XXXX-XX                                   │
│    → Remove espaços: "0001- 02" → "0001-02"                                 │
│    → 1.130 CNPJs corrigidos; 282 com fragmentação irreversível (marcados)  │
│                                                                              │
│  Saída: backend/data/mcmv_rural_lista.json (arquivo definitivo)             │
│    • 1.022 registros com UUID + CNPJ válidos                                │
│    •   390 registros com fragmentação (UUID inválido — filtrados no seed)   │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ETAPA 4 — Seed do banco de dados                                           │
│  script: backend/app/seed.py                                                │
│                                                                              │
│  • Executa na primeira inicialização do FastAPI (lifespan)                  │
│  • Filtra registros com UUID inválido (fragmentos)                          │
│  • Aplica _clean_cnpj() para normalizar CNPJs restantes                     │
│  • bulk_save_objects() → SQLite (dev) ou PostgreSQL (prod)                  │
│                                                                              │
│  Resultado final no banco:                                                  │
│    1.022 propostas com UUID e CNPJ válidos                                  │
│    48.911 unidades habitacionais                                             │
│    27 UFs · 736 municípios                                                  │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ETAPA 5 — API FastAPI                                                      │
│  backend/app/main.py + routes/                                               │
│                                                                              │
│  GET /api/propostas/stats  → totais, por_etapa, por_uf                      │
│  GET /api/propostas        → paginado + filtros (uf, etapa, busca)          │
│  PUT /api/propostas/{id}/etapa → avança etapa + registra histórico          │
│  GET /api/propostas/export → CSV com filtros                                │
│                                                                              │
│  Ambientes:                                                                  │
│    Dev  : SQLite  (sqlite:///./mcmv_rural.db)                               │
│    Prod : PostgreSQL / Fly.io (mcmv-rural-painel.fly.dev)                   │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ETAPA 6 — Visualização                                                     │
│                                                                              │
│  a) Vue 3 SPA (frontend-vue/)                                               │
│     Pinia store ← /api/propostas/stats + /api/propostas                    │
│     Dashboard: funil 6 etapas, gráfico bar, ranking UF                     │
│     Propostas: tabela paginada, filtros, edição de etapa                    │
│                                                                              │
│  b) Angular (frontend-angular/)                                             │
│     McmvService (TypeScript tipado) ← mesmos endpoints                     │
│                                                                              │
│  c) Painel HTML standalone (static-html/painel_mcmv_rural.html)            │
│     Vue 3 via CDN · sem build · lê do backend via fetch()                   │
│     CNPJ linkado → cnpj.biz/{14 dígitos} (consulta Receita Federal)        │
│     UUID com botão copiar + modal de detalhe                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Qualidade dos dados extraídos

| Campo | Válidos | Fragmentados | Observação |
|---|---|---|---|
| `num_proposta` (UUID) | 1.022 (72%) | 390 (28%) | Pdfplumber divide célula multi-linha |
| `cnpj` | 1.130 (80%) | 282 (20%) | Mesmo problema + espaços corrigidos |
| `unidades` | 1.412 (100%) | — | Sempre presente |
| `municipio` | 1.412 (100%) | — | Propagado por UF detectada |

Os 390 registros fragmentados são descartados no `seed.py` (UUID inválido).  
Os CNPJs válidos (1.130) são expostos como links para consulta no painel.

---

## Como re-executar a captura

```bash
# 1. Colocar o PDF do MCID em C:\Users\erics\.claude\...\webfetch-*.pdf
python static-html/extrai_mcmv.py          # → Downloads/mcmv_rural_lista.json

# 2. Limpar
python static-html/limpa_mcmv.py           # → mesmo arquivo, limpo

# 3. Copiar para o backend
copy mcmv_rural_lista.json backend/data/

# 4. Apagar o banco para re-seed
del backend/mcmv_rural.db                  # (SQLite local)

# 5. Iniciar — seed roda automaticamente
cd backend && uvicorn app.main:app --port 8082 --reload
```
