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
- ams OSRAM PLT5 520B datasheet: reference 520 nm 3-pin laser diode, forward
  operation only, operating current up to the relevant 260 mA class, operating
  voltage up to the relevant 7 V class, monitor current specified with reverse-
  biased monitor PD and not guaranteed as an absolute power measurement.

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

## Common `LASER_V+` Constraint

For each channel:

```text
Vds(AO3400A) = LASER_V+ - Vf(laser) - I * Rsense
Pmosfet      = Vds * I
```

The board uses one shared `LASER_V+` rail. That is a bench convenience, not a
universal production source architecture. A voltage high enough for a green
laser can overheat a red or IR channel if the lower-forward-voltage diode is
allowed near the same current.

Using a conservative continuous AO3400A budget of `(125 degC - ambient) / 125
degC/W`, the checker estimates:

| Scenario | `LASER_V+` | Diode `Vf(max)` | Result |
|---|---:|---:|---|
| PLT5 520B reference green | 10.5 V | 7.0 V | Pass, narrow supply window |
| PLT5 520B reference green | 12.0 V | 7.0 V | Fail, AO3400A heat |
| Low-Vf red/IR-style diode on green rail | 10.5 V | 2.5 V | Fail, AO3400A heat |

For a PLT5 520B-style green diode at the 247.5 mA command clamp, the estimated
high-ambient rail window is roughly 10.0 V to 10.8 V. Below that, the current
loop runs out of headroom. Above that, the SOT-23 MOSFET becomes the heat sink.

## Design Decision

Current bench board:

- Use a current-limited external `LASER_V+` supply.
- Set `LASER_V+` from the actual diode forward-voltage table, not from habit.
- Treat the 247.5 mA clamp as an upper bound, not the default operating point.
- Do not run all four colors at the clamp from one high rail without thermal
  measurement.
- Build the J4 harness only after checking each actual laser MPN pin table and
  can/common-node polarity.

Production design:

- Use per-channel laser driver/APC topology or per-channel supply/headroom
  control. A single common high rail plus SOT-23 linear sinks is not a good
  production architecture for mixed red/green/blue/IR forward voltages.
- Keep the monitor-PD feedback concept, but close production APC around a driver
  selected for each diode package polarity.

## Verification

Expected pass for the PLT5 520B reference at a controlled 10.5 V laser rail:

```text
python3 circuits/check_laser_current_budget.py --policy plt5-520b-green-10v5
```

Expected fail for too much rail headroom:

```text
python3 circuits/check_laser_current_budget.py --policy plt5-520b-green-12v
```

Expected fail for a low-forward-voltage diode on the same green-sized rail:

```text
python3 circuits/check_laser_current_budget.py --policy low-vf-diode-on-10v5
```
