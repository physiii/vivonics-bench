# Laser Controller Review Gate

Generated: 2026-06-28T20:32:57+00:00

This is a generated local audit artifact. It proves only the checks listed below.
Fabrication remains blocked if any row is `FAIL` or `BLOCKED`.

Overall release status: BLOCKED

| Status | Step | Return | Command |
|---|---|---:|---|
| PASS | Python compile | 0 | `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_pcb_staging.py circuits/check_laser_controller_release_gate.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_schematic_presentation.py circuits/check_power_thermal_budget.py circuits/check_laser_current_budget.py circuits/check_laser_monitor_pd_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py` |
| PASS | Generate schematic/BOM | 0 | `python3 circuits/gen_laser_controller.py` |
| PASS | Export schematic netlist | 0 | `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net` |
| PASS | Netlist assertions | 0 | `python3 circuits/check_laser_controller_netlist.py /tmp/lc.net` |
| PASS | Schematic hierarchy/label assertions | 0 | `python3 circuits/check_schematic_hierarchy_labels.py circuits/laser_controller.kicad_sch` |
| PASS | Schematic presentation assertions | 0 | `python3 circuits/check_schematic_presentation.py circuits/laser_controller.kicad_sch` |
| PASS | Source-register assertions | 0 | `python3 circuits/check_laser_controller_sources.py /tmp/lc.net` |
| PASS | Part-note completeness assertions | 0 | `python3 circuits/check_part_notes_completeness.py` |
| PASS | Source-document evidence | 0 | `python3 circuits/check_source_documents.py` |
| PASS | Passive derating assertions | 0 | `python3 circuits/check_passive_derating.py` |
| PASS | Generate PCB | 0 | `env LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 circuits/gen_pcb.py` |
| PASS | PCB staging assertions | 0 | `python3 circuits/check_pcb_staging.py circuits/laser_controller.kicad_pcb /tmp/lc.net` |
| BLOCKED | Generated-copper release gate | 1 | `python3 circuits/check_laser_controller_release_gate.py circuits/laser_controller.kicad_pcb /tmp/lc.net` |
| PASS | AP2112 bench thermal policy | 0 | `python3 circuits/check_power_thermal_budget.py --policy bench-uart-usb` |
| PASS | AP2112 sustained Wi-Fi expected fail | 1 | `python3 circuits/check_power_thermal_budget.py --policy wifi-tx-100-duty` |
| PASS | Green high-Vf laser-current thermal reference | 0 | `python3 circuits/check_laser_current_budget.py --policy green-high-vf-10v5` |
| PASS | PLT5 520EB_P monitor-PD high-side bias policy | 0 | `python3 circuits/check_laser_monitor_pd_budget.py --policy plt5-520ebp-green-10v5` |
| PASS | MPD ADC-scale-only policy | 0 | `python3 circuits/check_laser_monitor_pd_budget.py --policy adc-scale-only-10v5` |
| PASS | Green high-Vf 12V laser-current expected fail | 1 | `python3 circuits/check_laser_current_budget.py --policy green-high-vf-12v` |
| PASS | Low-Vf diode on green rail expected fail | 1 | `python3 circuits/check_laser_current_budget.py --policy low-vf-diode-on-10v5` |
| BLOCKED | Open fabrication/release blockers | 2 | `python3 circuits/check_laser_controller_release_readiness.py` |
| PASS | Regenerate audit inventory | 0 | `python3 circuits/generate_laser_controller_audit_tables.py /tmp/lc.net circuits/laser_controller.kicad_pcb circuits/review/2026-06-25_full_net_pin_inventory.md` |
| PASS | Export placement | 0 | `kicad-cli pcb export pos circuits/laser_controller.kicad_pcb -o /tmp/lc_pos.csv` |
| BLOCKED | KiCad ERC availability | 1 | `kicad-cli sch erc circuits/laser_controller.kicad_sch -o /tmp/lc_erc.rpt` |
| BLOCKED | KiCad DRC availability | 1 | `kicad-cli pcb drc circuits/laser_controller.kicad_pcb -o /tmp/lc_drc.rpt` |
| PASS | Git diff whitespace | 0 | `git diff --check` |
| PASS | Trailing whitespace scan | 1 | `rg -n [ \t]+$ circuits docs -g *.md -g *.py -g *.kicad_sch -g *.kicad_pcb` |

