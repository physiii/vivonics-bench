# Bench Laser Current Thermal Budget

Generated design state: 2026-07-05.

This note covers the four low-side laser current sinks:

```text
PWM -> 10k / per-channel limiter / 1 uF command filter -> TLV9001 -> AO3400A -> 10 ohm sense resistor
```

The schematic pins and generated PCB routing now check out, but the actual
thermal margin still depends on each laser diode's forward voltage, the shared
`LASER_V+` supply, the current limit, duty cycle, board temperature, and optical
safety behavior.

## Sources

- AO3400A datasheet: SOT-23 N-channel MOSFET, RthetaJA measured on a 1 in2 FR-4
  board with 2 oz copper; power dissipation and SOA ratings are junction-
  temperature limited and application-board dependent.
- JLCPCB C5123624 / HoCR2512-2W-10R-1% listing: 10 ohm, 2512, 2 W, 1 percent,
  250 V chip resistor.
- Selected laser datasheets: US-Lasers D6505I and D7805I 5.6 mm Style-A cans,
  ams OSRAM PLT5 520EB_P 5.6 mm monitor-PD can, and ams OSRAM PLT5 450GB
  5.6 mm laser-only can.

## Per-Channel Command Limits

The old common `30k LIMIT` pulldown produced a 2.475 V command, or 247.5 mA
through the 10 ohm sense resistor. That value exceeded every selected laser
diode's datasheet operating-current maximum and left essentially no AO3400A
gate-drive margin at the raw clamp. It has been replaced by per-channel SMT
limiter resistors:

| Channel | Limiter | LCSC | Vcmd(max) | Ilimit |
|---|---:|---|---:|---:|
| LD1 IR D7805I | 1.3k LIMIT | C22767 | 0.380 V | 38.0 mA |
| LD2 red D6505I | 750R LIMIT | C23241 | 0.230 V | 23.0 mA |
| LD3 green PLT5 520EB_P | 3k LIMIT | C4211 | 0.762 V | 76.2 mA |
| LD4 blue PLT5 450GB | 4.7k LIMIT | C23162 | 1.055 V | 105.5 mA |

The all-channel analog command-limit sum is now about 242.7 mA nominal, or
246.4 mA at the 1 percent high-current resistor tolerance corner. That is an
electrical current-limit proof only; it does not waive optical output,
duty-cycle, loop-stability, or board-temperature signoff.

## Control-Loop Range / Gate Drive

`check_laser_driver_control_loop.py` separates the TLV9001/AO3400A control-loop
topology from the laser thermal policy. It asserts that each PWM net feeds the
10k/per-channel-limiter/1 uF command node into TLV9001 IN+, each MOSFET
source/sense-resistor high side feeds TLV9001 IN-, TLV9001 OUT drives the
AO3400A gate through 1 kOhm, and each AO3400A drain lands on the correct
`LASER_Nx` direct-laser cathode net.

The selected max-current design points pass the first-order TLV9001 input range
and AO3400A gate-drive checks:

| Channel | Checked current | Available AO3400A Vgs margin vs 2.5 V characterization |
|---|---:|---:|
| IR | 50.0 mA | 1.980 V |
| Red | 25.0 mA | 2.230 V |
| Green | 78.0 mA | 1.700 V |
| Blue | 120.0 mA | 1.280 V |

The per-channel analog limiter gate also passes:

```text
python3 circuits/check_laser_driver_control_loop.py --policy hardware-clamp-gate-margin
```

That compatibility policy name is retained for review-script continuity, but it
now checks the per-channel analog command limits, not the removed 247.5 mA
common clamp.

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
degC/W`, the checker keeps the generic rail-headroom guardrails visible:

| Scenario | `LASER_V+` | Diode `Vf(max)` | Result |
|---|---:|---:|---|
| High-Vf green reference | 10.5 V | 7.0 V | Pass, narrow supply window |
| High-Vf green reference | 12.0 V | 7.0 V | Fail, AO3400A heat |
| Low-Vf red/IR-style diode on green rail | 10.5 V | 2.5 V | Fail unless current is reduced |

## Selected-Diode Current Limits

The checker includes the actual LD1-LD4 diode set from the Digikey cart and
source notes. Datasheet values used by the executable policy are:

| Channel | MPN | Optical power | Datasheet operating current | Datasheet operating voltage | Source note |
|---|---|---:|---:|---:|---|
| LD1 IR | D7805I | 5 mW | 35 mA typ, 50 mA max | 2.1 V typ, 2.5 V max | US-Lasers 780 nm source page |
| LD2 red | D6505I | 5 mW | 20 mA typ, 25 mA max | 2.2 V typ, 2.6 V max | Digikey D650-5I source used conservatively; US-Lasers mirror conflicts at 40 mA typ / 60 mA max |
| LD3 green | PLT5 520EB_P | 20 mW | 65 mA typ, 78 mA max | 5.4 V typ, 6.1 V max | ams OSRAM datasheet |
| LD4 blue | PLT5 450GB | 100 mW | 87 mA typ, 120 mA max | 5.2 V typ, 6.5 V max | ams OSRAM datasheet |

The present 9.3 V-class common-rail reference passes for the selected diodes at
datasheet typical operating points, datasheet maximum operating points, and the
per-channel analog command limits:

```text
python3 circuits/check_laser_current_budget.py --policy selected-diodes-typ-9v3
python3 circuits/check_laser_current_budget.py --policy selected-diodes-max-9v3
python3 circuits/check_laser_current_budget.py --policy selected-diodes-hardware-clamp-9v3
```

## Design Decision

Current bench board:

- Use the per-channel analog command limiters generated into LD1-LD4.
- Keep firmware current clamps at or below the selected diode operating limits.
- Set `LASER_V+` from the actual diode forward-voltage table, not from habit.
- Treat the 9.3 V-class common rail as a checked bench reference, not a
  production driver architecture for every future laser source.
- Do not run all four colors continuously at maximum command without thermal
  measurement.
- Solder direct laser cans only after inspecting each received part against the
  2026-07-04 signed-off MPN/footprint pin table and can/common-node polarity.
- Follow `circuits/review/signoff/2026-07-05-laser-first-article-bringup-signoff.md`
  for one-channel-at-a-time first-article optical and temperature measurements.

Production design:

- Use per-channel laser driver/APC topology or per-channel supply/headroom
  control if this evolves beyond a bench board.
- Keep the monitor-PD feedback concept, but close production APC around a driver
  selected for each diode package polarity.
- Close driver/sense-resistor temperature and optical-output measurements during
  bring-up before using the board as a released laser source.

## Verification

Expected pass for the high-forward-voltage green reference at a controlled
10.5 V laser rail:

```text
python3 circuits/check_laser_current_budget.py --policy green-high-vf-10v5
```

Expected pass for the actual selected diodes on the 9.3 V common-rail reference:

```text
python3 circuits/check_laser_current_budget.py --policy selected-diodes-typ-9v3
python3 circuits/check_laser_current_budget.py --policy selected-diodes-max-9v3
python3 circuits/check_laser_current_budget.py --policy selected-diodes-hardware-clamp-9v3
```

Expected pass for per-channel analog-limit gate-drive margin:

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
