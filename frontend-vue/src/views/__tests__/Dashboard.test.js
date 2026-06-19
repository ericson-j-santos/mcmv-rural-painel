import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../Dashboard.vue'
import { useMcmvStore } from '../../stores/mcmv'
import * as api from '../../api'

vi.mock('../../api', () => ({
  getStats: vi.fn(),
  getEtapas: vi.fn(),
  getPropostas: vi.fn(),
  atualizarEtapa: vi.fn(),
  exportarCSV: vi.fn(),
}))

// Chart.js não funciona em jsdom — substitui por classe vazia
vi.mock('chart.js/auto', () => ({
  default: class Chart {
    constructor() {}
    destroy() {}
    update() {}
  },
}))

const STATS_MOCK = {
  total_propostas: 5,
  total_unidades: 240,
  total_ufs: 4,
  total_municipios: 5,
  por_etapa: [
    { etapa: 'Selecionado',             cor: '#3b82f6', propostas: 3, unidades: 150 },
    { etapa: 'Habilitação da Entidade', cor: '#8b5cf6', propostas: 0, unidades: 0   },
    { etapa: 'Contratação',             cor: '#f59e0b', propostas: 1, unidades: 20  },
    { etapa: 'Início das Obras',        cor: '#f97316', propostas: 0, unidades: 0   },
    { etapa: 'Em Execução',             cor: '#06b6d4', propostas: 1, unidades: 30  },
    { etapa: 'Entrega das Chaves',      cor: '#16a34a', propostas: 0, unidades: 0   },
  ],
  por_uf: [
    { uf: 'BA', propostas: 3, unidades: 150 },
    { uf: 'SP', propostas: 1, unidades: 30  },
    { uf: 'MG', propostas: 1, unidades: 60  },
  ],
}

function makeWrapper() {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: { template: '<div/>' } },
      { path: '/dashboard', component: Dashboard },
      { path: '/propostas', component: { template: '<div/>' } },
    ],
  })
  return mount(Dashboard, {
    global: { plugins: [createPinia(), router] },
  })
}

describe('Dashboard.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    api.getStats.mockResolvedValue({ data: STATS_MOCK })
  })

  describe('renderização inicial', () => {
    it('mostra loading antes dos dados chegarem', () => {
      api.getStats.mockImplementation(() => new Promise(() => {})) // nunca resolve
      const wrapper = makeWrapper()
      expect(wrapper.text()).toContain('Carregando')
    })

    it('exibe cards de resumo após carregar', async () => {
      const wrapper = makeWrapper()
      await flushPromises()
      const cards = wrapper.findAll('.card')
      expect(cards.length).toBeGreaterThanOrEqual(4)
    })

    it('exibe total de propostas correto', async () => {
      const wrapper = makeWrapper()
      await flushPromises()
      expect(wrapper.text()).toContain('5')
    })

    it('exibe total de unidades correto', async () => {
      const wrapper = makeWrapper()
      await flushPromises()
      expect(wrapper.text()).toContain('240')
    })
  })

  describe('funil de etapas', () => {
    it('renderiza 6 cards de etapa', async () => {
      const wrapper = makeWrapper()
      await flushPromises()
      const etapaCards = wrapper.findAll('.etapa-card')
      expect(etapaCards).toHaveLength(6)
    })

    it('exibe nome de cada etapa', async () => {
      const wrapper = makeWrapper()
      await flushPromises()
      expect(wrapper.text()).toContain('Selecionado')
      expect(wrapper.text()).toContain('Contratação')
      expect(wrapper.text()).toContain('Entrega das Chaves')
    })

    it('etapa com 0 propostas mostra "0"', async () => {
      const wrapper = makeWrapper()
      await flushPromises()
      const cards = wrapper.findAll('.etapa-card')
      const habilitacao = cards.find(c => c.text().includes('Habilitação'))
      expect(habilitacao.text()).toContain('0')
    })
  })

  describe('ranking de UFs', () => {
    it('renderiza linhas de UF', async () => {
      const wrapper = makeWrapper()
      await flushPromises()
      expect(wrapper.text()).toContain('BA')
      expect(wrapper.text()).toContain('SP')
    })
  })

  describe('navegação por etapa', () => {
    it('clicar em etapa-card navega para /propostas', async () => {
      const router = createRouter({
        history: createWebHistory(),
        routes: [
          { path: '/dashboard', component: Dashboard },
          { path: '/propostas', component: { template: '<div/>' } },
        ],
      })
      const wrapper = mount(Dashboard, {
        global: { plugins: [createPinia(), router] },
      })
      await flushPromises()
      const store = useMcmvStore()
      store.stats = STATS_MOCK

      const card = wrapper.find('.etapa-card')
      await card.trigger('click')
      await flushPromises()
      expect(router.currentRoute.value.path).toBe('/propostas')
    })
  })
})