## PASS: Python compile

Command: `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_pcb_staging.py circuits/check_laser_controller_release_gate.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_schematic_presentation.py circuits/check_power_thermal_budget.py circuits/check_laser_current_budget.py circuits/check_laser_monitor_pd_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py`

## PASS: Generate schematic/BOM

Command: `python3 circuits/gen_laser_controller.py`

```text
wrote tia_ir.kicad_sch (34648 bytes, 547 lines)
  wrote tia_red.kicad_sch (34649 bytes, 547 lines)
  wrote tia_green.kicad_sch (34663 bytes, 547 lines)
  wrote tia_blue.kicad_sch (34666 bytes, 547 lines)
  wrote laser_ir.kicad_sch (35184 bytes, 538 lines)
  wrote laser_red.kicad_sch (35185 bytes, 538 lines)
  wrote laser_green.kicad_sch (35180 bytes, 538 lines)
  wrote laser_blue.kicad_sch (34871 bytes, 536 lines)
  wrote power_io.kicad_sch (96259 bytes, 1476 lines)
  wrote laser_controller.kicad_sch (27388 bytes, 223 lines)
  wrote laser_controller_bom_jlcpcb.csv
```

## PASS: Export schematic netlist

Command: `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net`

## PASS: Netlist assertions

Command: `python3 circuits/check_laser_controller_netlist.py /tmp/lc.net`

```text
PASS 457 netlist assertions across 139 nets
```

## PASS: Schematic hierarchy/label assertions

Command: `python3 circuits/check_schematic_hierarchy_labels.py circuits/laser_controller.kicad_sch`

```text
PASS schematic hierarchy/label guardrails: 10 root sheets, 52 whitelisted root global labels, 54 child hierarchical labels, typed sheet pins, zero child-sheet global labels, and checked schematic annotation designators
```

## PASS: Schematic presentation assertions

Command: `python3 circuits/check_schematic_presentation.py circuits/laser_controller.kicad_sch`

```text
PASS schematic presentation guardrails: no generated wire segments enter symbol bodies, no loose wire endpoints, labels clear symbols/text, symbol pin anchors/strokes touch their glyphs, and generated connection objects stay on the 50 mil grid; imported source sheets are checked for non-diagonal wires
```

## PASS: Source-register assertions

Command: `python3 circuits/check_laser_controller_sources.py /tmp/lc.net`

```text
PASS source-register coverage for 68 MPN/LCSC tokens across 151 components, intent coverage for 139 exported nets, 452 component-pin intent roles, and 4 documentation designator guard files
```

## PASS: Part-note completeness assertions

Command: `python3 circuits/check_part_notes_completeness.py`

```text
PASS part-note completeness: 15 notes, 133 required phrases, 2 stale-phrase guards
```

## PASS: Source-document evidence

Command: `python3 circuits/check_source_documents.py`

```text
WARN ST USBLC6-2 official datasheet: not reachable; Primary source, but ST/Akamai times out from this shell environment; manual release-time verification remains required. [GET failed: The read operation timed out; HEAD failed: The read operation timed out]
WARN Alpha & Omega AO3400A datasheet: reachable; Primary source, but AOS currently returns a bot/noindex HTML page to this shell environment; manual release-time verification remains required. [HEAD HTTP 200, type=application/pdf, length=317848]
WARN JLCPCB via-design article: reachable; Advisory article only; JLCPCB quote capability page wins. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN Vishay SS12-SS16 family datasheet: reachable; Family reference only; exact LCSC C2480 manufacturer must be confirmed at order. [HEAD HTTP 200, type=application/pdf, length=1174123]
WARN LCSC C2480 SS14 order page: reachable; Distributor/order source, not a replacement for final order-time manufacturer confirmation. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN Wuerth Mini/Micro USB family page: reachable; Family/product page; final 65100516121 drawing still needs release verification. [HEAD HTTP 200, type=text/html; charset=UTF-8, length=1]
WARN Farnell mirror of Wuerth 65100516121 drawing: reachable; Distributor mirror used because the exact official Wuerth drawing URL was not directly reachable. [HEAD HTTP 200, type=application/pdf, length=276116]
WARN LCSC C2907002 FRC0603F1001TS 1k resistor page: reachable; Distributor/order source for active 1k 0603 passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C22984 30k resistor page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LCSC C844918 CRCW060310K0FKEA 10k resistor page: reachable; Distributor/order source for active 10k 0603 passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C5123624 10 ohm 2512 sense resistor page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
PASS source-document evidence: 18 required online sources, 13 required local artifacts, and 11 secondary/open-risk sources reviewed
```

