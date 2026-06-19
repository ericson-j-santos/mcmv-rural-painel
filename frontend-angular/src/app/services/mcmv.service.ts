import { Injectable } from '@angular/core'
import { HttpClient, HttpParams } from '@angular/common/http'
import { Observable } from 'rxjs'

export interface Proposta {
  num_proposta: string
  uf: string
  municipio: string
  entidade: string
  cnpj: string
  unidades: number
  etapa_atual: string
  atualizado_em: string
}

export interface Stats {
  total_propostas: number
  total_unidades: number
  total_ufs: number
  total_municipios: number
  por_etapa: { etapa: string; cor: string; propostas: number; unidades: number }[]
  por_uf: { uf: string; propostas: number; unidades: number }[]
}

export interface Etapa { nome: string; cor: string }

export interface PropostasPage {
  total: number; pagina: number; por_pagina: number; total_paginas: number
  items: Proposta[]
}

@Injectable({ providedIn: 'root' })
export class McmvService {
  constructor(private http: HttpClient) {}

  getStats(): Observable<Stats> {
    return this.http.get<Stats>('/api/propostas/stats')
  }

  getEtapas(): Observable<Etapa[]> {
    return this.http.get<Etapa[]>('/api/etapas')
  }

  getPropostas(params: Record<string, any>): Observable<PropostasPage> {
    let p = new HttpParams()
    Object.entries(params).forEach(([k, v]) => { if (v) p = p.set(k, v) })
    return this.http.get<PropostasPage>('/api/propostas', { params: p })
  }

  atualizarEtapa(numProposta: string, etapa: string, obs?: string) {
    return this.http.put(`/api/propostas/${numProposta}/etapa`, { etapa, observacao: obs })
  }

  exportarCSV(uf?: string, etapa?: string) {
    const params = new URLSearchParams()
    if (uf) params.set('uf', uf)
    if (etapa) params.set('etapa', etapa)
    window.open(`/api/propostas/export?${params}`)
  }
}
