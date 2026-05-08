# Vivonics Pi Bench

Standalone Raspberry Pi bench runner for Vivonics C1/X1 work. The parent
Vivonics repo consumes this repo as the `pi/` git submodule, matching the
radio-mapper buoy pattern.

The Pi owns the tight first-loop instrumentation:

- HDMI projector pattern display
- `IMX477` camera capture through `rpicam` / RTSP frame grabs
- optional `TSL2591` and `AS7341` I2C sensor snapshots
- later BPW34 photodiode data only after an ESP32/external ADC or TIA path

## Files

- `bench_service.py`: FastAPI service for projector/camera/sensor runs.
- `x1_measurement.py`: file-backed CLI smoke-test runner.
- `capture.py`, `projector.py`, `sensors.py`: hardware adapters.
- `photocycle.py`: C1/X1 red-linearity and green-write/red-read protocols.
- `install.sh`: user systemd service installer for `vivonics-bench`.
- `scripts/deploy_remote.sh`: workstation-to-Pi deploy helper.

## Install on the Pi

```bash
cd /home/andy/vivonics/pi
python3 -m pip install --user -r requirements.txt
sudo raspi-config nonint do_i2c 0
```

Check I2C sensor visibility:

```bash
i2cdetect -y 1
python3 x1_measurement.py sensor-check
```

Run the bench service:

```bash
./install.sh
curl http://raspberrypi.local:8090/status
curl http://raspberrypi.local:8090/sensors
```

Run a file-backed red linearity check:

```bash
python3 x1_measurement.py linearity --output-dir /tmp/vivonics_x1_linearity
```

Deploy from the workstation:

```bash
scripts/deploy_remote.sh andy@192.168.1.174 /home/andy/vivonics/pi
```

Claim boundary: these scripts are instrumentation for C1/X1 smoke tests. They
do not promote Carolina `NRC-1` material to evidence-grade bR or purified
purple-membrane claims.