## PASS: Passive derating assertions

Command: `python3 circuits/check_passive_derating.py`

```text
PASS passive derating: checked 45 capacitors and 60 resistors/trimmers
  max capacitor voltage utilization: 31.6% at C36 (100nF MPD bias)
  max resistor power utilization: 40.0% at R57 (1K)
  max resistor voltage utilization: 10.0% at R60 (10K)
```

## PASS: Generate PCB

Command: `env LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 circuits/gen_pcb.py`

```text
wrote laser_controller.kicad_pcb  (162 blocks, 151 ref instances)
  refs: 151 unique
```

## PASS: PCB staging assertions

Command: `python3 circuits/check_pcb_staging.py circuits/laser_controller.kicad_pcb /tmp/lc.net`

```text
PASS PCB staging: 151 physical footprints loaded, 0 empty-footprint symbols skipped, 0 board-level segments/vias/zones, 1 footprint-internal zone/keepout block(s), 151 non-overlapping staged bboxes outside the 90 x 50 mm outline; sections TIA_IR:11, TIA_RED:11, TIA_GREEN:11, TIA_BLUE:11, LASER_IR:11, LASER_RED:11, LASER_GREEN:11, LASER_BLUE:11, MCU_ESP32-S3:35, POWER_IO:28
```

## BLOCKED: Generated-copper release gate

Command: `python3 circuits/check_laser_controller_release_gate.py circuits/laser_controller.kicad_pcb /tmp/lc.net`

The current PCB artifact is intentionally placement-only: components are staged outside the outline with pad nets, but routing, zones, KiCad refill, DRC, and return-path review remain future fabrication work.

