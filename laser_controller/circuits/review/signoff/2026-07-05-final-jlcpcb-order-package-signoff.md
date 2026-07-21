# Final JLCPCB Order Package Signoff

> **Superseded / critical hold (2026-07-12):** the hashes in this signoff bind to
> the pre-repair package. The 2026-07-07 OPA380/Bourns signoff found real mirrored
> U1–U4 and RV5–RV8 footprints and says this old package should not be approved.
> No archived JLCPCB production-file confirmation proves that the corrected
> package replaced the paid submission. See the order journal before accepting
> or powering any returned board.

Date: 2026-07-05; updated 2026-07-06 for J1/J2 USB and J5/J6 THT assembly inclusion

Scope: Current laser-controller fabrication package for JLCPCB PCB plus top-side
SMT assembly and J5/J6 THT connector assembly upload, with only the optical
PD/LD devices on the backside.

## Package Status

`python3 circuits/run_laser_controller_review.py` reports:

- `JLCPCB order package status: READY`
- `First-article/production release status: BLOCKED`
- `DEFERRED: Open first-article/production blockers`

The deferred blockers are calibration, firmware, thermal, protection,
procurement, and measured bring-up work. They do not invalidate the current
Gerber/BOM/POS upload package, but they must be closed before trusting the board
for bench measurements, optical safety behavior, production, or field use.

## Placed First-Article Order

Order placed and paid on 2026-07-06:

- JLCPCB work order / batch: `W2026070704037950`
- PCB order: `Y57-2673627A`
- PCBA order: `SMT026070663451-2673627A`
- Invoice: `2673627A2026070704037950`
- Gerber file name on JLCPCB: `laser_controller_gerbers_Y57`
- BOM/CPL files: `laser_controller_bom_jlcpcb.csv`,
  `laser_controller_pos.csv`
- Quantity: 5 boards
- Assembly side captured from order page: top side
- Grand total: USD 731.20

The order record is archived in
`circuits/review/journal/2026-07-06-jlcpcb-laser-controller-order.md`.
Shipping/billing PII and card details were intentionally left out of git.

## Verification

- `python3 circuits/check_jlcpcb_order_package.py`
  - PASS: 14 Gerber/drill files
  - PASS: package archive includes BOM/POS
  - PASS: 175/175 BOM/POS designators match
  - PASS: J5/J6 are included for THT connector assembly
  - PASS: J7 is `C192300` 2x4 SMD
  - PASS: only PD/LD footprints are bottom-side
  - PASS: PD/laser labels and backside `vivonics` mark are present
- KiCad 10.0.4 hard DRC: PASS, 0 violations, 0 unconnected pads, 0
  schematic-parity errors at error severity.
- KiCad 10.0.4 full DRC: PASS for layout/connectivity, with 36
  footprint/symbol metadata field warnings only.
- Optical-side placement readback: B.Cu footprints are `D1`-`D4` and
  `LD1`-`LD4`; B.Paste footprints are `D1`-`D4` only.
- 3D model coverage: PASS.
- Signal-PD footprint geometry: PASS.
- Laser-diode footprint pinout: PASS.

## Upload Artifacts

- `circuits/laser_controller_jlcpcb_package.zip`
- `circuits/laser_controller_gerbers.zip`
- `circuits/laser_controller_bom_jlcpcb.csv`
- `circuits/fab/laser_controller_pos.csv`
- `circuits/fab/laser_controller_jlcpcb_upload_manifest.md`

`circuits/laser_controller_jlcpcb_package.zip` contains 16 files: front/back
copper, two inner copper layers, paste, silkscreen, mask, Edge.Cuts, Gerber job,
PTH/NPTH drills, JLCPCB BOM, and JLCPCB POS.

The CPL uses the same coordinate frame as the KiCad Gerbers, including negative
Y coordinates. Do not shift it to a board-local `0,0` origin before upload.

For the JLCPCB web flow, upload `laser_controller_gerbers.zip` on the PCB page,
then upload `laser_controller_bom_jlcpcb.csv` and
`circuits/fab/laser_controller_pos.csv` on the PCBA page. The combined
`laser_controller_jlcpcb_package.zip` is a flat transfer/review archive, not the
preferred PCBA BOM/CPL upload.

## PCBA Side Policy

All ICs, passives, trimmers, switches, buck parts, SMD connectors, and the J5/J6
through-hole power connectors are on the front/top side. The only backside SMT
parts intended for JLCPCB placement are `D1`-`D4` (`SFH2201`) if two-sided SMT
assembly is selected. `LD1`-`LD4` direct laser cans remain
hand-installed/mechanically inspected optical parts.

After BOM/CPL upload, the JLCPCB quote should show:

- no unmatched components,
- no CPL processing failure,
- `J1,J2` selected as `C46391` for top-side Mini-B USB assembly,
- `J5` selected as `C194407` for THT/wave/manual connector assembly,
- `J6` selected as `C386757` for THT/wave/manual connector assembly,
- `J7` selected as `C192300`,
- top-side assembly containing the normal SMT population,
- bottom-side assembly, if enabled, containing only `D1`-`D4` `SFH2201`.

If ordering top-side assembly only, remove or deselect `D1`-`D4` in the JLCPCB
PCBA review and hand-place the SFH2201 photodiodes with the laser cans.

## Quote-Time Procurement Notes

The July 5 quote triage replaced the three rows JLCPCB flagged:

- `R42,R44,R46,R48`: `RTT032400FTP`, JLCPCB `C103446`, 240 ohm 0603.
- `R41`: `0603WAF2491T5E`, JLCPCB `C22908`, 2.49 k 0603.
- `C70`: `100CE22FS+P`, JLCPCB `C242011`, 22 uF 100 V SMD electrolytic.

`R41` was moved to `C22908` after JLCPCB reported a shortfall for `C103460`.
`C242011` had enough live stock for a 5-board first-article order but little
margin during the July 5 quote review. If `C70` is short when uploading, do not
change copper or footprints; either select a same-footprint JLCPCB substitute on
the quote page and checkpoint the new C-code, or mark the single row
not-assembled and hand-place that part.

## SHA256

```text
99edd53cbfd12dce3b5175e06c791c4805ac131a8c83f409c281d4962d1f306f  circuits/laser_controller_gerbers.zip
1923d2e624c5fecf20f3a804278eac854853a2d5e9b1e9ac31bfbd97530b8c29  circuits/laser_controller_jlcpcb_package.zip
0d0de72c72e62a764d51373d87a15c74c038ac83cad23bf5caaeb77b6064c286  circuits/laser_controller_bom_jlcpcb.csv
cc2a82c030d8bbb17dc394fd4fdf4b33de54d7cf10f1a0a383278b746caf655d  circuits/fab/laser_controller_pos.csv
9e6e2266a2cebb7bb652c375bdf4190f4084cacffa63eb1634251269d71d228f  circuits/fab/laser_controller_full_procurement.csv
```
