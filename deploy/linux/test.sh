#!/usr/bin/env bash
# test.sh — Testes de integração do MCMV Rural deployado
#
# Uso:
#   bash test.sh <IP_ou_hostname>          # testa o servidor deployado
#   bash test.sh --local                   # testa servidor local (127.0.0.1:8082 direto)
#
# Saída: PASS / FAIL por teste + código de saída 0 (tudo OK) ou 1 (algum falhou)
set -euo pipefail

TARGET="${1:?Informe o servidor ou --local}"
LOCAL_PORT="${LOCAL_PORT:-8082}"   # sobrescreva com: LOCAL_PORT=8083 bash test.sh --local
PASS=0; FAIL=0

# ── Helpers ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'; BOLD='\033[1m'

pass() { echo -e "  ${GREEN}✔ PASS${NC}  $1"; ((++PASS)); }
fail() { echo -e "  ${RED}✘ FAIL${NC}  $1 — $2"; ((++FAIL)); }

# Detecta python funcional (python3 no Linux, python no Windows/Git Bash)
# Testa cada candidato antes de aceitar (evita stub da Microsoft Store no Windows)
PY=""
for _py_cand in python3 python python3.12 python3.11; do
    if command -v "$_py_cand" &>/dev/null && "$_py_cand" -c "import sys; sys.exit(0)" 2>/dev/null; then
        PY="$_py_cand"; break
    fi
done
if [ -z "$PY" ]; then echo "ERRO: python não encontrado." >&2; exit 1; fi