```text
FAIL fabrication release gate
  signal/control multi-pad nets are not explicitly routed: /LASER_BLUE/FB: U8.4 | Q4.2 | R33.1 | R34.1 | C28.1; /LASER_BLUE/LOUT: U8.1 | R32.1 | C28.2; /LASER_GREEN/FB: U7.4 | Q3.2 | R28.1 | R29.1 | C25.1; /LASER_GREEN/LOUT: U7.1 | R27.1 | C25.2; /LASER_IR/FB: U5.4 | Q1.2 | R18.1 | R19.1 | C19.1; /LASER_IR/LOUT: U5.1 | R17.1 | C19.2; /LASER_RED/FB: U6.4 | Q2.2 | R23.1 | R24.1 | C22.1; /LASER_RED/LOUT: U6.1 | R22.1 | C22.2; /MCU_ESP32-S3/D+: U10.4 | J1.3 | D8.2; /MCU_ESP32-S3/D-: U10.5 | J1.2 | D7.2; /MCU_ESP32-S3/DTR: Q6.3 | R50.1 | U10.28; /MCU_ESP32-S3/EN: U9.3 | C44.1 | R54.2 | SW1.1 | SW1.1 | Q5.3; /MCU_ESP32-S3/FACT: U9.39 | SW3.1 | SW3.1 | R52.2; /MCU_ESP32-S3/IO13: U9.21 | R60.1; /MCU_ESP32-S3/IO14: U9.22 | R59.2; /MCU_ESP32-S3/IO19: U9.13 | J2.2 | D12.2; /MCU_ESP32-S3/IO20: U9.14 | J2.3 | D11.2; /MCU_ESP32-S3/IO43: U9.37 | U10.25; /MCU_ESP32-S3/IO44: U9.36 | U10.26; /MCU_ESP32-S3/PROG: U9.27 | SW2.1 | SW2.1 | Q6.2 | R53.2 | C46.1
  rail/zone multi-pad nets still require pour/trunk routing and KiCad refill/DRC: +3V3, +5V, /POWER_IO/EXT5V, GND, LASER_V+, VBUS_5V
    +3V3 split into 16 copper groups: group 1 (1 pads): U9.2 | group 2 (1 pads): C43.1 | group 3 (1 pads): R54.1 | group 4 (1 pads): R59.1 | group 5 (1 pads): R60.2 | group 6 (1 pads): R52.1 | group 7 (1 pads): R53.1 | group 8 (1 pads): U10.6 | group 9 (1 pads): U10.7 | group 10 (1 pads): R57.1 | group 11 (1 pads): C47.1 | group 12 (1 pads): U11.5 | group 13 (1 pads): C49.1 | group 14 (1 pads): C50.1 | group 15 (1 pads): U12.4 | group 16 (1 pads): C35.1
    +5V split into 30 copper groups: group 1 (1 pads): R2.1 | group 2 (1 pads): U1.7 | group 3 (1 pads): C2.1 | group 4 (1 pads): R4.1 | group 5 (1 pads): R6.1 | group 6 (1 pads): U2.7 | group 7 (1 pads): C6.1 | group 8 (1 pads): R8.1 | group 9 (1 pads): R10.1 | group 10 (1 pads): U3.7 | group 11 (1 pads): C10.1 | group 12 (1 pads): R12.1 | group 13 (1 pads): R14.1 | group 14 (1 pads): U4.7 | group 15 (1 pads): C14.1 | group 16 (1 pads): R16.1 | group 17 (1 pads): U5.5 | group 18 (1 pads): C17.1 | group 19 (1 pads): U6.5 | group 20 (1 pads): C20.1 | group 21 (1 pads): U7.5 | group 22 (1 pads): C23.1 | group 23 (1 pads): U8.5 | group 24 (1 pads): C26.1 | group 25 (1 pads): D5.2 | group 26 (1 pads): D6.2 | group 27 (1 pads): C34.1 | group 28 (1 pads): U11.1 | group 29 (1 pads): U11.3 | group 30 (1 pads): C48.1
    /POWER_IO/EXT5V split into 2 copper groups: group 1 (1 pads): D6.1 | group 2 (1 pads): J6.1
    GND split into 92 copper groups: group 1 (2 pads): U9.41, U9.41 | group 2 (2 pads): U9.41, U9.41 | group 3 (1 pads): C3.2 | group 4 (1 pads): U1.4 | group 5 (1 pads): C2.2 | group 6 (1 pads): RV1.3 | group 7 (1 pads): C4.2 | group 8 (1 pads): C7.2 | group 9 (1 pads): U2.4 | group 10 (1 pads): C6.2 | group 11 (1 pads): RV2.3 | group 12 (1 pads): C8.2 | group 13 (1 pads): C11.2 | group 14 (1 pads): U3.4 | group 15 (1 pads): C10.2 | group 16 (1 pads): RV3.3 | group 17 (1 pads): C12.2 | group 18 (1 pads): C15.2 | group 19 (1 pads): U4.4 | group 20 (1 pads): C14.2 | group 21 (1 pads): RV4.3 | group 22 (1 pads): C16.2 | group 23 (1 pads): U5.2 | group 24 (1 pads): R18.2 | group 25 (1 pads): C17.2 | group 26 (1 pads): R21.2 | group 27 (1 pads): C18.2 | group 28 (1 pads): U6.2 | group 29 (1 pads): R23.2 | group 30 (1 pads): C20.2 | group 31 (1 pads): R26.2 | group 32 (1 pads): C21.2 | group 33 (1 pads): U7.2 | group 34 (1 pads): R28.2 | group 35 (1 pads): C23.2 | group 36 (1 pads): R31.2 | group 37 (1 pads): C24.2 | group 38 (1 pads): U8.2 | group 39 (1 pads): R33.2 | group 40 (1 pads): C26.2 | group 41 (1 pads): R36.2 | group 42 (1 pads): C27.2 | group 43 (1 pads): U9.1 | group 44 (1 pads): U9.40 | group 45 (1 pads): U9.41 | group 46 (1 pads): U9.41 | group 47 (1 pads): U9.41 | group 48 (1 pads): U9.41 | group 49 (1 pads): U9.41 | group 50 (1 pads): U9.41 | group 51 (1 pads): U9.41 | group 52 (1 pads): C43.2 | group 53 (1 pads): C41.2 | group 54 (1 pads): C42.2 | group 55 (1 pads): C44.2 | group 56 (1 pads): SW1.2 | group 57 (1 pads): SW1.2 | group 58 (1 pads): SW2.2 | group 59 (1 pads): SW2.2 | group 60 (1 pads): SW3.2 | group 61 (1 pads): SW3.2 | group 62 (1 pads): R58.2 | group 63 (1 pads): U10.3 | group 64 (1 pads): U10.29 | group 65 (1 pads): J1.5 | group 66 (1 pads): D7.1 | group 67 (1 pads): D8.1 | group 68 (1 pads): R56.1 | group 69 (1 pads): C45.2 | group 70 (1 pads): C46.2 | group 71 (1 pads): C47.2 | group 72 (1 pads): J2.5 | group 73 (1 pads): D9.1 | group 74 (1 pads): D11.1 | group 75 (1 pads): D12.1 | group 76 (1 pads): D14.1 | group 77 (1 pads): J6.2 | group 78 (1 pads): J5.2 | group 79 (1 pads): C34.2 | group 80 (1 pads): U11.2 | group 81 (1 pads): C48.2 | group 82 (1 pads): C49.2 | group 83 (1 pads): C50.2 | group 84 (1 pads): J3.6 | group 85 (1 pads): J4.10 | group 86 (1 pads): U12.11 | group 87 (1 pads): C35.2 | group 88 (1 pads): R41.2 | group 89 (1 pads): C37.2 | group 90 (1 pads): C38.2 | group 91 (1 pads): C39.2 | group 92 (1 pads): C40.2
    LASER_V+ split into 8 copper groups: group 1 (1 pads): LD1.2 | group 2 (1 pads): LD2.2 | group 3 (1 pads): LD3.2 | group 4 (1 pads): LD4.1 | group 5 (1 pads): J5.1 | group 6 (1 pads): J4.9 | group 7 (1 pads): U13.1 | group 8 (1 pads): C36.1
    VBUS_5V split into 8 copper groups: group 1 (1 pads): C41.1 | group 2 (1 pads): C42.1 | group 3 (1 pads): R55.2 | group 4 (1 pads): D9.2 | group 5 (1 pads): D10.1 | group 6 (1 pads): D13.1 | group 7 (1 pads): D14.2 | group 8 (1 pads): D5.1
  LASER_V+: no routed laser-anode supply copper found
  laser sense returns: only 0 high-current GND vias, expected at least 4
  LASER_IR sense resistor R18.2 lacks a routed high-current GND via within 6.00mm; nearest routed path unrouted
  LASER_RED sense resistor R23.2 lacks a routed high-current GND via within 6.00mm; nearest routed path unrouted
  LASER_GREEN sense resistor R28.2 lacks a routed high-current GND via within 6.00mm; nearest routed path unrouted
  LASER_BLUE sense resistor R33.2 lacks a routed high-current GND via within 6.00mm; nearest routed path unrouted
  laser sense returns cannot be assigned to distinct high-current GND vias within 6.00mm
  This does not mean the audit checker failed; it means the board still has known release blockers.
```

