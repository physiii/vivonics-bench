# Laser Controller Review Gate

Generated: 2026-07-04T23:34:22+00:00

This is a generated local audit artifact. It proves only the checks listed below.
Fabrication remains blocked if any row is `FAIL` or `BLOCKED`.

Overall release status: BLOCKED

| Status | Step | Return | Command |
|---|---|---:|---|
| PASS | Python compile | 0 | `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_pcb_staging.py circuits/check_laser_controller_release_gate.py circuits/check_layout_review_geometry.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_schematic_presentation.py circuits/check_power_thermal_budget.py circuits/check_ad7606_package_pcb.py circuits/check_ad7606_interface_budget.py circuits/check_tia_readout_budget.py circuits/check_ap6320x_package_pcb.py circuits/check_buck_input_power_budget.py circuits/check_vin24_input_protection.py circuits/check_usb_vbus_interface.py circuits/check_esp32_reset_boot_controls.py circuits/check_laser_driver_control_loop.py circuits/check_laser_driver_package_pcb.py circuits/check_laser_diode_footprints.py circuits/check_monitor_pd_package_pcb.py circuits/check_laser_current_budget.py circuits/check_laser_monitor_pd_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py` |
| PASS | Generate schematic/BOM | 0 | `python3 circuits/gen_laser_controller.py` |
| PASS | Export schematic netlist | 0 | `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net` |
| PASS | Netlist assertions | 0 | `python3 circuits/check_laser_controller_netlist.py /tmp/lc.net` |
| PASS | Schematic hierarchy/label assertions | 0 | `python3 circuits/check_schematic_hierarchy_labels.py circuits/laser_controller.kicad_sch` |
| PASS | Schematic presentation assertions | 0 | `python3 circuits/check_schematic_presentation.py circuits/laser_controller.kicad_sch` |
| PASS | Source-register assertions | 0 | `python3 circuits/check_laser_controller_sources.py /tmp/lc.net` |
| PASS | Part-note completeness assertions | 0 | `python3 circuits/check_part_notes_completeness.py` |
| PASS | Source-document evidence | 0 | `python3 circuits/check_source_documents.py` |
| PASS | Passive derating assertions | 0 | `python3 circuits/check_passive_derating.py` |
| PASS | USB/VBUS topology | 0 | `python3 circuits/check_usb_vbus_interface.py --netlist /tmp/lc.net` |
| PASS | ESP32 reset/boot controls | 0 | `python3 circuits/check_esp32_reset_boot_controls.py --netlist /tmp/lc.net` |
| PASS | USB connector footprint/source match | 0 | `python3 circuits/check_usb_vbus_interface.py --netlist /tmp/lc.net --policy connector-source-match` |
| PASS | AD7606 package/PCB pinout | 0 | `python3 circuits/check_ad7606_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb` |
| PASS | AD7606 interface budget | 0 | `python3 circuits/check_ad7606_interface_budget.py /tmp/lc.net` |
| PASS | TIA readout budget | 0 | `python3 circuits/check_tia_readout_budget.py --netlist /tmp/lc.net` |
| PASS | TIA bright-ambient expected fail | 1 | `python3 circuits/check_tia_readout_budget.py --netlist /tmp/lc.net --policy sfh2201-1000lx-example` |
| PASS | AP6320x package/PCB pinout | 0 | `python3 circuits/check_ap6320x_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb` |
| PASS | Buck/input selected-diode max-current reference | 0 | `python3 circuits/check_buck_input_power_budget.py --netlist /tmp/lc.net --policy bench-selected-max-9v3` |
| PASS | Buck/input hardware clamp expected fail | 1 | `python3 circuits/check_buck_input_power_budget.py --netlist /tmp/lc.net --policy hardware-clamp-9v3` |
| PASS | Buck datasheet capacitor recommendation expected fail | 1 | `python3 circuits/check_buck_input_power_budget.py --netlist /tmp/lc.net --policy datasheet-recommended-components` |
| PASS | VIN24 bench input topology | 0 | `python3 circuits/check_vin24_input_protection.py --netlist /tmp/lc.net` |
| PASS | VIN24 production input-protection expected fail | 1 | `python3 circuits/check_vin24_input_protection.py --netlist /tmp/lc.net --policy production-protection` |
| PASS | Laser-driver selected-current control-loop budget | 0 | `python3 circuits/check_laser_driver_control_loop.py --netlist /tmp/lc.net` |
| PASS | Laser-driver package/PCB pinout | 0 | `python3 circuits/check_laser_driver_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb` |
| PASS | Laser-driver hardware-clamp gate-margin expected fail | 1 | `python3 circuits/check_laser_driver_control_loop.py --netlist /tmp/lc.net --policy hardware-clamp-gate-margin` |
| PASS | Direct laser-can footprint pinout | 0 | `python3 circuits/check_laser_diode_footprints.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb` |
| PASS | Monitor-PD package/PCB pinout | 0 | `python3 circuits/check_monitor_pd_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb` |
| PASS | Generate staging PCB to temp file | 0 | `env LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 circuits/gen_pcb.py --output /tmp/lc_generated_staging.kicad_pcb` |
| PASS | PCB staging assertions | 0 | `python3 circuits/check_pcb_staging.py /tmp/lc_generated_staging.kicad_pcb /tmp/lc.net` |
| PASS | Generated-copper release gate | 0 | `python3 circuits/check_laser_controller_release_gate.py circuits/laser_controller.kicad_pcb /tmp/lc.net` |
| BLOCKED | Focused layout-geometry review | 2 | `python3 circuits/check_layout_review_geometry.py circuits/laser_controller.kicad_pcb` |
| PASS | AP2112 bench thermal policy | 0 | `python3 circuits/check_power_thermal_budget.py --policy bench-uart-usb` |
| PASS | AP2112 sustained Wi-Fi expected fail | 1 | `python3 circuits/check_power_thermal_budget.py --policy wifi-tx-100-duty` |
| PASS | Green high-Vf laser-current thermal reference | 0 | `python3 circuits/check_laser_current_budget.py --policy green-high-vf-10v5` |
| PASS | Selected-diode max-current 9.3V laser-current reference | 0 | `python3 circuits/check_laser_current_budget.py --policy selected-diodes-max-9v3` |
| PASS | PLT5 520EB_P monitor-PD high-side bias policy | 0 | `python3 circuits/check_laser_monitor_pd_budget.py --netlist /tmp/lc.net --policy plt5-520ebp-green-10v5` |
| PASS | MPD ADC-scale-only policy | 0 | `python3 circuits/check_laser_monitor_pd_budget.py --netlist /tmp/lc.net --policy adc-scale-only-10v5` |
| PASS | Selected-laser monitor-PD typical | 0 | `python3 circuits/check_laser_monitor_pd_budget.py --netlist /tmp/lc.net --policy selected-monitor-typ-9v3` |
| PASS | Selected-laser monitor-PD high-end | 0 | `python3 circuits/check_laser_monitor_pd_budget.py --netlist /tmp/lc.net --policy selected-monitor-worst-9v3` |
| PASS | Green high-Vf 12V laser-current expected fail | 1 | `python3 circuits/check_laser_current_budget.py --policy green-high-vf-12v` |
| PASS | Selected-diode 9.3V typical (production gate, must PASS) | 0 | `python3 circuits/check_laser_current_budget.py --policy selected-diodes-typ-9v3` |
| PASS | Selected-diode hardware clamp expected fail | 1 | `python3 circuits/check_laser_current_budget.py --policy selected-diodes-hardware-clamp-9v3` |
| PASS | Low-Vf diode on green rail expected fail | 1 | `python3 circuits/check_laser_current_budget.py --policy low-vf-diode-on-10v5` |
| BLOCKED | Open fabrication/release blockers | 2 | `python3 circuits/check_laser_controller_release_readiness.py` |
| PASS | Regenerate audit inventory | 0 | `python3 circuits/generate_laser_controller_audit_tables.py /tmp/lc.net circuits/laser_controller.kicad_pcb circuits/review/2026-06-25_full_net_pin_inventory.md` |
| PASS | Export placement | 0 | `kicad-cli pcb export pos circuits/laser_controller.kicad_pcb -o /tmp/lc_pos.csv` |
| BLOCKED | KiCad ERC availability | 1 | `kicad-cli sch erc circuits/laser_controller.kicad_sch -o /tmp/lc_erc.rpt` |
| BLOCKED | KiCad DRC availability | 1 | `kicad-cli pcb drc circuits/laser_controller.kicad_pcb -o /tmp/lc_drc.rpt` |
| PASS | Git diff whitespace | 0 | `git diff --check` |
| PASS | Trailing whitespace scan | 1 | `rg -n [ \t]+$ circuits docs -g *.md -g *.py -g *.kicad_sch -g *.kicad_pcb` |

