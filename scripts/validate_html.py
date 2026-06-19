import re

with open(r'C:\Users\erics\Downloads\mcmv-rural-painel\static-html\painel_mcmv_rural.html', encoding='utf-8') as f:
    c = f.read()

# Localiza a tag <script> principal (sem atributos src=)
m = re.search(r'<script>(.*?)</script>', c, re.DOTALL)
if not m:
    print('ERRO: script tag nao encontrada')
    exit(1)

js = m.group(1)
print(f'Script length: {len(js)} chars')

bad = re.findall(r'</script>', js, re.IGNORECASE)
status = 'OK' if not bad else f'FAIL ({len(bad)} ocorrencias)'
print(f'</script> dentro do bloco JS: {status}')

syms = ['cnpjValido', 'cnpjNums', 'copiarHash', 'abrirDetalhe',
        'detalhe', 'hashCopiado', 'CNPJ_RE', 'createApp', '.mount']
for s in syms:
    present = s in js
    print(f'  {s}: {"OK" if present else "AUSENTE"}')

print(f'\nmodal-overlay no HTML: {"OK" if "modal-overlay" in c else "AUSENTE"}')
print(f'cnpj.biz no HTML: {"OK" if "cnpj.biz" in c else "AUSENTE"}')
print(f'hash-chip no HTML: {"OK" if "hash-chip" in c else "AUSENTE"}')
