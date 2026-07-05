# Category 3 Expected-Fail Policy Signoff

Date: 2026-07-05

Scope: Review-gate rows that intentionally expect a nonzero checker result for
unsafe, out-of-policy, or deliberately bad operating scenarios.

## Result

These rows are correct when the command returns exit code `1`. The review wrapper
marks them `PASS` because the unsafe scenario is still rejected.

| Policy | Command | Expected result |
|---|---|---|
| Bright-ambient SFH2201/TIA overload | `python3 circuits/check_tia_readout_budget.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy sfh2201-1000lx-example` | Fails because the 1000 lx datasheet short-circuit-current example would need about 152 V of TIA swing at 2 Mohm. |
| VIN24 production protection | `python3 circuits/check_vin24_input_protection.py --netlist circuits/review/generated/laser_controller_kicad9.net --policy production-protection` | Fails because there is no onboard fuse/PTC/TVS/reverse-protection/eFuse/hot-swap stage between J5/J6 and U15/U16. |
| AP2112 sustained Wi-Fi load | `python3 circuits/check_power_thermal_budget.py --policy wifi-tx-100-duty` | Fails because sustained ESP32-S3 Wi-Fi TX load exceeds the SOT25 AP2112 thermal budget. |
| Green high-Vf diode at 12 V rail | `python3 circuits/check_laser_current_budget.py --policy green-high-vf-12v` | Fails because the AO3400A continuous thermal budget is exceeded at the 12 V rail assumption. |
| Low-Vf diode on green-sized rail | `python3 circuits/check_laser_current_budget.py --policy low-vf-diode-on-10v5` | Fails because a low-forward-voltage diode on the green-sized rail would over-dissipate the AO3400A unless current or rail voltage is reduced. |

## Interpretation

These are not JLCPCB Gerber/BOM/POS package defects. They are guardrails that
prove the review suite still rejects unsafe usage assumptions. If any of these
commands starts returning `0`, the corresponding policy has weakened and must be
reviewed before bench-use or production release.