http_get() {
    local url="$1"
    local status
    status=$(curl -sS -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    echo "$status"
}

json_field() {
    # Extrai campo de JSON via python (sem jq)
    "$PY" -c "import json,sys; d=json.load(sys.stdin); print(d.get('$1',''))" 2>/dev/null || echo ""
}

# ── Configuração dos endpoints ──────────────────────────────────────────────────
if [ "$TARGET" = "--local" ]; then
    BASE_HTTP="http://127.0.0.1:$LOCAL_PORT"
    BASE_HTTPS=""
    echo -e "\n${BOLD}MCMV Rural — Testes locais (127.0.0.1:$LOCAL_PORT)${NC}"
else
    BASE_HTTP="http://$TARGET"
    BASE_HTTPS="https://$TARGET"
    echo -e "\n${BOLD}MCMV Rural — Testes em $TARGET${NC}"
fi
echo "────────────────────────────────────────────────"

# ══ Grupo 1: Redirecionamento e SSL ═══════════════════════════════════════════
if [ -n "$BASE_HTTPS" ]; then
    echo -e "\n${BOLD}[1] SSL / Portas${NC}"

    # HTTP → HTTPS redirect
    RED_STATUS=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_HTTP/" 2>/dev/null || echo "000")
    if [[ "$RED_STATUS" =~ ^30[12]$ ]]; then
        pass "HTTP :80 redireciona para HTTPS (status $RED_STATUS)"
    else
        fail "HTTP :80 deve redirecionar" "status=$RED_STATUS"
    fi

   # HTTPS acessível; valida certificado TLS sem -k
    HTTPS_STATUS=$(http_get "$BASE_HTTPS/")
    [ "$HTTPS_STATUS" = "200" ] \
        && pass "HTTPS :443 acessível (status 200)" \
        || fail "HTTPS :443" "status=$HTTPS_STATUS"

    # Headers de segurança
    HSTS=$(curl -sS -I "$BASE_HTTPS/" | grep -i "x-frame-options" | tr -d '\r')
    [ -n "$HSTS" ] \
        && pass "Header X-Frame-Options presente" \
        || fail "Header X-Frame-Options ausente" "verifique nginx.conf"
fi

# ══ Grupo 2: API — endpoints principais ═══════════════════════════════════════
echo -e "\n${BOLD}[2] API — Endpoints${NC}"
API="${BASE_HTTPS:-$BASE_HTTP}"

# /api/health
HEALTH=$(curl -sS "$API/api/health" 2>/dev/null | json_field "status")
[ "$HEALTH" = "ok" ] \
    && pass "/api/health retorna status=ok" \
    || fail "/api/health" "resposta: '$HEALTH'"

# /api/etapas — deve retornar 6 etapas
ETAPAS_N=$(curl -sS "$API/api/etapas" 2>/dev/null | "$PY" -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
[ "$ETAPAS_N" = "6" ] \
    && pass "/api/etapas retorna 6 etapas" \
    || fail "/api/etapas" "retornou $ETAPAS_N etapas"

# /api/propostas/stats — deve ter total_propostas > 0
TOTAL=$(curl -sS "$API/api/propostas/stats" 2>/dev/null | json_field "total_propostas")
[ "${TOTAL:-0}" -gt 0 ] 2>/dev/null \
    && pass "/api/propostas/stats total_propostas=$TOTAL" \
    || fail "/api/propostas/stats" "total_propostas='$TOTAL'"

# /api/propostas paginação
PAGE_TOTAL=$(curl -sS "$API/api/propostas?por_pagina=5" 2>/dev/null \
    | "$PY" -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('items',[])))" 2>/dev/null || echo "0")
[ "${PAGE_TOTAL:-0}" -gt 0 ] 2>/dev/null \
    && pass "/api/propostas paginação retornou $PAGE_TOTAL itens" \
    || fail "/api/propostas paginação" "itens=$PAGE_TOTAL"

# /api/propostas filtro por UF
UF_TOTAL=$(curl -sS "$API/api/propostas?uf=BA&por_pagina=1" 2>/dev/null \
    | json_field "total")
[ "${UF_TOTAL:-0}" -gt 0 ] 2>/dev/null \
    && pass "/api/propostas?uf=BA retornou $UF_TOTAL propostas" \
    || fail "/api/propostas?uf=BA" "total='$UF_TOTAL'"

# ══ Grupo 3: Detalhe e histórico (somente leitura) ════════════════════════════
echo -e "\\n${BOLD}[3] API — Detalhe de Proposta (read-only)${NC}"

# Smoke remoto não pode alterar registros reais nem "reverter" criando histórico.
# A transição PUT é testada em backend/tests com banco isolado em memória.
FIRST_ID=$(curl -sS "$API/api/propostas?por_pagina=1" 2>/dev/null \\
    | "$PY" -c "import json,sys; d=json.load(sys.stdin); print(d['items'][0]['num_proposta'] if d.get('items') else '')" \\
    2>/dev/null || echo "")

if [ -n "$FIRST_ID" ]; then
    DETAIL_JSON=$(curl -sS "$API/api/propostas/$FIRST_ID" 2>/dev/null || echo "")
    DETAIL_ID=$(printf '%s' "$DETAIL_JSON" | json_field "num_proposta")
    [ "$DETAIL_ID" = "$FIRST_ID" ] \\
        && pass "GET /api/propostas/{id} retorna o ID solicitado" \\
        || fail "GET /api/propostas/{id}" "ID divergente ou detalhe inválido"
    HIST_VALID=$(printf '%s' "$DETAIL_JSON" | "$PY" -c \\
        "import json,sys; d=json.load(sys.stdin); print(int(isinstance(d.get('historico'), list)))" \\
        2>/dev/null || echo "0")
    [ "$HIST_VALID" = "1" ] \\
        && pass "GET histórico é lista válida (não exige histórico preexistente)" \\
        || fail "GET histórico" "estrutura não é lista"
else
    fail "GET detalhe" "lista vazia; não há proposta elegível para conferir"
fi

echo "INFO: escrita de etapa (PUT) não é exercitada por este smoke; validar com banco de teste isolado."

# ══ Grupo 4: Export CSV ═══════════════════════════════════════════════════════
echo -e "\n${BOLD}[4] Export CSV${NC}"
CSV_STATUS=$(http_get "$API/api/propostas/export")
[ "$CSV_STATUS" = "200" ] \
    && pass "/api/propostas/export retornou status=200" \
    || fail "/api/propostas/export" "status=$CSV_STATUS"

# ══ Grupo 5: Frontend estático ════════════════════════════════════════════════
echo -e "\n${BOLD}[5] Frontend Vue${NC}"
INDEX_TITLE=$(curl -sS "${BASE_HTTPS:-$BASE_HTTP}/" 2>/dev/null | grep -o '<title>[^<]*</title>' || echo "")
echo "$INDEX_TITLE" | grep -qi "MCMV" \
    && pass "index.html contém título MCMV" \
    || fail "index.html" "título não encontrado: '$INDEX_TITLE'"

# CSS/JS assets acessíveis
ASSET=$(curl -sS "${BASE_HTTPS:-$BASE_HTTP}/" 2>/dev/null | grep -oP 'src="[^"]*\.js"' | head -1 | grep -oP '".*"' | tr -d '"' || echo "")
if [ -n "$ASSET" ]; then
    ASSET_STATUS=$(http_get "${BASE_HTTPS:-$BASE_HTTP}$ASSET")
    [ "$ASSET_STATUS" = "200" ] \
        && pass "Asset JS ($ASSET) acessível" \
        || fail "Asset JS" "status=$ASSET_STATUS"
else
    fail "Asset JS" "não encontrado no HTML"
fi

# ══ Grupo 6: Systemd (apenas se deployado) ═══════════════════════════════════
if [ "$TARGET" != "--local" ]; then
    echo -e "\n${BOLD}[6] Serviço Systemd${NC}"
    if command -v systemctl &>/dev/null; then
        SVC=$(systemctl is-active mcmv-rural 2>/dev/null || echo "inativo")
        [ "$SVC" = "active" ] \
            && pass "systemd mcmv-rural está ativo" \
            || fail "systemd mcmv-rural" "status=$SVC"
    else
        echo "  (systemctl não disponível neste contexto)"
    fi
fi

# ══ Resultado ════════════════════════════════════════════════════════════════
echo ""
echo "────────────────────────────────────────────────"
TOTAL_TESTS=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✔  Todos os testes passaram ($PASS/$TOTAL_TESTS)${NC}"
    exit 0
else
    echo -e "${RED}${BOLD}✘  $FAIL teste(s) falharam de $TOTAL_TESTS${NC}"
    exit 1
fi
