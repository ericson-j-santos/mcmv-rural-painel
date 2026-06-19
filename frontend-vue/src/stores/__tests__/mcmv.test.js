import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMcmvStore } from '../mcmv'
import * as api from '../../api'

// ─── Mocks da API ─────────────────────────────────────────────────────────────
vi.mock('../../api', () => ({
  getStats: vi.fn(),
  getEtapas: vi.fn(),
  getPropostas: vi.fn(),
  atualizarEtapa: vi.fn(),
  exportarCSV: vi.fn(),
}))

const STATS_MOCK = {
  total_propostas: 5,
  total_unidades: 240,
  total_ufs: 4,
  total_municipios: 5,
  por_etapa: [
    { etapa: 'Selecionado',             cor: '#3b82f6', propostas: 2, unidades: 80 },
    { etapa: 'Habilitação da Entidade', cor: '#8b5cf6', propostas: 0, unidades: 0  },
    { etapa: 'Contratação',             cor: '#f59e0b', propostas: 1, unidades: 20 },
    { etapa: 'Início das Obras',        cor: '#f97316', propostas: 0, unidades: 0  },
    { etapa: 'Em Execução',             cor: '#06b6d4', propostas: 1, unidades: 100},
    { etapa: 'Entrega das Chaves',      cor: '#16a34a', propostas: 1, unidades: 40 },
  ],
  por_uf: [
    { uf: 'BA', propostas: 2, unidades: 50 },
    { uf: 'SP', propostas: 1, unidades: 100 },
  ],
}

const PROPOSTAS_MOCK = {
  total: 5, pagina: 1, por_pagina: 20, total_paginas: 1,
  items: [
    { num_proposta: 'aaa-001', uf: 'AC', municipio: 'Acrelândia', entidade: 'Assoc. AC', unidades: 50, etapa_atual: 'Selecionado', atualizado_em: '2026-06-18T00:00:00' },
    { num_proposta: 'bbb-002', uf: 'BA', municipio: 'Salvador',   entidade: 'Coop. BA',  unidades: 30, etapa_atual: 'Selecionado', atualizado_em: '2026-06-18T00:00:00' },
  ],
}

const ETAPAS_MOCK = [
  { nome: 'Selecionado',             cor: '#3b82f6' },
  { nome: 'Habilitação da Entidade', cor: '#8b5cf6' },
  { nome: 'Contratação',             cor: '#f59e0b' },
  { nome: 'Início das Obras',        cor: '#f97316' },
  { nome: 'Em Execução',             cor: '#06b6d4' },
  { nome: 'Entrega das Chaves',      cor: '#16a34a' },
]

// ─── Testes ───────────────────────────────────────────────────────────────────
describe('useMcmvStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('estado inicial', () => {
    it('stats começa null', () => {
      const store = useMcmvStore()
      expect(store.stats).toBeNull()
    })

    it('etapas começa vazio', () => {
      const store = useMcmvStore()
      expect(store.etapas).toEqual([])
    })

    it('propostas começa vazio', () => {
      const store = useMcmvStore()
      expect(store.propostas).toEqual([])
    })

    it('loading começa false', () => {
      const store = useMcmvStore()
      expect(store.loading).toBe(false)
    })

    it('filtros começa com valores padrão', () => {
      const store = useMcmvStore()
      expect(store.filtros.uf).toBe('')
      expect(store.filtros.etapa).toBe('')
      expect(store.filtros.pagina).toBe(1)
    })
  })

  describe('carregarStats', () => {
    it('popula stats com dados da API', async () => {
      api.getStats.mockResolvedValue({ data: STATS_MOCK })
      const store = useMcmvStore()
      await store.carregarStats()
      expect(store.stats).toEqual(STATS_MOCK)
    })

    it('chama getStats uma vez', async () => {
      api.getStats.mockResolvedValue({ data: STATS_MOCK })
      const store = useMcmvStore()
      await store.carregarStats()
      expect(api.getStats).toHaveBeenCalledTimes(1)
    })
  })

  describe('carregarEtapas', () => {
    it('popula etapas com 6 itens', async () => {
      api.getEtapas.mockResolvedValue({ data: ETAPAS_MOCK })
      const store = useMcmvStore()
      await store.carregarEtapas()
      expect(store.etapas).toHaveLength(6)
    })

    it('cada etapa tem nome e cor', async () => {
      api.getEtapas.mockResolvedValue({ data: ETAPAS_MOCK })
      const store = useMcmvStore()
      await store.carregarEtapas()
      store.etapas.forEach(e => {
        expect(e).toHaveProperty('nome')
        expect(e).toHaveProperty('cor')
      })
    })
  })

  describe('carregarPropostas', () => {
    it('popula propostas e meta', async () => {
      api.getPropostas.mockResolvedValue({ data: PROPOSTAS_MOCK })
      const store = useMcmvStore()
      await store.carregarPropostas()
      expect(store.propostas).toHaveLength(2)
      expect(store.meta.total).toBe(5)
    })

    it('ativa loading durante a chamada', async () => {
      let loadingDurante = false
      api.getPropostas.mockImplementation(async () => {
        loadingDurante = true
        return { data: PROPOSTAS_MOCK }
      })
      const store = useMcmvStore()
      const promise = store.carregarPropostas()
      expect(store.loading).toBe(true)
      await promise
      expect(store.loading).toBe(false)
    })

    it('passa filtros como parâmetros', async () => {
      api.getPropostas.mockResolvedValue({ data: PROPOSTAS_MOCK })
      const store = useMcmvStore()
      store.filtros.uf = 'BA'
      store.filtros.etapa = 'Selecionado'
      await store.carregarPropostas()
      expect(api.getPropostas).toHaveBeenCalledWith(
        expect.objectContaining({ uf: 'BA', etapa: 'Selecionado' })
      )
    })
  })

  describe('mudarEtapa', () => {
    it('chama atualizarEtapa com id e etapa corretos', async () => {
      api.atualizarEtapa.mockResolvedValue({ data: {} })
      api.getStats.mockResolvedValue({ data: STATS_MOCK })
      api.getPropostas.mockResolvedValue({ data: PROPOSTAS_MOCK })
      const store = useMcmvStore()
      await store.mudarEtapa('aaa-001', 'Contratação')
      expect(api.atualizarEtapa).toHaveBeenCalledWith('aaa-001', { etapa: 'Contratação', observacao: undefined })
    })

    it('atualiza stats após mudança de etapa', async () => {
      api.atualizarEtapa.mockResolvedValue({ data: {} })
      api.getStats.mockResolvedValue({ data: STATS_MOCK })
      api.getPropostas.mockResolvedValue({ data: PROPOSTAS_MOCK })
      const store = useMcmvStore()
      await store.mudarEtapa('aaa-001', 'Contratação')
      expect(api.getStats).toHaveBeenCalled()
    })
  })
})
