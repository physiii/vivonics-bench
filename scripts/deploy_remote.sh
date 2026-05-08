#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${1:-andy@192.168.1.174}"
REMOTE_DIR="${2:-/home/andy/vivonics/pi}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "Deploying Vivonics Pi bench to ${REMOTE_HOST}:${REMOTE_DIR}"

ssh "${REMOTE_HOST}" "mkdir -p '${REMOTE_DIR}'"

rsync -az --delete \
  --exclude '.git' \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  "${REPO_ROOT}/" "${REMOTE_HOST}:${REMOTE_DIR}/"

ssh "${REMOTE_HOST}" "cd '${REMOTE_DIR}' && chmod +x install.sh && ./install.sh"
ssh "${REMOTE_HOST}" "systemctl --user --no-pager -l status vivonics-bench.service || true"
ssh "${REMOTE_HOST}" "curl -fsS http://127.0.0.1:8090/status || true"
