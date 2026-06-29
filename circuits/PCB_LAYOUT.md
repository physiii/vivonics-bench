# Laser Controller — PCB layout & routing guide

`laser_controller.kicad_pcb` currently has **recovered hand-placement coordinates
and pad-net assignments**: 160 physical footprints match the schematic reference set
with no duplicate refs, and the old laser/MPD header footprint is not present. PCB
pad nets are explicit and derived from the exported KiCad schematic netlist.
It also emits checked net classes for laser current, power rails, USB, TIA-sensitive analog,
monitor/ADC telemetry, laser control, and digital control nets; the fallback `Default` class
is required to stay empty by `check_laser_controller_pcb.py`.
The generated stackup is four copper layers: `F.Cu` signal, `In1.Cu` ground/reference,
`In2.Cu` power/reference, and `B.Cu` signal.
The current PCB does not yet contain a filled `In1.Cu` `GND` reference-zone
definition. Add/refill zones in KiCad after placement/routing so the actual
copper pour is generated and checked by DRC. `check_laser_controller_pcb.py`
fails routed segments on `In1.Cu`; that layer is reserved as the quiet
ground/reference plane, while `F.Cu`, `B.Cu`, and selected `In2.Cu` trunks carry
routed copper once routing exists.
The board checker also enforces pad-to-pad proximity limits: USB connectors at their
discrete ESD clamps and CP2102N/native-USB endpoints, AP2112 input/output capacitors,
local ESP32 3V3 decoupling, EN RC, BOOT pull-up, every OPA380/SFH2201 TIA input-feedback-bias cluster,
every TLV9001/AO3400A laser gate/sense/control/compensation cluster, and every monitor-PD
sense/reference/ADC-isolation cluster near the direct laser footprints.
It also fails on different-net pad bounding-box overlaps between different footprints.
It also fails if any physical pad geometry falls outside the 90 x 50 mm board outline.
It also fails if routed copper endpoints/vias leave the board outline or if any same-net
segment endpoint/via is dangling instead of terminating on a same-net pad, via, or segment.
It also fails route-layer policy violations, including USB/MPD_RAW/TIA-local and laser-loop
local nets escaping from `F.Cu`.
It also fails route-width policy violations: USB must remain 0.25 mm, low-current
signal/telemetry/local-control copper must remain 0.20 mm unless explicitly widened,
laser cathodes must remain 0.60 mm, `LASER_V+` must remain 0.80 mm, and power/ground
trunks may use only their documented width sets.
It also fails sensitive local-route length violations for `MPD_RAWx`, OPA380 summing/
bias nodes, photodiode cathode/bias stubs, trim wipers, TLV9001 laser-control nodes,
and AO3400A gate-drive nodes.
Current blocker: the PCB is not release-clean. The measured board has 0
board-level routed segments, 0 vias, recovered placement for 160 physical
footprints, and one footprint-internal ESP32 antenna keepout zone.
`check_laser_controller_pcb.py` still fails because final board-boundary and
placement-proximity limits are not met, USB routes are absent, and no filled
`In1.Cu` GND reference plane exists. `check_laser_controller_release_gate.py`
also fails because
signal/control multi-pad nets, rails, pours, laser-anode copper, and
high-current GND vias are not routed.
The old J3 AD7606 debug/output header has been removed now that U14 is on-board.

## Board

- Outline **90 × 50 mm**, 1.6 mm, 4× M3 mounting holes at corners (3 mm from edges).
- **Power**: USB VBUS or optional EXT 5V via J6 feeds +5V through SS14 OR-ing diodes.
  `LASER_V+` is a separate laser-anode rail from J5.
- Floorplan:
  - **Left edge** (x≈3mm) — 4× SFH2201 photodiodes (D1–D4), stacked vertically,
    rotated 270° so light enters from the left.
  - **Left-centre** (x≈10–32mm) — TIA ×4 (OPA380 + VBIAS trim-pot + passives).
  - **Centre** (x≈37–55mm) — Laser drivers ×4 (TLV9001 + AO3400A + passives).
  - **Right** (x≈58–85mm) — ESP32-S3-WROOM-1 (rotated 90°, antenna toward top edge)
    + CP2102N USB-UART + AP2112K LDO + discrete USB/VBUS ESD + decoupling.
  - **Right edge** — J5 laser PSU, J6 external 5V.
  - **Bottom edge** — J1 USB Mini-B.
  - **Top edge** — J2 USB Mini-B.

## Connectors

| Ref | Function | Pins | Type |
|-----|----------|------|------|
| J1  | USB Mini-B to CP2102N USB-UART | 6 | SMD horizontal, JLCPCB assembly; shield pad 6 to GND |
| J2  | USB Mini-B to ESP32-S3 native USB | 6 | SMD horizontal, JLCPCB assembly; shield pad 6 to GND |
| J5  | LASER PSU input (`LASER_V+` + GND) | 2 | TH pin header, hand-solder |
| J6  | EXT 5V in (optional) | 2 | TH pin header, hand-solder |

## Finish it in KiCad

1. **Eeschema → Inspect → Electrical Rules Checker** — run GUI ERC against the generated unique-ref schematic and review every violation or warning.
2. **Pcbnew → Tools → Update PCB from Schematic** (F8) — syncs netlist + refs.
3. Refill/review the `In1.Cu` `GND` zone per `POWER_TREE.md`.
4. Run **DRC** with refilled zones and schematic parity for 0 unwaived unrouted/violations.
5. **File → Fabrication Outputs → Gerbers + Drill** only after ERC, DRC, rail review, and visual return-path review pass.

