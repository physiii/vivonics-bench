# KiCad DRC Partial Signoff - 2026-07-04

Scope: `circuits/laser_controller.kicad_pcb`.

Evidence artifact:

- `circuits/review/signoff/2026-07-04-kicad-drc-zero-violations.png`

Observed KiCad GUI DRC state from the captured screenshot:

- `Refill all zones before performing DRC` was enabled.
- `Report all errors for each track` was enabled.
- `Violations (0)`.
- `Unconnected Items (0)`.
- `Schematic Parity (not run)`.
- `Ignored Tests (4)`.

Companion automated evidence from this repo state:

```text
kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net
python3 circuits/check_laser_controller_netlist.py /tmp/lc.net
python3 circuits/check_laser_controller_pcb.py circuits/laser_controller.kicad_pcb /tmp/lc.net
python3 circuits/check_laser_controller_release_gate.py circuits/laser_controller.kicad_pcb /tmp/lc.net
/snap/bin/kicad.kicad-cli pcb drc --all-track-errors --severity-all --format report --output circuits/review/generated/laser_controller_kicad9_physical_drc.rpt circuits/laser_controller.kicad_pcb
/snap/bin/kicad.kicad-cli pcb drc --all-track-errors --schematic-parity --severity-all --format report --output circuits/review/generated/laser_controller_kicad9_drc.rpt circuits/laser_controller.kicad_pcb
/snap/bin/kicad.kicad-cli sch erc --severity-all --format report --output circuits/review/generated/laser_controller_kicad9_erc.rpt circuits/laser_controller.kicad_sch
/usr/bin/python3 circuits/check_kicad_pcbnew_drc_report.py
/usr/bin/python3 circuits/check_courtyard_overlap_triage.py
python3 circuits/check_schematic_pcb_parity.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb
python3 circuits/check_jlcpcb_order_package.py
```

The automated gates exported the current schematic netlist, passed 603 netlist
assertions, passed 554 PCB pad-net assignments, found 0 zone/rail pending nets,
proved 110/110 multi-pad nets explicitly routed, and passed the generated-copper
release gate.

Current 2026-07-05 generated evidence:

- `circuits/review/generated/laser_controller_kicad9_physical_drc.rpt` reports
  4 native KiCad 9 DRC findings, all `[courtyards_overlap]` warnings, with
  `Found 0 unconnected pads` and `Found 0 Footprint errors`.
- `circuits/review/generated/laser_controller_kicad9_drc.rpt` runs native KiCad
  9 DRC with schematic parity enabled. Physical DRC remains at the same 4
  courtyard warnings, but native schematic parity still reports 136 footprint
  errors that need cleanup or explicit review.
- `circuits/review/generated/laser_controller_kicad9_erc.rpt` captures native
  KiCad 9 ERC output and still contains schematic findings.
- `circuits/review/generated/laser_controller_pcbnew_drc_report.rpt` reports
  4 native Pcbnew DRC findings, all `[courtyards_overlap]` warnings, with
  `Found 0 unconnected pads` and `Found 0 Footprint errors`.
- `circuits/review/generated/laser_controller_courtyard_overlap_triage.md`
  reports `F.Fab/body-box overlaps: 0`, `Courtyard-only overlaps: 4`,
  `Waived courtyard-only overlaps: 4`, and `Unwaived courtyard-only overlaps: 0`.
- `circuits/review/assembly_clearance_waivers.json` documents the four accepted
  courtyard-only assembly-spacing waivers: `C62/U16`, `C62/C70`, `U4/D4`, and
  `C61/L1`.
- `python3 circuits/check_jlcpcb_order_package.py` passes on the generated
  Gerber/drill/BOM/POS package and verifies the required PD/laser/backside
  board labels plus the J7 C192300 2x4 SMD header metadata.

Disposition:

This is a partial CAD signoff only. The screenshot is useful evidence that a
zone-refilled GUI DRC run reported zero board-rule violations and zero
unconnected items at the time of capture. The current board now has durable
KiCad 9 physical DRC, headless Pcbnew DRC, custom schematic/PCB parity,
package-body triage, explicit courtyard-only waivers, and JLCPCB package
evidence. It still does not prove final native CAD signoff because KiCad 9 ERC
and schematic-parity DRC still report findings. Keep
`KICAD_ERC_DRC_ZONE_SIGNOFF` open for full release until those native ERC/parity
items are fixed or explicitly waived and the final reports are regenerated.
