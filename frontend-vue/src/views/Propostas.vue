<template>
  <div>
    <div class="section-title">Lista de Propostas</div>

    <!-- Filtros -->
    <div class="filtros">
      <select v-model="store.filtros.uf" @change="buscar">
        <option value="">Todos os estados</option>
        <option v-for="uf in ufs" :key="uf" :value="uf">{{ uf }}</option>
      </select>
      <select v-model="store.filtros.etapa" @change="buscar">
        <option value="">Todas as etapas</option>
        <option v-for="e in store.etapas" :key="e.nome" :value="e.nome">{{ e.nome }}</option>
      </select>
      <input
        v-model="store.filtros.busca"
        @input="buscarDebounced"
        placeholder="Buscar município ou entidade..."
      />
      <button class="btn-exportar" @click="exportar">⬇ Exportar CSV</button>
      <span class="count-badge">{{ store.meta.total.toLocaleString('pt-BR') }} propostas</span>
    </div>

    <!-- Tabela -->
    <div class="tabela-wrap">
      <div v-if="store.loading" class="loading-row">Carregando...</div>
      <table v-else>
        <thead>
          <tr>
            <th>UF</th>
            <th>Município</th>
            <th>Entidade Organizadora</th>
            <th style="text-align:right">Unidades</th>
            <th>Etapa Atual</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in store.propostas" :key="p.num_proposta">
            <td class="td-uf">{{ p.uf }}</td>
            <td>
              <div class="td-mun">{{ p.municipio }}</div>
              <div class="td-id">{{ p.num_proposta.substring(0, 8) }}…</div>
            </td>
            <td class="td-ent">{{ p.entidade }}</td>
            <td style="text-align:right; font-weight:700">{{ p.unidades }}</td>
            <td>
              <select
                :value="p.etapa_atual"
                class="etapa-sel"
                :style="{ color: corEtapa(p.etapa_atual) }"
                @change="e => mudar(p, e.target.value)"
              >
                <option v-for="et in store.etapas" :key="et.nome" :value="et.nome">
                  {{ et.nome }}
                </option>
              </select>
            </td>
          </tr>
          <tr v-if="!store.propostas.length && !store.loading">
            <td colspan="5" class="empty">Nenhuma proposta encontrada.</td>
          </tr>
        </tbody>
      </table>

      <!-- Paginação -->
      <div class="paginacao">
        <span class="pg-info">Página {{ store.meta.pagina }} de {{ store.meta.total_paginas }}</span>
        <button @click="irPara(1)" :disabled="store.meta.pagina === 1">«</button>
        <button @click="irPara(store.meta.pagina - 1)" :disabled="store.meta.pagina === 1">‹</button>
        <button
          v-for="p in paginasVisiveis"
          :key="p"
          :class="{ ativa: p === store.meta.pagina }"
          @click="irPara(p)"
        >{{ p }}</button>
        <button @click="irPara(store.meta.pagina + 1)" :disabled="store.meta.pagina === store.meta.total_paginas">›</button>
        <button @click="irPara(store.meta.total_paginas)" :disabled="store.meta.pagina === store.meta.total_paginas">»</button>
        <select v-model.number="store.filtros.por_pagina" @change="buscar" class="pp-sel">
          <option :value="20">20/pág</option>
          <option :value="50">50/pág</option>
          <option :value="100">100/pág</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed, ref } from 'vue'
import { useMcmvStore } from '../stores/mcmv'
import { exportarCSV } from '../api'

const store = useMcmvStore()
const ufs = computed(() => [...new Set(store.propostas.map(p => p.uf))].sort())

let debounceTimer = null
function buscarDebounced() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => buscar(), 400)
}

function buscar() {
  store.filtros.pagina = 1
  store.carregarPropostas()
}

function irPara(p) {
  store.filtros.pagina = p
  store.carregarPropostas()
}

const paginasVisiveis = computed(() => {
  const t = store.meta.total_paginas, cur = store.meta.pagina
  const arr = []
  for (let i = Math.max(1, cur - 2); i <= Math.min(t, cur + 2); i++) arr.push(i)
  return arr
})

const COR = {
  'Selecionado': '#3b82f6',
  'Habilitação da Entidade': '#8b5cf6',
  'Contratação': '#f59e0b',
  'Início das Obras': '#f97316',
  'Em Execução': '#06b6d4',
  'Entrega das Chaves': '#16a34a',
}
const corEtapa = nome => COR[nome] || '#94a3b8'

async function mudar(proposta, novaEtapa) {
  proposta.etapa_atual = novaEtapa
  await store.mudarEtapa(proposta.num_proposta, novaEtapa)
}

function exportar() {
  exportarCSV({ uf: store.filtros.uf, etapa: store.filtros.etapa })
}

onMounted(async () => {
  await store.carregarEtapas()
  await store.carregarPropostas()
})
</script>

<style scoped>
.section-title { font-size:1rem; font-weight:700; margin-bottom:12px; display:flex; align-items:center; gap:8px; }
.section-title::before { content:''; display:block; width:4px; height:18px; background:var(--primary); border-radius:2px; }

.filtros { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:14px; align-items:center; }
.filtros select, .filtros input { padding:7px 12px; border:1px solid var(--gray-200); border-radius:7px; font-size:0.82rem; outline:none; }
.filtros select:focus, .filtros input:focus { border-color:var(--primary); }
.count-badge { margin-left:auto; font-size:0.78rem; color:var(--gray-600); background:var(--gray-100); padding:5px 12px; border-radius:20px; }
.btn-exportar { background:var(--primary); color:white; border:none; border-radius:7px; padding:7px 16px; font-size:0.82rem; font-weight:600; }
.btn-exportar:hover { background:var(--primary-dark); }

.tabela-wrap { background:white; border-radius:var(--radius); box-shadow:var(--shadow-sm); overflow:hidden; }
.loading-row { text-align:center; padding:32px; color:var(--gray-400); }
table { width:100%; border-collapse:collapse; font-size:0.82rem; }
thead th { background:var(--primary); color:white; padding:10px 12px; text-align:left; font-size:0.78rem; white-space:nowrap; }
tbody tr { border-bottom:1px solid var(--gray-100); }
tbody tr:hover { background:var(--gray-50); }
tbody td { padding:9px 12px; vertical-align:middle; }
.td-uf { font-weight:700; color:var(--primary); }
.td-mun { font-weight:600; }
.td-id { font-family:monospace; font-size:0.7rem; color:var(--gray-400); }
.td-ent { max-width:260px; font-size:0.78rem; }
.empty { text-align:center; color:var(--gray-400); padding:24px; }

.etapa-sel {
  border:1px solid var(--gray-200); border-radius:6px;
  padding:3px 6px; font-size:0.78rem; font-weight:600;
  background:var(--gray-50); cursor:pointer;
}
.etapa-sel:hover { border-color:var(--primary); }

.paginacao { display:flex; align-items:center; gap:6px; padding:12px 16px; border-top:1px solid var(--gray-100); flex-wrap:wrap; }
.pg-info { font-size:0.78rem; color:var(--gray-600); }
.paginacao button { padding:4px 10px; border:1px solid var(--gray-200); background:white; border-radius:6px; font-size:0.8rem; }
.paginacao button:disabled { opacity:.4; cursor:default; }
.paginacao button.ativa { background:var(--primary); color:white; border-color:var(--primary); }
.pp-sel { margin-left:auto; padding:4px 8px; border:1px solid var(--gray-200); border-radius:6px; font-size:0.8rem; }
</style>
