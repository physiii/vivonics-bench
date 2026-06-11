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
| Red laser enable | `GPIO15` | `10` |
| Green laser enable | `GPIO24` | `18` |

Do not power or ground a laser module directly through a Pi GPIO pin. Use each
GPIO as a logic signal into a low-side MOSFET or transistor switch, with the
laser supply ground tied to Pi ground. The Pi pin drives the gate/base; laser
negative goes to the MOSFET drain / transistor collector; source / emitter goes
to ground. Keep the laser module's own current limiting or driver in place.

The user service defaults to `VIVONICS_LIGHT_DRIVER=both`, so HDMI frames and
GPIO laser outputs are updated together. The GPIO path is active-high by default:
`Off` drives the pins low; red or green on drives the selected channel high. It
uses `10 kHz` PWM, mapping protocol levels `0..255` to `0..100%` active duty
cycle. Override the driver with `hdmi`, `gpio`, or `both`; override pins with
`VIVONICS_RED_LASER_GPIO` and `VIVONICS_GREEN_LASER_GPIO`. Set
`VIVONICS_LASER_ACTIVE_HIGH=0` only for active-low driver hardware.

## Reactor AD7606 Wiring and Bring-Up Notes

This is the working wiring map for the second Raspberry Pi bench
(`192.168.1.122`) that replaces the camera read path with BPW34 photodiodes
through an AD7606 module. It was brought up on `2026-05-25` on the second
reactor plane: `BUSY` began responding only after `CVA` and `CVB` were tied
together to the Pi conversion strobe.

Current reactor laser pins:

| Function | Raspberry Pi pin |
| --- | --- |
| Red laser 2N7000 gate | `GPIO15`, physical pin `10` |
| Second write laser 2N7000 gate (`green` in the service; may be blue in the reactor) | `GPIO24`, physical pin `18` |
| Infrared laser 2N7000 gate | `GPIO23`, physical pin `16` |
| Blue laser 2N7000 gate | `GPIO14`, physical pin `8` |
| 2N7000 sources / laser supply negative / ADC ground | Pi `GND`, common ground |

Observed AD7606 module digital header, top-to-bottom as shown by the board
silkscreen:

| Left column | Right column |
| --- | --- |
| `GND` | `+5V` |
| `OS1` | `OS0` |
| `RAGE` / `RANGE` | `OS2` |
| `CVB` | `CVA` |
| `RD` | `RST` |
| `BUSY` | `CS` |
| `FRST` | `VIO` |
| `DB1` | `DB0` |
| `DB3` | `DB2` |
| `DB5` | `DB4` |
| `DB7` | `DB6` |
| `DB9` | `DB8` |
| `DB11` | `DB10` |
| `DB13` | `DB12` |
| `DB15` | `DB14` |

Raspberry Pi top-down header map:

```text
Raspberry Pi 40-pin header, physical pin numbers.
Pin 1 is upper-left when looking down at the GPIO header.

 LEFT ROW                         RIGHT ROW
  1  3V3  -> AD7606 VIO           2  5V   -> AD7606 +5V
  3  GPIO2   unused               4  5V   optional +5V
  5  GPIO3   unused               6  GND  -> AD7606 GND/common
  7  GPIO4   -> AD7606 CVA+CVB    8  GPIO14 -> blue 2N7000 gate
  9  GND     common              10  GPIO15 -> red 2N7000 gate
 11  GPIO17  <- AD7606 DB0       12  GPIO18 <- AD7606 DB1
 13  GPIO27  <- AD7606 DB2       14  GND
 15  GPIO22  <- AD7606 DB3       16  GPIO23 -> infrared 2N7000 gate
 17  3V3     optional VIO        18  GPIO24 -> green 2N7000 gate
 19  GPIO10  <- AD7606 DB4       20  GND
 21  GPIO9   <- AD7606 DB5       22  GPIO25 <- AD7606 DB6
 23  GPIO11  <- AD7606 DB7       24  GPIO8  <- AD7606 DB8
 25  GND                         26  GPIO7  <- AD7606 DB9
 27  GPIO0   unused              28  GPIO1  unused
 29  GPIO5   <- AD7606 DB10      30  GND
 31  GPIO6   <- AD7606 DB11      32  GPIO12 <- AD7606 DB12
 33  GPIO13  <- AD7606 DB13      34  GND
 35  GPIO19  <- AD7606 DB14      36  GPIO16 <- AD7606 DB15
 37  GPIO26  <- AD7606 BUSY      38  GPIO20 -> AD7606 RD
 39  GND                         40  GPIO21 -> AD7606 RST
```

Fixed ADC pins:

| AD7606 pin | Draft connection | Reason |
| --- | --- | --- |
| `CS` | `GND` | Single ADC, always selected during bring-up. |
| `OS0`, `OS1`, `OS2` | `GND` | No oversampling for first tests. |
| `RAGE` / `RANGE` | `GND` | Start in the lower analog input range if supported by the module. |
| `FRST` | no connect | Optional first-data marker; not needed for first channel test. |
| `VIO` | Pi `3V3` | Keep ADC digital outputs at Pi-safe logic level. |

Do not connect or rework the AD7606 `DB0..DB15` outputs unless `VIO` is
confirmed to be tied to `3V3`; the Pi GPIO bus is not 5 V tolerant. The
validated bring-up sequence is: power the module, hold data pins as Pi inputs,
set `RD` inactive high, pulse `RST`, pulse tied `CVA`/`CVB`, confirm `BUSY`
returns low, then read the eight 16-bit parallel words.

For a one-channel BPW34 test, connect the photodiode resistor sense node to
`V1`, and connect the matching `G` input beside `V1` to the common ground. Even
when using only `V1`, the AD7606 digital read path still needs the 16-bit data
bus unless the module is separately configured for serial/SPI mode.

