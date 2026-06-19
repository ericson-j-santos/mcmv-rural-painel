# Frontend Vue — MCMV Rural

Vue 3 + Vite + Pinia + Chart.js. SPA com painel de acompanhamento e lista interativa de propostas.

## Requisitos

- Node.js 18+

## Instalação

```bash
npm install
```

## Desenvolvimento

```bash
npm run dev
```

Abre em `http://localhost:5173`. Requisições `/api/*` são proxiadas para o backend em `http://localhost:8082` (configurado em `vite.config.js`).

O backend precisa estar rodando antes de iniciar o frontend:

```bash
# Em outra aba:
cd ../backend && uvicorn app.main:app --port 8082 --reload
```

## Build (produção)

```bash
npm run build
```

Os arquivos são gerados em `../backend/static/` e servidos diretamente pelo FastAPI/nginx.

## Testes

```bash
npm run test          # vitest modo watch
npm run test:run      # uma execução
```

## Views

| View | Rota | Descrição |
|---|---|---|
| `Dashboard` | `/` | Cards de resumo, funil de etapas, gráfico bar, ranking por UF |
| `Propostas` | `/propostas` | Tabela paginada com filtros UF/etapa/busca e edição inline de etapa |

## Estrutura

```
src/
├── api.js              # Wrappers axios para todos os endpoints
├── stores/mcmv.js      # Pinia store (stats, propostas, etapas)
└── views/
    ├── Dashboard.vue
    └── Propostas.vue
```