## PASS: Python compile

Command: `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_pcb_staging.py circuits/check_laser_controller_release_gate.py circuits/check_layout_review_geometry.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_schematic_presentation.py circuits/check_power_thermal_budget.py circuits/check_ad7606_package_pcb.py circuits/check_ad7606_interface_budget.py circuits/check_tia_readout_budget.py circuits/check_ap6320x_package_pcb.py circuits/check_buck_input_power_budget.py circuits/check_vin24_input_protection.py circuits/check_usb_vbus_interface.py circuits/check_esp32_reset_boot_controls.py circuits/check_laser_driver_control_loop.py circuits/check_laser_driver_package_pcb.py circuits/check_laser_diode_footprints.py circuits/check_monitor_pd_package_pcb.py circuits/check_laser_current_budget.py circuits/check_laser_monitor_pd_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py`

## PASS: Generate schematic/BOM

Command: `python3 circuits/gen_laser_controller.py`

```text
wrote tia_ir.kicad_sch (36315 bytes, 569 lines)
  wrote tia_red.kicad_sch (36316 bytes, 569 lines)
  wrote tia_green.kicad_sch (36330 bytes, 569 lines)
  wrote tia_blue.kicad_sch (36331 bytes, 569 lines)
  wrote laser_ir.kicad_sch (35160 bytes, 538 lines)
  wrote laser_red.kicad_sch (35161 bytes, 538 lines)
  wrote laser_green.kicad_sch (35156 bytes, 538 lines)
  wrote laser_blue.kicad_sch (34847 bytes, 536 lines)
  wrote power_io.kicad_sch (199066 bytes, 3121 lines)
  wrote laser_controller.kicad_sch (30750 bytes, 247 lines)
  wrote laser_controller_bom_jlcpcb.csv
```

## PASS: Export schematic netlist

Command: `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net`

## PASS: Netlist assertions

Command: `python3 circuits/check_laser_controller_netlist.py /tmp/lc.net`

```text
PASS 603 netlist assertions across 156 nets
```

## PASS: Schematic hierarchy/label assertions

Command: `python3 circuits/check_schematic_hierarchy_labels.py circuits/laser_controller.kicad_sch`

```text
PASS schematic hierarchy/label guardrails: 10 root sheets, 60 whitelisted root global labels, 62 child hierarchical labels, typed sheet pins, zero child-sheet global labels, and checked schematic annotation designators
```

## PASS: Schematic presentation assertions

Command: `python3 circuits/check_schematic_presentation.py circuits/laser_controller.kicad_sch`

```text
PASS schematic presentation guardrails: no generated wire segments enter symbol bodies, no loose wire endpoints, labels clear symbols/text, symbol pin anchors/strokes touch their glyphs, and generated connection objects stay on the 50 mil grid; imported source sheets are checked for non-diagonal wires
```

## PASS: Source-register assertions

Command: `python3 circuits/check_laser_controller_sources.py /tmp/lc.net`

```text
PASS source-register coverage for 92 MPN/LCSC tokens across 179 components, intent coverage for 156 exported nets, 589 component-pin intent roles, and 3 documentation designator guard files
```

## PASS: Part-note completeness assertions

Command: `python3 circuits/check_part_notes_completeness.py`

```text
PASS part-note completeness: 16 notes, 218 required phrases, 3 stale-phrase guards
```

## PASS: Source-document evidence

Command: `python3 circuits/check_source_documents.py`

```text
WARN Alpha & Omega AO3400A datasheet: reachable; Primary source reachable from this shell; manual release-time latest-revision verification remains required. [HEAD HTTP 200, type=application/pdf, length=317848]
WARN JLCPCB via-design article: reachable; Advisory article only; JLCPCB quote capability page wins. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN Vishay SS12-SS16 family datasheet: reachable; Family reference only; exact LCSC C2480 manufacturer must be confirmed at order. [HEAD HTTP 200, type=application/pdf, length=1174123]
WARN LCSC C2480 SS14 order page: reachable; Distributor/order source, not a replacement for final order-time manufacturer confirmation. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C408410 MWSA0503S-4R7MT inductor page: reachable; Distributor/order source for the AP63205 4.7uH inductor; final AVL should retain a manufacturer datasheet copy. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C98364 WPN4020H100MT inductor page: reachable; Distributor/order source for the AP63200 10uH inductor; final AVL should retain a manufacturer datasheet copy. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN Wuerth Mini/Micro USB family page: reachable; Family/product page; exact 65100516121 drawing is required separately above. [HEAD HTTP 200, type=text/html; charset=UTF-8, length=1]
WARN LCSC C5120592 Wuerth 65100516121 Mini-B order page: reachable; Distributor/order source for the Wuerth Mini-B part used by the active J1/J2 BOM metadata. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN Farnell mirror of Wuerth 65100516121 drawing: reachable; Distributor mirror only; the official Wuerth drawing URL is the required source. [HEAD HTTP 200, type=application/pdf, length=276116]
WARN LCSC C2907002 FRC0603F1001TS 1k resistor page: reachable; Distributor/order source for active 1k 0603 passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C22984 30k resistor page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LCSC C844918 CRCW060310K0FKEA 10k resistor page: reachable; Distributor/order source for active 10k 0603 passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LCSC C114613 RC0603FR-07240RL 240 ohm resistor page: reachable; Distributor/order source for active 240 ohm monitor-PD sense resistor evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LRC L8050QLT1G transistor datasheet: reachable; Manufacturer datasheet for the Q5 NPN SOT-23 auto-reset transistor. [HEAD HTTP 200, type=application/pdf, length=543317]
WARN LCSC C39282 L8550HQLT1G transistor page: reachable; Distributor/order source for the Q6 PNP SOT-23 auto-reset transistor; final AVL should retain a manufacturer datasheet copy. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LCSC C127509 K2-1102SP-C4SC-04 switch page: reachable; Distributor/order source for the SW1-SW3 tactile reset/program/factory buttons. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C5123624 10 ohm 2512 sense resistor page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
PASS source-document evidence: 22 required online sources, 24 required local artifacts, and 17 secondary/open-risk sources reviewed
```

