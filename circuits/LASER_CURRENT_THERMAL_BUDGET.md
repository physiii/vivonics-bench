# Bench Laser Current Thermal Budget

Generated design state: 2026-06-25.

This note covers the four low-side laser current sinks:

```text
PWM -> 10k / 30k command limiter -> TLV9001 -> AO3400A -> 10 ohm sense resistor
```

The schematic pins and generated PCB routing now check out, but the actual
thermal margin depends on each laser diode's forward voltage, the shared
`LASER_V+` supply, the current limit, and duty cycle.

## Sources

- AO3400A datasheet: SOT-23 N-channel MOSFET, RthetaJA measured on a 1 in2 FR-4
  board with 2 oz copper; power dissipation and SOA ratings are junction-
  temperature limited and application-board dependent.
- JLCPCB C5123624 / HoCR2512-2W-10R-1% listing: 10 ohm, 2512, 2 W, 1 percent,
  250 V chip resistor.
- Selected laser datasheets: US-Lasers D6505I and D7805I 5.6 mm Style-A cans,
  ams OSRAM PLT5 520EB_P 5.6 mm monitor-PD can, and ams OSRAM PLT5 450GB
  5.6 mm laser-only can. The high-forward-voltage green current policy is a
  thermal reference, not an approval to run every selected diode at the hardware
  command clamp.

## Current Clamp

The command limiter is:

```text
Vcmd(max) = 3.3 V * 30k / (10k + 30k) = 2.475 V
Ilimit    = Vcmd(max) / 10 ohm = 247.5 mA
Psense    = Ilimit^2 * 10 ohm = 0.613 W
```

The 10 ohm 2512 2 W sense resistor is correctly upsized for this nominal clamp,
but it still needs board-temperature measurement because there are four channels
and the heat is close to the laser-driver cluster.

## Control-Loop Range / Gate Drive

`check_laser_driver_control_loop.py` separates the TLV9001/AO3400A control-loop
topology from the laser thermal policy. It asserts that each PWM net feeds the
10k/30k/1 uF command node into TLV9001 IN+, each MOSFET source/sense-resistor
high side feeds TLV9001 IN-, TLV9001 OUT drives the AO3400A gate through 1 kOhm,
and each AO3400A drain lands on the correct `LASER_Nx` direct-laser cathode net.

The selected 120 mA design point passes the first-order TLV9001 input range and
AO3400A gate-drive check:

```text
selected-max-current: sense feedback = 1.200 V, available AO3400A Vgs ~= 3.780 V
```

The raw analog command clamp remains an expected-fail condition for production
use:

```text
hardware-clamp-gate-margin: sense feedback = 2.475 V, available AO3400A Vgs ~= 2.505 V
```

That leaves only about 5 mV above the AO3400A 2.5 V RDS(on) characterization
point under the light-load TLV9001 output-high assumption, before considering
temperature, part spread, loop dynamics, diode current limits, optical safety, or
SOT-23 heat.

## Common `LASER_V+` Constraint

For each channel:

```text
Vds(AO3400A) = LASER_V+ - Vf(laser) - I * Rsense
Pmosfet      = Vds * I
```

The board uses one shared `LASER_V+` rail. That is a bench convenience, not a
universal production source architecture. A voltage high enough for one laser
class can overheat another channel if the lower-headroom/current combination is
driven continuously through the same SOT-23 linear sink.

Using a conservative continuous AO3400A budget of `(125 degC - ambient) / 125
degC/W`, the checker estimates:

| Scenario | `LASER_V+` | Diode `Vf(max)` | Result |
|---|---:|---:|---|
| High-Vf green reference | 10.5 V | 7.0 V | Pass, narrow supply window |
| High-Vf green reference | 12.0 V | 7.0 V | Fail, AO3400A heat |
| Low-Vf red/IR-style diode on green rail | 10.5 V | 2.5 V | Fail, AO3400A heat |

For a high-forward-voltage green diode at the 247.5 mA command clamp, the estimated
high-ambient rail window is roughly 10.0 V to 10.8 V. Below that, the current
loop runs out of headroom. Above that, the SOT-23 MOSFET becomes the heat sink.

## Selected-Diode Current Limits

The checker now includes the actual LD1-LD4 diode set from the Digikey cart and
source notes. Datasheet values used by the executable policy are:

