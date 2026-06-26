# Bench Laser Controller Circuit Audit

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
| Netlist assertions | `check_laser_controller_netlist.py` passes 352 assertions across 109 nets. |
| Hierarchy and labels | `check_schematic_hierarchy_labels.py` passes: 10 root sheets, 44 whitelisted root global labels, 44 child hierarchical labels, typed sheet pins, zero child-sheet globals. |
| Source coverage | `check_laser_controller_sources.py` passes: 41 MPN/LCSC tokens, 117 components, 109 exported net-intent mappings, 343 component-pin roles. |
| Source-document evidence | `check_source_documents.py` passes for required reachable sources and local artifacts; secondary/distributor and vendor-CDN risks remain warnings. |
| Passive stress | `check_passive_derating.py` passes for 38 capacitors and 52 resistors/trimmers. |
| PCB generated artifact | `gen_pcb.py` in strict route mode emits a 4-layer board with 117 referenced footprints. |
| PCB pad/net/route checks | `check_laser_controller_pcb.py` passes: 311 pad-net assignments, 77 named nets, 1260 routed segments, 141 vias, 109/109 connected critical local route links. |
| Signal/control route state | No signal/control multi-pad nets are split in the current custom PCB gate. |
| Release gate | `check_laser_controller_release_gate.py` fails closed only on rail/zone signoff for `+5V` and `GND`. |
| KiCad ERC/DRC | Blocked in this shell because KiCad 7.0.11 CLI exposes `sch export` and `pcb export`, not `sch erc` or `pcb drc`. GUI ERC/DRC or a fuller KiCad CLI is required. |

## Datasheet-Backed Component Checks

`check_laser_controller_netlist.py` asserts exact value, footprint, MPN, and
LCSC identity for all generated schematic components. It also asserts
package-sensitive pin functions for the active and polarity-sensitive parts.

| Component group | Datasheet/package decision checked |
|---|---|
| ESP32-S3-WROOM-1 `U9` | Uses the real `Espressif:ESP32-S3-WROOM-1` symbol block from `~/projects/access-controller/circuits/controller/microcontroller.kicad_sch`, with only the footprint-library substitution allowed. |
| ESP32 native USB | `USB_DM` to GPIO19/module pin 13 and `USB_DP` to GPIO20/module pin 14 through USBLC6 and 22 ohm series resistors. |
| ESP32 telemetry/control | `ISENSE1..4` on GPIO4/5/6/7, `MPD1..4` on GPIO2/1/8/9, `PWM1..4` on GPIO16/38/13/14, `CONVST` on GPIO17. |
| ESP32 straps/no-connects | GPIO0/BOOT has a pull-up and J2 access; unused ESP32 pads export only as explicit no-connect single-node nets. |
| OPA380AID `U1..U4` | SOIC-8 pins 1/5/8 are NC, pin 2 is summing input, pin 3 is VBIAS, pin 6 is output, pin 7 is +5V, pin 4 is GND. |
| SFH2201 `D1..D4` | Pin 1 cathode is reverse-biased from +5V through 1k and bypassed; pin 2 anode goes to the OPA380 summing node. |
| TLV9001IDBVR `U5..U8` | Non-U DBV SOT-23-5 pinout: OUT=1, V-=2, IN+=3, IN-=4, V+=5. |
| AO3400A `Q1..Q4` | SOT-23 gate/source/drain pins are asserted; drain goes to `LASER_Nx`, source to the 10 ohm sense node, gate through 1k from TLV9001. |
| AP2112K-3.3 `U11` | SOT-23-5 VIN=1, GND=2, EN=3, NC=4, VOUT=5. Accepted only for bench USB/UART/no-RF continuous load. |
| USBLC6 `U10` | SOT-23-6 IO1 pair protects D-, IO2 pair protects D+, pin 5 is VBUS clamp reference, pin 2 is GND. |
| USB Mini-B `J1` | VBUS, D-, D+, ID no-connect, GND, and shield nets are asserted against the intended connector pin order. |
| SS14 `D5/D6` | SMA pin 1 anode receives pre-OR 5V source; pin 2 cathode feeds `+5V`. Exact C2480 source remains an order-time check. |
| Bourns 3224 `RV1..RV4` | Three-terminal trim nets are bounded by source/register checks; final wiper/pin-1 orientation still requires visual PCB signoff. |
| Passive components | BOM identity and steady-state bench derating are checked for every assembled resistor, capacitor, and SMD trimmer MPN. |

## Laser Diode Monitor-PD Feedback

The bench circuit now uses the third laser-can monitor-photodiode pin when the
selected laser package polarity supports it. The monitor pins are not tied
together.

J4 pinout:

