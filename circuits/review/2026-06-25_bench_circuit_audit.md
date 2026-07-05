# Bench Laser Controller Circuit Audit

Historical note: this dated snapshot predates the copied access-controller MCU
sheet and current recovered-placement PCB state. Use
`review/generated/laser_controller_review_gate.md`, `docs/source-register.md`,
and the live checker commands for current component counts, PCB routing state,
and release blockers.

Updated: 2026-06-26.

This file records the current audit state for the generated bench laser
controller. It replaces earlier exploratory notes that contained stale routed
copper failures. It is not a production release waiver.

## Gate

Fabrication is still blocked.

The generated schematic, source-register, source-document, passive-derating,
PCB pad/net/route, and project-specific generated-copper checks are repeatable
and mostly passing, but release still needs KiCad ERC, zone refill, KiCad DRC
with schematic parity, and a human return-path/manufacturing review.

Current release blockers are tracked by
`circuits/check_laser_controller_release_readiness.py`.

## Current Proven State

The current review wrapper proves these generated-artifact facts:

| Area | Current evidence |
|---|---|
| Schematic generation | `python3 circuits/gen_laser_controller.py` regenerates the root sheet, 4 TIA sheets, 4 laser sheets, MCU sheet, power/IO sheet, and JLCPCB BOM. |
| Netlist export | `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net` succeeds in this KiCad CLI environment. |
| Netlist assertions | `check_laser_controller_netlist.py` passes 542 assertions across 144 nets. |
| Hierarchy and labels | `check_schematic_hierarchy_labels.py` passes: 10 root sheets, 60 whitelisted root global labels, 62 child hierarchical labels, typed sheet pins, zero child-sheet globals. |
| Source coverage | `check_laser_controller_sources.py` passes: 70 MPN/LCSC tokens, 160 components, 144 exported net-intent mappings, 526 component-pin roles. |
| Source-document evidence | `check_source_documents.py` passes for required reachable sources and local artifacts; secondary/distributor and vendor-CDN risks remain warnings. |
| Passive stress | `check_passive_derating.py` passes for 55 capacitors and 60 resistors/trimmers. |
| PCB generated artifact | `gen_pcb.py` emits a 4-layer staged-placement board with 160 referenced footprints, explicit pad nets, 0 board-level routed segments, 0 vias, and one footprint-internal ESP32 antenna keepout zone. |
| PCB pad/net/route checks | `check_laser_controller_pcb.py` currently fails because footprints are staged outside the Edge.Cuts outline, USB routes are missing, no filled `In1.Cu` GND reference plane exists, and placement-proximity limits are not yet met. |
| Signal/control route state | Signal/control multi-pad nets are not explicitly routed in the current PCB artifact. |
| Release gate | `check_laser_controller_release_gate.py` fails on missing signal/control routing, rail/zone trunks and pours, LASER_V+ anode copper, and high-current GND vias for laser sense returns. |
| KiCad ERC/DRC | Blocked in this shell because KiCad 7.0.11 CLI exposes `sch export` and `pcb export`, not `sch erc` or `pcb drc`. GUI ERC/DRC or a fuller KiCad CLI is required. |

## Datasheet-Backed Component Checks

`check_laser_controller_netlist.py` asserts exact value, footprint, MPN, and
LCSC identity for all generated schematic components. It also asserts
package-sensitive pin functions for the active and polarity-sensitive parts.

