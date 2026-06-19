import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getStats   = ()              => api.get('/propostas/stats')
export const getEtapas  = ()              => api.get('/etapas')
export const getPropostas = (params)      => api.get('/propostas', { params })
export const atualizarEtapa = (id, body) => api.put(`/propostas/${id}/etapa`, body)
export const exportarCSV = (params)      => {
  const qs = new URLSearchParams(params).toString()
  window.open(`/api/propostas/export?${qs}`)
}
