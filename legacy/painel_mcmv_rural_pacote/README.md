# Painel MCMV Rural

Aplicacao HTML estatica para acompanhar a implantacao do MCMV Rural.

## Como abrir

1. Extraia este ZIP em uma pasta.
2. Abra o arquivo `painel_mcmv_rural.html` no navegador.

O painel ja possui os dados embutidos no HTML. O arquivo
`mcmv_rural_lista.json` tambem segue no pacote para consulta, backup ou
regeneracao futura.

## Conteudo do pacote

- `painel_mcmv_rural.html`: aplicacao principal.
- `mcmv_rural_lista.json`: base de dados limpa.
- `extrai_mcmv.py`: script usado para extrair registros do PDF original.
- `limpa_mcmv.py`: script usado para limpar a base extraida.
- `gera_painel.py`: script usado para embutir o JSON no HTML.
- `abrir_painel.py`: abre o painel no navegador padrao.
- `manifest.json`: metadados do pacote.

## Observacao

O painel usa Vue 3 e Chart.js por CDN. Portanto, para carregar essas
bibliotecas em um computador novo, o navegador precisa ter acesso a internet.
Depois de carregado, os dados do painel ficam no proprio HTML/localStorage.
