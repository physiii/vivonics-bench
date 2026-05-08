# Vivonics Pi Bench

This folder holds the Raspberry Pi-side bench runner for C1/X1 work.

The Pi owns the tight first-loop instrumentation:

- HDMI projector pattern display
- `IMX477` camera capture through `rpicam` / RTSP frame grabs
- optional `TSL2591` and `AS7341` I2C sensor snapshots
- later BPW34 photodiode data only after an ESP32/external ADC or TIA path

Install on the Pi:

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

Claim boundary: these scripts are instrumentation for C1/X1 smoke tests. They
do not promote Carolina `NRC-1` material to evidence-grade bR or purified
purple-membrane claims.
