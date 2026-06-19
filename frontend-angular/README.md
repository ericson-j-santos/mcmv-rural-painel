# Frontend Angular — MCMV Rural

Angular com serviço HTTP tipado e componente de dashboard.

## Requisitos

- Node.js 18+
- Angular CLI (`npm i -g @angular/cli`)

## Instalação

```bash
npm install
```

## Desenvolvimento

```bash
ng serve
```

Abre em `http://localhost:4200`. O proxy `/api` → `http://localhost:8082` está configurado em `proxy.conf.json`.

O backend precisa estar rodando antes:

```bash
# Em outra aba:
cd ../backend && uvicorn app.main:app --port 8082 --reload
```

## Serviço HTTP

`src/app/services/mcmv.service.ts` expõe métodos tipados para todos os endpoints:

```typescript
mcmvService.getStats()                     // Observable<Stats>
mcmvService.getEtapas()                    // Observable<Etapa[]>
mcmvService.getPropostas(filtros)          // Observable<PropostasPage>
mcmvService.getProposta(id)                // Observable<Proposta>
mcmvService.atualizarEtapa(id, payload)   // Observable<Proposta>
mcmvService.exportarCsv(filtros)          // Observable<Blob>
```

## Interfaces

```typescript
interface Stats {
  total_propostas: number;
  total_unidades: number;
  total_ufs: number;
  total_municipios: number;
  por_etapa: { etapa: string; cor: string; propostas: number; unidades: number }[];
  por_uf: { uf: string; propostas: number; unidades: number }[];
}
```

## Build

```bash
ng build --configuration production
```