## PASS: AP2112 bench thermal policy

Command: `python3 circuits/check_power_thermal_budget.py --policy bench-uart-usb`

```text
AP2112 thermal policy: bench-uart-usb
  Bench policy: RF disabled, USB/UART control, ESP32 active current plus reset/boot pulls kept below 120 mA continuous at 85 degC.
  constants: Vin=5.00V, Vout=3.30V, Iq(max)=80uA, thetaJA=184degC/W
  load=120.0mA, ambient=85.0degC, dissipation=0.204W, rise=37.6degC, Tj=122.6degC
  target Tj=125.0degC, margin=2.4degC, max continuous current at this ambient=127.6mA
PASS AP2112 thermal policy: acceptable for the checked bench/no-RF continuous-current assumption. Sustained Wi-Fi/BLE remains a separate fail case.
```

## PASS: AP2112 sustained Wi-Fi expected fail

Command: `python3 circuits/check_power_thermal_budget.py --policy wifi-tx-100-duty`

```text
AP2112 thermal policy: wifi-tx-100-duty
  Espressif ESP32-S3-WROOM-1 Wi-Fi 802.11b 1 Mbps TX current at 100 percent duty cycle, 20.5 dBm.
  constants: Vin=5.00V, Vout=3.30V, Iq(max)=80uA, thetaJA=184degC/W
  load=355.0mA, ambient=25.0degC, dissipation=0.604W, rise=111.1degC, Tj=136.1degC
  target Tj=125.0degC, margin=-11.1degC, max continuous current at this ambient=319.5mA
FAIL AP2112 thermal policy: this 3V3 load needs a buck regulator, larger thermal package, lower ambient/current, or measured duty-cycle proof.
```

