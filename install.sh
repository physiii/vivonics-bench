#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"

echo "Installing Vivonics bench service..."

pip install --user -r "${SCRIPT_DIR}/requirements.txt"

mkdir -p "${SERVICE_DIR}"

cat > "${SERVICE_DIR}/vivonics-bench.service" << EOF
[Unit]
Description=Vivonics X1 Bench Service
After=network.target c1-mediamtx.service c1-camera-rtsp.service

[Service]
Type=simple
WorkingDirectory=${SCRIPT_DIR}
ExecStart=$(which python3) -m uvicorn bench_service:app --host 0.0.0.0 --port 8090
Restart=on-failure
RestartSec=5
Environment=SDL_VIDEODRIVER=kms

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable vivonics-bench.service
systemctl --user start vivonics-bench.service

echo "Service installed and started."
echo "Check status: systemctl --user status vivonics-bench"
echo "View logs:    journalctl --user -u vivonics-bench -f"
echo "I2C sensors:  sudo raspi-config nonint do_i2c 0 && i2cdetect -y 1"
echo "Sensor check: python3 ${SCRIPT_DIR}/x1_measurement.py sensor-check"
