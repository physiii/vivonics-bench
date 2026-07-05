# 2026-07-05 Laser Command Limiter Signoff

Scope: LD1-LD4 analog command limiter values, JLCPCB order identities, current
budget checks, and regenerated manufacturing package metadata.

## Result

The old common 30k PWM limiter has been replaced by per-channel SMT limiter
resistors so the analog command path no longer exposes every selected diode to
the old 247.5 mA clamp.

| Channel | Ref | Color | Limiter | MPN | LCSC | Analog current limit |
|---|---|---|---:|---|---|---:|
| LD1 | R21 | IR | 1.3k | 0603WAF1301T5E | C22767 | 38.0 mA |
| LD2 | R26 | Red | 750R | 0603WAF7500T5E | C23241 | 23.0 mA |
| LD3 | R31 | Green | 3k | 0603WAF3001T5E | C4211 | 76.2 mA |
| LD4 | R36 | Blue | 4.7k | 0603WAF4701T5E | C23162 | 105.5 mA |

All four parts are 0603 SMT resistors and are present in the generated JLCPCB
BOM/POS flow. The all-channel analog current-limit sum is about 242.7 mA
nominal, or 246.4 mA at the 1 percent high-current resistor tolerance corner.

## Verification

Commands run:

```text
python3 -m py_compile circuits/laser_command_limits.py circuits/check_laser_current_budget.py circuits/check_laser_driver_control_loop.py circuits/check_buck_input_power_budget.py circuits/check_laser_controller_netlist.py circuits/check_laser_driver_package_pcb.py circuits/check_passive_derating.py
kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net
python3 circuits/check_laser_controller_netlist.py /tmp/lc.net
python3 circuits/check_laser_driver_control_loop.py --netlist /tmp/lc.net
python3 circuits/check_laser_driver_control_loop.py --netlist /tmp/lc.net --policy hardware-clamp-gate-margin
python3 circuits/check_laser_current_budget.py --policy selected-diodes-hardware-clamp-9v3
python3 circuits/check_buck_input_power_budget.py --netlist /tmp/lc.net --policy hardware-clamp-9v3
python3 circuits/check_laser_driver_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb
python3 circuits/check_passive_derating.py /tmp/lc.net
python3 circuits/run_laser_controller_review.py
```

Observed local gate results:

- Netlist assertions passed: 603 assertions across 156 nets.
- Selected-diode per-channel analog-limit thermal policy passed at the
  high-current tolerance corner.
- Laser-driver per-channel limiter gate-margin policy passed at the
  high-current tolerance corner.
- Buck/input all-channel analog-limit budget passed at the high-current
  tolerance corner.
- Laser-driver package/PCB guard passed.
- Passive derating passed for 65 capacitors and 64 resistors/trimmers.
- Full review wrapper passed all automated local checks, with only the known
  release blockers still reported for KiCad native ERC/DRC availability and
  non-automated bring-up/signoff items.

## Remaining Release Risk

This signoff closes the electrical schematic/BOM/CPL limiter error. It does not
close driver/sense-resistor temperature measurement, optical output calibration,
firmware clamp behavior, duty cycle limits, loop transient behavior, or laser
safety signoff.
