#!/usr/bin/env bash
# update.sh — Atualiza o MCMV Rural sem reinstalar (código + estático)
# Uso:
#   sudo bash update.sh              # atualiza Python + Vue
#   sudo bash update.sh --skip-vue   # só Python
set -euo pipefail

APP_DIR="/opt/mcmv-rural"
STATIC_DIR="/var/www/mcmv-rural/static"
APP_USER="mcmv"
SKIP_VUE="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "[update] Parando serviço..."
systemctl stop mcmv-rural

echo "[update] Atualizando código Python..."
cp -r "$REPO_ROOT/backend/app"              "$APP_DIR/"
cp    "$REPO_ROOT/backend/requirements.txt" "$APP_DIR/"

echo "[update] Atualizando dependências Python..."
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

if [ "$SKIP_VUE" != "--skip-vue" ]; then
    echo "[update] Buildando Vue 3..."
    cd "$REPO_ROOT/frontend-vue" && npm run build
    echo "[update] Copiando estático..."
    cp -r "$REPO_ROOT/backend/static/." "$STATIC_DIR/"
fi

echo "[update] Ajustando permissões..."
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chown -R "$APP_USER:www-data"  "$STATIC_DIR"

echo "[update] Reiniciando serviço..."
systemctl start  mcmv-rural
systemctl reload nginx

sleep 2
systemctl is-active mcmv-rural && echo "[update] mcmv-rural: ATIVO" || echo "[update] FALHOU"
curl -sf http://127.0.0.1:8082/api/health && echo " — API: OK" || echo " — API: sem resposta"