## PASS: Passive derating assertions

Command: `python3 circuits/check_passive_derating.py`

```text
PASS passive derating: checked 65 capacitors and 64 resistors/trimmers
  max capacitor voltage utilization: 48.0% at C62 (10uF 50V)
  max resistor power utilization: 48.4% at R63 (10K)
  max resistor voltage utilization: 29.3% at R63 (10K)
```

## PASS: USB/VBUS topology

Command: `python3 circuits/check_usb_vbus_interface.py --netlist /tmp/lc.net`

```text
PASS USB/VBUS topology: J1 USB-UART, J2 native USB, ESD clamps, 1N5819 VBUS isolation, D5 +5V OR-ing, CP2102N VBUS divider, UART, EN/BOOT, and ID/shield nets match the exported schematic
```

## PASS: ESP32 reset/boot controls

Command: `python3 circuits/check_esp32_reset_boot_controls.py --netlist /tmp/lc.net`

```text
PASS ESP32 reset/boot controls: EN 10k/1uF/reset, GPIO0 BOOT 10k/1uF/PROG, GPIO1 FACT, CP2102N DTR/RTS auto-reset transistors, RST/SUSPEND pulls, and IO13/IO14 pulls match the exported schematic
```

## PASS: USB connector footprint/source match

Command: `python3 circuits/check_usb_vbus_interface.py --netlist /tmp/lc.net --policy connector-source-match`

```text
PASS USB connector source/footprint match
```

## PASS: AD7606 package/PCB pinout

Command: `python3 circuits/check_ad7606_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb`

```text
PASS AD7606 package/PCB pinout: U14 AD7606BSTZ-4RL schematic pin nets, C51-C60 decoupling/reference support, current PCB pad nets, FRSTDATA no-connect, and KiCad LQFP-64 pad geometry agree
```

## PASS: AD7606 interface budget

Command: `python3 circuits/check_ad7606_interface_budget.py /tmp/lc.net`

```text
PASS AD7606 interface budget
  hardware: AD7606BSTZ-4RL LQFP-64, AVCC=+5V, VDRIVE=+3V3, internal reference, serial mode
  straps: RANGE=0 (+/-5V), OS[2:0]=000 (no oversampling), STBY=1, REF_SELECT=1, DB15/BYTE_SEL=0
  ESP32: CONVST=GPIO15, SCLK=GPIO17, CS=GPIO18, BUSY=GPIO47, RESET=GPIO48, DOUTA=GPIO21, DOUTB=GPIO38
  read policy: 4 channels, 2 DOUT lines, 32 SCLK edges per DOUT line, 10.00MHz SCLK -> 3.20us read
  timing budget: conversion=2.00us, read-after cycle=5.20us, target=100.0kSPS period=10.00us, margin=4.80us
  firmware requirements: RESET high >= 50ns, RESET-low to CONVST >= 25ns, CONVST low/high >= 25/25ns, CS after BUSY fall >= 0ns, avoid reading on BUSY falling edge and keep >= 25ns guard if reading during conversion
  scale: 16-bit twos-complement, +/-5V range, 152.59uV/LSB
```

## PASS: TIA readout budget

Command: `python3 circuits/check_tia_readout_budget.py --netlist /tmp/lc.net`

```text
PASS TIA readout budget (bench-range)
  topology: SFH2201 cathode +5V bias, anode to OPA380 summing node, 2M/10pF feedback, VOUT1..4 into AD7606
  VBIAS trim range: 0.00..2.50 V; OPA380 common-mode guard max=3.20 V
  guarded output/readout window: OPA380 0.10..4.30 V inside AD7606 +/-5 V range
  at VBIAS=1.50 V, RF=2 MOhm: +1.40/-0.70 uA one-sided headroom, +/-0.70 uA symmetric headroom
  SFH2201 reverse bias is 5.00 V versus 16.00 V maximum
  production caveat: optical signal range and calibration are still not proven by this first-order check
```

## PASS: TIA bright-ambient expected fail

Command: `python3 circuits/check_tia_readout_budget.py --netlist /tmp/lc.net --policy sfh2201-1000lx-example`

```text
FAIL TIA readout budget (sfh2201-1000lx-example): 1 issue(s)
  - SFH2201 1000 lx short-circuit-current example is not measurable at RF=2 MOhm: 76.0 uA would need 152.0 V of TIA swing
  note: VBIAS trim range: 0.00..2.50 V; OPA380 common-mode guard max=3.20 V
  note: guarded output/readout window: OPA380 0.10..4.30 V inside AD7606 +/-5 V range
  note: at VBIAS=1.50 V, RF=2 MOhm: +1.40/-0.70 uA one-sided headroom, +/-0.70 uA symmetric headroom
  note: SFH2201 reverse bias is 5.00 V versus 16.00 V maximum
```

## PASS: AP6320x package/PCB pinout

Command: `python3 circuits/check_ap6320x_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb`

```text
PASS AP6320x package/PCB guard: U15/U16 schematic pin nets, current PCB pad nets, TSOT-23-6 geometry, and L1/L2 local inductor footprints match the datasheet-derived contract.
```

## PASS: Buck/input selected-diode max-current reference

Command: `python3 circuits/check_buck_input_power_budget.py --netlist /tmp/lc.net --policy bench-selected-max-9v3`

```text
24V/buck current policy: bench-selected-max-9v3
  Bench current policy using the selected laser datasheet max currents, a reduced 9.3V LASER_V+ reference, and a conservative 350mA +5V load.
  VIN nominal=24.0V, AP632 input range=3.8V to 32V, J5 bench connector limit=500mA
  AP63200 feedback: 0.8V * (1 + 237k/22.1k) = 9.38V
  loads: +5V=350.0mA, LASER_V+=274.7mA at 9.30V
  estimated VIN current: BUCK_5V=85.8mA, LASER_V+=125.2mA, RJ45 LED/contact=2.2mA, total=213.2mA
  AP63205 BUCK_5V: load=0.350A, ripple=0.766A, peak=0.733A/3.68A Isat, rms=0.414A/4.00A Irms, inductor loss~0.010W
  AP63200 LASER_V+: load=0.275A, ripple=1.139A, peak=0.844A/2.80A Isat, rms=0.429A/2.00A Irms, inductor loss~0.040W
PASS 24V/buck policy for the checked assumptions.
```

