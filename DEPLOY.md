# Vivonics Pi Bench Deployment

The Pi bench repo is designed to run as the `pi/` submodule inside the parent
Vivonics checkout, and also as a standalone repo while developing on the Pi.

## Current bench target

- Host: `raspberrypi.local`
- Current IPv4s observed on the Pi: `192.168.1.174`, `192.168.1.176`
- User used by local scripts: `andy`
- Service port: `8090`
- Expected path in the parent Vivonics checkout: `/home/andy/vivonics/pi`

## Deploy from this workstation

From this repo:

```bash
scripts/deploy_remote.sh andy@raspberrypi.local /home/andy/vivonics/pi
```

The deploy script rsyncs this repo into the target path, installs Python
dependencies in a repo-local `.venv`, installs/restarts the user systemd
service, and prints the service status plus `/status` response.

## Manual Pi install

On the Pi:

```bash
cd /home/andy/vivonics/pi
sudo raspi-config nonint do_i2c 0
./install.sh
curl http://127.0.0.1:8090/status
curl http://127.0.0.1:8090/sensors
/usr/sbin/i2cdetect -y 1
```

The bench service installed by `install.sh` defaults to:

```text
VIVONICS_LIGHT_DRIVER=both
VIVONICS_RED_LASER_GPIO=23
VIVONICS_GREEN_LASER_GPIO=24
VIVONICS_LASER_ACTIVE_HIGH=1
```

That maps red laser enable to physical pin `16` and green laser enable to
physical pin `18`. The laser control is active-high by default: `Off` drives the
GPIO pins low, and an active channel is driven high. Treat the GPIO pins as
logic outputs into transistor or MOSFET switches; do not sink laser current
directly through the Pi.

`sudo raspi-config nonint do_i2c 0` is intentionally not run by the deploy
script because it may require an operator password and should only be changed
when the Pi wiring is in a known state.

## Claim boundary

This repo only owns C1/X1 bench instrumentation: HDMI projector frames, IMX477
capture, auxiliary I2C sensor snapshots, and smoke-test measurement scripts.
It does not make evidence-grade bacteriorhodopsin, purple-membrane, or
weight-plane claims by itself.
