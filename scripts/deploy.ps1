#!/usr/bin/env pwsh
# Deploy completo: build Vue → copia static → deploy Fly.io
param(
    [switch]$VueOnly,
    [switch]$FlyOnly
)

$ROOT = Split-Path $PSScriptRoot -Parent

if (-not $FlyOnly) {
    Write-Host "=== [1/3] Build Vue 3 ===" -ForegroundColor Cyan
    Set-Location "$ROOT\frontend-vue"
    npm run build
    if ($LASTEXITCODE -ne 0) { Write-Error "Build Vue falhou"; exit 1 }
    Write-Host "Build gerado em backend/static" -ForegroundColor Green
}

if (-not $VueOnly) {
    Write-Host "=== [2/3] Copiar JSON de dados ===" -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path "$ROOT\backend\data" | Out-Null
    if (Test-Path "C:\Users\erics\Downloads\mcmv_rural_lista.json") {
        Copy-Item "C:\Users\erics\Downloads\mcmv_rural_lista.json" "$ROOT\backend\data\mcmv_rural_lista.json" -Force
    }
    Write-Host "Dados prontos." -ForegroundColor Green

    Write-Host "=== [3/3] Deploy Fly.io ===" -ForegroundColor Cyan
    Set-Location $ROOT
    flyctl deploy --config fly.toml
    if ($LASTEXITCODE -ne 0) { Write-Error "Deploy Fly.io falhou"; exit 1 }
}

Write-Host "=== Deploy concluido ===" -ForegroundColor Green
Write-Host "URL: https://mcmv-rural-painel.fly.dev"
