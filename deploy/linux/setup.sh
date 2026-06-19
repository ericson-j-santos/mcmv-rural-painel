#!/usr/bin/env bash
# setup.sh — MCMV Rural em Ubuntu 22.04/24.04 (sem Docker, sem DuckDNS)
#
# Uso:
#   sudo bash setup.sh <IP_ou_hostname>        # HTTPS com cert autoassinado (padrão)
#   sudo bash setup.sh <hostname> --ssl        # HTTPS via Let's Encrypt (porta 80 pública)
#   sudo bash setup.sh <IP> --test             # executa suite de testes após instalar
#
# Exemplos:
#   sudo bash setup.sh 192.168.1.50
#   sudo bash setup.sh meu-servidor.empresa.com --ssl
set -euo pipefail

SERVER_NAME="${1:?Informe o IP ou hostname. Ex: 192.168.1.50}"
MODE="${2:-}"           # --ssl | --test | vazio
APP_DIR="/opt/mcmv-rural"
STATIC_DIR="/var/www/mcmv-rural/static"
APP_USER="mcmv"
DATA_DIR="$APP_DIR/data"
SSL_DIR="/etc/ssl/mcmv-rural"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "======================================================"
echo " MCMV Rural — Setup Linux"
echo " Servidor : $SERVER_NAME"
echo " SSL      : ${MODE/--ssl/Let's Encrypt}${MODE:-autoassinado}"
echo "======================================================"

# ─── 1. Dependências ───────────────────────────────────────────────────────────
echo "[1/8] Instalando dependências..."
apt-get update -qq
PKGS="python3.12 python3.12-venv python3-pip nginx openssl"
[ "$MODE" = "--ssl" ] && PKGS="$PKGS certbot python3-certbot-nginx"
apt-get install -y -qq $PKGS

# ─── 2. Usuário dedicado ───────────────────────────────────────────────────────
echo "[2/8] Criando usuário $APP_USER..."
id "$APP_USER" &>/dev/null || \
    useradd --system --shell /bin/false --create-home --home-dir "$APP_DIR" "$APP_USER"

# ─── 3. Certificado SSL ────────────────────────────────────────────────────────
echo "[3/8] Configurando certificado SSL..."
mkdir -p "$SSL_DIR"

if [ "$MODE" = "--ssl" ]; then
    # Let's Encrypt — feito depois que o nginx subir (passo 7)
    CERT_PATH="/etc/letsencrypt/live/$SERVER_NAME/fullchain.pem"
    KEY_PATH="/etc/letsencrypt/live/$SERVER_NAME/privkey.pem"
    echo "  Let's Encrypt será configurado após o nginx subir."
else
    # Autoassinado — válido por 3650 dias
    CERT_PATH="$SSL_DIR/cert.pem"
    KEY_PATH="$SSL_DIR/key.pem"
    if [ ! -f "$CERT_PATH" ]; then
        openssl req -x509 -nodes -days 3650 \
            -newkey rsa:2048 \
            -keyout "$KEY_PATH" \
            -out    "$CERT_PATH" \
            -subj   "/CN=$SERVER_NAME/O=MCMVRural/C=BR" \
            -addext "subjectAltName=IP:$SERVER_NAME,DNS:$SERVER_NAME" \
            2>/dev/null
        echo "  Certificado autoassinado gerado em $SSL_DIR"
    else
        echo "  Certificado já existe, mantendo."
    fi
fi
chmod 640 "$KEY_PATH" "$CERT_PATH"

# ─── 4. Aplicação ──────────────────────────────────────────────────────────────
echo "[4/8] Instalando aplicação em $APP_DIR..."
mkdir -p "$DATA_DIR" "$STATIC_DIR"
cp -r "$REPO_ROOT/backend/app"              "$APP_DIR/"
cp    "$REPO_ROOT/backend/requirements.txt" "$APP_DIR/"
[ -d "$REPO_ROOT/backend/data"   ] && cp -r "$REPO_ROOT/backend/data/."   "$DATA_DIR/"
[ -d "$REPO_ROOT/backend/static" ] && cp -r "$REPO_ROOT/backend/static/." "$STATIC_DIR/" \
    || echo "  AVISO: static/ não encontrado — execute 'npm run build' no frontend-vue."

# ─── 5. Virtualenv ─────────────────────────────────────────────────────────────
echo "[5/8] Criando virtualenv..."
python3.12 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# ─── 6. .env ───────────────────────────────────────────────────────────────────
echo "[6/8] Gerando .env..."
cat > "$APP_DIR/.env" <<EOF
DATABASE_URL=sqlite:///${DATA_DIR}/mcmv_rural.db
APP_ENV=production
EOF
chmod 640 "$APP_DIR/.env"

# ─── 7. Nginx ──────────────────────────────────────────────────────────────────
echo "[7/8] Configurando nginx..."
NGINX_CONF="/etc/nginx/sites-available/mcmv-rural.conf"

# Substitui SERVER_NAME e caminhos do certificado
sed \
    -e "s|SERVER_NAME_AQUI|$SERVER_NAME|g" \
    -e "s|/etc/ssl/mcmv-rural/cert.pem|$CERT_PATH|g" \
    -e "s|/etc/ssl/mcmv-rural/key.pem|$KEY_PATH|g" \
    "$SCRIPT_DIR/nginx/mcmv-rural.conf" > "$NGINX_CONF"

ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/mcmv-rural.conf
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable --now nginx
systemctl reload nginx

if [ "$MODE" = "--ssl" ]; then
    echo "  Obtendo certificado Let's Encrypt para $SERVER_NAME..."
    certbot --nginx \
        --non-interactive --agree-tos --redirect \
        --email "admin@$(hostname -d 2>/dev/null || echo local)" \
        --domains "$SERVER_NAME" \
        && systemctl reload nginx \
        || echo "  AVISO: certbot falhou (verifique porta 80 pública)."
fi

# ─── 8. Systemd ────────────────────────────────────────────────────────────────
echo "[8/8] Configurando serviço systemd..."
cp "$SCRIPT_DIR/systemd/mcmv-rural.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable mcmv-rural
systemctl start  mcmv-rural

# Permissões
chown -R "$APP_USER:$APP_USER"    "$APP_DIR" "$SSL_DIR"
chown -R "$APP_USER:www-data"     "$STATIC_DIR"
chmod -R 750 "$APP_DIR"
chmod -R 755 "$STATIC_DIR"
chmod 770    "$DATA_DIR"

# ─── Testes (opcional) ─────────────────────────────────────────────────────────
if [ "$MODE" = "--test" ]; then
    sleep 3
    bash "$SCRIPT_DIR/test.sh" "$SERVER_NAME"
fi

# ─── Resumo ────────────────────────────────────────────────────────────────────
sleep 2
SVC=$(systemctl is-active mcmv-rural 2>/dev/null || echo "inativo")
echo ""
echo "======================================================"
echo " Instalação concluída! [$SVC]"
echo "======================================================"
echo " URL (HTTPS) : https://$SERVER_NAME"
echo " URL (HTTP ) : http://$SERVER_NAME  → redireciona para 443"
echo " Banco       : $DATA_DIR/mcmv_rural.db"
echo " Certificado : $CERT_PATH"
echo ""
echo " Comandos úteis:"
echo "   systemctl status mcmv-rural"
echo "   journalctl -u mcmv-rural -f"
echo "   bash deploy/linux/test.sh $SERVER_NAME"
echo "======================================================"
