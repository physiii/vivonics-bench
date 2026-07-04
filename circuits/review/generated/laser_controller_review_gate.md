# Laser Controller Review Gate

Generated: 2026-07-04T21:32:53+00:00

This is a generated local audit artifact. It proves only the checks listed below.
Fabrication remains blocked if any row is `FAIL` or `BLOCKED`.

Overall release status: BLOCKED

| Status | Step | Return | Command |
|---|---|---:|---|
| PASS | Python compile | 0 | `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_pcb_staging.py circuits/check_laser_controller_release_gate.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_schematic_presentation.py circuits/check_power_thermal_budget.py circuits/check_ad7606_package_pcb.py circuits/check_ad7606_interface_budget.py circuits/check_tia_readout_budget.py circuits/check_ap6320x_package_pcb.py circuits/check_buck_input_power_budget.py circuits/check_vin24_input_protection.py circuits/check_usb_vbus_interface.py circuits/check_esp32_reset_boot_controls.py circuits/check_laser_driver_control_loop.py circuits/check_laser_driver_package_pcb.py circuits/check_laser_diode_footprints.py circuits/check_monitor_pd_package_pcb.py circuits/check_laser_current_budget.py circuits/check_laser_monitor_pd_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py` |
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
| PASS | USB connector footprint/source expected fail | 1 | `python3 circuits/check_usb_vbus_interface.py --netlist /tmp/lc.net --policy connector-source-match` |
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
| FAIL | PCB staging assertions | 1 | `python3 circuits/check_pcb_staging.py /tmp/lc_generated_staging.kicad_pcb /tmp/lc.net` |

## PASS: Python compile

Command: `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_pcb_staging.py circuits/check_laser_controller_release_gate.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_schematic_presentation.py circuits/check_power_thermal_budget.py circuits/check_ad7606_package_pcb.py circuits/check_ad7606_interface_budget.py circuits/check_tia_readout_budget.py circuits/check_ap6320x_package_pcb.py circuits/check_buck_input_power_budget.py circuits/check_vin24_input_protection.py circuits/check_usb_vbus_interface.py circuits/check_esp32_reset_boot_controls.py circuits/check_laser_driver_control_loop.py circuits/check_laser_driver_package_pcb.py circuits/check_laser_diode_footprints.py circuits/check_monitor_pd_package_pcb.py circuits/check_laser_current_budget.py circuits/check_laser_monitor_pd_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py`

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
WARN Farnell mirror of Wuerth 65100516121 drawing: reachable; Distributor mirror only; the official Wuerth drawing URL is the required source. [HEAD HTTP 200, type=application/pdf, length=276116]
WARN LCSC C2907002 FRC0603F1001TS 1k resistor page: reachable; Distributor/order source for active 1k 0603 passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C22984 30k resistor page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LCSC C844918 CRCW060310K0FKEA 10k resistor page: reachable; Distributor/order source for active 10k 0603 passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LCSC C114613 RC0603FR-07240RL 240 ohm resistor page: reachable; Distributor/order source for active 240 ohm monitor-PD sense resistor evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LRC L8050QLT1G transistor datasheet: reachable; Manufacturer datasheet for the Q5 NPN SOT-23 auto-reset transistor. [HEAD HTTP 200, type=application/pdf, length=543317]
WARN LCSC C39282 L8550HQLT1G transistor page: reachable; Distributor/order source for the Q6 PNP SOT-23 auto-reset transistor; final AVL should retain a manufacturer datasheet copy. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN LCSC C127509 K2-1102SP-C4SC-04 switch page: reachable; Distributor/order source for the SW1-SW3 tactile reset/program/factory buttons. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C5123624 10 ohm 2512 sense resistor page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
PASS source-document evidence: 22 required online sources, 24 required local artifacts, and 16 secondary/open-risk sources reviewed
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

## PASS: USB connector footprint/source expected fail

Command: `python3 circuits/check_usb_vbus_interface.py --netlist /tmp/lc.net --policy connector-source-match`

```text
FAIL USB connector source/footprint match
  - J1: footprint is Wuerth 65100516121 but BOM metadata is MPN='920-462A2021S10101', LCSC='C46391'; orderable connector/land-pattern fit needs release signoff
  - J2: footprint is Wuerth 65100516121 but BOM metadata is MPN='920-462A2021S10101', LCSC='C46391'; orderable connector/land-pattern fit needs release signoff
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
wrote /tmp/lc_generated_staging.kicad_pcb  (190 blocks, 179 ref instances)
  refs: 179 unique
```

## FAIL: PCB staging assertions

Command: `python3 circuits/check_pcb_staging.py /tmp/lc_generated_staging.kicad_pcb /tmp/lc.net`

```text
FAIL PCB staging
  - Edge.Cuts outline mismatch: expected=[((0.0, 0.0), (90.0, 0.0)), ((0.0, 50.0), (0.0, 0.0)), ((90.0, 0.0), (90.0, 50.0)), ((90.0, 50.0), (0.0, 50.0))] got=[((30.975, 79.875), (204.0, 79.875)), ((30.975, 141.0), (30.975, 79.875)), ((204.0, 79.875), (204.0, 141.0)), ((204.0, 141.0), (30.975, 141.0))]
```
