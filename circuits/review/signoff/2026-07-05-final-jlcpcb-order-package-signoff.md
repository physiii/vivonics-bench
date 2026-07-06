# Final JLCPCB Order Package Signoff

Date: 2026-07-05

Scope: Current laser-controller fabrication package for JLCPCB PCB plus top-side
SMT assembly upload, with only the optical PD/LD devices on the backside.

## Package Status

`python3 circuits/run_laser_controller_review.py` reports:

- `JLCPCB order package status: READY`
- `First-article/production release status: BLOCKED`
- `DEFERRED: Open first-article/production blockers`

The deferred blockers are calibration, firmware, thermal, protection,
procurement, and measured bring-up work. They do not invalidate the current
Gerber/BOM/POS upload package, but they must be closed before trusting the board
for bench measurements, optical safety behavior, production, or field use.

## Verification

- `python3 circuits/check_jlcpcb_order_package.py`
  - PASS: 14 Gerber/drill files
  - PASS: package archive includes BOM/POS
  - PASS: 173/173 BOM/POS designators match
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

For the JLCPCB web flow, upload `laser_controller_gerbers.zip` on the PCB page,
then upload `laser_controller_bom_jlcpcb.csv` and
`circuits/fab/laser_controller_pos.csv` on the PCBA page. The combined
`laser_controller_jlcpcb_package.zip` is a flat transfer/review archive, not the
preferred PCBA BOM/CPL upload.

## PCBA Side Policy

All ICs, passives, connectors, trimmers, switches, and buck parts are on the
front/top side. The only backside SMT parts intended for JLCPCB placement are
`D1`-`D4` (`SFH2201`) if two-sided SMT assembly is selected. `LD1`-`LD4` direct
laser cans, `J5` barrel input, and `J6` RJ45 input are not part of the JLCPCB
SMT BOM and remain hand-installed/mechanically inspected parts.

After BOM/CPL upload, the JLCPCB quote should show:

- no unmatched components,
- no CPL processing failure,
- `J7` selected as `C192300`,
- top-side assembly containing the normal SMT population,
- bottom-side assembly, if enabled, containing only `D1`-`D4` `SFH2201`.

If ordering top-side assembly only, remove or deselect `D1`-`D4` in the JLCPCB
PCBA review and hand-place the SFH2201 photodiodes with the laser cans.

## Quote-Time Procurement Notes

The July 5 quote triage replaced the three rows JLCPCB flagged:

- `R42,R44,R46,R48`: `RTT032400FTP`, JLCPCB `C103446`, 240 ohm 0603.
- `R41`: `RTT032491FTP`, JLCPCB `C103460`, 2.49 k 0603.
- `C70`: `100CE22FS+P`, JLCPCB `C242011`, 22 uF 100 V SMD electrolytic.

`C103460` and `C242011` had enough live stock for a 5-board first-article order
but little margin during the July 5 quote review. If either row is short when
uploading, do not change copper or footprints; either select a same-footprint
JLCPCB substitute on the quote page and checkpoint the new C-code, or mark the
single row not-assembled and hand-place that part.

## SHA256

```text
33c8f6449577ae67f07ff8e31ee011681506ea8993b0e252b03f5605c0534d2d  circuits/laser_controller_gerbers.zip
f075d82c0d6a9324df66dfd3cbf389ebdfa800796416dfd0a56a55c0b4fe4584  circuits/laser_controller_jlcpcb_package.zip
55adad1c70b27a3081e82dbff26a597234760427a83e7209e614c154f2aff3f2  circuits/laser_controller_bom_jlcpcb.csv
4a6c5aeeabfd5a95fe43617c8fc85b13948063afd09e5b1d515f6554f7799e3b  circuits/fab/laser_controller_pos.csv
947c8f2afd85d1c2a3ab2536ab3597b26edd6fa468bd060c5235a962057314ab  circuits/fab/laser_controller_full_procurement.csv
```
