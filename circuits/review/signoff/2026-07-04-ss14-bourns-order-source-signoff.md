# SS14 and Bourns 3224W Order/Orientation Signoff

Date: 2026-07-04 CDT

Scope: D5-D6 SS14 OR-ing diodes and RV1-RV8 Bourns 3224W trimmers on
`circuits/laser_controller.kicad_pcb`.

Supersession note: the 2026-07-07 JLCPCB-preview re-audit found this signoff
was insufficient for RV5-RV8 because it checked numeric pad nets but not local
physical footprint geometry. RV5-RV8 were repaired and re-signed in
`circuits/review/signoff/2026-07-07-opa380-bourns-orientation-repair-signoff.md`.
This document remains evidence for D5/D6 SS14 polarity and for the intended
Bourns pin-net roles, but the 2026-07-07 signoff is the controlling physical
Bourns 3224W orientation evidence.

## Source Evidence

- JLCPCB part detail page for C2480 identifies the orderable SMT assembly part
  as MDD(Microdiode Semiconductor) `SS14`, JLCPCB part `C2480`, package
  `SMA(DO-214AC)`, Basic assembly, 40 V / 1 A Schottky diode.
- LCSC C2480 page also identifies the part as MDD(Microdiode Semiconductor)
  `SS14`, package `SMA(DO-214AC)`, key attribute `DIODE SCHOTTKY 40V
  SMA(DO-214AC)`.
- Bourns 3224 datasheet identifies pin `2` as `WIPER`, with pins `1` and `3`
  as the end terminals.
- KiCad stock `Potentiometer_Bourns_3224W_Vertical` footprint is SMD and uses
  pad `2` as the large center pad, with pads `1` and `3` as the end terminals.

## PCB Extraction

Extraction command:

```bash
/usr/bin/python3 - <<'PY'
import pcbnew
board = pcbnew.LoadBoard('circuits/laser_controller.kicad_pcb')
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref in ['D5', 'D6'] or ref.startswith('RV'):
        print(ref, fp.GetValue(), fp.GetFPID().GetLibItemName(),
              fp.GetOrientationDegrees(), fp.GetLayerName())
        for pad in sorted(fp.Pads(), key=lambda p: p.GetNumber()):
            print(' ', pad.GetNumber(), pad.GetNetname())
PY
```

Relevant result:

| Ref | Pad 1 | Pad 2 | Pad 3 | Verdict |
|---|---|---|---|---|
| D5 | `VBUS_5V` anode | `+5V` cathode | - | USB VBUS OR-ing polarity is correct. |
| D6 | `/POWER_IO/BUCK_5V` anode | `+5V` cathode | - | Buck 5 V OR-ing polarity is correct. |
| RV1 | `Net-(R4-Pad2)` | `Net-(RV1-W)` | `GND` | Pin 2 is the VBIAS wiper net. |
| RV2 | `Net-(R8-Pad2)` | `Net-(RV2-W)` | `GND` | Pin 2 is the VBIAS wiper net. |
| RV3 | `Net-(R12-Pad2)` | `Net-(RV3-W)` | `GND` | Pin 2 is the VBIAS wiper net. |
| RV4 | `Net-(R16-Pad2)` | `Net-(RV4-W)` | `GND` | Pin 2 is the VBIAS wiper net. |
| RV5 | `Net-(D1-A)` | `VOUT1` | `VOUT1` | Pin 2 wiper is tied to output side. |
| RV6 | `Net-(D2-A)` | `VOUT2` | `VOUT2` | Pin 2 wiper is tied to output side. |
| RV7 | `Net-(D3-A)` | `VOUT3` | `VOUT3` | Pin 2 wiper is tied to output side. |
| RV8 | `Net-(D4-A)` | `VOUT4` | `VOUT4` | Pin 2 wiper is tied to output side. |

## Verdict

- D5/D6 use the current JLCPCB/LCSC C2480 MDD SS14 SMA(DO-214AC) assembly
  identity and the PCB pad nets match the intended anode-to-source,
  cathode-to-`+5V` OR-ing polarity.
- RV1-RV4 use pin 2 as the VBIAS wiper; RV5-RV8 tie Bourns pin 2 wiper to the
  OPA380 output side, with pin 3 also tied to the same output net, so the
  feedback parts are rheostats as intended.
- This closes the SS14 exact-order-source/polarity blocker and records the
  intended Bourns 3224W wiper net roles. The controlling physical Bourns 3224W
  footprint-orientation closure is the 2026-07-07 repair signoff. Recheck the
  JLCPCB quote/cart if C2480, C81348, or C116323 are substituted.