| Channel | MPN | Optical power | Datasheet operating current | Datasheet operating voltage | Source note |
|---|---|---:|---:|---:|---|
| LD1 IR | D7805I | 5 mW | 35 mA typ, 50 mA max | 2.1 V typ, 2.5 V max | US-Lasers 780 nm source page |
| LD2 red | D6505I | 5 mW | 20 mA typ, 25 mA max | 2.2 V typ, 2.6 V max | Digikey D650-5I source used conservatively; US-Lasers mirror conflicts at 40 mA typ / 60 mA max |
| LD3 green | PLT5 520EB_P | 20 mW | 65 mA typ, 78 mA max | 5.4 V typ, 6.1 V max | ams OSRAM datasheet |
| LD4 blue | PLT5 450GB | 100 mW | 87 mA typ, 120 mA max | 5.2 V typ, 6.5 V max | ams OSRAM datasheet |

At the old AP63200 feedback setting (`LASER_V+ ~= 10.72 V`), the selected
diodes at typical current mostly pass, but the blue PLT5 450GB channel fails the
conservative continuous AO3400A budget. This remains as an expected-fail
high-rail comparison:

```text
python3 circuits/check_laser_current_budget.py --policy selected-diodes-typ-10v72
```

The present 9.3 V-class common-rail reference below passes for the selected
diodes at datasheet maximum operating current/voltage and still assumes
firmware/hardware current limiting:

```text
python3 circuits/check_laser_current_budget.py --policy selected-diodes-max-9v3
```

The hardware command clamp is explicitly unsafe for all selected laser MPNs:

```text
python3 circuits/check_laser_current_budget.py --policy selected-diodes-hardware-clamp-10v72
```

## Design Decision

Current bench board:

- Use a current-limited external `LASER_V+` supply.
- Set `LASER_V+` from the actual diode forward-voltage table, not from habit.
- Treat the 247.5 mA clamp as an upper bound, not the default operating point.
- The old `LASER_V+ ~= 10.72 V` setting is not accepted for continuous
  PLT5 450GB typical-current operation under the conservative 85 degC / 125 degC
  AO3400A policy.
- A reduced common rail near 9.3 V is the current checked bench reference for
  the selected diodes at datasheet maximum operating currents, but production
  should not rely on a common rail plus firmware alone for laser safety.
- Do not run all four colors at the clamp from one high rail without thermal
  measurement.
- Solder direct laser cans only after checking each actual laser MPN pin table
  and can/common-node polarity.
- Do not treat the 247.5 mA hardware clamp as safe for the selected Digikey-cart
  D6505I, D7805I, PLT5 520EB_P, or PLT5 450GB without per-channel current
  limits and optical safety signoff.

Production design:

- Use per-channel laser driver/APC topology or per-channel supply/headroom
  control. A single common high rail plus SOT-23 linear sinks is not a good
  production architecture for mixed red/green/blue/IR forward voltages.
- Keep the monitor-PD feedback concept, but close production APC around a driver
  selected for each diode package polarity.

## Verification

Expected pass for the high-forward-voltage green reference at a controlled
10.5 V laser rail:

```text
python3 circuits/check_laser_current_budget.py --policy green-high-vf-10v5
```

Expected pass for the actual selected diodes at datasheet max current/voltage on
a reduced 9.3 V common-rail reference:

```text
python3 circuits/check_laser_current_budget.py --policy selected-diodes-max-9v3
```

Expected fail for the old 10.72 V common rail at typical selected-diode
currents because the blue PLT5 450GB AO3400A dissipation is too high:

```text
python3 circuits/check_laser_current_budget.py --policy selected-diodes-typ-10v72
```

Expected fail for the unsafe hardware current clamp:

```text
python3 circuits/check_laser_current_budget.py --policy selected-diodes-hardware-clamp-10v72
```

Expected fail for insufficient gate-drive margin at the raw hardware clamp:

```text
python3 circuits/check_laser_driver_control_loop.py --policy hardware-clamp-gate-margin
```

Expected fail for too much rail headroom:

```text
python3 circuits/check_laser_current_budget.py --policy green-high-vf-12v
```

Expected fail for a low-forward-voltage diode on the same green-sized rail:

```text
python3 circuits/check_laser_current_budget.py --policy low-vf-diode-on-10v5
```
