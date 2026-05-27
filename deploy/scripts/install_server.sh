#!/usr/bin/env bash
set -euo pipefail

if [ "${EUID}" -ne 0 ]; then
  echo "Please run as root."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx unzip git curl ca-certificates
systemctl enable docker nginx
systemctl start docker nginx

echo "Server packages installed: Docker, Compose plugin, Nginx, Certbot."
echo "If the server says 'System restart required', run: reboot"