## PASS: Buck/input hardware clamp expected fail

Command: `python3 circuits/check_buck_input_power_budget.py --netlist /tmp/lc.net --policy hardware-clamp-9v3`

```text
24V/buck current policy: hardware-clamp-9v3
  Unsafe all-channel laser hardware-clamp case at the production AP63200 feedback setting. This is expected to fail the 500mA bench input limit.
  VIN nominal=24.0V, AP632 input range=3.8V to 32V, J5 bench connector limit=500mA
  AP63200 feedback: 0.8V * (1 + 237k/22.1k) = 9.38V
  loads: +5V=350.0mA, LASER_V+=991.7mA at 9.30V
  estimated VIN current: BUCK_5V=85.8mA, LASER_V+=452.1mA, RJ45 LED/contact=2.2mA, total=540.1mA
  AP63205 BUCK_5V: load=0.350A, ripple=0.766A, peak=0.733A/3.68A Isat, rms=0.414A/4.00A Irms, inductor loss~0.010W
  AP63200 LASER_V+: load=0.992A, ripple=1.139A, peak=1.561A/2.80A Isat, rms=1.045A/2.00A Irms, inductor loss~0.236W
FAIL 24V/buck policy
  VIN_24V input current 540.1mA exceeds J5 barrel 500mA bench connector rating
```

## PASS: Buck datasheet capacitor recommendation expected fail

Command: `python3 circuits/check_buck_input_power_budget.py --netlist /tmp/lc.net --policy datasheet-recommended-components`

```text
24V/buck production component recommendation policy: datasheet-recommended-components
  Diodes AP63200/AP63205 application guidance calls for close VIN ceramic capacitance, 2x22uF style output capacitance in the reference designs/tables, close feedback parts, and 2oz/thermal-via layout for 2A operation.
  current input ceramic: C61+C62=20.0uF plus C70 22uF electrolytic; recommended ceramic threshold=10.0uF
  current output caps: C64+C65=20.0uF on BUCK_5V, C67+C68=20.0uF on LASER_V+; reference target=44.0uF each
FAIL 24V/buck policy
  BUCK_5V nominal ceramic output capacitance is 20.0uF, below the 2x22uF reference target
  LASER_V+ nominal ceramic output capacitance is 20.0uF, below the 2x22uF reference target
```

## PASS: VIN24 bench input topology

Command: `python3 circuits/check_vin24_input_protection.py --netlist /tmp/lc.net`

```text
VIN_24V input policy: bench-topology
  J5 barrel source: 24 V nominal into a 30 V / 500 mA connector rating
  J6 RJ45 source: access-controller pin convention, connector operating temp 0C..70C
  AP632 VIN range guard used here: 3.8 V operating minimum to 32 V maximum
  candidate protection refs found: none
PASS VIN_24V input policy for the checked assumptions.
```

## PASS: VIN24 production input-protection expected fail

Command: `python3 circuits/check_vin24_input_protection.py --netlist /tmp/lc.net --policy production-protection`

```text
VIN_24V input policy: production-protection
  J5 barrel source: 24 V nominal into a 30 V / 500 mA connector rating
  J6 RJ45 source: access-controller pin convention, connector operating temp 0C..70C
  AP632 VIN range guard used here: 3.8 V operating minimum to 32 V maximum
  candidate protection refs found: none
FAIL VIN_24V input policy
  J5/J6 connector power pins and U15/U16 buck IN pins are on the same VIN_24V net; there is no schematic fuse/current-limit/reverse-protection/TVS stage between field input and bucks
  no fuse/PTC/TVS/reverse-protection/eFuse/hot-swap component is present in the schematic BOM
  24 V nominal input uses 80% of the 30 V J5 barrel voltage rating before adapter/harness/hot-plug transients
  24 V nominal input uses 75% of the 32 V AP632 absolute input limit before transients
```

## PASS: Laser-driver selected-current control-loop budget

Command: `python3 circuits/check_laser_driver_control_loop.py --netlist /tmp/lc.net`

```text
PASS laser-driver control-loop budget (selected-max-current)
  topology: PWM divider -> TLV9001 +IN, sense resistor high side -> -IN, OUT -> AO3400A gate, drain -> LASER_Nx
  PWM divider clamp: 3.30 V * 30k/(10k+30k) = 2.475 V -> 247.5 mA
  selected-max-current: checked current=120.0 mA, sense feedback=1.200 V
  TLV9001 input range policy: -0.1..5.1 V on a 5 V rail
  available AO3400A Vgs at checked current ~= 3.780 V; margin vs 2.5 V characterized point=1.280 V
  production caveat: this does not waive diode current limits, MOSFET SOA/heat, optical safety, or firmware clamps
```

## PASS: Laser-driver package/PCB pinout

Command: `python3 circuits/check_laser_driver_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb`

```text
PASS laser-driver package/PCB guard: TLV9001/AO3400A schematic pin nets, local driver sense/command/gate/compensation component identities, current PCB pad nets, and KiCad SOT-23-5/SOT-23/2512/0603/0402/0603-cap geometry agree.
```

## PASS: Laser-driver hardware-clamp gate-margin expected fail

Command: `python3 circuits/check_laser_driver_control_loop.py --netlist /tmp/lc.net --policy hardware-clamp-gate-margin`

```text
FAIL laser-driver control-loop budget (hardware-clamp-gate-margin): 1 issue(s)
  - hardware clamp leaves only 0.005 V above the AO3400A 2.5 V RDS(on) characterization point; required margin is 0.250 V
  note: PWM divider clamp: 3.30 V * 30k/(10k+30k) = 2.475 V -> 247.5 mA
  note: hardware-clamp-gate-margin: checked current=247.5 mA, sense feedback=2.475 V
  note: TLV9001 input range policy: -0.1..5.1 V on a 5 V rail
  note: available AO3400A Vgs at checked current ~= 2.505 V; margin vs 2.5 V characterized point=0.005 V
```

## PASS: Direct laser-can footprint pinout

Command: `python3 circuits/check_laser_diode_footprints.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb`

```text
PASS laser diode footprint pinout: LD1/LD2 Style-A TO18, LD3 PLT5 520EB_P TO56, LD4 PLT5 450GB case NC; schematic nets, current PCB pad nets, and KiCad TO18/TO56 pad geometry agree
```

## PASS: Monitor-PD package/PCB pinout

Command: `python3 circuits/check_monitor_pd_package_pcb.py --netlist /tmp/lc.net --board circuits/laser_controller.kicad_pcb`

```text
PASS monitor-PD package/PCB guard: U12/U13 schematic pin nets, local MPD sense/filter/bias component identities, current PCB pad nets, LD4 case no-connect, and KiCad package geometry agree.
```

