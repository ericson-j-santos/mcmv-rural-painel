import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getStats, getEtapas, getPropostas, atualizarEtapa } from '../api'

export const useMcmvStore = defineStore('mcmv', () => {
  const stats     = ref(null)
  const etapas    = ref([])
  const propostas = ref([])
  const meta      = ref({ total: 0, pagina: 1, por_pagina: 20, total_paginas: 1 })
  const loading   = ref(false)
  const filtros   = ref({ uf: '', etapa: '', busca: '', pagina: 1, por_pagina: 20 })

  async function carregarStats() {
    const { data } = await getStats()
    stats.value = data
  }

  async function carregarEtapas() {
    const { data } = await getEtapas()
    etapas.value = data
  }

  async function carregarPropostas(params) {
    loading.value = true
    try {
      const { data } = await getPropostas(params || filtros.value)
      propostas.value = data.items
      meta.value = { total: data.total, pagina: data.pagina, por_pagina: data.por_pagina, total_paginas: data.total_paginas }
    } finally {
      loading.value = false
    }
  }

  async function mudarEtapa(numProposta, etapa, observacao) {
    await atualizarEtapa(numProposta, { etapa, observacao })
    await carregarStats()
    await carregarPropostas()
  }

  return { stats, etapas, propostas, meta, loading, filtros, carregarStats, carregarEtapas, carregarPropostas, mudarEtapa }
})
