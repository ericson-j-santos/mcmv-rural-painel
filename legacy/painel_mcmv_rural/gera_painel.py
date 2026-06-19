import json

with open(r'C:\Users\erics\Downloads\mcmv_rural_lista.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

with open(r'C:\Users\erics\Downloads\painel_mcmv_rural.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Injeta os dados como constante JS antes do bloco de setup
dados_js = json.dumps(dados, ensure_ascii=False)
inject = f'\nconst DADOS_EMBED = {dados_js};\n'
html = html.replace('const ETAPAS = [', inject + 'const ETAPAS = [')

# Atualiza a função carregar para usar DADOS_EMBED se fetch falhar
html = html.replace(
    "// fallback: mostra instrução\n        console.warn('Carregue o arquivo mcmv_rural_lista.json na mesma pasta que este HTML.');",
    "dados.value = DADOS_EMBED;\n        salvarEstado();"
)

# Também usa DADOS_EMBED como primeira tentativa quando não há localStorage
html = html.replace(
    "// 2. Tenta carregar do arquivo local\n      try {",
    "// 2. Usa dados embutidos se não encontrar JSON externo\n      if (typeof DADOS_EMBED !== 'undefined' && !salvo) {\n        dados.value = DADOS_EMBED;\n        salvarEstado();\n        return;\n      }\n      try {"
)

with open(r'C:\Users\erics\Downloads\painel_mcmv_rural.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML gerado com {len(dados)} registros embutidos.')
print('Arquivo: C:\\Users\\erics\\Downloads\\painel_mcmv_rural.html')
