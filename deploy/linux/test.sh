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
    status=$(curl -sk -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
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
    RED_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" "$BASE_HTTP/" 2>/dev/null || echo "000")
    if [[ "$RED_STATUS" =~ ^30[12]$ ]]; then
        pass "HTTP :80 redireciona para HTTPS (status $RED_STATUS)"
    else
        fail "HTTP :80 deve redirecionar" "status=$RED_STATUS"
    fi

    # HTTPS acessível (aceita cert autoassinado com -k)
    HTTPS_STATUS=$(http_get "$BASE_HTTPS/")
    [ "$HTTPS_STATUS" = "200" ] \
        && pass "HTTPS :443 acessível (status 200)" \
        || fail "HTTPS :443" "status=$HTTPS_STATUS"

    # Headers de segurança
    HSTS=$(curl -sk -I "$BASE_HTTPS/" | grep -i "x-frame-options" | tr -d '\r')
    [ -n "$HSTS" ] \
        && pass "Header X-Frame-Options presente" \
        || fail "Header X-Frame-Options ausente" "verifique nginx.conf"
fi

# ══ Grupo 2: API — endpoints principais ═══════════════════════════════════════
echo -e "\n${BOLD}[2] API — Endpoints${NC}"
API="${BASE_HTTPS:-$BASE_HTTP}"

# /api/health
HEALTH=$(curl -sk "$API/api/health" 2>/dev/null | json_field "status")
[ "$HEALTH" = "ok" ] \
    && pass "/api/health retorna status=ok" \
    || fail "/api/health" "resposta: '$HEALTH'"

# /api/etapas — deve retornar 6 etapas
ETAPAS_N=$(curl -sk "$API/api/etapas" 2>/dev/null | "$PY" -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
[ "$ETAPAS_N" = "6" ] \
    && pass "/api/etapas retorna 6 etapas" \
    || fail "/api/etapas" "retornou $ETAPAS_N etapas"

# /api/propostas/stats — deve ter total_propostas > 0
TOTAL=$(curl -sk "$API/api/propostas/stats" 2>/dev/null | json_field "total_propostas")
[ "${TOTAL:-0}" -gt 0 ] 2>/dev/null \
    && pass "/api/propostas/stats total_propostas=$TOTAL" \
    || fail "/api/propostas/stats" "total_propostas='$TOTAL'"

# /api/propostas paginação
PAGE_TOTAL=$(curl -sk "$API/api/propostas?por_pagina=5" 2>/dev/null \
    | "$PY" -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('items',[])))" 2>/dev/null || echo "0")
[ "${PAGE_TOTAL:-0}" -gt 0 ] 2>/dev/null \
    && pass "/api/propostas paginação retornou $PAGE_TOTAL itens" \
    || fail "/api/propostas paginação" "itens=$PAGE_TOTAL"

# /api/propostas filtro por UF
UF_TOTAL=$(curl -sk "$API/api/propostas?uf=BA&por_pagina=1" 2>/dev/null \
    | json_field "total")
[ "${UF_TOTAL:-0}" -gt 0 ] 2>/dev/null \
    && pass "/api/propostas?uf=BA retornou $UF_TOTAL propostas" \
    || fail "/api/propostas?uf=BA" "total='$UF_TOTAL'"

# ══ Grupo 3: PUT etapa ════════════════════════════════════════════════════════
echo -e "\n${BOLD}[3] API — Atualização de Etapa${NC}"

# Pega o primeiro ID disponível
FIRST_ID=$(curl -sk "$API/api/propostas?por_pagina=1" 2>/dev/null \
    | "$PY" -c "import json,sys; d=json.load(sys.stdin); print(d['items'][0]['num_proposta'] if d.get('items') else '')" \
    2>/dev/null || echo "")

if [ -n "$FIRST_ID" ]; then
    # Usa arquivo temporário para garantir UTF-8 correto no body JSON
    TMP_BODY=$(mktemp)
    printf '{"etapa":"Habilitação da Entidade","observacao":"Teste automatizado"}' > "$TMP_BODY"

    PUT_STATUS=$(curl -sk -o /dev/null -w "%{http_code}" \
        -X PUT "$API/api/propostas/$FIRST_ID/etapa" \
        -H 'Content-Type: application/json; charset=utf-8' \
        --data-binary "@$TMP_BODY" \
        2>/dev/null || echo "000")
    [ "$PUT_STATUS" = "200" ] \
        && pass "PUT /api/propostas/{id}/etapa status=200" \
        || fail "PUT /api/propostas/{id}/etapa" "status=$PUT_STATUS"

    # Verifica se o histórico foi registrado
    HIST_N=$(curl -sk "$API/api/propostas/$FIRST_ID" 2>/dev/null \
        | "$PY" -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('historico',[])))" \
        2>/dev/null || echo "0")
    [ "${HIST_N:-0}" -gt 0 ] 2>/dev/null \
        && pass "Histórico registrado ($HIST_N entrada(s))" \
        || fail "Histórico vazio" "esperava >= 1 entrada"

    # Reverte para Selecionado (limpa o teste)
    printf '{"etapa":"Selecionado","observacao":"Revertido pelo teste"}' > "$TMP_BODY"
    curl -sk -X PUT "$API/api/propostas/$FIRST_ID/etapa" \
        -H 'Content-Type: application/json; charset=utf-8' \
        --data-binary "@$TMP_BODY" > /dev/null 2>&1 || true
    rm -f "$TMP_BODY"
else
    fail "Não foi possível obter ID para teste de PUT" "lista vazia"
fi

# ══ Grupo 4: Export CSV ═══════════════════════════════════════════════════════
echo -e "\n${BOLD}[4] Export CSV${NC}"
CSV_STATUS=$(http_get "$API/api/propostas/export")
[ "$CSV_STATUS" = "200" ] \
    && pass "/api/propostas/export retornou status=200" \
    || fail "/api/propostas/export" "status=$CSV_STATUS"

# ══ Grupo 5: Frontend estático ════════════════════════════════════════════════
echo -e "\n${BOLD}[5] Frontend Vue${NC}"
INDEX_TITLE=$(curl -sk "${BASE_HTTPS:-$BASE_HTTP}/" 2>/dev/null | grep -o '<title>[^<]*</title>' || echo "")
echo "$INDEX_TITLE" | grep -qi "MCMV" \
    && pass "index.html contém título MCMV" \
    || fail "index.html" "título não encontrado: '$INDEX_TITLE'"

# CSS/JS assets acessíveis
ASSET=$(curl -sk "${BASE_HTTPS:-$BASE_HTTP}/" 2>/dev/null | grep -oP 'src="[^"]*\.js"' | head -1 | grep -oP '".*"' | tr -d '"' || echo "")
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
