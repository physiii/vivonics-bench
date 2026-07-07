# Laser Controller JLCPCB Upload Manifest

Date: 2026-07-06

Scope: first-article laser-controller PCB plus PCBA upload package.

## Upload Files

Use these three files in the JLCPCB order flow:

| JLCPCB step | Upload file |
|---|---|
| PCB Gerber upload | `circuits/laser_controller_gerbers.zip` |
| PCBA Bill of Materials | `circuits/laser_controller_bom_jlcpcb.csv` |
| PCBA Component Placements / CPL | `circuits/fab/laser_controller_pos.csv` |

`circuits/laser_controller_jlcpcb_package.zip` is a flat archive containing the
Gerbers, drills, BOM, and CPL for transfer/review. Prefer the separate files
above in the web form.

For the complete build kit, including JLCPCB-assembled SMT/THT parts and
hand-install optical parts, use:

- `circuits/fab/laser_controller_full_procurement.csv`

## Expected JLCPCB Parser Result

After re-uploading the BOM and CPL, the quote page should show:

- no unmatched components,
- no failed CPL processing,
- no inventory shortage for the current 5-board order,
- `J1,J2` selected as `C46391` for top-side USB assembly,
- `J7` selected as `C192300`,
- `J5` selected as `C194407` for THT/wave/manual connector assembly,
- `J6` selected as `C386757` for THT/wave/manual connector assembly,
- `R41` selected as `C22908`,
- `R42,R44,R46,R48` selected as `C103446`,
- `C70` selected as `C970665`.

The CPL is in JLCPCB's five-column sample format:

```text
Designator,Mid X,Mid Y,Layer,Rotation
```

Coordinates include the `mm` suffix and intentionally remain in the same
coordinate frame as the Gerbers, including KiCad's negative Y coordinate. Do not
shift the CPL to a board-local `0,0` origin before upload.

## Side Selection

All ICs, passives, trimmers, switches, buck parts, SMD connectors, and the J5/J6
through-hole power connectors are on the top/front side.

The bottom/back side should contain only optical parts:

- `D1`-`D4`: `SFH2201` SMT signal photodiodes, included in the JLCPCB BOM/CPL.
- `LD1`-`LD4`: direct laser cans, not in the JLCPCB BOM/CPL; hand-install.

If the order is top-side PCBA only, deselect or do-not-assemble `D1`-`D4` during
JLCPCB review and hand-place them. If ordering two-sided PCBA, verify the bottom
side contains only `D1`-`D4` and no ICs/passives.

If JLCPCB flags `J5` or `J6` as non-SMT, keep them selected only if the quote
flow offers through-hole/wave/manual assembly for those rows. Otherwise deselect
only `J5`/`J6` and move them back to hand-install without changing the PCB.

## Current Quote-Time Watch Items

These rows were changed after the July 5 JLCPCB parser page reported shortage or
no-selection issues:

| Designators | MPN | JLCPCB/LCSC | Action if JLC flags it again |
|---|---|---:|---|
| `J1,J2` | `920-462A2021S10101` | `C46391` | Keep; this is the access-controller USB assembly row and its JLC/EasyEDA pad geometry matches the existing 5-pin USB land pattern. |
| `R42,R44,R46,R48` | `RTT032400FTP` | `C103446` | Keep; choose same-footprint 240 ohm 0603 1% only if JLC stock changes. |
| `R41` | `0603WAF2491T5E` | `C22908` | Same-footprint 2.49 k 0603 1% replacement for short `C103460`; keep unless JLC stock changes. |
| `C70` | `RVT2A220M0810 22UF 100V` | `C970665` | Same D8xL10.2 mm JLCPCB SMT substitute for short `C242011`; quote page lists 22 uF, 100 V, 8 mm diameter, 10.2 mm height, 90 mA ripple at 120 Hz. |

Do not change the PCB just to resolve one quote-time stock row. For this
first-article build, a quote-page substitute or hand-place decision is lower
risk than another layout churn.

## Placed Order

Order placed and paid on 2026-07-06:

- JLCPCB work order / batch: `W2026070704037950`
- PCB order: `Y57-2673627A`
- PCBA order: `SMT026070663451-2673627A`
- Invoice: `2673627A2026070704037950`
- Quantity: 5 boards
- PCB line: USD 37.20
- PCBA line: USD 432.83
- Shipping: USD 51.66
- State sales/use tax: USD 44.99
- Customs duties and taxes: USD 164.52
- Grand total: USD 731.20

Detailed order capture is archived in
`circuits/review/journal/2026-07-06-jlcpcb-laser-controller-order.md`.

## Final Go/No-Go

Go for JLCPCB first-article ordering when the quote page shows zero unmatched
parts, zero CPL errors, and acceptable stock for the selected quantity. This is
not a production-release signoff; first-article bring-up, optical calibration,
laser safety behavior, VIN24 protection, and temperature evidence remain open.