## PASS: Green high-Vf laser-current thermal reference

Command: `python3 circuits/check_laser_current_budget.py --policy green-high-vf-10v5`

```text
Laser current-loop policy: green-high-vf-10v5
  High-forward-voltage green reference using 7.0 V diode headroom and a 10.5 V laser rail. This is a thermal policy reference, not an approval to drive the selected Digikey-cart lasers at the 247.5 mA hardware command clamp.
  command clamp: 3.30V * 30k/(10k+30k) / 10.0ohm = 247.5mA
  sense resistor: drop=2.475V, power=0.613W, rating=2.0W
  laser rail=10.50V, diode Vf(max)=7.00V, AO3400A Vds=1.02V, power=0.254W
  at ambient=85.0degC and target Tj=125.0degC, AO3400A continuous power budget=0.320W
  estimated safe laser rail window at this diode Vf/current: 9.97V to 10.77V
PASS laser current-loop policy for this diode/supply assumption. Actual laser MPN and harness pinout still require release review.
```

## PASS: PLT5 520EB_P monitor-PD high-side bias policy

Command: `python3 circuits/check_laser_monitor_pd_budget.py --policy plt5-520ebp-green-10v5`

```text
Monitor-PD policy: plt5-520ebp-green-10v5
  PLT5 520EB_P monitor-current reference case. The datasheet monitor current is specified at VRPD=5V and is not guaranteed as an accurate absolute power measurement. The bench circuit uses a high-side INA4180 sense path and LM4040-derived MPD_BIAS node. PLT5 450GB has no monitor photodiode, so MPD_RAW4 is only a spare/open front-end input.
  front end: MPD_RAWx -> 750 ohm sense -> MPD_BIAS; INA4180 gain=20; 1k/100nF ADC-side RC
  typical monitor current=150uA -> sense=0.112V, ADC=2.25V, RC tau=0.10ms
  LASER_V+=10.50V, MPD_BIAS=5.50V -> monitor-PD reverse bias typ=4.89V, dark/off=5.00V
  LM4040 current: no-MPD=2.21mA, 4x typ MPD=1.61mA; ADC linear monitor-current limit about 218uA
PASS monitor-PD policy for this scope. This does not replace per-laser datasheet pinout, reverse-bias, optical safety, and calibration review.
```

## PASS: MPD ADC-scale-only policy

Command: `python3 circuits/check_laser_monitor_pd_budget.py --policy adc-scale-only-10v5`

```text
Monitor-PD policy: adc-scale-only-10v5
  ADC headroom check only for the high-side monitor front end. This does not approve any real laser MPN without its own pinout and reverse-bias review.
  front end: MPD_RAWx -> 750 ohm sense -> MPD_BIAS; INA4180 gain=20; 1k/100nF ADC-side RC
  typical monitor current=150uA -> sense=0.112V, ADC=2.25V, RC tau=0.10ms
  LASER_V+=10.50V, MPD_BIAS=5.50V -> monitor-PD reverse bias typ=4.89V, dark/off=5.00V
  LM4040 current: no-MPD=2.21mA, 4x typ MPD=1.61mA; ADC linear monitor-current limit about 218uA
PASS monitor-PD policy for this scope. This does not replace per-laser datasheet pinout, reverse-bias, optical safety, and calibration review.
```

## PASS: Green high-Vf 12V laser-current expected fail

Command: `python3 circuits/check_laser_current_budget.py --policy green-high-vf-12v`

```text
Laser current-loop policy: green-high-vf-12v
  High-forward-voltage green reference at a 12 V laser rail; this is expected to fail the conservative continuous AO3400A thermal budget.
  command clamp: 3.30V * 30k/(10k+30k) / 10.0ohm = 247.5mA
  sense resistor: drop=2.475V, power=0.613W, rating=2.0W
  laser rail=12.00V, diode Vf(max)=7.00V, AO3400A Vds=2.52V, power=0.625W
  at ambient=85.0degC and target Tj=125.0degC, AO3400A continuous power budget=0.320W
  estimated safe laser rail window at this diode Vf/current: 9.97V to 10.77V
FAIL laser current-loop policy
  AO3400A dissipates 0.625W, above 0.320W continuous budget at 85.0degC
```

