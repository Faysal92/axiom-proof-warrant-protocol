#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-axiom.stack-moderne.fr}"
ENABLE_HTTPS="${ENABLE_HTTPS:-0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

echo "[1/4] Building and starting AXIOM demo containers..."
docker compose up -d --build

echo "[2/4] Writing Nginx reverse proxy for ${DOMAIN}..."
sed "s/server_name axiom.stack-moderne.fr;/server_name ${DOMAIN};/" \
  deploy/nginx/axiom.stack-moderne.fr.conf \
  > "/etc/nginx/sites-available/${DOMAIN}"
ln -sf "/etc/nginx/sites-available/${DOMAIN}" "/etc/nginx/sites-enabled/${DOMAIN}"
nginx -t
systemctl reload nginx

echo "[3/4] Local health checks..."
curl -fsS http://127.0.0.1:8001/health >/dev/null
curl -fsS http://127.0.0.1:8081/ >/dev/null

echo "[4/4] HTTPS..."
if [ "${ENABLE_HTTPS}" = "1" ]; then
  certbot --nginx -d "${DOMAIN}"
else
  echo "HTTPS not enabled automatically. Run when DNS is ready:"
  echo "  ENABLE_HTTPS=1 deploy/scripts/deploy.sh ${DOMAIN}"
fi

echo "Done. Open: http://${DOMAIN}"
echo "After HTTPS: https://${DOMAIN}"
