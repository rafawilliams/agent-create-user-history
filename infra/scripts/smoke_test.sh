#!/usr/bin/env bash
# Prueba de humo posterior al despliegue (cicd-pipeline.md). No llama al modelo ni inicia sesion.
#
#   smoke_test.sh <web_url> <api_url> <cognito_domain>
#
# Comprueba: (1) la raiz de la pantalla responde 200 con la politica de contenido exacta y las
# demas cabeceras; (2) el preflight de /v1/stories y de /v1/session responde con el origen exacto,
# los metodos y las cabeceras permitidas; (3) POST /v1/stories sin token responde 401 con el cuerpo
# de error de C1 (SESSION_INVALID).
# Codigos de salida: 0 correcto, 1 una comprobacion fallo, 2 uso incorrecto.
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Uso: smoke_test.sh <web_url> <api_url> <cognito_domain>" >&2
  exit 2
fi

WEB_URL="${1%/}"
API_URL="${2%/}"
COGNITO_DOMAIN="$3"
RETRIES="${SMOKE_RETRIES:-6}"
DELAY="${SMOKE_DELAY:-10}"

# El origen de la API en connect-src es solo esquema y host (sin la etapa /live).
API_ORIGIN="$(printf '%s' "$API_URL" | sed -E 's#^(https?://[^/]+).*#\1#')"

EXPECTED_CSP="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' ${API_ORIGIN} https://${COGNITO_DOMAIN} https://cognito-idp.us-east-1.amazonaws.com; img-src 'self' data:; font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
EXPECTED_METHODS="GET,POST,DELETE,OPTIONS"
EXPECTED_HEADERS="Authorization,Content-Type"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fail() {
  echo "FALLO: $*" >&2
  exit 1
}

# Valor de una cabecera de respuesta (sin distinguir mayusculas), sin retorno de carro.
header_value() {
  grep -i "^$1:" "$2" | head -n 1 | sed -E 's/^[^:]*:[[:space:]]*//' | tr -d '\r' || true
}

# --- 1. La raiz de la pantalla ---------------------------------------------------------------
# La propagacion de CloudFront tras un cambio de politica puede tardar: se reintenta.
check_root() {
  local status csp
  status="$(curl -sS --max-time 30 -D "$WORK/root.h" -o "$WORK/root.b" -w '%{http_code}' "$WEB_URL/")" || return 1
  [ "$status" = "200" ] || { echo "la raiz respondio $status" >&2; return 1; }
  csp="$(header_value content-security-policy "$WORK/root.h")"
  [ "$csp" = "$EXPECTED_CSP" ] || { echo "Content-Security-Policy distinta de la esperada" >&2; return 1; }
  header_value strict-transport-security "$WORK/root.h" | grep -q 'max-age=31536000' || { echo "falta Strict-Transport-Security" >&2; return 1; }
  [ "$(header_value x-content-type-options "$WORK/root.h")" = "nosniff" ] || { echo "falta X-Content-Type-Options: nosniff" >&2; return 1; }
  [ "$(header_value referrer-policy "$WORK/root.h")" = "no-referrer" ] || { echo "falta Referrer-Policy: no-referrer" >&2; return 1; }
}

attempt=1
until check_root; do
  [ "$attempt" -lt "$RETRIES" ] || fail "la raiz de la pantalla no cumple (Content-Security-Policy y cabeceras de seguridad) tras $RETRIES intentos"
  attempt=$((attempt + 1))
  sleep "$DELAY"
done
echo "OK raiz de la pantalla: 200 con la politica de contenido y las cabeceras exactas"

# --- 2. Preflight de CORS --------------------------------------------------------------------
for path in /v1/stories /v1/session; do
  status="$(curl -sS --max-time 30 -X OPTIONS -D "$WORK/pre.h" -o /dev/null -w '%{http_code}' \
    -H "Origin: $WEB_URL" -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: authorization,content-type" \
    "$API_URL$path")" || fail "preflight de $path: la solicitud fallo"
  case "$status" in 2??) ;; *) fail "preflight de $path respondio $status" ;; esac
  [ "$(header_value access-control-allow-origin "$WORK/pre.h")" = "$WEB_URL" ] || fail "preflight de $path: el origen permitido no es exactamente $WEB_URL"
  [ "$(header_value access-control-allow-methods "$WORK/pre.h")" = "'$EXPECTED_METHODS'" ] \
    || [ "$(header_value access-control-allow-methods "$WORK/pre.h")" = "$EXPECTED_METHODS" ] \
    || fail "preflight de $path: metodos permitidos distintos de $EXPECTED_METHODS"
  [ "$(header_value access-control-allow-headers "$WORK/pre.h")" = "'$EXPECTED_HEADERS'" ] \
    || [ "$(header_value access-control-allow-headers "$WORK/pre.h")" = "$EXPECTED_HEADERS" ] \
    || fail "preflight de $path: cabeceras permitidas distintas de $EXPECTED_HEADERS"
  echo "OK preflight de $path con el origen, los metodos y las cabeceras exactos"
done

# --- 3. Una solicitud sin token se rechaza ---------------------------------------------------
status="$(curl -sS --max-time 30 -X POST -o "$WORK/post.b" -w '%{http_code}' \
  -H "Origin: $WEB_URL" -H "Content-Type: application/json" \
  -d '{"title":"prueba de humo"}' "$API_URL/v1/stories")" || fail "POST /v1/stories: la solicitud fallo"
[ "$status" = "401" ] || fail "POST /v1/stories sin token respondio $status en lugar de 401"
grep -q '"SESSION_INVALID"' "$WORK/post.b" || fail "el 401 no trae el cuerpo de error de C1 (SESSION_INVALID)"
echo "OK POST /v1/stories sin token: 401 SESSION_INVALID"

echo "OK prueba de humo completa"
