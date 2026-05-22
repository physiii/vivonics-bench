# Vivonics Pi Bench

Standalone Raspberry Pi bench runner for Vivonics C1/X1 work. The parent
Vivonics repo consumes this repo as the `pi/` git submodule, matching the
radio-mapper buoy pattern.

The Pi owns the tight first-loop instrumentation:

- HDMI projector pattern display
- `IMX477` camera capture through `rpicam` / RTSP frame grabs
- optional GPIO control for external red / green laser drivers
- optional `TSL2591` and `AS7341` I2C sensor snapshots
- later BPW34 photodiode data only after an ESP32/external ADC or TIA path

## Files

- `bench_service.py`: FastAPI service for projector/camera/sensor runs.
- `x1_measurement.py`: file-backed CLI smoke-test runner.
- `capture.py`, `projector.py`, `sensors.py`: hardware adapters.
- `laser_gpio.py`: Raspberry Pi GPIO outputs for red / green laser switching.
- `photocycle.py`: C1/X1 red-linearity and green-write/red-read protocols.
- `install.sh`: user systemd service installer for `vivonics-bench`.
- `scripts/deploy_remote.sh`: workstation-to-Pi deploy helper.

## Install on the Pi

```bash
cd /home/andy/vivonics/pi
./install.sh
sudo raspi-config nonint do_i2c 0
```

`install.sh` creates a repo-local `.venv` so Raspberry Pi OS PEP 668 system
Python protection does not block dependency installation.

Check I2C sensor visibility:

```bash
/usr/sbin/i2cdetect -y 1
python3 x1_measurement.py sensor-check
```

Run the bench service:

```bash
./install.sh
curl http://raspberrypi.local:8090/status
curl http://raspberrypi.local:8090/sensors
```

## Laser GPIO Wiring

Use these Raspberry Pi BCM pins:

| Channel | BCM GPIO | Physical pin |
| --- | ---: | ---: |
| Red laser enable | `GPIO22` | `15` |
| Green laser enable | `GPIO27` | `13` |

Do not power or ground a laser module directly through a Pi GPIO pin. Use each
GPIO as a logic signal into a low-side MOSFET or transistor switch, with the
laser supply ground tied to Pi ground. The Pi pin drives the gate/base; laser
negative goes to the MOSFET drain / transistor collector; source / emitter goes
to ground. Keep the laser module's own current limiting or driver in place.

The user service defaults to `VIVONICS_LIGHT_DRIVER=both`, so HDMI frames and
GPIO laser outputs are updated together. The GPIO path is active-low by default:
`Off` drives the pins high; red or green on pulls the selected channel low. It
uses `1 kHz` PWM, mapping protocol levels `0..255` to `0..100%` active duty
cycle. Override the driver with `hdmi`, `gpio`, or `both`; override pins with
`VIVONICS_RED_LASER_GPIO` and `VIVONICS_GREEN_LASER_GPIO`. Set
`VIVONICS_LASER_ACTIVE_HIGH=1` only for active-high driver hardware.

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