Verified reactor-plane response on `192.168.1.122`:

| Test state | ADC channel 1 mean | ADC channel 2 mean | Main observed delta |
| --- | ---: | ---: | --- |
| Lasers off before red test | `11214.9` | `29411.8` | baseline |
| `GPIO23` red laser at level `128` | `13622.8` | `29351.4` | `ch1 +2407.9` |
| Lasers off before second-laser test | `11220.6` | `29381.1` | baseline |
| `GPIO24` second laser at level `128` | `13927.3` | `29331.9` | `ch1 +2706.7` |

As currently wired, both laser controls produce the strongest positive optical
response on AD7606 channel `1`. Channel `2` is high at baseline but only shifts
by about `-50` to `-60` counts in these tests. Channels `3..8` stayed near zero.
The bench was left idle with both laser GPIOs off after the red test.

### 2026-05-26 Concentrated-Vial BPW34 / AD7606 Result

The concentrated-vial test did not produce an evidence-grade bR write/read
signal. The reactor bench hardware was working, but the read channel was
dominated by optical/electrical recovery from the green write pulse.

Key observed CH1 states with the concentrated vial:

| State | AD7606 CH1 mean | Notes |
| --- | ---: | --- |
| Lasers off | `11196` | dark/readout baseline |
| Red probe on | `29564` | strong red-path response |
| Green write on | `29497` | green also couples strongly into CH1 |
| Red + green on | `29618` | near the same high-count regime |

The best CH1-only direct capture ran at about `4.7 kHz`, enough to inspect the
sub-millisecond to tens-of-milliseconds bR window. In that run the immediate
green-write/red-probe bin showed about `+181` counts in `0-0.1 ms`, but the
red-off dark control showed about `+18,392` counts in the same bin. After
`0.5 ms`, the red-probe effect collapsed to the noise floor. A delayed red-read
check at `0`, `0.5`, `1`, `2`, `5`, and `10 ms` after green write did not show
a significant green-vs-control separation in the useful bins.

Artifacts from this run are in the parent workspace:

- `bench-output/reactor_direct_strong_vial_ch1fast_20260526T110410Z.json`
- `bench-output/reactor_direct_strong_vial_delayed_read_20260526T110611Z.json`

Interpretation: the AD7606 has enough code resolution for the current signal
levels; the blocker is not ADC bit depth. The BPW34 is sensitive to green light,
and the raw photodiode/resistor/ADC node stores charge when hit by the green
write pulse. That recovery transient can masquerade as an early read signal.

Next optical fixes, in priority order:

1. Add a red-pass or `650 nm` bandpass filter directly in front of the BPW34 so
   the detector sees the red probe but rejects the green write pulse.
2. Add black baffling, tubing, or a small aperture around the BPW34 so direct
   green scatter cannot reach the detector.
3. Keep paired controls for every run: green-write run, no-green control, and
   red-off dark control. A bR claim must survive all three.
4. Add a reference photodiode if possible, then subtract common laser drift and
   scattered-light pickup from the through-vial detector.

A TIA is still useful, but not because the ADC lacks resolution. A TIA can hold
the BPW34 near a fixed bias/virtual-ground point, lower the source impedance into
the AD7606, define the bandwidth with known feedback components, and recover
faster after a large light pulse. It can also support clamping or blanking during
the write pulse. A TIA will not, by itself, reject green light that physically
reaches the BPW34; optical filtering and baffling come first.

### 2026-05-26 No-Vial Green Leakage Control

After pulling the BPW34 back into the cavity to reduce side light, the vial was
removed and the reactor was tested with only laser light in the chamber. This is
the current negative control for deciding whether the immediate post-green
signal is protein or setup artifact.

No-vial CH1 steady states:

| State | AD7606 CH1 mean | Notes |
| --- | ---: | --- |
| Lasers off | `11497 +/- 191` | dark/readout baseline |
| Red probe on | `15352 +/- 189` | red path reaches CH1 |
| Green write on | `18036 +/- 195` | green still reaches CH1 strongly |
| Red + green on | `21852 +/- 191` | additive optical pickup |

The no-vial fast CH1 run reproduced the same immediate post-green transient that
appeared with the vial:

| Window | Red-probe sequence | Red-off dark control | Interpretation |
| --- | ---: | ---: | --- |
| `0-0.1 ms` | `+6372` | `+6377` | artifact, not protein |
| `0.1-0.25 ms` | `+4617` | `+4606` | artifact, not protein |
| `0.25-0.5 ms` | `+1666` | `+1635` | artifact, not protein |
| `0.5-1 ms` | `+424` | `+387` | artifact tail |

Because the same response appears with no vial and even in the red-off dark
control, the first sub-millisecond response cannot be used as bR evidence. The
exact sequence `green on -> green off -> red on` was also tested with delays of
`0`, `0.5`, `1`, `2`, `5`, and `10 ms`. After about `0.5-1 ms`, the no-vial
green-vs-control separation was mostly insignificant, but that is also the time
region where fast liquid-phase bR response may already be decaying.

Artifacts from this control were produced as local temp files:

- `/tmp/reactor_no_vial_ch1fast_20260526T114617Z.json`
- `/tmp/reactor_no_vial_delayed_read_20260526T114754Z.json`

Updated conclusion: BPW34 and AD7606 timing are not the main blocker. The
detector path is fast enough for millisecond-scale checks, but green write light
still reaches CH1 and creates detector/readout recovery that is larger than the
candidate bR readout. The next useful geometry target is that `green on` should
stay near the lasers-off CH1 baseline while `red on` remains clearly above it.
Use tighter black baffling/tubing/aperture first, then a red-pass or `650 nm`
filter directly in front of the BPW34.

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