## Before fabrication

- **ESP32-S3-WROOM-1**: real Espressif symbol; USB D− = GPIO19/module pin 13, USB D+ =
  GPIO20/module pin 14; GPIO0/BOOT is pulled up and has a local PROG button.
- **USB Mini-B**: `920-462A2021S10101` / C46391 metadata on the KiCad Würth
  65100516121 footprint, horizontal SMD, port faces board edge; resolve exact
  connector/footprint fit before fabrication.
- **SFH2201**: pad 1 = cathode, pad 2 = anode — check PD orientation.
- **Direct laser pinout**: confirm every raw laser MPN's LD/PD/common/case pin table before
  soldering a diode into `LD1..LD4`. Current Digikey-cart
  mapping: `D7805I` -> channel 1 with `OptoDevice:LaserDiode_TO18-D5.6-3`,
  `D6505I` -> channel 2 with `OptoDevice:LaserDiode_TO18-D5.6-3`,
  `PLT5 520EB_P` -> channel 3 with `OptoDevice:LaserDiode_TO56-3`, and
  `PLT5 450GB` -> channel 4 with `OptoDevice:LaserDiode_TO56-3`. The first
  three expose compatible monitor photodiodes; `PLT5 450GB` has no monitor
  photodiode, so `MPD_RAW4` is a spare/open monitor input and must
  not be tied to the blue diode case pin.

## Routing notes

- Route as **4-layer Sig/GND/PWR/Sig**. `In1.Cu` should be the main quiet ground/reference
  plane and `In2.Cu` the power/reference plane; keep the ESP32 antenna keepout copper-free on
  every copper layer.
- Solid ground plane; keep TIA summing nodes (OPA380 −IN) tiny and guarded.
- **Analog/digital split**: ESP32 + PWM returns off TIA analog return; star ground.
- **Laser current path** (AO3400A drain -> `LASER_Nx` -> `LDx`): short wide traces, away from TIA.
- **Monitor PD path** (`MPD_RAWx`): route as quiet analog telemetry, not with the laser
  cathode current paths. Keep the 750 ohm sense resistors, INA4180 inputs, LM4040 bias
  reference, 2.49 k sink, and 1 k / 100 nF ADC filters close to the direct laser footprints or the ESP32 ADC
  entry area.
- The custom PCB checker now enforces same-layer spacing from laser-current copper:
  `TIA_Sensitive` >= 2.00 mm, `MPD_RAWx` >= 0.50 mm, and filtered `Monitor_ADC`
  telemetry >= 0.25 mm once routed copper exists. The current recovered-placement PCB has
  zero board-level segments, so these spacing minima still need to be measured
  after placement/routing. Cross-layer overlap near the dense direct-laser
  cluster is still a visual review item.
- **USB D+/D−**: short USB routes with copied-sheet discrete ESD at each connector.
- **Antenna keep-out**: copper-free zone around ESP32 antenna (top edge).
- **Decoupling**: 100 nF adjacent to each IC V+ pin.

## Regenerate

```bash
python3 gen_laser_controller.py
kicad-cli sch export netlist laser_controller.kicad_sch -o /tmp/lc.net
python3 check_laser_controller_netlist.py /tmp/lc.net
LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 gen_pcb.py
python3 check_laser_controller_pcb.py laser_controller.kicad_pcb /tmp/lc.net
python3 check_laser_controller_release_gate.py laser_controller.kicad_pcb /tmp/lc.net
python3 check_power_thermal_budget.py --policy bench-uart-usb
python3 check_laser_current_budget.py --policy green-high-vf-10v5
python3 check_laser_controller_release_readiness.py
```

The equivalent local wrapper from the repo root is:

```bash
python3 circuits/run_laser_controller_review.py
```

For release/fabrication, run:

```bash
python3 circuits/run_laser_controller_review.py --release
```

The custom PCB and generated-copper release gates do not pass on the current
board. Placement, routing, GND plane creation/refill, laser-current return vias,
KiCad DRC, and visual return-path review still need to be completed before
fabrication.
The bench/no-RF AP2112 thermal policy passes, and the PLT5 520EB_P
reference laser-current budget passes only for a controlled 10.5 V green-style
supply assumption. `check_laser_controller_release_readiness.py` intentionally
reports the remaining open blockers. KiCad GUI ERC, zone refill, PCB DRC with
schematic parity, AP2112 bring-up temperature measurement, actual laser direct-footprint
MPN review, per-diode laser-current thermal budget, and visual return-path
review still must pass before fabrication. This actual laser direct-footprint MPN review
must verify every selected diode pin table before the diodes are soldered.

## BOM Summary

See `laser_controller_bom_jlcpcb.csv`. Key notes:
- **Power**: USB/external +5V for logic/analog; separate J5 `LASER_V+` for laser anodes.
- **10k resistors**: C844918 (Vishay CRCW060310K0FKEA, live LCSC stock checked 2026-06-28).
- **SFH2201**: C2900216 (Extended, one-time feeder fee).
- **Pin headers J5,J6**: through-hole, hand-soldered.
