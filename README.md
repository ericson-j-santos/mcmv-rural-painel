# MCMV Rural — Painel de Acompanhamento de Implantação

Painel para acompanhamento das 1.412 propostas selecionadas do **Minha Casa Minha Vida Rural** (HIS Rural), publicadas pelo MCID via Portaria nº 1.161/2025, resultado divulgado em 12/06/2026.

## Estrutura

```
mcmv-rural-painel/
├── backend/              # FastAPI + SQLAlchemy (SQLite dev / PostgreSQL prod)
├── frontend-vue/         # Vue 3 + Vite + Pinia + Chart.js
├── frontend-angular/     # Angular (serviço tipado + componente dashboard)
├── static-html/          # Painel HTML standalone (sem build, lê do backend)
├── deploy/linux/         # nginx + systemd + setup/test scripts (sem Docker)
├── copilot-studio/       # Definições de agente para Power Platform
└── legacy/               # Versões anteriores com dados embutidos
```

## Quick start (desenvolvimento)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8082 --reload

# Frontend Vue (outra aba)
cd frontend-vue
npm install
npm run dev          # proxy /api → localhost:8082

# Painel HTML standalone
# Abrir static-html/painel_mcmv_rural.html no browser
# (backend deve estar rodando em localhost:8082)
```

## Produção

| Ambiente | URL |
|---|---|
| Fly.io | https://mcmv-rural-painel.fly.dev |
| Linux nativo | `bash deploy/linux/setup.sh <IP_ou_hostname>` |

## Etapas de implantação

1. Selecionado
2. Habilitação da Entidade
3. Contratação
4. Início das Obras
5. Em Execução
6. Entrega das Chaves

## Dados

- **1.412 propostas** · **48.911 unidades habitacionais** · **27 UFs** · **736 municípios**
- Fonte: Portaria MCID nº 1.161/2025
- Arquivo: `backend/data/mcmv_rural_lista.json`