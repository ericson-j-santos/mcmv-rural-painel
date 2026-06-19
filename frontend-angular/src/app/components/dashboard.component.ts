import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core'
import { CommonModule } from '@angular/common'
import { Router } from '@angular/router'
import Chart from 'chart.js/auto'
import { McmvService, Stats } from '../services/mcmv.service'

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="stats">
      <!-- Cards -->
      <div class="cards">
        <div class="card" style="--accent:#1a56a0"><div class="val">{{fmt(stats.total_propostas)}}</div><div class="lbl">Propostas</div></div>
        <div class="card" style="--accent:#0d9488"><div class="val">{{fmt(stats.total_unidades)}}</div><div class="lbl">Unidades</div></div>
        <div class="card" style="--accent:#7c3aed"><div class="val">{{stats.total_ufs}}</div><div class="lbl">Estados</div></div>
        <div class="card" style="--accent:#d97706"><div class="val">{{fmt(stats.total_municipios)}}</div><div class="lbl">Municípios</div></div>
        <div class="card" style="--accent:#dc2626"><div class="val">{{qtdEtapa('Selecionado')}}</div><div class="lbl">Aguard. Contratação</div></div>
        <div class="card" style="--accent:#16a34a"><div class="val">{{qtdEtapa('Entrega das Chaves')}}</div><div class="lbl">Chaves Entregues</div></div>
      </div>

      <!-- Funil -->
      <div class="section-title">Funil de Implantação</div>
      <div class="etapas-grid">
        <div *ngFor="let e of stats.por_etapa; let i = index"
          class="etapa-card" [style.--cor]="e.cor"
          (click)="irParaEtapa(e.etapa)">
          <span class="badge-pct">{{pct(e.propostas)}}%</span>
          <div class="etapa-num">Etapa {{i+1}}</div>
          <div class="etapa-nome">{{e.etapa}}</div>
          <div class="etapa-total">{{fmt(e.propostas)}}</div>
          <div class="etapa-sub">{{fmt(e.unidades)}} unidades</div>
        </div>
      </div>

      <!-- Gráfico + UF -->
      <div class="dois-col">
        <div class="painel-box">
          <div class="section-title">Por Etapa</div>
          <div style="height:260px;position:relative">
            <canvas #chartCanvas></canvas>
          </div>
        </div>
        <div class="painel-box">
          <div class="section-title">Top Estados</div>
          <div class="uf-lista">
            <div *ngFor="let uf of stats.por_uf.slice(0,15)" class="uf-row">
              <div class="uf-nome">{{uf.uf}}</div>
              <div class="uf-bar-wrap"><div class="uf-bar-fill"
                [style.width.%]="uf.propostas / stats.por_uf[0].propostas * 100"></div></div>
              <div class="uf-qtd">{{uf.propostas}} · {{fmt(uf.unidades)}}un</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div *ngIf="!stats" class="loading">Carregando...</div>
  `,
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit, AfterViewInit {
  @ViewChild('chartCanvas') chartCanvas!: ElementRef
  stats: Stats | null = null
  private chart: any = null

  constructor(private svc: McmvService, private router: Router) {}

  ngOnInit() {
    this.svc.getStats().subscribe(s => { this.stats = s })
  }

  ngAfterViewInit() {
    if (this.stats) this.renderChart()
  }

  renderChart() {
    if (!this.chartCanvas || !this.stats) return
    if (this.chart) this.chart.destroy()
    this.chart = new Chart(this.chartCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels: this.stats.por_etapa.map(e => e.etapa),
        datasets: [{ label: 'Propostas', data: this.stats.por_etapa.map(e => e.propostas),
          backgroundColor: this.stats.por_etapa.map(e => e.cor + 'cc'),
          borderColor: this.stats.por_etapa.map(e => e.cor),
          borderWidth: 2, borderRadius: 6 }]
      },
      options: { responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true }, x: { ticks: { font: { size: 10 } } } } }
    })
  }

  fmt(n: number) { return n?.toLocaleString('pt-BR') }
  qtdEtapa(nome: string) { return this.stats?.por_etapa.find(e => e.etapa === nome)?.propostas ?? 0 }
  pct(n: number) { return this.stats?.total_propostas ? Math.round(n / this.stats.total_propostas * 100) : 0 }
  irParaEtapa(etapa: string) { this.router.navigate(['/propostas'], { queryParams: { etapa } }) }
}
