# Agente Copilot Studio - MCMV Rural

Esta pasta contem um pacote pratico para criar um agente no Microsoft Copilot Studio usando a API do painel MCMV Rural.

## O que criar no Copilot Studio

Nome sugerido:

`Agente MCMV Rural`

Descricao curta:

`Ajuda equipes a consultar propostas, acompanhar etapas, resumir indicadores e orientar atualizacoes do painel MCMV Rural.`

Instrucoes do agente:

Use o conteudo de `agent-instructions.md`.

## Como conectar na API

1. Publique o backend do painel e confirme que `/api/health` responde.
2. No arquivo `openapi.actions.json`, troque `https://SEU-DOMINIO-AQUI` pela URL publica do backend.
3. No Copilot Studio, abra o agente.
4. Adicione uma ferramenta/action usando uma especificacao OpenAPI.
5. Importe `openapi.actions.json`.
6. Teste primeiro as acoes de leitura:
   - `ObterStats`
   - `ListarPropostas`
   - `DetalharProposta`
   - `ListarEtapas`
7. So libere `AtualizarEtapa` para usuarios autorizados.

## Canais de uso

Canais recomendados:

- Microsoft Teams
- Microsoft 365 Copilot
- Site interno ou demo website

## Observacao de seguranca

A acao `AtualizarEtapa` altera dados. Configure autenticacao, permissoes e confirmacao humana antes de publicar para toda a organizacao.