## PASS: Low-Vf diode on green rail expected fail

Command: `python3 circuits/check_laser_current_budget.py --policy low-vf-diode-on-10v5`

```text
Laser current-loop policy: low-vf-diode-on-10v5
  Low-forward-voltage red/IR-style diode on the green-sized 10.5 V common laser rail; this is expected to fail unless current is reduced.
  command clamp: 3.30V * 30k/(10k+30k) / 10.0ohm = 247.5mA
  sense resistor: drop=2.475V, power=0.613W, rating=2.0W
  laser rail=10.50V, diode Vf(max)=2.50V, AO3400A Vds=5.53V, power=1.367W
  at ambient=85.0degC and target Tj=125.0degC, AO3400A continuous power budget=0.320W
  estimated safe laser rail window at this diode Vf/current: 5.47V to 6.27V
FAIL laser current-loop policy
  AO3400A dissipates 1.367W, above 0.320W continuous budget at 85.0degC
```

## BLOCKED: Open fabrication/release blockers

Command: `python3 circuits/check_laser_controller_release_readiness.py`

The release-readiness registry has unresolved source, harness, thermal, manufacturing, and human-inspection blockers.

```text
BLOCKED release readiness: 13 open fabrication/release blockers
  [GENERATED_COPPER_NETCLASS_CLEARANCE] Rail/zone KiCad signoff remains open after generated signal copper pass
    Detail: The PCB generator now runs in strict/capped route-search mode, using the same generated net-class clearances enforced by the PCB checker. The custom PCB gate passes with all signal/control multi-pad nets explicitly routed and 109/109 critical local route links connected. The generated-copper release gate still fails closed on +5V/GND rail/zone signoff: the laser-driver TLV9001 inter-channel +5V trunk is routed, but bulk +5V is still split from that trunk until placement or the bulk-to-laser bridge is fixed, KiCad zones are refilled, DRC is run, and visual return-path review is complete.
    Required action: Fix the bulk +5V bridge into the laser-driver +5V trunk without regressing LASER_N/USB/MPD/PWM routing or antenna keepout, refill and inspect zones in KiCad, run PCB DRC with schematic parity, and review +5V/GND rail and return-path copper before fabrication.
  [KICAD_ERC_DRC_ZONE_SIGNOFF] KiCad ERC, zone refill, and DRC signoff are still open
    Detail: Available netlist/source checks pass, but the current generated PCB is not release-clean and this KiCad 7.0.11 CLI only exposes sch/pcb export commands, not ERC/DRC. Formal KiCad ERC, refilled-zone copper, and board-rule DRC remain unproven.
    Required action: Run GUI ERC on the regenerated schematic, update PCB from schematic, refill zones, run PCB DRC with schematic parity, or use a KiCad CLI build that supports sch erc and pcb drc, then document any waivers.
  [VISUAL_RETURN_PATH_REVIEW] GND and sensitive return paths need visual review after zone refill
    Detail: The graph proves pads are connected, not that laser current, USB ESD, ESP32, and TIA returns have acceptable real copper paths.
    Required action: After KiCad zone refill, inspect GND islands/stitching and keep laser-current returns away from TIA summing-node return paths.
  [ACTUAL_LASER_MPN_HARNESS] Actual laser MPN pin tables and J4 harness are not released
    Detail: The Digikey cart MPNs have mixed pin-code behavior: D7805I, D6505I, and PLT5 520EB_P match the bench monitor front end, while PLT5 450GB has no monitor photodiode and its case pin must not be tied into MPD_RAW4.
    Required action: Build and inspect the J4 harness from the exact per-MPN pin table, verify can/case handling, and document that PLT5 450GB has no MPD telemetry before laser bring-up.
  [PER_DIODE_LASER_THERMAL_BUDGET] Per-diode laser current and heat budget is still open
    Detail: A single LASER_V+ rail can be safe for one diode class and unsafe for another because AO3400A heat is set by rail headroom.
    Required action: Run the laser-current budget for every selected diode, intended LASER_V+, current setpoint, and duty cycle; measure driver/sense-resistor temperature during bring-up.
  [AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE] AP2112 bench thermal measurement and production regulator decision are open
    Detail: The AP2112 is acceptable only for the bench no-RF policy. Sustained ESP32 wireless load fails the current SOT25 LDO budget.
    Required action: Measure AP2112 package temperature and +3V3 current during bring-up, keep RF disabled for this bench board, or replace the rail before sustained Wi-Fi/BLE.
  [EXT5V_CURRENT_LIMIT_OR_PROTECTION] External 5 V input protection/current limit is not released
    Detail: J6 external 5 V is accepted for bench use only if the upstream source is current-limited; the current board has no fuse/PTC on that input.
    Required action: Define the off-board current limit for bench builds or add board-level input protection before production.
  [USB_CONNECTOR_OFFICIAL_DRAWING] Official current Wuerth USB connector drawing still needs release verification
    Detail: The design uses a local KiCad footprint and a distributor mirror because the official exact drawing was not reachable from this shell.
    Required action: Verify the current 65100516121 manufacturer drawing, pin order, shield pads, and footprint orientation before fabrication.
  [SS14_EXACT_ORDER_DATASHEET] Exact SS14 C2480 manufacturer datasheet and polarity are still order-time checks
    Detail: The schematic and board assert diode polarity, but the source register still relies on distributor/order evidence plus a family reference.
    Required action: Confirm the exact C2480 manufacturer datasheet, package polarity, and orderable part before board order.
  [BOURNS_TRIMMER_WIPER_VISUAL] Bourns trimmer wiper orientation still needs visual PCB signoff
    Detail: The schematic and netlist bound the VBIAS range, but the production board still needs a human pin-1/wiper orientation check.
    Required action: Open the PCB in Pcbnew and verify RV1-RV4 pin-1/wiper orientation against the Bourns 3224 drawing before fabrication.
  [PASSIVE_PRODUCTION_AVL_AND_DERATING] Production passive AVL, pulse/surge derating, and temperature evidence are open
    Detail: The current derating gate covers bench steady-state voltage and power, not lifecycle, surge, pulse, or production procurement lock.
    Required action: Create a production procurement lock with final orderable passive datasheets, lifecycle/AVL state, pulse/surge/current derating, and board-temperature evidence.
  [MANUFACTURING_CLASS_AND_FAB_TIER] Manufacturing class, fab tier, and release package constraints are not selected
    Detail: The generated geometry is conservative, but IPC/J-STD class, final fabricator settings, and order-tier constraints are still not locked.
    Required action: Select IPC/J-STD class, fab tier, stackup/rule settings, assembly assumptions, and release notes before ordering.
  [AD7606_SYSTEM_INTERFACE] External AD7606 range and host-side assumptions are still open
    Detail: The bench board exports VOUT1..4 and CONVST, but the external AD7606 range and firmware/host configuration remain system-level checks.
    Required action: Verify the AD7606 variant/range pin, firmware timing, oversampling, and expected input range before relying on bench readings.
```

