<template>
  <header class="app-header">
    <span class="logo">🏘️</span>
    <div class="header-info">
      <h1>MCMV Rural — Painel de Implantação</h1>
      <p>Seleção MCID 2025/2026 · Portaria nº 1.161/2025 · Publicado 12/06/2026</p>
    </div>
    <nav class="app-nav">
      <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
      <router-link to="/propostas" class="nav-link">Propostas</router-link>
    </nav>
  </header>
  <main class="app-main">
    <router-view />
  </main>
</template>

<style>
.app-header {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white; padding: 14px 24px;
  display: flex; align-items: center; gap: 14px;
  position: sticky; top: 0; z-index: 100;
}
.logo { font-size: 28px; }
.header-info h1 { font-size: 1.15rem; font-weight: 700; }
.header-info p { font-size: 0.73rem; opacity: 0.75; margin-top: 2px; }
.app-nav { margin-left: auto; display: flex; gap: 6px; }
.nav-link {
  padding: 6px 14px; border-radius: 6px; font-size: 0.85rem; font-weight: 600;
  color: rgba(255,255,255,.8); transition: all .15s;
}
.nav-link:hover, .nav-link.router-link-active {
  background: rgba(255,255,255,.15); color: white;
}
.app-main { max-width: 1400px; margin: 0 auto; padding: 20px 16px; }
</style>
