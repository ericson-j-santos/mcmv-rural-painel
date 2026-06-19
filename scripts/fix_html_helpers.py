import pathlib

p = pathlib.Path(r'C:\Users\erics\Downloads\mcmv-rural-painel\static-html\painel_mcmv_rural.html')
c = p.read_text(encoding='utf-8')

# 1. CDATA wrapper — silencia warnings do linter HTML sobre < > em JS
c = c.replace('\n<script>\n/*', '\n<script>//<![CDATA[\n/*', 1)
c = c.replace('\n</script>\n</body>', '\n//]]>\n</script>\n</body>', 1)

# 2. Helpers CNPJ / hash / modal antes do onMounted
HELPERS = '''
        // ── CNPJ helpers ─────────────────────────────────────────────────────
        const CNPJ_RE = /^\\d{2}\\.\\d{3}\\.\\d{3}\\/\\d{4}-\\d{2}$/;
        const cnpjValido = cnpj => CNPJ_RE.test(cnpj || '');
        const cnpjNums   = cnpj => (cnpj || '').replace(/[^\\d]/g, '');

        // ── Clipboard ────────────────────────────────────────────────────────
        const copiarHash = hash => {
            if (!hash) return;
            navigator.clipboard?.writeText(hash).catch(() => {});
            hashCopiado.value = hash;
            setTimeout(() => { hashCopiado.value = ''; }, 1800);
        };

        // ── Modal detalhe ─────────────────────────────────────────────────────
        const abrirDetalhe = row => { detalhe.value = row; };

'''
c = c.replace(
    '        onMounted(async () => {',
    HELPERS + '        onMounted(async () => {'
)

# 3. Expõe novos helpers no return
c = c.replace(
    '            toggleFiltroEtapa, salvarEtapa, exportarCSV,\n            ordenar, iconeOrdem,',
    '            toggleFiltroEtapa, salvarEtapa, exportarCSV,\n            ordenar, iconeOrdem,\n            detalhe, hashCopiado, cnpjValido, cnpjNums, copiarHash, abrirDetalhe,'
)

p.write_text(c, encoding='utf-8')
print('OK - helpers adicionados')
print('Tamanho final:', len(c), 'bytes')
