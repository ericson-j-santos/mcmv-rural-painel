"""Atualiza painel_mcmv_rural.html para ler do backend em vez de dados embutidos."""
import re, pathlib

SRC = pathlib.Path(__file__).parent.parent / "static-html" / "painel_mcmv_rural.html"
content = SRC.read_text(encoding="utf-8")

# ── Template substitutions ────────────────────────────────────────────────────
SUBS = [
    ('<div class="container" v-if="dados.length">',
     '<div class="container" v-if="stats && !carregando">'),
    ("{{ fmt(totalPropostas) }}",  "{{ fmt(stats.total_propostas) }}"),
    ("{{ fmt(totalUnidades) }}",   "{{ fmt(stats.total_unidades) }}"),
    ("{{ totalUFs }}",              "{{ stats.total_ufs }}"),
    ("{{ fmt(totalMunicipios) }}", "{{ fmt(stats.total_municipios) }}"),
    ("propostas · {{ fmt(unidadesEtapa(etapa.nome)) }} unidades",
     "propostas · {{ fmt(unidEtapa(etapa.nome)) }} unidades"),
    ("(uf.qtd / rankingUF[0].qtd * 100)", "(uf.propostas / rankingUF[0].propostas * 100)"),
    ("{{ fmt(uf.qtd) }} prop · {{ fmt(uf.unidades) }} un",
     "{{ fmt(uf.propostas) }} prop · {{ fmt(uf.unidades) }} un"),
    ('<span class="count-badge">{{ dadosFiltrados.length }} propostas encontradas</span>',
     '<span class="count-badge">{{ totalFiltrado }} propostas encontradas</span>'),
    ('v-for="(row, i) in paginado"', 'v-for="(row, i) in items"'),
    ('@change="salvarEstado"',       '@change="salvarEtapa(row, $event.target.value)"'),
    ('v-if="!paginado.length"',     'v-if="!items.length && !carregando"'),
    ("⏳ Carregando dados do MCMV Rural...", "⏳ Conectando ao backend..."),
    ('<div id="app">\n\n<header>',
     '<div id="app">\n\n'
     '<div v-if="erro" style="background:#fef2f2;border-left:4px solid #dc2626;'
     'padding:14px 20px;font-size:0.85rem;color:#7f1d1d">\n'
     '  ⚠️ {{ erro }}\n'
     '  <br><small style="opacity:.7">Configure <code>window.MCMV_API_BASE</code> '
     'ou inicie o backend em localhost:8082</small>\n'
     '</div>\n\n<header>'),
]

for old, new in SUBS:
    if old in content:
        content = content.replace(old, new)
        print(f"  OK: {old[:60]!r}")
    else:
        print(f"  MISS: {old[:60]!r}")

# ── Corta a partir de <script> e insere novo script ──────────────────────────
cut = content.find("\n<script>")
if cut == -1:
    cut = content.find("<script>")