| J4 pin | Net |
|---:|---|
| 1 | `LASER_N1` |
| 2 | `MPD_RAW1` |
| 3 | `LASER_N2` |
| 4 | `MPD_RAW2` |
| 5 | `LASER_N3` |
| 6 | `MPD_RAW3` |
| 7 | `LASER_N4` |
| 8 | `MPD_RAW4` |
| 9 | `LASER_V+` |
| 10 | `GND` |

Each `MPD_RAWx` net is exactly:

| Raw monitor net | Nodes |
|---|---|
| `/POWER_IO/MPD_RAW1` | `J4.2`, `R42.1`, `U12.3` |
| `/POWER_IO/MPD_RAW2` | `J4.4`, `R44.1`, `U12.5` |
| `/POWER_IO/MPD_RAW3` | `J4.6`, `R46.1`, `U12.10` |
| `/POWER_IO/MPD_RAW4` | `J4.8`, `R48.1`, `U12.12` |

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
| `MPD2` | `R45.2`, `C38.1`, `U9.39` GPIO1/ADC1_CH0 |
| `MPD3` | `R47.2`, `C39.1`, `U9.12` GPIO8/ADC1_CH7 |
| `MPD4` | `R49.2`, `C40.1`, `U9.17` GPIO9/ADC1_CH8 |

The front end is a high-side monitor-current sense circuit:
`MPD_RAWx -> 750R -> MPD_BIAS`; INA4180A1 gain 20 drives
`MPD_AMPx -> 1k/100 nF -> ESP32 ADC1`. LM4040C50 holds
`LASER_V+ - MPD_BIAS` near 5 V through a 2.49 k sink.

This is polarity-compatible with PLT5-style and Thorlabs A-code common-anode /
monitor-PD-cathode laser cans. For PLT5 520B at `LASER_V+ = 10.5 V`, typical
150 uA monitor current produces about 2.25 V at the ESP32 ADC and about 4.89 V
monitor-PD reverse bias. It does not directly support the canonical `L785P090`
C-code monitor topology without an adapter or different monitor front end, and
`L450G2` has no monitor photodiode. Actual MPN, reverse-bias limit, and harness
pinout remain release blockers.

## PCB Route Evidence

The PCB checker verifies every generated routed segment against layer, width,
clearance, endpoint, via, and local-length policies. Current key route evidence:

| Route group | Evidence |
|---|---|
| USB | D- total 22.26 mm, D+ total 24.05 mm, 1.79 mm skew, F.Cu only, 0.25 mm, zero vias. |
| Laser cathodes | `LASER_N1..4` are explicitly routed with 0.60 mm current-path copper and pass the generated width/length gate. |
| Laser anode rail | `LASER_V+` is explicitly routed with 0.80 mm current-path copper and passes the generated width/length gate. |
| Laser sense returns | Each 10 ohm 2512 sense resistor ground pad reaches a distinct 0.60/0.30 mm high-current GND via within the project limit. |
| TIA sensitive nets | Summing-node, photodiode-bias, feedback, VBIAS, and local decoupling routes pass placement and sensitive local-route length checks. |
| Monitor PD nets | `MPD_RAWx`, `MPD_BIAS`, INA4180, LM4040, sense, filter, and isolation parts are placed as the monitor front end and pass the schematic-level source/net checks. |
| ESP32 antenna | Keepout intrusions are checked against the generated board artifact. |
| Pending rails | `+5V` and `GND` remain rail/zone pending and need KiCad refill/DRC plus visual return-path signoff. The laser-driver TLV9001 inter-channel `+5V` trunk is routed, but the bulk `+5V` bridge into that trunk is still missing. |

The current generated-board report is
`circuits/review/generated/laser_controller_review_gate.md`; the full generated
inventory is `circuits/review/2026-06-25_full_net_pin_inventory.md`.

## Remaining Release Blockers

These are not optional:

1. Run KiCad ERC on the regenerated schematic and document any waiver.
2. Refill zones and run KiCad PCB DRC with schematic parity.
3. Review `+5V` and `GND` rail/zone copper visually after refill.
4. Inspect return paths so laser current does not share the TIA summing-node return path.
5. Lock actual laser MPNs, can pin code, common/case node, and J4 harness wiring.
6. Run per-diode laser current and thermal budgets for the chosen `LASER_V+`, current, and duty cycle.
7. Measure AP2112 package temperature and +3V3 current during bring-up, or replace the regulator before sustained RF.
8. Define external 5V current limiting/protection or add board protection.
9. Verify the official current Wuerth 65100516121 drawing before fabrication.
10. Confirm exact SS14 C2480 manufacturer/source and polarity at order time.
11. Visually verify Bourns 3224 wiper orientation in Pcbnew.
12. Lock production AVL/derating and final fab/assembly class.
13. Confirm external AD7606 range/interface assumptions against the actual acquisition board.

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