## PASS: Generate staging PCB to temp file

Command: `env LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 circuits/gen_pcb.py --output /tmp/lc_generated_staging.kicad_pcb`

```text
wrote /tmp/lc_generated_staging.kicad_pcb  (192 blocks, 181 ref instances)
  refs: 181 unique
```

## PASS: PCB staging assertions

Command: `python3 circuits/check_pcb_staging.py /tmp/lc_generated_staging.kicad_pcb /tmp/lc.net`

```text
PASS PCB staging: 181 physical footprints loaded, 2 board-only mechanical footprints, 0 empty-footprint symbols skipped, 0 board-level segments/vias/zones, 1 footprint-internal zone/keepout block(s), 179 non-overlapping electrical staged bboxes outside the 173.025 x 61.125 mm outline; sections TIA_IR:11, TIA_RED:11, TIA_GREEN:11, TIA_BLUE:11, LASER_IR:11, LASER_RED:11, LASER_GREEN:11, LASER_BLUE:11, MCU_ESP32-S3:36, POWER_IO:55
```

## PASS: Generated-copper release gate

Command: `python3 circuits/check_laser_controller_release_gate.py circuits/laser_controller.kicad_pcb /tmp/lc.net`

```text
PASS fabrication release gate: 110/110 multi-pad nets explicitly routed, no pending rail/zone nets, laser cathode/anode routes meet generated width targets, and laser sense returns have distinct high-current GND vias. This does not replace GUI ERC/DRC with zone refill.
```

## BLOCKED: Focused layout-geometry review

Command: `python3 circuits/check_layout_review_geometry.py circuits/laser_controller.kicad_pcb`

The board still has high-risk physical layout distances in buck, USB ESD, TIA summing-node, monitor-PD, or laser-current local loops.

```text
BLOCKED layout geometry review: 13 high-risk layout distances exceed targets
  [usb-esd] Native USB D- ESD-to-ESP32 distance: 18.57 mm exceeds 4.50 mm; D12.2 (/MCU_ESP32-S3/IO19) at (45.175,101.650) -> U9.13 (/MCU_ESP32-S3/IO19) at (63.125,96.895). USB D-/D+ routes should keep the clamp and protected device path compact.
  [usb-esd] Native USB D+ ESD-to-ESP32 distance: 20.06 mm exceeds 4.50 mm; D11.2 (/MCU_ESP32-S3/IO20) at (43.375,101.650) -> U9.14 (/MCU_ESP32-S3/IO20) at (63.125,98.165). USB D-/D+ routes should keep the clamp and protected device path compact.
  [tia-sensitive] IR signal photodiode anode to OPA380 summing node: 20.02 mm exceeds 6.00 mm; D1.2 (Net-(D1-A)) at (156.165,102.438) -> U1.2 (Net-(D1-A)) at (142.531,87.782). Photodiode anode and OPA380 inverting input are the highest-impedance TIA node.
  [tia-sensitive] Red signal photodiode anode to OPA380 summing node: 16.59 mm exceeds 6.00 mm; D2.2 (Net-(D2-A)) at (140.190,102.438) -> U2.2 (Net-(D2-A)) at (123.895,105.550). Photodiode anode and OPA380 inverting input are the highest-impedance TIA node.
  [tia-sensitive] Green signal photodiode anode to OPA380 summing node: 12.99 mm exceeds 6.00 mm; D3.2 (Net-(D3-A)) at (156.165,118.438) -> U3.2 (Net-(D3-A)) at (158.425,131.225). Photodiode anode and OPA380 inverting input are the highest-impedance TIA node.
  [tia-sensitive] Blue signal photodiode anode to OPA380 summing node: 16.22 mm exceeds 6.00 mm; D4.2 (Net-(D4-A)) at (140.165,118.438) -> U4.2 (Net-(D4-A)) at (134.450,133.620). Photodiode anode and OPA380 inverting input are the highest-impedance TIA node.
  [monitor-pd] IR monitor-PD raw path from LD1 to sense resistor: 103.36 mm exceeds 25.00 mm; LD1.3 (MPD_RAW1) at (170.880,118.438) -> R42.1 (MPD_RAW1) at (67.600,114.475). Raw monitor-PD current should not cross the board before the current-sense resistor.
  [monitor-pd] Red monitor-PD raw path from LD2 to sense resistor: 121.96 mm exceeds 25.00 mm; LD2.3 (MPD_RAW2) at (186.880,102.438) -> R44.1 (MPD_RAW2) at (65.525,114.543). Raw monitor-PD current should not cross the board before the current-sense resistor.
  [monitor-pd] Green monitor-PD raw path from LD3 to sense resistor: 114.29 mm exceeds 25.00 mm; LD3.3 (MPD_RAW3) at (186.900,118.438) -> R46.1 (MPD_RAW3) at (72.738,113.100). Raw monitor-PD current should not cross the board before the current-sense resistor.
  [laser-current] IR laser FET source to sense resistor: 5.49 mm exceeds 3.00 mm; Q1.2 (/LASER_IR/FB) at (170.673,133.397) -> R18.1 (/LASER_IR/FB) at (172.261,128.142). Laser current sense loop should be tight to avoid injecting error and current-loop noise.
  [laser-current] Red laser FET source to sense resistor: 5.85 mm exceeds 3.00 mm; Q2.2 (/LASER_RED/FB) at (195.325,86.600) -> R23.1 (/LASER_RED/FB) at (192.650,91.800). Laser current sense loop should be tight to avoid injecting error and current-loop noise.
  [laser-current] Green laser FET source to sense resistor: 5.49 mm exceeds 3.00 mm; Q3.2 (/LASER_GREEN/FB) at (189.300,133.425) -> R28.1 (/LASER_GREEN/FB) at (190.888,128.169). Laser current sense loop should be tight to avoid injecting error and current-loop noise.
  [laser-current] Blue laser FET source to sense resistor: 5.77 mm exceeds 3.00 mm; Q4.2 (/LASER_BLUE/FB) at (176.025,86.312) -> R33.1 (/LASER_BLUE/FB) at (173.250,91.375). Laser current sense loop should be tight to avoid injecting error and current-loop noise.
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
PASS laser current-loop policy for this diode/supply assumption. Actual laser MPN and direct-footprint pinout still require release review.
```

## PASS: Selected-diode max-current 9.3V laser-current reference

Command: `python3 circuits/check_laser_current_budget.py --policy selected-diodes-max-9v3`

