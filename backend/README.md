# Backend — MCMV Rural API

FastAPI + SQLAlchemy com suporte a **SQLite** (desenvolvimento) e **PostgreSQL** (produção/Fly.io).

## Requisitos

- Python 3.12+

## Instalação

```bash
pip install -r requirements.txt
```

## Executar

```bash
# SQLite (padrão)
uvicorn app.main:app --port 8082 --reload

# PostgreSQL
DATABASE_URL=postgresql://user:pass@host/db uvicorn app.main:app --port 8082
```

Na primeira execução o banco é criado e as 1.412 propostas são carregadas automaticamente a partir de `data/mcmv_rural_lista.json`.

## Endpoints

| Método | Path | Descrição |
|---|---|---|
| `GET` | `/api/propostas/stats` | Totais + distribuição por etapa e UF |
| `GET` | `/api/etapas` | Lista as 6 etapas com cores |
| `GET` | `/api/propostas` | Listagem paginada e filtrada |
| `GET` | `/api/propostas/{id}` | Detalhe + histórico da proposta |
| `PUT` | `/api/propostas/{id}/etapa` | Avança/retrocede etapa |
| `GET` | `/api/propostas/export` | Download CSV (respeita filtros) |
| `GET` | `/api/health` | Health check |

### Parâmetros de listagem

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `uf` | string | Filtrar por UF (ex: `BA`) |
| `etapa` | string | Filtrar por etapa atual |
| `busca` | string | Busca em município e entidade |
| `pagina` | int | Página (padrão: 1) |
| `por_pagina` | int | Itens por página (padrão: 20) |

### Body do PUT /etapa

```json
{
  "etapa": "Contratação",
  "observacao": "Documentação recebida"
}
```

## Testes

```bash
pip install -r requirements-test.txt
TESTING=1 pytest -v
```

`TESTING=1` desativa o seed automático para os testes usarem banco em memória.

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./mcmv_rural.db` | URL do banco |
| `APP_ENV` | `development` | Ambiente (`production` desativa reload) |

## Deploy Fly.io

```bash
cd backend
fly deploy
```

App configurado em `fly.toml` (região `gru`, 512MB RAM).