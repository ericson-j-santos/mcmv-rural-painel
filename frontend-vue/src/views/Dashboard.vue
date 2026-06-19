<template>
  <div>
    <div v-if="!store.stats" class="loading">Carregando estatísticas...</div>
    <template v-else>

      <!-- Cards de resumo -->
      <div class="cards">
        <div class="card" style="--accent:#1a56a0">
          <div class="val">{{ fmt(store.stats.total_propostas) }}</div>
          <div class="lbl">Propostas Selecionadas</div>
        </div>
        <div class="card" style="--accent:#0d9488">
          <div class="val">{{ fmt(store.stats.total_unidades) }}</div>
          <div class="lbl">Unidades Habitacionais</div>
        </div>
        <div class="card" style="--accent:#7c3aed">
          <div class="val">{{ store.stats.total_ufs }}</div>
          <div class="lbl">Estados (UF)</div>
        </div>
        <div class="card" style="--accent:#d97706">
          <div class="val">{{ fmt(store.stats.total_municipios) }}</div>
          <div class="lbl">Municípios</div>
        </div>
        <div class="card" style="--accent:#dc2626">
          <div class="val">{{ fmt(qtdEtapa('Selecionado')) }}</div>
          <div class="lbl">Aguardando Contratação</div>
        </div>
        <div class="card" style="--accent:#16a34a">
          <div class="val">{{ fmt(qtdEtapa('Entrega das Chaves')) }}</div>
          <div class="lbl">Chaves Entregues</div>
        </div>
      </div>

      <!-- Funil de etapas -->
      <div class="section-title">Funil de Implantação</div>
      <div class="etapas-grid">
        <div
          v-for="(e, i) in store.stats.por_etapa"
          :key="e.etapa"
          class="etapa-card"
          :style="{ '--cor': e.cor }"
          @click="irParaEtapa(e.etapa)"
        >
          <span class="badge-pct">{{ pct(e.propostas) }}%</span>
          <div class="etapa-num">Etapa {{ i + 1 }}</div>
          <div class="etapa-nome">{{ e.etapa }}</div>
          <div class="etapa-total">{{ fmt(e.propostas) }}</div>
          <div class="etapa-sub">{{ fmt(e.unidades) }} unidades</div>
          <div class="etapa-bar-wrap">
            <div class="etapa-bar-fill" :style="{ width: pct(e.propostas) + '%', background: e.cor }"></div>
          </div>
        </div>
      </div>

      <!-- Dois painéis -->
      <div class="dois-col">
        <div class="painel-box">
          <div class="section-title">Distribuição por Etapa</div>
          <div class="chart-wrap">
            <canvas ref="chartCanvas"></canvas>
          </div>
        </div>
        <div class="painel-box">
          <div class="section-title">Top Estados por Propostas</div>
          <div class="uf-lista">
            <div class="uf-row" v-for="uf in store.stats.por_uf.slice(0, 15)" :key="uf.uf">
              <div class="uf-nome">{{ uf.uf }}</div>
              <div class="uf-bar-wrap">
                <div class="uf-bar-fill"
                  :style="{ width: (uf.propostas / store.stats.por_uf[0].propostas * 100) + '%' }">
                </div>
              </div>
              <div class="uf-qtd">{{ uf.propostas }} · {{ fmt(uf.unidades) }} un</div>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { onMounted, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Chart from 'chart.js/auto'
import { useMcmvStore } from '../stores/mcmv'

const store = useRouter ? useMcmvStore() : null
const router = useRouter()
const chartCanvas = ref(null)
let chart = null

onMounted(async () => {
  await store.carregarStats()
  await nextTick()
  renderChart()
})

watch(() => store.stats, async () => {
  await nextTick()
  renderChart()
})

function renderChart() {
  if (!chartCanvas.value || !store.stats) return
  if (chart) chart.destroy()
  const etapas = store.stats.por_etapa
  chart = new Chart(chartCanvas.value, {
    type: 'bar',
    data: {
      labels: etapas.map(e => e.etapa),
      datasets: [{
        label: 'Propostas',
        data: etapas.map(e => e.propostas),
        backgroundColor: etapas.map(e => e.cor + 'cc'),
        borderColor: etapas.map(e => e.cor),
        borderWidth: 2,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } }, x: { ticks: { font: { size: 10 } } } }
    }
  })
}

const fmt = n => Number(n).toLocaleString('pt-BR')
const qtdEtapa = nome => store.stats?.por_etapa?.find(e => e.etapa === nome)?.propostas ?? 0
const pct = n => store.stats?.total_propostas ? Math.round(n / store.stats.total_propostas * 100) : 0

function irParaEtapa(etapa) {
  store.filtros.etapa = etapa
  router.push('/propostas')
}
</script>

<style scoped>
.loading { text-align:center; padding:60px; color:var(--gray-400); }

.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:24px; }
.card { background:white; border-radius:var(--radius); padding:16px 18px; box-shadow:var(--shadow-sm); border-left:4px solid var(--accent,#1a56a0); }
.card .val { font-size:2rem; font-weight:800; color:var(--accent,#1a56a0); line-height:1; }
.card .lbl { font-size:0.73rem; color:var(--gray-400); margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }

.section-title { font-size:1rem; font-weight:700; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
.section-title::before { content:''; display:block; width:4px; height:18px; background:var(--primary); border-radius:2px; }

.etapas-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; margin-bottom:28px; }
.etapa-card {
  background:white; border-radius:var(--radius); padding:14px 16px;
  box-shadow:var(--shadow-sm); cursor:pointer;
  transition:transform .15s, box-shadow .15s;
  border-top:3px solid var(--cor,#94a3b8); position:relative;
}
.etapa-card:hover { transform:translateY(-2px); box-shadow:var(--shadow-md); }
.badge-pct { position:absolute; top:10px; right:10px; font-size:0.7rem; font-weight:700; padding:2px 7px; border-radius:20px; background:var(--cor,#94a3b8); color:white; }
.etapa-num { font-size:0.65rem; font-weight:700; color:var(--cor,#64748b); text-transform:uppercase; letter-spacing:1px; }
.etapa-nome { font-size:0.86rem; font-weight:600; margin:4px 0 2px; }
.etapa-total { font-size:1.6rem; font-weight:800; color:var(--cor,#1a56a0); }
.etapa-sub { font-size:0.72rem; color:var(--gray-400); margin-bottom:8px; }
.etapa-bar-wrap { height:5px; background:var(--gray-200); border-radius:3px; overflow:hidden; }
.etapa-bar-fill { height:100%; border-radius:3px; transition:width .4s; }

.dois-col { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:28px; }
@media (max-width:900px) { .dois-col { grid-template-columns:1fr; } }
.painel-box { background:white; border-radius:var(--radius); padding:18px; box-shadow:var(--shadow-sm); }
.chart-wrap { height:260px; position:relative; }

.uf-lista { max-height:320px; overflow-y:auto; }
.uf-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.uf-nome { width:32px; font-size:0.78rem; font-weight:700; color:var(--primary); flex-shrink:0; }
.uf-bar-wrap { flex:1; height:9px; background:var(--gray-200); border-radius:5px; overflow:hidden; }
.uf-bar-fill { height:100%; border-radius:5px; background:linear-gradient(90deg,var(--primary),var(--primary-light)); transition:width .4s; }
.uf-qtd { width:90px; text-align:right; font-size:0.72rem; color:var(--gray-400); flex-shrink:0; }
</style>