```text
Selected laser current-loop policy: selected-diodes-max-9v3
  Actual LD1-LD4 MPNs at datasheet maximum operating current/voltage on the production 9.3V common LASER_V+ reference. All selected diodes must pass this gate before production release.
  hardware command clamp remains 247.5mA (3.30V * 30k/(10k+30k) / 10.0ohm)
  AO3400A continuous budget=0.320W at ambient=85.0degC, target Tj=125.0degC
  LD1 IR D7805I: datasheet maximum operating-current point; Popt=5mW, I=50.0mA (datasheet max 50.0mA), Vf=2.50V, LASER_V+=9.30V
    sense drop=0.500V, sense power=0.025W, AO3400A Vds=6.30V, AO3400A power=0.315W
    safe rail window at this current/Vf: 3.50V to 9.40V; source: US-Lasers D7805I 780nm 5mW datasheet
  LD2 RED D6505I: datasheet maximum operating-current point; Popt=5mW, I=25.0mA (datasheet max 25.0mA), Vf=2.60V, LASER_V+=9.30V
    sense drop=0.250V, sense power=0.006W, AO3400A Vds=6.45V, AO3400A power=0.161W
    safe rail window at this current/Vf: 3.35V to 15.65V; source: Digikey D650-5I 650nm 5mW datasheet; lower-current source used conservatively because the US-Lasers mirror gives a conflicting 40mA typ / 60mA max operating-current table
  LD3 GREEN PLT5 520EB_P: datasheet maximum operating-current point; Popt=20mW, I=78.0mA (datasheet max 78.0mA), Vf=6.10V, LASER_V+=9.30V
    sense drop=0.780V, sense power=0.061W, AO3400A Vds=2.42V, AO3400A power=0.189W
    safe rail window at this current/Vf: 7.38V to 10.98V; source: ams OSRAM PLT5 520EB_P datasheet
  LD4 BLUE PLT5 450GB: datasheet maximum operating-current point; Popt=100mW, I=120.0mA (datasheet max 120.0mA), Vf=6.50V, LASER_V+=9.30V
    sense drop=1.200V, sense power=0.144W, AO3400A Vds=1.60V, AO3400A power=0.192W
    safe rail window at this current/Vf: 8.20V to 10.37V; source: ams OSRAM PLT5 450GB datasheet
PASS selected laser current-loop policy for the checked current/rail assumptions. This does not waive optical safety, duty-cycle, firmware clamp, or temperature measurement.
```

## PASS: PLT5 520EB_P monitor-PD high-side bias policy

Command: `python3 circuits/check_laser_monitor_pd_budget.py --netlist /tmp/lc.net --policy plt5-520ebp-green-10v5`

```text
Monitor-PD policy: plt5-520ebp-green-10v5
  PLT5 520EB_P monitor-current reference case. The datasheet monitor current is specified at VRPD=5V and is not guaranteed as an accurate absolute power measurement. The bench circuit uses a high-side INA4180 sense path and LM4040-derived MPD_BIAS node. PLT5 450GB has no monitor photodiode, so MPD_RAW4 is only a spare/open front-end input.
  front end: MPD_RAWx -> 240 ohm sense -> MPD_BIAS; INA4180 gain=20; 1k/100nF ADC-side RC
  schematic connectivity checked against /tmp/lc.net
  PLT5-style CH1: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  PLT5-style CH2: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  PLT5-style CH3: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  PLT5-style CH4: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  LASER_V+=10.50V, MPD_BIAS=5.50V -> monitor-PD reverse bias dark/off=5.00V; RC tau=0.10ms
  LM4040 current: no-MPD=2.21mA, active MPD=1.61mA; INA linear monitor-current limit about 681uA, ESP32 11dB limit about 646uA, production guard about 604uA
PASS monitor-PD policy for this scope. This does not replace per-laser datasheet pinout, reverse-bias, optical safety, and calibration review.
```

## PASS: MPD ADC-scale-only policy

Command: `python3 circuits/check_laser_monitor_pd_budget.py --netlist /tmp/lc.net --policy adc-scale-only-10v5`

```text
Monitor-PD policy: adc-scale-only-10v5
  ADC headroom check only for the high-side monitor front end. This does not approve any real laser MPN without its own pinout and reverse-bias review.
  front end: MPD_RAWx -> 240 ohm sense -> MPD_BIAS; INA4180 gain=20; 1k/100nF ADC-side RC
  schematic connectivity checked against /tmp/lc.net
  PLT5-style CH1: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  PLT5-style CH2: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  PLT5-style CH3: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  PLT5-style CH4: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  LASER_V+=10.50V, MPD_BIAS=5.50V -> monitor-PD reverse bias dark/off=5.00V; RC tau=0.10ms
  LM4040 current: no-MPD=2.21mA, active MPD=1.61mA; INA linear monitor-current limit about 681uA, ESP32 11dB limit about 646uA, production guard about 604uA
PASS monitor-PD policy for this scope. This does not replace per-laser datasheet pinout, reverse-bias, optical safety, and calibration review.
```

## PASS: Selected-laser monitor-PD typical

Command: `python3 circuits/check_laser_monitor_pd_budget.py --netlist /tmp/lc.net --policy selected-monitor-typ-9v3`

```text
Monitor-PD policy: selected-monitor-typ-9v3
  Selected Digikey-cart monitor-current typical case. LD1 D7805I is 200uA typ, LD2 D6505I is 150uA typ, LD3 PLT5 520EB_P is 150uA typ, and LD4 PLT5 450GB has no monitor photodiode. This case should fit the local production ADC-headroom guard after the sense resistor was reduced to 240R.
  front end: MPD_RAWx -> 240 ohm sense -> MPD_BIAS; INA4180 gain=20; 1k/100nF ADC-side RC
  schematic connectivity checked against /tmp/lc.net
  LD1 D7805I: typ monitor current=200uA -> sense=0.048V, ADC=0.96V, VRPD=4.95V
  LD2 D6505I: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  LD3 PLT5 520EB_P: typ monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  LD4 PLT5 450GB: no monitor photodiode; MPD_RAW4/MPD4 is spare/open
  LASER_V+=9.30V, MPD_BIAS=4.30V -> monitor-PD reverse bias dark/off=5.00V; RC tau=0.10ms
  LM4040 current: no-MPD=1.73mA, active MPD=1.23mA; INA linear monitor-current limit about 681uA, ESP32 11dB limit about 646uA, production guard about 604uA
PASS monitor-PD policy for this scope. This does not replace per-laser datasheet pinout, reverse-bias, optical safety, and calibration review.
```

## PASS: Selected-laser monitor-PD high-end

Command: `python3 circuits/check_laser_monitor_pd_budget.py --netlist /tmp/lc.net --policy selected-monitor-worst-9v3`

