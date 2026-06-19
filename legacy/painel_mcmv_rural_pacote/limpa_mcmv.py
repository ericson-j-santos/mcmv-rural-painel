import json

with open(r'C:\Users\erics\Downloads\mcmv_rural_lista.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

# Remove linhas de cabeçalho capturadas (uf='UF') e sem município real
limpos = [r for r in dados if r['uf'] != 'UF' and r['municipio'] and r['municipio'] not in ['Município', 'Municipio', 'UF']]

print(f'Antes: {len(dados)} | Depois da limpeza: {len(limpos)}')
total_un = sum(r['unidades'] for r in limpos)
print(f'Total unidades habitacionais: {total_un:,}')

# Adiciona campos de acompanhamento com etapas padrão
etapas = [
    'Selecionado',
    'Habilitação da Entidade',
    'Contratação',
    'Início das Obras',
    'Em Execução',
    'Entrega das Chaves'
]

for r in limpos:
    r['etapa_atual'] = 'Selecionado'
    r['historico'] = []

with open(r'C:\Users\erics\Downloads\mcmv_rural_lista.json', 'w', encoding='utf-8') as f:
    json.dump(limpos, f, ensure_ascii=False, indent=2)

print(f'\nEtapas do processo:')
for i, e in enumerate(etapas, 1):
    print(f'  {i}. {e}')

print(f'\nJSON atualizado salvo.')
