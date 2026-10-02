#!/usr/bin/env pwsh
# Guard fail-closed: Fly.io foi retirado definitivamente em 2026-10-02.
param(
    [switch]$VueOnly,
    [switch]$FlyOnly
)

Write-Error "Deploy bloqueado: Fly.io foi retirado definitivamente do MCMV Rural e não pode ser usado como destino ou contingência. Use a infraestrutura Linux vigente."
exit 1
