# Passive AVL And Derating Category Review - 2026-07-05

Scope: severity-ranked category 7 from
`circuits/review/signoff/2026-07-05-release-category-matrix.md`.

## Category Rank

Rank 7, medium. A passive substitution, stale C-code, missed pulse/surge case,
or hotter assembled board can invalidate the steady-state assumptions even when
the schematic and generated JLCPCB package are internally consistent.

## Current Result

The current passive and procurement state is acceptable for controlled
first-article ordering under the existing bench boundary:

- The first-article passive MPN/LCSC set is locked against the exported netlist.
- The steady-state capacitor voltage, resistor voltage, and resistor power
  derating gate passes for the current board assumptions.
- The JLCPCB package gate confirms Gerbers, BOM, and POS are present and agree
  on the 173 assembled designators.
- Quote-time procurement evidence must still be captured before treating the
  order as release evidence.
- Passive substitutions must be rejected or explicitly reviewed in a new
  checkpoint before ordering.
- Pulse/surge/current derating and board-temperature evidence remain required
  before field or production release.

This category is not production-closed. The repo proves the static first-article
passive list, steady-state derating assumptions, and procurement evidence
template; it does not prove live JLCPCB/LCSC stock, quote substitutions,
current lifecycle status, pulse/surge behavior, or measured board temperature.

## Evidence Reviewed

- `python3 circuits/check_passive_derating.py circuits/review/generated/laser_controller_kicad9.net`
  passes for 65 capacitors and 64 resistors/trimmers.
- `python3 circuits/check_passive_avl_lock.py --netlist circuits/review/generated/laser_controller_kicad9.net`
  passes for 24 passive MPN/LCSC pairs and 129 placements.
- `python3 circuits/check_procurement_release_template.py`
  passes the quote-time BOM/POS, substitution, derating, temperature, and
  order-archive evidence rows.
- `python3 circuits/check_jlcpcb_order_package.py`
  passes the Gerber/drill archive, BOM/POS inclusion, BOM/POS designator match,
  J7 C192300 2x4 SMD header check, board labels, and backside `vivonics` mark.

## Closure State

Do not mark any `PASSIVE_PRODUCTION_AVL_AND_DERATING` row closed in
`circuits/review/calibration/first_article_release_evidence.csv` until the
specific evidence exists:

- `quote_acceptance`: current JLCPCB quote timestamp, accepted BOM/POS together,
  accepted C-codes, rejected or explicitly reviewed substitutions, order
  archive, and checkpoint commit hash.
- `passive_derating`: pulse/surge/current derating for the 24 V input and
  laser-current paths plus measured board temperature at the accepted duty
  cycle.

## Decision

No additional pre-order layout defect was found in this category by the current
automated gates. The remaining risk is live procurement and first-article
thermal/derating evidence, not a static CAD/package defect.
