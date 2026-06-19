"""Corrige CNPJs no banco SQLite sem apagar dados de etapa."""
import re, sqlite3

DB = r'C:\Users\erics\Downloads\mcmv-rural-painel\backend\mcmv_rural.db'

def clean_cnpj(v):
    if not v:
        return ''
    nums = re.sub(r'[^\d]', '', v)
    if len(nums) == 14:
        return f'{nums[:2]}.{nums[2:5]}.{nums[5:8]}/{nums[8:12]}-{nums[12:14]}'
    return re.sub(r'\s+', '', v)

conn = sqlite3.connect(DB)
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tabelas:', tables)

# Descobre o nome da tabela de propostas
tbl = next((t for t in tables if 'proposta' in t.lower()), None)
if not tbl:
    print('ERRO: tabela de propostas nao encontrada')
    conn.close()
    exit(1)

cols = [r[1] for r in conn.execute(f'PRAGMA table_info({tbl})').fetchall()]
print(f'Tabela {tbl!r}, colunas: {cols}')

pk = 'num_proposta' if 'num_proposta' in cols else cols[0]
rows = conn.execute(f'SELECT {pk}, cnpj FROM {tbl}').fetchall()
dirty = []
for pid, cnpj in rows:
    cleaned = clean_cnpj(cnpj)
    if cnpj != cleaned:
        dirty.append((cleaned, pid))

print(f'CNPJs a corrigir: {len(dirty)}')
if dirty:
    conn.executemany(f'UPDATE {tbl} SET cnpj=? WHERE {pk}=?', dirty)
    conn.commit()
    print('Corrigido com sucesso.')

conn.close()