```text
Monitor-PD policy: selected-monitor-worst-9v3
  Selected Digikey-cart monitor-current high-end case. D7805I max monitor current is 600uA and D6505I max monitor current is 300uA; PLT5 520EB_P has only a typical 150uA monitor-current value in the captured table and PLT5 450GB has no monitor PD. This high-end case should fit the local production ADC-headroom guard with the 240R/gain20 front end. It still needs optical calibration before MPD can be used as production feedback.
  front end: MPD_RAWx -> 240 ohm sense -> MPD_BIAS; INA4180 gain=20; 1k/100nF ADC-side RC
  schematic connectivity checked against /tmp/lc.net
  LD1 D7805I: max monitor current=600uA -> sense=0.144V, ADC=2.88V, VRPD=4.86V
  LD2 D6505I: max monitor current=300uA -> sense=0.072V, ADC=1.44V, VRPD=4.93V
  LD3 PLT5 520EB_P: max monitor current=150uA -> sense=0.036V, ADC=0.72V, VRPD=4.96V
  LD4 PLT5 450GB: no monitor photodiode; MPD_RAW4/MPD4 is spare/open
  LASER_V+=9.30V, MPD_BIAS=4.30V -> monitor-PD reverse bias dark/off=5.00V; RC tau=0.10ms
  LM4040 current: no-MPD=1.73mA, active MPD=0.68mA; INA linear monitor-current limit about 681uA, ESP32 11dB limit about 646uA, production guard about 604uA
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

## PASS: Selected-diode 9.3V typical (production gate, must PASS)

Command: `python3 circuits/check_laser_current_budget.py --policy selected-diodes-typ-9v3`

```text
Selected laser current-loop policy: selected-diodes-typ-9v3
  Actual LD1-LD4 MPNs at datasheet typical operating current/voltage on the production AP63200 LASER_V+ setting (~9.3V). This is the primary production thermal gate for the common-rail architecture.
  hardware command clamp remains 247.5mA (3.30V * 30k/(10k+30k) / 10.0ohm)
  AO3400A continuous budget=0.320W at ambient=85.0degC, target Tj=125.0degC
  LD1 IR D7805I: datasheet typical operating point; Popt=5mW, I=35.0mA (datasheet max 50.0mA), Vf=2.10V, LASER_V+=9.30V
    sense drop=0.350V, sense power=0.012W, AO3400A Vds=6.85V, AO3400A power=0.240W
    safe rail window at this current/Vf: 2.95V to 11.59V; source: US-Lasers D7805I 780nm 5mW datasheet
  LD2 RED D6505I: datasheet typical operating point; Popt=5mW, I=20.0mA (datasheet max 25.0mA), Vf=2.20V, LASER_V+=9.30V
    sense drop=0.200V, sense power=0.004W, AO3400A Vds=6.90V, AO3400A power=0.138W
    safe rail window at this current/Vf: 2.90V to 18.40V; source: Digikey D650-5I 650nm 5mW datasheet; lower-current source used conservatively because the US-Lasers mirror gives a conflicting 40mA typ / 60mA max operating-current table
  LD3 GREEN PLT5 520EB_P: datasheet typical operating point; Popt=20mW, I=65.0mA (datasheet max 78.0mA), Vf=5.40V, LASER_V+=9.30V
    sense drop=0.650V, sense power=0.042W, AO3400A Vds=3.25V, AO3400A power=0.211W
    safe rail window at this current/Vf: 6.55V to 10.97V; source: ams OSRAM PLT5 520EB_P datasheet
  LD4 BLUE PLT5 450GB: datasheet typical operating point; Popt=100mW, I=87.0mA (datasheet max 120.0mA), Vf=5.20V, LASER_V+=9.30V
    sense drop=0.870V, sense power=0.076W, AO3400A Vds=3.23V, AO3400A power=0.281W
    safe rail window at this current/Vf: 6.57V to 9.75V; source: ams OSRAM PLT5 450GB datasheet
PASS selected laser current-loop policy for the checked current/rail assumptions. This does not waive optical safety, duty-cycle, firmware clamp, or temperature measurement.
```

## PASS: Selected-diode hardware clamp expected fail

Command: `python3 circuits/check_laser_current_budget.py --policy selected-diodes-hardware-clamp-9v3`

```text
Selected laser current-loop policy: selected-diodes-hardware-clamp-9v3
  Actual LD1-LD4 MPNs driven to the 247.5mA analog command clamp on the production 9.3V LASER_V+ setting. This is expected to fail: the clamp is an electrical upper bound, not a safe optical current limit.
  hardware command clamp remains 247.5mA (3.30V * 30k/(10k+30k) / 10.0ohm)
  AO3400A continuous budget=0.320W at ambient=85.0degC, target Tj=125.0degC
  LD1 IR D7805I: hardware command clamp with datasheet max Vf for least-worst MOSFET heat; Popt=5mW, I=247.5mA (datasheet max 50.0mA), Vf=2.50V, LASER_V+=9.30V
    sense drop=2.475V, sense power=0.613W, AO3400A Vds=4.33V, AO3400A power=1.070W
    safe rail window at this current/Vf: 5.47V to 6.27V; source: US-Lasers D7805I 780nm 5mW datasheet
  LD2 RED D6505I: hardware command clamp with datasheet max Vf for least-worst MOSFET heat; Popt=5mW, I=247.5mA (datasheet max 25.0mA), Vf=2.60V, LASER_V+=9.30V
    sense drop=2.475V, sense power=0.613W, AO3400A Vds=4.23V, AO3400A power=1.046W
    safe rail window at this current/Vf: 5.58V to 6.37V; source: Digikey D650-5I 650nm 5mW datasheet; lower-current source used conservatively because the US-Lasers mirror gives a conflicting 40mA typ / 60mA max operating-current table
  LD3 GREEN PLT5 520EB_P: hardware command clamp with datasheet max Vf for least-worst MOSFET heat; Popt=20mW, I=247.5mA (datasheet max 78.0mA), Vf=6.10V, LASER_V+=9.30V
    sense drop=2.475V, sense power=0.613W, AO3400A Vds=0.73V, AO3400A power=0.179W
    safe rail window at this current/Vf: 9.07V to 9.87V; source: ams OSRAM PLT5 520EB_P datasheet
  LD4 BLUE PLT5 450GB: hardware command clamp with datasheet max Vf for least-worst MOSFET heat; Popt=100mW, I=247.5mA (datasheet max 120.0mA), Vf=6.50V, LASER_V+=9.30V
    sense drop=2.475V, sense power=0.613W, AO3400A Vds=0.33V, AO3400A power=0.080W
    safe rail window at this current/Vf: 9.47V to 10.27V; source: ams OSRAM PLT5 450GB datasheet
FAIL selected laser current-loop policy
  LD1 D7805I: commanded 247.5mA exceeds datasheet operating-current max 50.0mA
  LD1 D7805I: AO3400A dissipates 1.070W, above 0.320W continuous budget at 85.0degC
  LD2 D6505I: commanded 247.5mA exceeds datasheet operating-current max 25.0mA
  LD2 D6505I: AO3400A dissipates 1.046W, above 0.320W continuous budget at 85.0degC
  LD3 PLT5 520EB_P: commanded 247.5mA exceeds datasheet operating-current max 78.0mA
  LD4 PLT5 450GB: commanded 247.5mA exceeds datasheet operating-current max 120.0mA
  LD4 PLT5 450GB: AO3400A Vds headroom is 0.33V, below 0.50V target
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

The release-readiness registry has unresolved source, direct-laser, thermal, manufacturing, and human-inspection blockers.

