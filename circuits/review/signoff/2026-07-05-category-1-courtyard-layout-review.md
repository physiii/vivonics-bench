# Category 1 Courtyard/Layout Review

Date: 2026-07-05

Scope: Native KiCad courtyard-overlap warnings in the current
`laser_controller.kicad_pcb` layout.

## Overall Severity Ranking

The current category order for release cleanup is:

1. Open first-article/release blockers: calibration, thermal, VIN24 protection,
   AD7606 firmware/readback, AP2112 measurement, passive AVL/derating.
2. Layout/manufacturing warnings: native KiCad courtyard-overlap warnings.
3. Review-harness/reporting accuracy: do not let warning-only DRC findings hide
   schematic-parity status.
4. Expected-fail policy checks: deliberately bad operating scenarios that must
   keep failing.

## Courtyard/Layout Category Result

The native KiCad 9 physical DRC report still lists four warning-level
`[courtyards_overlap]` pairs:

- `C62` / `U16`
- `C62` / `C70`
- `U4` / `D4`
- `C61` / `L1`

`/usr/bin/python3 circuits/check_courtyard_overlap_triage.py` classifies all
four as courtyard-only:

- `F.Fab/body-box overlaps: 0`
- `Courtyard-only overlaps: 4`
- `Waived courtyard-only overlaps: 4`
- `Unwaived courtyard-only overlaps: 0`

The explicit waivers live in
`circuits/review/assembly_clearance_waivers.json`. This category is accepted for
JLCPCB upload on the current footprint set because there is no package-body
overlap and the tighter placement preserves the buck input loops and the blue
TIA summing-node geometry.

## Required Recheck

Re-run the native KiCad DRC, courtyard triage, focused layout-geometry review,
and JLCPCB package check after any placement, footprint, or selected assembly
part change in these areas.
