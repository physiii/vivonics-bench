# OPA380 and Bourns 3224W Orientation Repair Signoff

Date: 2026-07-07 CDT

Scope: U1-U4 OPA380AID SOIC-8 TIA amplifiers and RV1-RV8 Bourns 3224W
trimmers on `circuits/laser_controller.kicad_pcb`.

## Finding

JLCPCB's assembly preview for U1, U2, U3, and U4 showed the package dot/arrow
disagreeing with the expected OPA380 pin-1 corner. Re-audit confirmed this was
a real footprint mirror defect. The old board assigned the intended schematic
nets to numeric pads, but the embedded SOIC-8 copper was mirrored relative to
TI's OPA380 top-view pinout. A numeric pad-net check alone was not enough.

The same re-audit found RV5-RV8 Bourns 3224W feedback trimmers mirrored in the
embedded PCB footprint versus the stock Bourns/KiCad physical geometry.

## Repair

`circuits/repair_orientation_sensitive_footprints.py` repairs only the confirmed
mirror-risk parts:

- U1-U4 OPA380AID SOIC-8 local footprint primitives and pads.
- RV5-RV8 Bourns 3224W feedback trimmer local footprint primitives and pads.
- Directly attached local escape traces/vias affected by those pad moves.

The repaired OPA380 local SOIC-8 pad order is:

| Pin | Local coordinate | Net |
|---:|---:|---|
| 1 | `(-2.475, -1.905)` | NC |
| 2 | `(-2.475, -0.635)` | local `PD_ANODE` summing node |
| 3 | `(-2.475, 0.635)` | local `VBIAS` |
| 4 | `(-2.475, 1.905)` | `GND` |
| 5 | `(2.475, 1.905)` | NC |
| 6 | `(2.475, 0.635)` | `VOUTx` |
| 7 | `(2.475, -0.635)` | `+5V` |
| 8 | `(2.475, -1.905)` | NC |

U1-U4 remain intentionally rotated 180 degrees on the board. With TI's SOIC-8
top-view pinout, that places physical pin 1 and the package dot at the
lower-right board corner. That is the correct board rotation, not a mirror.

The repaired Bourns 3224W local pad order is:

| Pin | Local coordinate | Net role |
|---:|---:|---|
| 1 | `(1.25, -1.45)` | end terminal |
| 2 | `(0, 1.45)` | wiper |
| 3 | `(-1.25, -1.45)` | end terminal |

RV1-RV4 use pad 2 as the VBIAS wiper. RV5-RV8 tie pad 2/wiper and pad 3 to
`VOUT1..4`, making the feedback trims rheostats with the wiper on the OPA380
output side.

## Verification

Commands run after repair:

```bash
python3 circuits/check_orientation_polarity_pcb.py --board circuits/laser_controller.kicad_pcb
kicad-cli pcb drc --all-track-errors --refill-zones --severity-all --exit-code-violations --format report --output circuits/review/generated/laser_controller_kicad9_physical_drc.rpt circuits/laser_controller.kicad_pcb
python3 circuits/check_jlcpcb_order_package.py
python3 circuits/run_laser_controller_review.py
```

Results:

- `check_orientation_polarity_pcb.py` passes U1-U4 OPA380 physical pad order,
  intentional 180-degree rotation, and pin nets against the TI OPA380 datasheet
  top-view pinout.
- `check_orientation_polarity_pcb.py` passes RV1-RV8 Bourns 3224W wiper
  geometry and nets.
- Native KiCad DRC with refilled zones reports 0 violations and 0 unconnected
  pads.
- The regenerated JLCPCB package gate passes after rebuilding Gerbers, drill
  files, BOM, CPL/POS, and transfer zip.

Visual evidence generated from the current PCB:

- `circuits/review/generated/laser_controller_top_render.png` is the full
  top-side KiCad 3D render for this board state.
- `circuits/review/generated/laser_controller_tia_top_render_crop.png` is the
  TIA-area crop showing U1-U4 with package dots at the lower-right board
  corner.
- `circuits/review/generated/opa380_orientation_visual_audit.svg` shows the TI
  OPA380 top-view pin contract next to the current U1-U4 board-side physical
  pin order and nets.
- `circuits/review/generated/opa380_orientation_visual_audit.png` is the
  rendered PNG version of the same datasheet-vs-board visual audit.

## JLCPCB Reply Basis

The old JLCPCB order package should not be approved. It was current to the
mirrored board. The regenerated package dated 2026-07-07 is the corrected
artifact. In JLCPCB's assembly preview after upload, U1-U4 should show the
SOIC package dot at the lower-right board corner for the current placement.