| Component group | Datasheet/package decision checked |
|---|---|
| ESP32-S3-WROOM-1 `U9` | Uses the real `Espressif:ESP32-S3-WROOM-1` symbol block from `~/projects/access-controller/circuits/controller/microcontroller.kicad_sch`, with only the footprint-library substitution allowed. |
| ESP32 USB | J1 D-/D+ feed CP2102N through copied-sheet discrete LESD clamps; J2 D-/D+ feed ESP32 GPIO19/module pin 13 and GPIO20/module pin 14 through copied-sheet discrete LESD clamps. |
| ESP32 telemetry/control | `ISENSE1..4` on GPIO4/5/6/7, `MPD1..4` on GPIO2/3/8/9, `PWM1..4` on GPIO10/11/12/16, `CONVST` on GPIO15. |
| ESP32 straps/no-connects | GPIO0/BOOT has a pull-up and J2 access; unused ESP32 pads export only as explicit no-connect single-node nets. |
| OPA380AID `U1..U4` | SOIC-8 pins 1/5/8 are NC, pin 2 is summing input, pin 3 is VBIAS, pin 6 is output, pin 7 is +5V, pin 4 is GND. |
| SFH2201 `D1..D4` | Pin 1 cathode is reverse-biased from +5V through 1k and bypassed; pin 2 anode goes to the OPA380 summing node. |
| TLV9001IDBVR `U5..U8` | Non-U DBV SOT-23-5 pinout: OUT=1, V-=2, IN+=3, IN-=4, V+=5. |
| AO3400A `Q1..Q4` | SOT-23 gate/source/drain pins are asserted; drain goes to `LASER_Nx`, source to the 10 ohm sense node, gate through 1k from TLV9001. |
| AP2112K-3.3 `U11` | SOT-23-5 VIN=1, GND=2, EN=3, NC=4, VOUT=5. Accepted only for bench USB/UART/no-RF continuous load. |
| Copied USB ESD/VBUS support | LESD5D5.0CT1G clamps protect the copied Mini-B data/VBUS paths; 1N5819HW diodes isolate J1/J2 VBUS before `VBUS_5V`. |
| USB Mini-B `J1` | VBUS, D-, D+, ID no-connect, GND, and shield nets are asserted against the intended connector pin order. |
| SS14 `D5/D6` | SMA pin 1 anode receives pre-OR 5V source; pin 2 cathode feeds `+5V`. Exact C2480 source remains an order-time check. |
| Bourns 3224 `RV1..RV4` | Three-terminal trim nets are bounded by source/register checks; final wiper/pin-1 orientation still requires visual PCB signoff. |
| Passive components | BOM identity and steady-state bench derating are checked for every assembled resistor, capacitor, and SMD trimmer MPN. |

## Laser Diode Monitor-PD Feedback

The bench circuit now uses direct through-hole `LD1..LD4` laser-can footprints.
The third laser-can monitor-photodiode pin is used when the selected laser
package polarity supports it. The old laser/MPD harness header is removed, so
the monitor pins are not tied together through a connector.

Direct laser footprint nets:

| Footprint | Nets |
|---|---|
| `LD1` | pin 1 `LASER_N1`; pin 2 `LASER_V+`; pin 3 `MPD_RAW1` |
| `LD2` | pin 1 `LASER_N2`; pin 2 `LASER_V+`; pin 3 `MPD_RAW2` |
| `LD3` | pin 1 `LASER_N3`; pin 2 `LASER_V+`; pin 3 `MPD_RAW3` |
| `LD4` | pin 1 `LASER_V+`; pin 2 no-connect case; pin 3 `LASER_N4` |

Each `MPD_RAWx` net is exactly:

| Raw monitor net | Nodes |
|---|---|
| `MPD_RAW1` | `LD1.3`, `R42.1`, `U12.3` |
| `MPD_RAW2` | `LD2.3`, `R44.1`, `U12.5` |
| `MPD_RAW3` | `LD3.3`, `R46.1`, `U12.10` |
| `MPD_RAW4` | `R48.1`, `U12.12`; spare/open for the current blue diode |

The shared monitor-bias net is:

| Bias net | Nodes |
|---|---|
| `/POWER_IO/MPD_BIAS` | `R42.2`, `R44.2`, `R46.2`, `R48.2`, `U12.2`, `U12.6`, `U12.9`, `U12.13`, `U13.2`, `U13.3`, `C36.2`, `R41.1` |

Each INA output net is exactly:

| Amplified monitor net | Nodes |
|---|---|
| `/POWER_IO/MPD_AMP1` | `U12.1`, `R43.1` |
| `/POWER_IO/MPD_AMP2` | `U12.7`, `R45.1` |
| `/POWER_IO/MPD_AMP3` | `U12.8`, `R47.1` |
| `/POWER_IO/MPD_AMP4` | `U12.14`, `R49.1` |

Each filtered monitor ADC net is exactly:

| ADC net | Nodes |
|---|---|
| `MPD1` | `R43.2`, `C37.1`, `U9.38` GPIO2/ADC1_CH1 |
| `MPD2` | `R45.2`, `C38.1`, `U9.15` GPIO3/ADC1_CH2 |
| `MPD3` | `R47.2`, `C39.1`, `U9.12` GPIO8/ADC1_CH7 |
| `MPD4` | `R49.2`, `C40.1`, `U9.17` GPIO9/ADC1_CH8 |

