# -*- coding: utf-8 -*-
"""Valida integridade do painel_mcmv_rural.html."""
import re, sys

HTML = r'C:\Users\erics\Downloads\mcmv-rural-painel\static-html\painel_mcmv_rural.html'

PASS = 0
FAIL = 0

def ok(msg):
    global PASS
    print(f'  PASS  {msg}')
    PASS += 1

def fail(msg, detail=''):
    global FAIL
    print(f'  FAIL  {msg}' + (f' -- {detail}' if detail else ''))
    FAIL += 1

def check(cond, msg_ok, msg_fail, detail=''):
    if cond:
        ok(msg_ok)
    else:
        fail(msg_fail, detail)

with open(HTML, encoding='utf-8') as f:
    c = f.read()

# -- Bloco <script> principal -------------------------------------------------
m = re.search(r'<script>(.*?)</script>', c, re.DOTALL)
if not m:
    fail('tag <script> principal nao encontrada')
    sys.exit(1)

js = m.group(1)
ok(f'script length={len(js)} chars')

bad = re.findall(r'</script>', js, re.IGNORECASE)
check(not bad, 'sem </script> prematuro', '</script> prematuro no bloco JS', f'{len(bad)} ocorrencia(s)')

# -- Helpers obrigatorios no JS -----------------------------------------------
print('\n[Helpers JS]')
for sym in ['resolveApiBase', 'API_BASE', 'createApp', '.mount',
            'cnpjValido', 'cnpjNums', 'copiarHash', 'abrirDetalhe',
            'detalhe', 'hashCopiado', 'CNPJ_RE',
            'apiBaseAtual', 'reconfigurarApi',
            'localStorage.getItem', 'localStorage.setItem']:
    check(sym in js, sym, sym, 'ausente no bloco JS')

# -- localStorage em qualquer protocolo (nao so file://) ----------------------
print('\n[resolveApiBase -- localStorage antes de file://]')
resolve_m = re.search(r'function resolveApiBase\(\)(.*?)\nconst API_BASE', js, re.DOTALL)
if resolve_m:
    fn = resolve_m.group(1)
    ls_pos   = fn.find('localStorage.getItem')
    file_pos = fn.find("'file:'")
    ok_order = (ls_pos != -1) and (file_pos == -1 or ls_pos < file_pos)
    check(ok_order,
          'localStorage verificado antes do check file://',
          'localStorage deve aparecer antes do check file://',
          f'ls_pos={ls_pos} file_pos={file_pos}')
else:
    fail('funcao resolveApiBase nao encontrada')

# -- Banner de erro sempre mostra botao Reconfigurar --------------------------
print('\n[Banner de erro]')
banner_m = re.search(r'v-if="erro"(.*?)</div>', c, re.DOTALL)
if banner_m:
    b = banner_m.group(1)
    check('@click="reconfigurarApi"' in b,
          'botao reconfigurarApi presente no banner',
          'botao reconfigurarApi ausente no banner')
    check('v-if="isFile"' not in b,
          'botao nao condicionado por v-if="isFile"',
          'botao ainda condicionado por v-if="isFile" -- mostra so em file://')
else:
    fail('banner de erro nao encontrado')

# -- Elementos HTML do modal e CNPJ -------------------------------------------
print('\n[Elementos HTML]')
for token in ['modal-overlay', 'cnpj.biz', 'hash-chip', 'abrirDetalhe']:
    check(token in c, token, token, 'ausente no HTML')

# -- Abas: existência dos 4 painéis ------------------------------------------
print('\n[Abas]')
for aba in ["aba==='dashboard'", "aba==='propostas'", "aba==='hash-cnpj'", "aba==='fluxo'"]:
    check(aba in c, f'tab panel v-show="{aba}"', f'tab panel ausente: {aba}')

# -- Tab nav buttons ---------------------------------------------------------
for btn in ['dashboard', 'propostas', 'hash-cnpj', 'fluxo']:
    check(f"aba='{btn}'" in c, f'tab-btn {btn}', f'tab-btn ausente: {btn}')

# -- Hash & CNPJ tab: variáveis e elementos ----------------------------------
print('\n[Hash & CNPJ tab]')
for sym in ['hcBusca', 'hcFiltroStatus', 'hcToggleFiltro', 'cnpj_status',
            'hcPagina', 'hcItems', 'hcTotal', 'hcTotalPaginas',
            'hcPaginasVisiveis', 'carregarHC', 'cnpj_validos', 'cnpj_invalidos',
            'uuid-full', 'dot-ok', 'dot-err', 'hc-hint', 'Limpar filtros']:
    check(sym in c, sym, sym, 'ausente')

# -- Fluxo tab: etapas do pipeline -------------------------------------------
print('\n[Fluxo tab]')
for token in ['pdfplumber', 'extrai_mcmv.py', 'limpa_mcmv.py', 'fix_proposta_ids',
              'seed.py', 'fluxo-pipeline', 'fluxo-qualidade']:
    check(token in c, token, token, 'ausente no fluxo tab')

# -- Modal global (fora dos tab panels) --------------------------------------
print('\n[Modal global]')
modal_pos = c.find('<!-- Modal global')
container_close = c.rfind('</div><!-- /container -->')
check(modal_pos != -1 and modal_pos < container_close,
      'modal global posicionado antes de /container',
      'modal global fora de posição ou ausente')

print('\n' + '-' * 50)
T = PASS + FAIL
if FAIL == 0:
    print(f'PASS {PASS}/{T} todos os checks passaram')
else:
    print(f'FAIL {FAIL} falha(s) de {T}')
    sys.exit(1)
