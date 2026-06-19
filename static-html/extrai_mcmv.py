import pdfplumber, json, re
from collections import defaultdict

pdf_path = r'C:\Users\erics\.claude\projects\c--Users-erics-Downloads\ccfd1282-4b3f-44c7-ae6f-9db80e81682f\tool-results\webfetch-1781718641670-1odefm.pdf'
registros = []
uf_atual = None
municipio_atual = None

with pdfplumber.open(pdf_path) as pdf:
    total = len(pdf.pages)
    print(f'Total paginas: {total}')
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if tables:
            for table in tables:
                for row in table:
                    if not row or all(c is None for c in row):
                        continue
                    cells = [c.strip().replace('\n', ' ') if c else '' for c in row]
                    if len(cells) >= 5:
                        if cells[0] and len(cells[0]) == 2 and cells[0].isupper() and cells[0].isalpha():
                            uf_atual = cells[0]
                        if cells[1] and cells[1] not in ['UF', 'Municipio', 'Município', '']:
                            municipio_atual = cells[1]
                        num_proposta = cells[2] if len(cells) > 2 else ''
                        entidade = cells[3] if len(cells) > 3 else ''
                        cnpj = cells[4] if len(cells) > 4 else ''
                        unidades_str = cells[5] if len(cells) > 5 else ''
                        if num_proposta and len(num_proposta) > 10 and uf_atual:
                            try:
                                qtd = int(re.sub(r'[^\d]', '', unidades_str)) if unidades_str else 0
                            except:
                                qtd = 0
                            registros.append({
                                'uf': uf_atual,
                                'municipio': municipio_atual or '',
                                'num_proposta': num_proposta,
                                'entidade': entidade,
                                'cnpj': cnpj,
                                'unidades': qtd,
                                'etapa_atual': 'Selecionado',
                                'status': 'pendente'
                            })

print(f'Total registros extraidos: {len(registros)}')

por_uf = defaultdict(lambda: {'propostas': 0, 'unidades': 0})
for r in registros:
    por_uf[r['uf']]['propostas'] += 1
    por_uf[r['uf']]['unidades'] += r['unidades']

print('\nResumo por UF:')
total_un = 0
for uf in sorted(por_uf):
    d = por_uf[uf]
    total_un += d['unidades']
    print(f'  {uf}: {d["propostas"]} propostas, {d["unidades"]} unidades')

print(f'\nTOTAL: {len(registros)} propostas, {total_un} unidades')

with open(r'C:\Users\erics\Downloads\mcmv_rural_lista.json', 'w', encoding='utf-8') as f:
    json.dump(registros, f, ensure_ascii=False, indent=2)
print('\nSalvo em C:/Users/erics/Downloads/mcmv_rural_lista.json')