NEW_SCRIPT = r"""
<script>
/*
 * Configuração do backend — adicione ANTES deste script se precisar de URL fixa:
 *   <script>window.MCMV_API_BASE = 'https://mcmv-rural-painel.fly.dev';</script>
 *   <script>window.MCMV_API_BASE = 'http://localhost:8082';</script>
 * Padrão: '' (mesmo host — funciona atrás do nginx)
 */
const API_BASE = (window.MCMV_API_BASE || '').replace(/\/$/, '');

const { createApp, ref, computed, onMounted, watch, nextTick } = Vue;

const ETAPAS_CONFIG = [
    { nome: 'Selecionado',             cor: '#3b82f6' },
    { nome: 'Habilitação da Entidade', cor: '#8b5cf6' },
    { nome: 'Contratação',             cor: '#f59e0b' },
    { nome: 'Início das Obras',        cor: '#f97316' },
    { nome: 'Em Execução',             cor: '#06b6d4' },
    { nome: 'Entrega das Chaves',      cor: '#16a34a' },
];

createApp({
    setup() {
        const carregando    = ref(true);
        const erro          = ref('');
        const stats         = ref(null);
        const items         = ref([]);
        const totalFiltrado = ref(0);
        const pagina        = ref(1);
        const porPagina     = ref(20);
        const totalPaginas  = ref(1);
        const filtroUF      = ref('');
        const filtroEtapa   = ref('');
        const busca         = ref('');
        const ordemCampo    = ref('');
        const ordemDir      = ref(1);
        let buscaTimer  = null;
        let graficoInst = null;

        const etapas    = ETAPAS_CONFIG;
        const listaUFs  = computed(() => (stats.value?.por_uf || []).map(r => r.uf));
        const rankingUF = computed(() => stats.value?.por_uf ?? []);

        const fmt = n => (n ?? 0).toLocaleString('pt-BR');
        const pct = n => stats.value?.total_propostas
            ? Math.round(n / stats.value.total_propostas * 100) : 0;

        const countEtapa = nome =>
            stats.value?.por_etapa?.find(e => e.etapa === nome)?.propostas ?? 0;
        const unidEtapa = nome =>
            stats.value?.por_etapa?.find(e => e.etapa === nome)?.unidades ?? 0;

        // ── API ──────────────────────────────────────────────────────────────
        const carregarStats = async () => {
            const r = await fetch(`${API_BASE}/api/propostas/stats`);
            if (!r.ok) throw new Error(`/api/propostas/stats retornou ${r.status}`);
            stats.value = await r.json();
        };

        const carregarPropostas = async () => {
            const p = new URLSearchParams({
                pagina: pagina.value,
                por_pagina: porPagina.value,
            });
            if (filtroUF.value)    p.append('uf',    filtroUF.value);
            if (filtroEtapa.value) p.append('etapa', filtroEtapa.value);
            if (busca.value)       p.append('busca', busca.value);

            const r = await fetch(`${API_BASE}/api/propostas?${p}`);
            if (!r.ok) throw new Error(`/api/propostas retornou ${r.status}`);
            const d = await r.json();
            items.value         = d.items ?? [];
            totalFiltrado.value = d.total ?? 0;
            totalPaginas.value  = d.total_paginas ?? 1;
        };

        const salvarEtapa = async (proposta, novaEtapa) => {
            if (!novaEtapa || novaEtapa === proposta.etapa_atual) return;
            const anterior = proposta.etapa_atual;
            proposta.etapa_atual = novaEtapa;
            try {
                const r = await fetch(
                    `${API_BASE}/api/propostas/${encodeURIComponent(proposta.num_proposta)}/etapa`,
                    {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ etapa: novaEtapa }),
                    }
                );
                if (!r.ok) throw new Error(`PUT /etapa ${r.status}`);
                await carregarStats();
                renderGrafico();
            } catch (e) {
                proposta.etapa_atual = anterior;
                alert('Erro ao salvar etapa: ' + e.message);
            }
        };

        const exportarCSV = () => {
            const p = new URLSearchParams();
            if (filtroUF.value)    p.append('uf',    filtroUF.value);
            if (filtroEtapa.value) p.append('etapa', filtroEtapa.value);
            if (busca.value)       p.append('busca', busca.value);
            window.open(`${API_BASE}/api/propostas/export?${p}`, '_blank');
        };

        // ── Gráfico ──────────────────────────────────────────────────────────
        const renderGrafico = () => {
            if (!stats.value) return;
            nextTick(() => {
                const ctx = document.getElementById('chartEtapas');
                if (!ctx) return;
                if (graficoInst) graficoInst.destroy();
                graficoInst = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: etapas.map(e => e.nome),
                        datasets: [{
                            label: 'Propostas',
                            data:  etapas.map(e => countEtapa(e.nome)),
                            backgroundColor: etapas.map(e => e.cor + 'cc'),
                            borderColor:     etapas.map(e => e.cor),
                            borderWidth: 1.5, borderRadius: 6,
                        }],
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                    },
                });
            });
        };

        const toggleFiltroEtapa = nome => {
            filtroEtapa.value = filtroEtapa.value === nome ? '' : nome;
            pagina.value = 1;
        };

        const ordenar = campo => {
            if (ordemCampo.value === campo) ordemDir.value *= -1;
            else { ordemCampo.value = campo; ordemDir.value = 1; }
            items.value = [...items.value].sort((a, b) => {
                const va = a[campo], vb = b[campo];
                return (va < vb ? -1 : va > vb ? 1 : 0) * ordemDir.value;
            });
        };

        const iconeOrdem = campo =>
            ordemCampo.value !== campo ? '' : ordemDir.value === 1 ? ' ↑' : ' ↓';

        const paginasVisiveis = computed(() => {
            const total = totalPaginas.value, atual = pagina.value;
            const start = Math.max(1, atual - 2), end = Math.min(total, atual + 2);
            const range = [];
            for (let i = start; i <= end; i++) range.push(i);
            return range;
        });

        watch([filtroUF, filtroEtapa, porPagina], () => {
            pagina.value = 1;
            carregarPropostas();
        });
        watch(pagina, carregarPropostas);
        watch(busca, () => {
            clearTimeout(buscaTimer);
            buscaTimer = setTimeout(() => { pagina.value = 1; carregarPropostas(); }, 350);
        });

        onMounted(async () => {
            try {
                await carregarStats();
                await carregarPropostas();
                renderGrafico();
            } catch (e) {
                erro.value = `Não foi possível conectar ao backend (${API_BASE || 'mesmo host'}): ${e.message}.`;
            } finally {
                carregando.value = false;
            }
        });

        return {
            carregando, erro, stats, items, totalFiltrado,
            pagina, porPagina, totalPaginas, paginasVisiveis,
            filtroUF, filtroEtapa, busca,
            etapas, listaUFs, rankingUF,
            fmt, pct, countEtapa, unidEtapa,
            toggleFiltroEtapa, salvarEtapa, exportarCSV,
            ordenar, iconeOrdem,
        };
    },
}).mount('#app');
</script>
</body>
</html>
"""

result = content[:cut] + NEW_SCRIPT
SRC.write_text(result, encoding="utf-8")
print(f"\nArquivo salvo: {len(result):,} bytes (era ~373KB com dados embutidos)")