# Assembly Courtyard Waiver Signoff - 2026-07-05

Scope: current `circuits/laser_controller.kicad_pcb` layout and generated
JLCPCB prototype order package.

## Current Evidence

Commands run:

```bash
/usr/bin/python3 circuits/check_kicad_pcbnew_drc_report.py
/usr/bin/python3 circuits/check_courtyard_overlap_triage.py
python3 circuits/check_layout_review_geometry.py
python3 circuits/check_jlcpcb_order_package.py
```

Observed result:

- Headless Pcbnew DRC refills zones in memory and reports 0 unconnected pads.
- Headless Pcbnew DRC reports 0 footprint errors.
- The only native Pcbnew findings are 4 `[courtyards_overlap]` warnings.
- Courtyard triage reports 0 F.Fab/body-box overlaps.
- All 4 courtyard-only warnings are covered by explicit waivers in
  `circuits/review/assembly_clearance_waivers.json`.
- `check_layout_review_geometry.py` passes, including the D4-to-U4 sensitive
  blue-channel geometry referenced by the courtyard waiver.
- `check_jlcpcb_order_package.py` passes for the Gerber/drill archive, flat
  JLCPCB package archive, BOM/POS designator match, J7 C192300 metadata, and
  required board labels.

Reverified after category-1 checkpoint `c3633d5` at
`2026-07-05T06:04:00-05:00`:

```bash
/usr/bin/python3 circuits/check_courtyard_overlap_triage.py
python3 circuits/check_layout_review_geometry.py
```

Observed result: 4 native courtyard warnings, 0 F.Fab/body-box overlaps, 4/4
covered by explicit courtyard-only waivers, and 15 high-risk layout distances
within targets.

## Waived Pairs

- `C62` / `U16`
- `C62` / `C70`
- `U4` / `D4`
- `C61` / `L1`

## Remaining Manual Review

This signoff accepts the current courtyard-only warnings for controlled
first-article ordering. It does not replace JLCPCB's quote/assembly viewer,
native KiCad schematic ERC/parity, physical part fit inspection, or re-running
the courtyard triage after any placement, footprint, package, or selected-part
change.