The front end is a high-side monitor-current sense circuit:
`MPD_RAWx -> 750R -> MPD_BIAS`; INA4180A1 gain 20 drives
`MPD_AMPx -> 1k/100 nF -> ESP32 ADC1`. LM4040C50 holds
`LASER_V+ - MPD_BIAS` near 5 V through a 2.49 k sink.

This is polarity-compatible with the selected D7805I, D6505I, and
PLT5 520EB_P monitor-photodiode pinouts when the direct `LDx` footprint is
soldered from each datasheet:
laser cathode to `LASER_Nx`, common/anode side to `LASER_V+`, and monitor anode
to `MPD_RAWx`. For PLT5 520EB_P at `LASER_V+ = 10.5 V`, typical 150 uA monitor
current produces about 2.25 V at the ESP32 ADC and about 4.89 V monitor-PD
reverse bias. PLT5 450GB has no monitor photodiode, so `MPD_RAW4` remains a
spare/open monitor-front-end input and the case pin is not wired to it. Actual
reverse-bias limit, current limit, optical safety limit, and direct-footprint soldering
remain release blockers.

## PCB Route Evidence

The PCB checker verifies every generated routed segment against layer, width,
clearance, endpoint, via, and local-length policies. Current recovered-placement
PCB evidence:

| Route group | Evidence |
|---|---|
| USB | J1/J2 data nets are present in schematic/netlist, but PCB USB sections are currently unrouted. |
| Laser cathodes | `LASER_N1..4` connect `LDx` cathodes to AO3400A drains in the schematic/netlist, but PCB current-path copper is currently unrouted. |
| Laser anode rail | `LASER_V+` connects J5, LD1-LD4, LM4040, and the MPD bias capacitor in the schematic/netlist, but final rail copper/zone review is still open. |
| Laser sense returns | The 10 ohm sense returns are netlisted, but high-current GND vias/routes are not present in the current recovered-placement PCB. |
| TIA sensitive nets | Summing-node, photodiode-bias, feedback, VBIAS, and local decoupling nets pass schematic/source checks; PCB placement and local-route proximity still need final layout signoff. |
| Monitor PD nets | `MPD_RAWx`, `MPD_BIAS`, INA4180, LM4040, sense, filter, and isolation parts pass schematic/source checks; direct laser-to-monitor-front-end PCB proximity still needs placement/routing. |
| ESP32 antenna | Footprint-internal antenna keepout is present with the ESP32 footprint; final antenna edge placement and copper/part clearance still need visual DRC review. |
| Pending rails | `VBUS_5V`, `+5V`, `+3V3`, `LASER_V+`, and `GND` remain route/zone pending and need KiCad refill/DRC plus visual return-path signoff. |

The current generated-board report is
`circuits/review/generated/laser_controller_review_gate.md`; the full generated
inventory is `circuits/review/2026-06-25_full_net_pin_inventory.md`.

## Remaining Release Blockers

These are not optional:

1. Run KiCad ERC on the regenerated schematic and document any waiver.
2. Refill zones and run KiCad PCB DRC with schematic parity.
3. Review `+5V` and `GND` rail/zone copper visually after refill.
4. Inspect return paths so laser current does not share the TIA summing-node return path.
5. Selected laser MPN/can pin-code/direct `LDx` footprint mapping is closed by
   `circuits/review/signoff/2026-07-04-direct-laser-mpn-footprint-signoff.md`;
   inspect received diode orientation before soldering.
6. Run per-diode laser current and thermal budgets for the chosen `LASER_V+`, current, and duty cycle.
7. Measure AP2112 package temperature and +3V3 current during bring-up, or replace the regulator before sustained RF.
8. Define external 5V current limiting/protection or add board protection.
9. Verify the official current Wuerth 65100516121 drawing before fabrication.
10. Confirm exact SS14 C2480 manufacturer/source and polarity at order time.
11. Visually verify Bourns 3224 wiper orientation in Pcbnew.
12. Lock production AVL/derating and final fab/assembly class.
13. Confirm on-board AD7606 range, serial timing, oversampling straps, and firmware assumptions.

## Commands

Run the normal local gate:

```bash
python3 circuits/run_laser_controller_review.py
```

Run release mode when a board-order decision is being made:

```bash
python3 circuits/run_laser_controller_review.py --release
```

Release mode must remain nonzero until every blocker above is closed or
explicitly waived with owner/date/risk.