## PASS: Regenerate audit inventory

Command: `python3 circuits/generate_laser_controller_audit_tables.py /tmp/lc.net circuits/laser_controller.kicad_pcb circuits/review/2026-06-25_full_net_pin_inventory.md`

## PASS: Export placement

Command: `kicad-cli pcb export pos circuits/laser_controller.kicad_pcb -o /tmp/lc_pos.csv`

```text
Loading board
```

## BLOCKED: KiCad ERC availability

Command: `kicad-cli sch erc circuits/laser_controller.kicad_sch -o /tmp/lc_erc.rpt`

Installed KiCad CLI exposes only export here; run KiCad GUI ERC/DRC or a fuller KiCad CLI before fabrication.

```text
Maximum number of positional arguments exceeded
Usage: sch [-h] {export}

Optional arguments:
  -h, --help	shows help message and exits

Subcommands:
  export
```

## BLOCKED: KiCad DRC availability

Command: `kicad-cli pcb drc circuits/laser_controller.kicad_pcb -o /tmp/lc_drc.rpt`

Installed KiCad CLI exposes only export here; run KiCad GUI ERC/DRC or a fuller KiCad CLI before fabrication.

```text
Maximum number of positional arguments exceeded
Usage: pcb [-h] {export}

Optional arguments:
  -h, --help	shows help message and exits

Subcommands:
  export
```

## PASS: Git diff whitespace

Command: `git diff --check`

## PASS: Trailing whitespace scan

Command: `rg -n [ \t]+$ circuits docs -g *.md -g *.py -g *.kicad_sch -g *.kicad_pcb`
