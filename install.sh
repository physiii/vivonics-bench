#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"
VENV_DIR="${VIVONICS_BENCH_VENV:-${SCRIPT_DIR}/.venv}"
PYTHON_BIN="${VENV_DIR}/bin/python"

echo "Installing Vivonics bench service..."

if [[ ! -x "${PYTHON_BIN}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

"${PYTHON_BIN}" -m pip install --upgrade pip
"${PYTHON_BIN}" -m pip install -r "${SCRIPT_DIR}/requirements.txt"

mkdir -p "${SERVICE_DIR}"

cat > "${SERVICE_DIR}/vivonics-bench.service" << EOF
[Unit]
Description=Vivonics X1 Bench Service
After=network.target c1-mediamtx.service c1-camera-rtsp.service

[Service]
Type=simple
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${PYTHON_BIN} -m uvicorn bench_service:app --host 0.0.0.0 --port 8090
Restart=on-failure
RestartSec=5
TimeoutStopSec=5
KillMode=mixed
Environment=SDL_VIDEODRIVER=kms
Environment=VIVONICS_LIGHT_DRIVER=${VIVONICS_LIGHT_DRIVER:-both}
Environment=VIVONICS_RED_LASER_GPIO=${VIVONICS_RED_LASER_GPIO:-15}
Environment=VIVONICS_GREEN_LASER_GPIO=${VIVONICS_GREEN_LASER_GPIO:-24}
Environment=VIVONICS_INFRARED_LASER_GPIO=${VIVONICS_INFRARED_LASER_GPIO:-23}
Environment=VIVONICS_BLUE_LASER_GPIO=${VIVONICS_BLUE_LASER_GPIO:-14}
Environment=VIVONICS_LASER_ACTIVE_HIGH=${VIVONICS_LASER_ACTIVE_HIGH:-1}
Environment=VIVONICS_LASER_PWM_HZ=${VIVONICS_LASER_PWM_HZ:-10000}
Environment=VIVONICS_AD7606_ENABLE=${VIVONICS_AD7606_ENABLE:-0}
Environment=VIVONICS_AD7606_AVG_SAMPLES=${VIVONICS_AD7606_AVG_SAMPLES:-1}
Environment=VIVONICS_AD7606_CV_GPIO=${VIVONICS_AD7606_CV_GPIO:-4}
Environment=VIVONICS_AD7606_RD_GPIO=${VIVONICS_AD7606_RD_GPIO:-20}
Environment=VIVONICS_AD7606_RST_GPIO=${VIVONICS_AD7606_RST_GPIO:-21}
Environment=VIVONICS_AD7606_BUSY_GPIO=${VIVONICS_AD7606_BUSY_GPIO:-26}
Environment=VIVONICS_AD7606_DATA_GPIOS=${VIVONICS_AD7606_DATA_GPIOS:-17,18,27,22,10,9,25,11,8,7,5,6,12,13,19,16}

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable vivonics-bench.service
systemctl --user restart vivonics-bench.service

echo "Service installed and started."
echo "Check status: systemctl --user status vivonics-bench"
echo "View logs:    journalctl --user -u vivonics-bench -f"
echo "I2C sensors:  sudo raspi-config nonint do_i2c 0 && /usr/sbin/i2cdetect -y 1"
echo "Sensor check: ${PYTHON_BIN} ${SCRIPT_DIR}/x1_measurement.py sensor-check"