```text
BLOCKED release readiness: 12 open fabrication/release blockers
  [KICAD_ERC_DRC_ZONE_SIGNOFF] KiCad ERC and schematic-parity signoff are still open
    Detail: Available netlist/source/custom PCB checks pass, and a 2026-07-04 GUI DRC screenshot captures refilled-zone DRC with 0 violations and 0 unconnected items. Full fabrication signoff is still not proven because this KiCad 7.0.11 CLI only exposes sch/pcb export commands, not ERC/DRC, and the captured GUI DRC did not run schematic parity. Formal KiCad ERC and native schematic-parity evidence remain unproven.
    Required action: Run GUI ERC on the regenerated schematic, update PCB from schematic, refill zones, run PCB DRC with schematic parity, or use a KiCad CLI build that supports sch erc and pcb drc, then document any waivers/reports.
  [VISUAL_RETURN_PATH_REVIEW] GND and sensitive return paths need visual review after zone refill
    Detail: The graph proves pads are connected, not that laser current, USB ESD, ESP32, and TIA returns have acceptable real copper paths.
    Required action: After KiCad zone refill, inspect GND islands/stitching and keep laser-current returns away from TIA summing-node return paths.
  [ACTUAL_LASER_MPN_DIRECT_FOOTPRINT] Actual laser MPN pin tables and direct footprints are not released
    Detail: The Digikey cart MPNs have mixed pin-code behavior: D7805I, D6505I, and PLT5 520EB_P match the bench monitor front end, while PLT5 450GB has no monitor photodiode and its case pin must not be tied into MPD_RAW4.
    Required action: Verify the exact per-MPN pin table against the direct LDx footprint wiring, inspect can/case handling, and document that PLT5 450GB has no MPD telemetry before laser bring-up.
  [MONITOR_PD_FRONTEND_RANGE_CALIBRATION] Monitor-PD front-end range and calibration are not released
    Detail: The exported netlist now proves the INA4180/LM4040 monitor topology is connected as intended, and the 240R/gain20 monitor scale covers the captured D7805I/D6505I/PLT5 520EB_P monitor-current range inside the local ADC-headroom guard. PLT5 450GB has no monitor photodiode, so MPD4 is not blue-source telemetry. Optical calibration and safety behavior are still unreleased.
    Required action: Calibrate each source against an external optical meter and define firmware behavior for MPD telemetry before using it for production APC, normalization, or safety decisions.
  [TIA_READOUT_RANGE_CALIBRATION] Signal-PD TIA readout range and optical calibration are not released
    Detail: The exported netlist now proves the four SFH2201/OPA380 signal-PD channels feed VOUT1..4 into the AD7606 as intended, and the first-order TIA checker shows the present 2 MOhm feedback trim is a high-sensitivity, low-current bench range. At VBIAS = 1.5 V it has about +1.40 uA / -0.70 uA one-sided OPA380 headroom before the guarded output window clips; the SFH2201 1000 lx datasheet short-circuit-current example would need about 152 V of TIA swing at 2 MOhm and is intentionally an expected-fail case.
    Required action: Define the real Vivonics optical photocurrent range at the SFH2201 under the bench optics, choose RF/VBIAS/firmware scaling for that range, shield or limit ambient light, and calibrate AD7606 counts against known optical/electrical inputs before using the signal-PD path for production measurements.
  [PER_DIODE_LASER_THERMAL_BUDGET] Per-diode laser current and heat budget is still open
    Detail: The selected-diode policies keep the old 10.72 V common rail as an expected-fail comparison for PLT5 450GB at typical current, while the 247.5 mA hardware clamp exceeds every selected laser MPN operating-current maximum.
    Required action: Lower/rework LASER_V+ or use per-channel drivers, enforce real per-diode current limits before firmware can command the clamp, then measure driver/sense-resistor temperature and optical output during bring-up.
  [AP2112_BENCH_MEASUREMENT_OR_REGULATOR_CHANGE] AP2112 bench thermal measurement and production regulator decision are open
    Detail: The AP2112 is acceptable only for the bench no-RF policy. Sustained ESP32 wireless load fails the current SOT25 LDO budget.
    Required action: Measure AP2112 package temperature and +3V3 current during bring-up, keep RF disabled for this bench board, or replace the rail before sustained Wi-Fi/BLE.
  [VIN24_INPUT_PROTECTION_AND_BUCK_LAYOUT] 24 V barrel/RJ45 input protection and buck layout are not released
    Detail: J5 barrel and J6 RJ45 inputs plus the U15/U16 buck supplies are accepted for bench use only with a selected current-limited adapter and reviewed switch-loop/thermal layout. The VIN24 checker proves the current bench topology is direct J5/J6 to U15/U16 input wiring and intentionally fails production protection because there is no fuse/PTC/TVS/reverse-protection/eFuse/hot-swap component. The AP632 checker passes the selected-diode 9.3 V max-current reference, but the 9.3 V all-channel hardware-clamp case exceeds the 500 mA J5 input budget and the current C64+C65/C67+C68 output capacitor set is below generic AP632 datasheet guidance.
    Required action: Define the adapter current limit, RJ45 harness current limit, fuse/current-limit element, reverse-polarity strategy, and transient/TVS protection; rework or justify the AP632 output capacitors; then verify AP63205/AP63200 switch-loop routing, copper width, output ripple/transient/stability, and temperature before production.
  [SS14_EXACT_ORDER_DATASHEET] Exact SS14 C2480 manufacturer datasheet and polarity are still order-time checks
    Detail: The schematic and board assert diode polarity, but the source register still relies on distributor/order evidence plus a family reference.
    Required action: Confirm the exact C2480 manufacturer datasheet, package polarity, and orderable part before board order.
  [BOURNS_TRIMMER_WIPER_VISUAL] Bourns trimmer wiper orientation still needs visual PCB signoff
    Detail: The schematic and netlist bound the VBIAS range, but the production board still needs a human pin-1/wiper orientation check.
    Required action: Open the PCB in Pcbnew and verify RV1-RV4 pin-1/wiper orientation against the Bourns 3224 drawing before fabrication.
  [PASSIVE_PRODUCTION_AVL_AND_DERATING] Production passive AVL, pulse/surge derating, and temperature evidence are open
    Detail: The current derating gate covers bench steady-state voltage and power, not lifecycle, surge, pulse, or production procurement lock.
    Required action: Create a production procurement lock with final orderable passive datasheets, lifecycle/AVL state, pulse/surge/current derating, and board-temperature evidence.
  [AD7606_SYSTEM_INTERFACE] On-board AD7606 firmware and bench-readout validation are still open
    Detail: The bench board routes VOUT1..4 into the on-board AD7606 and the hardware straps now have a checked 10 MHz / 100 kSPS default interface budget, but firmware implementation, timing on the real ESP32, scaling, and bench ADC readback remain system-level checks.
    Required action: Implement and scope the ESP32 AD7606 driver, verify RESET/CONVST/BUSY/CS/SCLK timing, confirm +/-5 V range scaling and oversampling assumptions in firmware, and compare readings against known optical/electrical inputs before relying on bench data.
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
