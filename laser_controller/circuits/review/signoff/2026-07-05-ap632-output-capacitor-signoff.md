# 2026-07-05 AP632 Output Capacitor Signoff

Scope: AP63205 `/POWER_IO/BUCK_5V` and AP63200 `LASER_V+` output capacitor
identity, BOM/POS state, and local datasheet-reference capacitance guard.

## Result

C64/C65 and C67/C68 were moved from 10 uF 0805 ceramics to Samsung
`CL21A226MAQNNNE` 22 uF 25 V X5R 0805 ceramics, JLCPCB/LCSC `C45783`.

| Rail | Refs | Value | MPN | LCSC | Nominal bank |
|---|---|---:|---|---|---:|
| `/POWER_IO/BUCK_5V` | C64, C65 | 22 uF | CL21A226MAQNNNE | C45783 | 44 uF |
| `LASER_V+` | C67, C68 | 22 uF | CL21A226MAQNNNE | C45783 | 44 uF |

The footprints and placement remain the existing 0805 pads, so this change is a
BOM/value substitution, not a copper reroute.

## Verification

Commands run:

```text
kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net
python3 circuits/check_laser_controller_netlist.py /tmp/lc.net
python3 circuits/check_buck_input_power_budget.py --netlist /tmp/lc.net --policy datasheet-recommended-components
python3 circuits/check_ap6320x_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb
python3 circuits/check_passive_derating.py /tmp/lc.net
python3 circuits/run_laser_controller_review.py
```

Observed local gate results:

- Netlist assertions passed: 603 assertions across 156 nets.
- `datasheet-recommended-components` now passes with C64+C65 = 44 uF and
  C67+C68 = 44 uF against the 44 uF reference target.
- AP6320x package/PCB guard passed with the existing C64/C65/C67/C68 pad nets.
- Passive derating passed for the new `C45783` capacitor MPN.
- BOM and POS now list C64/C65 as `22uF 5V buck` and C67/C68 as
  `22uF laser buck`, all with LCSC `C45783`.

## Remaining Release Risk

This signoff closes the local AP632 output-capacitance recommendation blocker.
It does not close VIN24 input protection, adapter/RJ45 harness current-limit
definition, reverse/transient protection, switch-loop layout review, ripple,
transient response, or buck temperature measurement.
