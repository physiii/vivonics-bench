# Laser Controller Full Net/Pin Inventory

Generated from KiCad exported netlist and the current generated PCB artifact.

Schematic references are generated globally unique before KiCad netlist export. Logical route names such as `LASER_GREEN/R12` are resolved through `circuit_designators.py`; physical net nodes use unique refs such as `R29` and `Q3`.

## PCB Trace State

| Metric | Value |
|---|---:|
| `footprint_objects` | 181 |
| `referenced_footprints` | 0 |
| `unique_references` | 0 |
| `copper_layers` | 4 |
| `segments` | 0 |
| `vias` | 0 |
| `zones` | 0 |
| `pad_net_lines` | 0 |
| `net_table_entries` | 0 |
| `keepout_zones` | 0 |
| `gnd_reference_zone_defs` | 0 |
| `placement_proximity_checks` | 39/111 PASS |
| `intentional_unnetted_pad_instances` | 79 |
| `connected_critical_local_route_links` | 111/111 |
| `multi_pad_nets` | 110 |
| `explicitly_routed_multi_pad_nets` | 108 |
| `unrouted_multi_pad_nets` | 1 |
| `zone_or_rail_pending_multi_pad_nets` | 1 |

### Routed Copper Geometry By Net Class

This table reports the generated routed copper that exists in the current PCB artifact. It does not waive KiCad zone refill, DRC, or manual current-path review.

| Net Class | Segment Widths | Via Size/Drill |
|---|---|---|
| `Laser_Current` | 0.20mm x28, 0.60mm x47, 0.80mm x45 | 1.20/0.60mm x5 |
| `Power_Rails` | 0.15mm x1, 0.20mm x34, 0.22mm x4, 0.25mm x189, 0.30mm x9, 0.50mm x133, 0.60mm x136 | 0.60/0.30mm x64, 1.00/0.50mm x78, 1.00/0.60mm x1 |
| `Switching_Power` | 0.40mm x14 | - |
| `Switcher_Control` | 0.20mm x11 | - |
| `USB` | 0.25mm x49 | 0.60/0.30mm x2 |
| `TIA_Sensitive` | 0.18mm x29, 0.20mm x106 | 0.60/0.30mm x26 |
| `Monitor_ADC` | 0.20mm x302 | 0.60/0.30mm x37 |
| `Laser_Control` | 0.20mm x147 | 0.60/0.30mm x22 |
| `Digital_Control` | 0.20mm x265 | 0.60/0.30mm x36 |

### USB Route Detail

USB is checked as the copied MCU-sheet connector-to-endpoint routed copper chain for each D+/D- leg. The PCB checker fails if either chain exceeds the generated-board length limit, uses vias, leaves F.Cu, changes width, or exceeds the pair-skew limit.

Pair routed-copper skew: 0.00 mm. PASS: USB generated-board route quality gate passed

| Chain | Section | Net | Segments | Length | Geometry | Status |
|---|---|---|---:|---:|---|---|
| `USB-UART D-` | J1 D- to CP2102N D- | `/MCU_ESP32-S3/D-` | 14 | 21.92 mm | B.Cu, F.Cu; widths 0.25 mm; vias 2 | PASS: measured route section is present |
| `USB-UART D-` | total | `-` | 14 | 21.92 mm | B.Cu, F.Cu; widths 0.25 mm; vias 2 | PASS: measured chain is inside generated-board USB limits |
| `USB-UART D+` | J1 D+ to CP2102N D+ | `/MCU_ESP32-S3/D+` | 16 | 20.28 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `USB-UART D+` | total | `-` | 16 | 20.28 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured chain is inside generated-board USB limits |
| `Native USB D-` | J2 D- to ESP32 GPIO19 | `/MCU_ESP32-S3/IO19` | 9 | 26.66 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `Native USB D-` | total | `-` | 9 | 26.66 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured chain is inside generated-board USB limits |
| `Native USB D+` | J2 D+ to ESP32 GPIO20 | `/MCU_ESP32-S3/IO20` | 10 | 26.22 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `Native USB D+` | total | `-` | 10 | 26.22 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured chain is inside generated-board USB limits |

### Laser Current Trace Detail

This table separates the high-current laser cathode/load paths from source-sense feedback copper. Any `BLOCKER` row is routed connectivity evidence only; it is not accepted current-path layout.

| Net | Layer | Width | Segments | Total Length | Role | Status |
|---|---|---:|---:|---:|---|---|
| `/LASER_BLUE/FB` | `F.Cu` | 0.20 mm | 9 | 13.96 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_BLUE/FB` | `F.Cu` | 0.60 mm | 6 | 14.62 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_GREEN/FB` | `F.Cu` | 0.20 mm | 3 | 5.55 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_GREEN/FB` | `F.Cu` | 0.60 mm | 9 | 17.97 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_IR/FB` | `F.Cu` | 0.20 mm | 3 | 6.21 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_IR/FB` | `F.Cu` | 0.60 mm | 9 | 17.70 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_RED/FB` | `F.Cu` | 0.20 mm | 13 | 19.69 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `LASER_N1` | `B.Cu` | 0.60 mm | 3 | 14.64 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N1` | `F.Cu` | 0.60 mm | 2 | 0.95 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N2` | `F.Cu` | 0.60 mm | 7 | 26.54 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N3` | `F.Cu` | 0.60 mm | 7 | 21.30 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N4` | `F.Cu` | 0.60 mm | 4 | 17.56 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_VP` | `B.Cu` | 0.80 mm | 9 | 72.57 mm | laser current net | REVIEW |
| `LASER_VP` | `F.Cu` | 0.80 mm | 21 | 51.19 mm | laser current net | REVIEW |
| `LASER_VP` | `In2.Cu` | 0.80 mm | 15 | 88.73 mm | laser current net | REVIEW |

### Laser Sense Return Detail

Each 10 ohm 2512 source-sense resistor must return into the GND reference plane through a distinct high-current 0.60/0.30 mm via within 6.0 mm of routed GND copper.

| Channel | Sense GND Pad | Routed GND Path | Via | Via Size/Drill | Status |
|---|---|---:|---|---|---|
| `LASER_IR` | `R18.2` | 1.45 mm | `(179.80, 128.18)` | 1.00/0.50 mm | PASS: routed sense return reaches an assigned high-current GND via |
| `LASER_RED` | `R23.2` | 1.53 mm | `(185.05, 91.88)` | 1.00/0.50 mm | PASS: routed sense return reaches an assigned high-current GND via |
| `LASER_GREEN` | `R28.2` | 1.72 mm | `(198.68, 128.10)` | 1.00/0.50 mm | PASS: routed sense return reaches an assigned high-current GND via |
| `LASER_BLUE` | `R33.2` | 1.51 mm | `(168.62, 91.45)` | 1.00/0.50 mm | PASS: routed sense return reaches an assigned high-current GND via |

PCB pad-net assignment, stackup, net classes, and footprint-internal keepouts are present and auditable, but trace-level electrical review is still blocked until placement, routing, board-level zones, and KiCad DRC exist. Current board evidence has no routed segments, no vias, and no board-level zones.

### Reviewed Rail/Zone Pending Nets

These are the only multi-pad nets currently allowed to remain route/zone pending in the current PCB. The PCB checker fails if a different rail or any signal/control net enters this state.

| Net | Pads | Copper Components | Review Status | Required Release Action | Component Groups |
|---|---:|---:|---|---|---|
| `GND` | 166 | 2 | REVIEWED_PENDING | Maintain the signed-off In1.Cu GND reference zone and keep laser-current return paths out of TIA summing-node returns after any reroute. | H1.1, H2.1, D14.1, C67.2, C44.2, C26.2, C55.2, C56.2 ... \| C12.2 |

### Placement Proximity Checks

These generated-board checks keep USB protection, ESP32-S3 support parts, AP2112 decoupling, every TIA input/feedback/decoupling/bias cluster, every laser gate/sense/control/compensation cluster, and every monitor-PD sense/reference/ADC-isolation cluster close to the pins they serve.
Rows marked `REVIEW` exceed generated ideal-placement targets; release gating is handled by the focused geometry, package, DRC, and connectivity checks.

| Check | Actual | Limit | Status |
|---|---:|---:|---|
| USB UART D- connector to ESD | 4.74 mm | 7.50 mm | PASS |
| USB UART D+ connector to ESD | 3.03 mm | 9.50 mm | PASS |
| USB UART D- ESD to CP2102N | 10.77 mm | 10.00 mm | REVIEW |
| USB UART D+ ESD to CP2102N | 11.88 mm | 10.00 mm | REVIEW |
| Native USB D- connector to ESD | 5.25 mm | 7.50 mm | PASS |
| Native USB D+ connector to ESD | 3.38 mm | 9.50 mm | PASS |
| Native USB D- ESD to ESP32 GPIO19 | 18.57 mm | 4.50 mm | REVIEW |
| Native USB D+ ESD to ESP32 GPIO20 | 20.06 mm | 4.50 mm | REVIEW |
| AP2112 input cap at VIN | 2.95 mm | 4.00 mm | PASS |
| AP2112 100n output cap at VOUT | 1.86 mm | 4.00 mm | PASS |
| AP2112 bulk output cap at VOUT | 2.19 mm | 4.00 mm | PASS |
| ESP32 local 3V3 decap | 2.67 mm | 3.00 mm | PASS |
| ESP32 EN capacitor | 44.54 mm | 4.00 mm | REVIEW |
| ESP32 EN pull-up | 44.61 mm | 5.00 mm | REVIEW |
| ESP32 BOOT pull-up | 33.03 mm | 4.00 mm | REVIEW |
| TIA_IR photodiode anode to OPA380 -IN | 2.36 mm | 5.50 mm | PASS |
| TIA_IR feedback trimmer at OPA380 -IN | 6.61 mm | 3.50 mm | REVIEW |
| TIA_IR feedback capacitor at OPA380 -IN | 3.52 mm | 2.50 mm | REVIEW |
| TIA_IR feedback trimmer at OPA380 OUT | 10.95 mm | 4.50 mm | REVIEW |
| TIA_IR feedback capacitor at OPA380 OUT | 5.35 mm | 2.50 mm | REVIEW |
| TIA_IR OPA380 supply decoupling | 7.25 mm | 2.50 mm | REVIEW |
| TIA_IR PD bias resistor at cathode | 23.13 mm | 4.50 mm | REVIEW |
| TIA_IR PD cathode bypass at cathode | 23.20 mm | 3.00 mm | REVIEW |
| TIA_IR VBIAS resistor at OPA380 +IN | 16.36 mm | 5.00 mm | REVIEW |
| TIA_IR VBIAS capacitor at OPA380 +IN | 18.24 mm | 4.00 mm | REVIEW |
| TIA_RED photodiode anode to OPA380 -IN | 2.36 mm | 5.50 mm | PASS |
| TIA_RED feedback trimmer at OPA380 -IN | 6.59 mm | 3.50 mm | REVIEW |
| TIA_RED feedback capacitor at OPA380 -IN | 3.50 mm | 2.50 mm | REVIEW |
| TIA_RED feedback trimmer at OPA380 OUT | 10.93 mm | 4.50 mm | REVIEW |
| TIA_RED feedback capacitor at OPA380 OUT | 5.33 mm | 2.50 mm | REVIEW |
| TIA_RED OPA380 supply decoupling | 7.27 mm | 2.50 mm | REVIEW |
| TIA_RED PD bias resistor at cathode | 14.47 mm | 4.50 mm | REVIEW |
| TIA_RED PD cathode bypass at cathode | 16.16 mm | 3.00 mm | REVIEW |
| TIA_RED VBIAS resistor at OPA380 +IN | 12.10 mm | 5.00 mm | REVIEW |
| TIA_RED VBIAS capacitor at OPA380 +IN | 10.03 mm | 4.00 mm | REVIEW |
| TIA_GREEN photodiode anode to OPA380 -IN | 2.36 mm | 5.50 mm | PASS |
| TIA_GREEN feedback trimmer at OPA380 -IN | 7.11 mm | 3.50 mm | REVIEW |
| TIA_GREEN feedback capacitor at OPA380 -IN | 4.01 mm | 2.50 mm | REVIEW |
| TIA_GREEN feedback trimmer at OPA380 OUT | 11.44 mm | 4.50 mm | REVIEW |
| TIA_GREEN feedback capacitor at OPA380 OUT | 5.79 mm | 2.50 mm | REVIEW |
| TIA_GREEN OPA380 supply decoupling | 6.65 mm | 2.50 mm | REVIEW |
| TIA_GREEN PD bias resistor at cathode | 15.75 mm | 4.50 mm | REVIEW |
| TIA_GREEN PD cathode bypass at cathode | 15.55 mm | 3.00 mm | REVIEW |
| TIA_GREEN VBIAS resistor at OPA380 +IN | 18.61 mm | 5.00 mm | REVIEW |
| TIA_GREEN VBIAS capacitor at OPA380 +IN | 17.25 mm | 4.00 mm | REVIEW |
| TIA_BLUE photodiode anode to OPA380 -IN | 2.36 mm | 5.50 mm | PASS |
| TIA_BLUE feedback trimmer at OPA380 -IN | 7.11 mm | 3.50 mm | REVIEW |
| TIA_BLUE feedback capacitor at OPA380 -IN | 4.01 mm | 2.50 mm | REVIEW |
| TIA_BLUE feedback trimmer at OPA380 OUT | 11.44 mm | 4.50 mm | REVIEW |
| TIA_BLUE feedback capacitor at OPA380 OUT | 5.79 mm | 2.50 mm | REVIEW |
| TIA_BLUE OPA380 supply decoupling | 6.65 mm | 2.50 mm | REVIEW |
| TIA_BLUE PD bias resistor at cathode | 15.31 mm | 4.50 mm | REVIEW |
| TIA_BLUE PD cathode bypass at cathode | 12.52 mm | 3.00 mm | REVIEW |
| TIA_BLUE VBIAS resistor at OPA380 +IN | 15.24 mm | 5.00 mm | REVIEW |
| TIA_BLUE VBIAS capacitor at OPA380 +IN | 13.23 mm | 4.00 mm | REVIEW |
| LASER_IR TLV9001 OUT to gate resistor | 2.70 mm | 3.50 mm | PASS |
| LASER_IR gate resistor to AO3400A gate | 3.33 mm | 2.50 mm | REVIEW |
| LASER_IR AO3400A source to sense resistor | 5.49 mm | 2.20 mm | REVIEW |
| LASER_IR sense feedback to TLV9001 -IN | 3.62 mm | 6.00 mm | PASS |
| LASER_IR isolated ISENSE tap at sense resistor | 2.38 mm | 3.50 mm | PASS |
| LASER_IR TLV9001 supply decoupling | 4.83 mm | 2.50 mm | REVIEW |
| LASER_IR PWM input resistor at TLV9001 +IN | 1.88 mm | 2.50 mm | PASS |
| LASER_IR command limiter at TLV9001 +IN | 4.09 mm | 3.00 mm | REVIEW |
| LASER_IR command filter cap at TLV9001 +IN | 5.80 mm | 3.00 mm | REVIEW |
| LASER_IR compensation cap at TLV9001 -IN | 7.91 mm | 2.50 mm | REVIEW |
| LASER_IR compensation cap at TLV9001 OUT | 3.78 mm | 3.00 mm | REVIEW |
| LASER_RED TLV9001 OUT to gate resistor | 2.70 mm | 3.50 mm | PASS |
| LASER_RED gate resistor to AO3400A gate | 4.26 mm | 2.50 mm | REVIEW |
| LASER_RED AO3400A source to sense resistor | 5.85 mm | 2.20 mm | REVIEW |
| LASER_RED sense feedback to TLV9001 -IN | 3.62 mm | 6.00 mm | PASS |
| LASER_RED isolated ISENSE tap at sense resistor | 2.57 mm | 3.50 mm | PASS |
| LASER_RED TLV9001 supply decoupling | 1.94 mm | 2.50 mm | PASS |
| LASER_RED PWM input resistor at TLV9001 +IN | 2.24 mm | 2.50 mm | PASS |
| LASER_RED command limiter at TLV9001 +IN | 4.09 mm | 3.00 mm | REVIEW |
| LASER_RED command filter cap at TLV9001 +IN | 5.80 mm | 3.00 mm | REVIEW |
| LASER_RED compensation cap at TLV9001 -IN | 5.78 mm | 2.50 mm | REVIEW |
| LASER_RED compensation cap at TLV9001 OUT | 1.92 mm | 3.00 mm | PASS |
| LASER_GREEN TLV9001 OUT to gate resistor | 2.50 mm | 3.50 mm | PASS |
| LASER_GREEN gate resistor to AO3400A gate | 3.15 mm | 2.50 mm | REVIEW |
| LASER_GREEN AO3400A source to sense resistor | 5.49 mm | 2.20 mm | REVIEW |
| LASER_GREEN sense feedback to TLV9001 -IN | 3.62 mm | 6.00 mm | PASS |
| LASER_GREEN isolated ISENSE tap at sense resistor | 2.57 mm | 3.50 mm | PASS |
| LASER_GREEN TLV9001 supply decoupling | 2.26 mm | 2.50 mm | PASS |
| LASER_GREEN PWM input resistor at TLV9001 +IN | 1.88 mm | 2.50 mm | PASS |
| LASER_GREEN command limiter at TLV9001 +IN | 4.09 mm | 3.00 mm | REVIEW |
| LASER_GREEN command filter cap at TLV9001 +IN | 5.80 mm | 3.00 mm | REVIEW |
| LASER_GREEN compensation cap at TLV9001 -IN | 6.79 mm | 2.50 mm | REVIEW |
| LASER_GREEN compensation cap at TLV9001 OUT | 2.42 mm | 3.00 mm | PASS |
| LASER_BLUE TLV9001 OUT to gate resistor | 2.70 mm | 3.50 mm | PASS |
| LASER_BLUE gate resistor to AO3400A gate | 4.41 mm | 2.50 mm | REVIEW |
| LASER_BLUE AO3400A source to sense resistor | 5.77 mm | 2.20 mm | REVIEW |
| LASER_BLUE sense feedback to TLV9001 -IN | 3.62 mm | 6.00 mm | PASS |
| LASER_BLUE isolated ISENSE tap at sense resistor | 2.57 mm | 3.50 mm | PASS |
| LASER_BLUE TLV9001 supply decoupling | 1.91 mm | 2.50 mm | PASS |
| LASER_BLUE PWM input resistor at TLV9001 +IN | 2.24 mm | 2.50 mm | PASS |
| LASER_BLUE command limiter at TLV9001 +IN | 4.09 mm | 3.00 mm | REVIEW |
| LASER_BLUE command filter cap at TLV9001 +IN | 5.80 mm | 3.00 mm | REVIEW |
| LASER_BLUE compensation cap at TLV9001 -IN | 5.78 mm | 2.50 mm | REVIEW |
| LASER_BLUE compensation cap at TLV9001 OUT | 1.92 mm | 3.00 mm | PASS |
| MPD_RAW1 direct LD monitor to sense resistor | 5.86 mm | 4.00 mm | REVIEW |
| MPD_RAW1 sense resistor to INA input | 101.63 mm | 4.00 mm | REVIEW |
| MPD1 ADC resistor to filter capacitor | 1.87 mm | 2.50 mm | PASS |
| MPD_RAW2 direct LD monitor to sense resistor | 16.57 mm | 4.00 mm | REVIEW |
| MPD_RAW2 sense resistor to INA input | 114.43 mm | 4.00 mm | REVIEW |
| MPD2 ADC resistor to filter capacitor | 1.84 mm | 2.50 mm | PASS |
| MPD_RAW3 direct LD monitor to sense resistor | 12.52 mm | 4.00 mm | REVIEW |
| MPD_RAW3 sense resistor to INA input | 105.31 mm | 4.00 mm | REVIEW |
| MPD3 ADC resistor to filter capacitor | 2.63 mm | 2.50 mm | REVIEW |
| MPD_RAW4 spare sense resistor to INA input | 3.55 mm | 4.00 mm | PASS |
| MPD_AMP4 INA output to ADC resistor | 2.06 mm | 4.00 mm | PASS |
| MPD4 ADC resistor to filter capacitor | 1.81 mm | 2.50 mm | PASS |

### Critical Local Route Connectivity

These route-link checks use routed segments, vias, pad copper, and filled zones for the same local clusters. Any `UNROUTED` entries are the next routing targets; they are not waived.

| Route Link | Status |
|---|---|
| USB UART D- connector to ESD | ROUTED |
| USB UART D+ connector to ESD | ROUTED |
| USB UART D- ESD to CP2102N | ROUTED |
| USB UART D+ ESD to CP2102N | ROUTED |
| Native USB D- connector to ESD | ROUTED |
| Native USB D+ connector to ESD | ROUTED |
| Native USB D- ESD to ESP32 GPIO19 | ROUTED |
| Native USB D+ ESD to ESP32 GPIO20 | ROUTED |
| AP2112 input cap at VIN | ROUTED |
| AP2112 100n output cap at VOUT | ROUTED |
| AP2112 bulk output cap at VOUT | ROUTED |
| ESP32 local 3V3 decap | ROUTED |
| ESP32 EN capacitor | ROUTED |
| ESP32 EN pull-up | ROUTED |
| ESP32 BOOT pull-up | ROUTED |
| TIA_IR photodiode anode to OPA380 -IN | ROUTED |
| TIA_IR feedback trimmer at OPA380 -IN | ROUTED |
| TIA_IR feedback capacitor at OPA380 -IN | ROUTED |
| TIA_IR feedback trimmer at OPA380 OUT | ROUTED |
| TIA_IR feedback capacitor at OPA380 OUT | ROUTED |
| TIA_IR OPA380 supply decoupling | ROUTED |
| TIA_IR PD bias resistor at cathode | ROUTED |
| TIA_IR PD cathode bypass at cathode | ROUTED |
| TIA_IR VBIAS resistor at OPA380 +IN | ROUTED |
| TIA_IR VBIAS capacitor at OPA380 +IN | ROUTED |
| TIA_RED photodiode anode to OPA380 -IN | ROUTED |
| TIA_RED feedback trimmer at OPA380 -IN | ROUTED |
| TIA_RED feedback capacitor at OPA380 -IN | ROUTED |
| TIA_RED feedback trimmer at OPA380 OUT | ROUTED |
| TIA_RED feedback capacitor at OPA380 OUT | ROUTED |
| TIA_RED OPA380 supply decoupling | ROUTED |
| TIA_RED PD bias resistor at cathode | ROUTED |
| TIA_RED PD cathode bypass at cathode | ROUTED |
| TIA_RED VBIAS resistor at OPA380 +IN | ROUTED |
| TIA_RED VBIAS capacitor at OPA380 +IN | ROUTED |
| TIA_GREEN photodiode anode to OPA380 -IN | ROUTED |
| TIA_GREEN feedback trimmer at OPA380 -IN | ROUTED |
| TIA_GREEN feedback capacitor at OPA380 -IN | ROUTED |
| TIA_GREEN feedback trimmer at OPA380 OUT | ROUTED |
| TIA_GREEN feedback capacitor at OPA380 OUT | ROUTED |
| TIA_GREEN OPA380 supply decoupling | ROUTED |
| TIA_GREEN PD bias resistor at cathode | ROUTED |
| TIA_GREEN PD cathode bypass at cathode | ROUTED |
| TIA_GREEN VBIAS resistor at OPA380 +IN | ROUTED |
| TIA_GREEN VBIAS capacitor at OPA380 +IN | ROUTED |
| TIA_BLUE photodiode anode to OPA380 -IN | ROUTED |
| TIA_BLUE feedback trimmer at OPA380 -IN | ROUTED |
| TIA_BLUE feedback capacitor at OPA380 -IN | ROUTED |
| TIA_BLUE feedback trimmer at OPA380 OUT | ROUTED |
| TIA_BLUE feedback capacitor at OPA380 OUT | ROUTED |
| TIA_BLUE OPA380 supply decoupling | ROUTED |
| TIA_BLUE PD bias resistor at cathode | ROUTED |
| TIA_BLUE PD cathode bypass at cathode | ROUTED |
| TIA_BLUE VBIAS resistor at OPA380 +IN | ROUTED |
| TIA_BLUE VBIAS capacitor at OPA380 +IN | ROUTED |
| LASER_IR TLV9001 OUT to gate resistor | ROUTED |
| LASER_IR gate resistor to AO3400A gate | ROUTED |
| LASER_IR AO3400A source to sense resistor | ROUTED |
| LASER_IR sense feedback to TLV9001 -IN | ROUTED |
| LASER_IR isolated ISENSE tap at sense resistor | ROUTED |
| LASER_IR TLV9001 supply decoupling | ROUTED |
| LASER_IR PWM input resistor at TLV9001 +IN | ROUTED |
| LASER_IR command limiter at TLV9001 +IN | ROUTED |
| LASER_IR command filter cap at TLV9001 +IN | ROUTED |
| LASER_IR compensation cap at TLV9001 -IN | ROUTED |
| LASER_IR compensation cap at TLV9001 OUT | ROUTED |
| LASER_RED TLV9001 OUT to gate resistor | ROUTED |
| LASER_RED gate resistor to AO3400A gate | ROUTED |
| LASER_RED AO3400A source to sense resistor | ROUTED |
| LASER_RED sense feedback to TLV9001 -IN | ROUTED |
| LASER_RED isolated ISENSE tap at sense resistor | ROUTED |
| LASER_RED TLV9001 supply decoupling | ROUTED |
| LASER_RED PWM input resistor at TLV9001 +IN | ROUTED |
| LASER_RED command limiter at TLV9001 +IN | ROUTED |
| LASER_RED command filter cap at TLV9001 +IN | ROUTED |
| LASER_RED compensation cap at TLV9001 -IN | ROUTED |
| LASER_RED compensation cap at TLV9001 OUT | ROUTED |
| LASER_GREEN TLV9001 OUT to gate resistor | ROUTED |
| LASER_GREEN gate resistor to AO3400A gate | ROUTED |
| LASER_GREEN AO3400A source to sense resistor | ROUTED |
| LASER_GREEN sense feedback to TLV9001 -IN | ROUTED |
| LASER_GREEN isolated ISENSE tap at sense resistor | ROUTED |
| LASER_GREEN TLV9001 supply decoupling | ROUTED |
| LASER_GREEN PWM input resistor at TLV9001 +IN | ROUTED |
| LASER_GREEN command limiter at TLV9001 +IN | ROUTED |
| LASER_GREEN command filter cap at TLV9001 +IN | ROUTED |
| LASER_GREEN compensation cap at TLV9001 -IN | ROUTED |
| LASER_GREEN compensation cap at TLV9001 OUT | ROUTED |
| LASER_BLUE TLV9001 OUT to gate resistor | ROUTED |
| LASER_BLUE gate resistor to AO3400A gate | ROUTED |
| LASER_BLUE AO3400A source to sense resistor | ROUTED |
| LASER_BLUE sense feedback to TLV9001 -IN | ROUTED |
| LASER_BLUE isolated ISENSE tap at sense resistor | ROUTED |
| LASER_BLUE TLV9001 supply decoupling | ROUTED |
| LASER_BLUE PWM input resistor at TLV9001 +IN | ROUTED |
| LASER_BLUE command limiter at TLV9001 +IN | ROUTED |
| LASER_BLUE command filter cap at TLV9001 +IN | ROUTED |
| LASER_BLUE compensation cap at TLV9001 -IN | ROUTED |
| LASER_BLUE compensation cap at TLV9001 OUT | ROUTED |
| MPD_RAW1 direct LD monitor to sense resistor | ROUTED |
| MPD_RAW1 sense resistor to INA input | ROUTED |
| MPD1 ADC resistor to filter capacitor | ROUTED |
| MPD_RAW2 direct LD monitor to sense resistor | ROUTED |
| MPD_RAW2 sense resistor to INA input | ROUTED |
| MPD2 ADC resistor to filter capacitor | ROUTED |
| MPD_RAW3 direct LD monitor to sense resistor | ROUTED |
| MPD_RAW3 sense resistor to INA input | ROUTED |
| MPD3 ADC resistor to filter capacitor | ROUTED |
| MPD_RAW4 spare sense resistor to INA input | ROUTED |
| MPD_AMP4 INA output to ADC resistor | ROUTED |
| MPD4 ADC resistor to filter capacitor | ROUTED |

### Whole-Board Explicit Route Connectivity

This table checks whether every pad on each multi-pad PCB net is connected by explicit routed copper segments. `ZONE_OR_RAIL_PENDING` nets are expected to rely on planes/zones or rail trunks that still require KiCad refill/DRC. `UNROUTED` nets still need board-level routing; critical local links passing does not waive these.

| Net | Pads | Copper Components | Status | Component Groups |
|---|---:|---:|---|---|
| `/TIA_BLUE/VBIAS` | 3 | 2 | UNROUTED | R15.2, U4.3 \| C16.1 |
| `GND` | 166 | 2 | ZONE_OR_RAIL_PENDING | H1.1, H2.1, D14.1, C67.2, C44.2, C26.2, C55.2, C56.2 ... \| C12.2 |
| `+3V3` | 24 | 1 | EXPLICITLY_ROUTED | C55.1, C49.1, C43.1, C47.1, J7.3, J7.4, U14.6, U14.7 ... |
| `+5V` | 41 | 1 | EXPLICITLY_ROUTED | C26.1, C56.1, C23.1, U2.7, R12.1, D6.2, C53.1, U4.7 ... |
| `/LASER_BLUE/CMD_FILTER` | 4 | 1 | EXPLICITLY_ROUTED | U8.3, C27.1, R35.2, R36.1 |
| `/LASER_BLUE/FB` | 5 | 1 | EXPLICITLY_ROUTED | U8.4, Q4.2, R33.1, C28.1, R34.1 |
| `/LASER_BLUE/GATE` | 2 | 1 | EXPLICITLY_ROUTED | Q4.1, R32.2 |
| `/LASER_BLUE/LOUT` | 3 | 1 | EXPLICITLY_ROUTED | U8.1, R32.1, C28.2 |
| `/LASER_GREEN/CMD_FILTER` | 4 | 1 | EXPLICITLY_ROUTED | R30.2, C24.1, U7.3, R31.1 |
| `/LASER_GREEN/FB` | 5 | 1 | EXPLICITLY_ROUTED | R28.1, R29.1, Q3.2, C25.1, U7.4 |
| `/LASER_GREEN/GATE` | 2 | 1 | EXPLICITLY_ROUTED | Q3.1, R27.2 |
| `/LASER_GREEN/LOUT` | 3 | 1 | EXPLICITLY_ROUTED | C25.2, U7.1, R27.1 |
| `/LASER_IR/CMD_FILTER` | 4 | 1 | EXPLICITLY_ROUTED | R21.1, R20.2, C18.1, U5.3 |
| `/LASER_IR/FB` | 5 | 1 | EXPLICITLY_ROUTED | Q1.2, R18.1, R19.1, C19.1, U5.4 |
| `/LASER_IR/GATE` | 2 | 1 | EXPLICITLY_ROUTED | Q1.1, R17.2 |
| `/LASER_IR/LOUT` | 3 | 1 | EXPLICITLY_ROUTED | R17.1, C19.2, U5.1 |
| `/LASER_RED/CMD_FILTER` | 4 | 1 | EXPLICITLY_ROUTED | R25.2, C21.1, R26.1, U6.3 |
| `/LASER_RED/FB` | 5 | 1 | EXPLICITLY_ROUTED | R24.1, C22.1, R23.1, Q2.2, U6.4 |
| `/LASER_RED/GATE` | 2 | 1 | EXPLICITLY_ROUTED | R22.2, Q2.1 |
| `/LASER_RED/LOUT` | 3 | 1 | EXPLICITLY_ROUTED | R22.1, C22.2, U6.1 |
| `/MCU_ESP32-S3/AUTO_BOOT_BASE` | 2 | 1 | EXPLICITLY_ROUTED | Q6.1, R51.2 |
| `/MCU_ESP32-S3/AUTO_EN_BASE` | 2 | 1 | EXPLICITLY_ROUTED | R50.2, Q5.1 |
| `/MCU_ESP32-S3/CP2102_RST` | 2 | 1 | EXPLICITLY_ROUTED | U10.9, R57.2 |
| `/MCU_ESP32-S3/CP2102_SUSPEND_N` | 2 | 1 | EXPLICITLY_ROUTED | U10.11, R58.1 |
| `/MCU_ESP32-S3/CP2102_VBUS` | 4 | 1 | EXPLICITLY_ROUTED | U10.8, R56.2, C45.1, R55.1 |
| `/MCU_ESP32-S3/D+` | 3 | 1 | EXPLICITLY_ROUTED | J1.3, D8.2, U10.4 |
| `/MCU_ESP32-S3/D-` | 3 | 1 | EXPLICITLY_ROUTED | J1.2, D7.2, U10.5 |
| `/MCU_ESP32-S3/DTR` | 3 | 1 | EXPLICITLY_ROUTED | Q6.3, U10.28, R50.1 |
| `/MCU_ESP32-S3/EN` | 6 | 1 | EXPLICITLY_ROUTED | C44.1, U9.3, R54.2, Q5.3, SW1.1, SW1.1 |
| `/MCU_ESP32-S3/FACT` | 4 | 1 | EXPLICITLY_ROUTED | U9.39, SW3.1, SW3.1, R52.2 |
| `/MCU_ESP32-S3/IO13` | 2 | 1 | EXPLICITLY_ROUTED | R60.1, U9.21 |
| `/MCU_ESP32-S3/IO14` | 2 | 1 | EXPLICITLY_ROUTED | U9.22, R59.2 |
| `/MCU_ESP32-S3/IO19` | 3 | 1 | EXPLICITLY_ROUTED | D12.2, J2.2, U9.13 |
| `/MCU_ESP32-S3/IO20` | 3 | 1 | EXPLICITLY_ROUTED | J2.3, U9.14, D11.2 |
| `/MCU_ESP32-S3/IO43` | 2 | 1 | EXPLICITLY_ROUTED | U10.25, U9.37 |
| `/MCU_ESP32-S3/IO44` | 2 | 1 | EXPLICITLY_ROUTED | U10.26, U9.36 |
| `/MCU_ESP32-S3/PROG` | 6 | 1 | EXPLICITLY_ROUTED | C46.1, Q6.2, U9.27, SW2.1, SW2.1, R53.2 |
| `/MCU_ESP32-S3/RTS` | 3 | 1 | EXPLICITLY_ROUTED | U10.24, R51.1, Q5.2 |
| `/MCU_ESP32-S3/USB_NATIVE_CONN_VBUS` | 2 | 1 | EXPLICITLY_ROUTED | J2.1, D13.2 |
| `/MCU_ESP32-S3/USB_UART_CONN_VBUS` | 2 | 1 | EXPLICITLY_ROUTED | J1.1, D10.2 |
| `/POWER_IO/ADC_CREFIN` | 2 | 1 | EXPLICITLY_ROUTED | C59.1, U14.42 |
| `/POWER_IO/ADC_CREG1` | 2 | 1 | EXPLICITLY_ROUTED | U14.36, C57.1 |
| `/POWER_IO/ADC_CREG2` | 2 | 1 | EXPLICITLY_ROUTED | U14.39, C58.1 |
| `/POWER_IO/ADC_REFCAP` | 3 | 1 | EXPLICITLY_ROUTED | U14.44, U14.45, C60.1 |
| `/POWER_IO/BUCK5_BST` | 2 | 1 | EXPLICITLY_ROUTED | C63.2, U15.6 |
| `/POWER_IO/BUCK5_SW` | 3 | 1 | EXPLICITLY_ROUTED | C63.1, L1.1, U15.5 |
| `/POWER_IO/BUCK_5V` | 5 | 1 | EXPLICITLY_ROUTED | D6.1, L1.2, C64.1, U15.1, C65.1 |
| `/POWER_IO/LASER_BUCK_BST` | 2 | 1 | EXPLICITLY_ROUTED | U16.6, C66.2 |
| `/POWER_IO/LASER_BUCK_FB` | 4 | 1 | EXPLICITLY_ROUTED | U16.1, R62.1, R61.2, C69.2 |
| `/POWER_IO/LASER_BUCK_SW` | 3 | 1 | EXPLICITLY_ROUTED | L2.1, U16.5, C66.1 |
| `/POWER_IO/MPD_AMP1` | 2 | 1 | EXPLICITLY_ROUTED | R43.1, U12.1 |
| `/POWER_IO/MPD_AMP2` | 2 | 1 | EXPLICITLY_ROUTED | R45.1, U12.7 |
| `/POWER_IO/MPD_AMP3` | 2 | 1 | EXPLICITLY_ROUTED | R47.1, U12.8 |
| `/POWER_IO/MPD_AMP4` | 2 | 1 | EXPLICITLY_ROUTED | R49.1, U12.14 |
| `/POWER_IO/MPD_BIAS` | 12 | 1 | EXPLICITLY_ROUTED | U13.2, U13.3, R48.2, C36.2, R42.2, R46.2, R44.2, R41.1 ... |
| `/POWER_IO/RJ45_LED_CONTACT` | 2 | 1 | EXPLICITLY_ROUTED | R64.2, J6.12 |
| `/POWER_IO/RJ45_PWR_DETECT` | 2 | 1 | EXPLICITLY_ROUTED | R63.2, J6.10 |
| `/TIA_BLUE/PD_ANODE` | 4 | 1 | EXPLICITLY_ROUTED | RV8.1, C13.1, U4.2, D4.2 |
| `/TIA_BLUE/PD_CATHODE` | 3 | 1 | EXPLICITLY_ROUTED | C15.1, R14.2, D4.1 |
| `/TIA_BLUE/VBIAS_TOP` | 2 | 1 | EXPLICITLY_ROUTED | R16.2, RV4.1 |
| `/TIA_BLUE/VBIAS_WIPER` | 2 | 1 | EXPLICITLY_ROUTED | R15.1, RV4.2 |
| `/TIA_GREEN/PD_ANODE` | 4 | 1 | EXPLICITLY_ROUTED | U3.2, C9.1, RV7.1, D3.2 |
| `/TIA_GREEN/PD_CATHODE` | 3 | 1 | EXPLICITLY_ROUTED | C11.1, R10.2, D3.1 |
| `/TIA_GREEN/VBIAS` | 3 | 1 | EXPLICITLY_ROUTED | U3.3, R11.2, C12.1 |
| `/TIA_GREEN/VBIAS_TOP` | 2 | 1 | EXPLICITLY_ROUTED | R12.2, RV3.1 |
| `/TIA_GREEN/VBIAS_WIPER` | 2 | 1 | EXPLICITLY_ROUTED | R11.1, RV3.2 |
| `/TIA_IR/PD_ANODE` | 4 | 1 | EXPLICITLY_ROUTED | C1.1, RV5.1, U1.2, D1.2 |
| `/TIA_IR/PD_CATHODE` | 3 | 1 | EXPLICITLY_ROUTED | C3.1, R2.2, D1.1 |
| `/TIA_IR/VBIAS` | 3 | 1 | EXPLICITLY_ROUTED | C4.1, R3.2, U1.3 |
| `/TIA_IR/VBIAS_TOP` | 2 | 1 | EXPLICITLY_ROUTED | RV1.1, R4.2 |
| `/TIA_IR/VBIAS_WIPER` | 2 | 1 | EXPLICITLY_ROUTED | RV1.2, R3.1 |
| `/TIA_RED/PD_ANODE` | 4 | 1 | EXPLICITLY_ROUTED | U2.2, C5.1, RV6.1, D2.2 |
| `/TIA_RED/PD_CATHODE` | 3 | 1 | EXPLICITLY_ROUTED | C7.1, R6.2, D2.1 |
| `/TIA_RED/VBIAS` | 3 | 1 | EXPLICITLY_ROUTED | U2.3, C8.1, R7.2 |
| `/TIA_RED/VBIAS_TOP` | 2 | 1 | EXPLICITLY_ROUTED | R8.2, RV2.1 |
| `/TIA_RED/VBIAS_WIPER` | 2 | 1 | EXPLICITLY_ROUTED | R7.1, RV2.2 |
| `ADC_BUSY` | 2 | 1 | EXPLICITLY_ROUTED | U14.14, U9.24 |
| `ADC_CS` | 2 | 1 | EXPLICITLY_ROUTED | U14.13, U9.11 |
| `ADC_MISO_A` | 2 | 1 | EXPLICITLY_ROUTED | U14.24, U9.23 |
| `ADC_MISO_B` | 2 | 1 | EXPLICITLY_ROUTED | U14.25, U9.31 |
| `ADC_RESET` | 2 | 1 | EXPLICITLY_ROUTED | U14.11, U9.25 |
| `ADC_SCLK` | 2 | 1 | EXPLICITLY_ROUTED | U14.12, U9.10 |
| `CONVST` | 3 | 1 | EXPLICITLY_ROUTED | U14.9, U14.10, U9.8 |
| `ISENSE1` | 2 | 1 | EXPLICITLY_ROUTED | R19.2, U9.4 |
| `ISENSE2` | 2 | 1 | EXPLICITLY_ROUTED | R24.2, U9.5 |
| `ISENSE3` | 2 | 1 | EXPLICITLY_ROUTED | R29.2, U9.6 |
| `ISENSE4` | 2 | 1 | EXPLICITLY_ROUTED | R34.2, U9.7 |
| `LASER_N1` | 2 | 1 | EXPLICITLY_ROUTED | Q1.3, LD1.1 |
| `LASER_N2` | 2 | 1 | EXPLICITLY_ROUTED | Q2.3, LD2.1 |
| `LASER_N3` | 2 | 1 | EXPLICITLY_ROUTED | Q3.3, LD3.1 |
| `LASER_N4` | 2 | 1 | EXPLICITLY_ROUTED | Q4.3, LD4.3 |
| `LASER_VP` | 11 | 1 | EXPLICITLY_ROUTED | C67.1, U13.1, C68.1, L2.2, C36.1, R61.1, C69.1, LD1.2 ... |
| `MPD1` | 3 | 1 | EXPLICITLY_ROUTED | C37.1, R43.2, U9.38 |
| `MPD2` | 3 | 1 | EXPLICITLY_ROUTED | C38.1, U9.15, R45.2 |
| `MPD3` | 3 | 1 | EXPLICITLY_ROUTED | C39.1, R47.2, U9.12 |
| `MPD4` | 3 | 1 | EXPLICITLY_ROUTED | R49.2, C40.1, U9.17 |
| `MPD_RAW1` | 3 | 1 | EXPLICITLY_ROUTED | R42.1, U12.3, LD1.3 |
| `MPD_RAW2` | 3 | 1 | EXPLICITLY_ROUTED | R44.1, U12.5, LD2.3 |
| `MPD_RAW3` | 3 | 1 | EXPLICITLY_ROUTED | R46.1, U12.10, LD3.3 |
| `MPD_RAW4` | 2 | 1 | EXPLICITLY_ROUTED | R48.1, U12.12 |
| `PWM1` | 2 | 1 | EXPLICITLY_ROUTED | U9.18, R20.1 |
| `PWM2` | 2 | 1 | EXPLICITLY_ROUTED | R25.1, U9.19 |
| `PWM3` | 2 | 1 | EXPLICITLY_ROUTED | R30.1, U9.20 |
| `PWM4` | 2 | 1 | EXPLICITLY_ROUTED | U9.9, R35.1 |
| `VBUS_5V` | 8 | 1 | EXPLICITLY_ROUTED | D14.2, D10.1, D9.2, C41.1, D5.1, D13.1, C42.1, R55.2 |
| `VIN_24V` | 13 | 1 | EXPLICITLY_ROUTED | C62.1, C61.1, U16.2, U16.3, J7.7, J7.8, U15.2, U15.3 ... |
| `VOUT1` | 5 | 1 | EXPLICITLY_ROUTED | U14.49, C1.2, RV5.2, RV5.3, U1.6 |
| `VOUT2` | 5 | 1 | EXPLICITLY_ROUTED | U2.6, C5.2, U14.51, RV6.2, RV6.3 |
| `VOUT3` | 5 | 1 | EXPLICITLY_ROUTED | U3.6, C9.2, U14.57, RV7.2, RV7.3 |
| `VOUT4` | 5 | 1 | EXPLICITLY_ROUTED | RV8.2, RV8.3, C13.2, U4.6, U14.59 |

## Pin Intent Coverage

Every exported netlist node is assigned a component-pin-level role. This is stricter than net-level intent: it explains why each specific pin belongs on its net.

| Metric | Value |
|---|---:|
| `exported_netlist_nodes` | 591 |
| `pin_intent_roles` | 591 |
| `missing_pin_intent_roles` | 0 |

## Net Inventory

Total exported nets: **156**.

| Net | Nodes | Intent / Review Note |
|---|---|---|
| `+3V3` | `C35.1`, `C43.1`, `C47.1`, `C49.1`, `C50.1`, `C55.1`, `J7.3` `+3V3`, `J7.4` `+3V3`, `R52.1`, `R53.1`, `R54.1`, `R57.1`, `R59.1`, `R60.2`, `R64.1`, `U10.6` `VDD`, `U10.7` `VREGIN`, `U11.5` `VOUT`, `U12.4` `VS`, `U14.23` `VDRIVE`, `U14.34` `REF_SELECT`, `U14.6` `PAR/SER/BYTE_SEL`, `U14.7` `STBY`, `U9.2` `3V3` | ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling. |
| `+5V` | `C10.1`, `C14.1`, `C17.1`, `C2.1`, `C20.1`, `C23.1`, `C26.1`, `C34.1`, `C48.1`, `C51.1`, `C52.1`, `C53.1`, `C54.1`, `C56.1`, `C6.1`, `D5.2` `K`, `D6.2` `K`, `J7.5` `+5V`, `J7.6` `+5V`, `R10.1`, `R12.1`, `R14.1`, `R16.1`, `R2.1`, `R4.1`, `R6.1`, `R8.1`, `U1.7` `V+`, `U11.1` `VIN`, `U11.3` `EN`, `U14.1` `AVCC`, `U14.37` `AVCC`, `U14.38` `AVCC`, `U14.48` `AVCC`, `U2.7` `V+`, `U3.7` `V+`, `U4.7` `V+`, `U5.5` `V+`, `U6.5` `V+`, `U7.5` `V+`, `U8.5` `V+` | Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input. |
| `/LASER_BLUE/CMD_FILTER` | `C27.1`, `R35.2`, `R36.1`, `U8.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `/LASER_BLUE/FB` | `C28.1`, `Q4.2` `S`, `R33.1`, `R34.1`, `U8.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_BLUE/GATE` | `Q4.1` `G`, `R32.2` | AO3400A gate node after TLV9001 output resistor. |
| `/LASER_BLUE/LOUT` | `C28.2`, `R32.1`, `U8.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_GREEN/CMD_FILTER` | `C24.1`, `R30.2`, `R31.1`, `U7.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `/LASER_GREEN/FB` | `C25.1`, `Q3.2` `S`, `R28.1`, `R29.1`, `U7.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_GREEN/GATE` | `Q3.1` `G`, `R27.2` | AO3400A gate node after TLV9001 output resistor. |
| `/LASER_GREEN/LOUT` | `C25.2`, `R27.1`, `U7.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_IR/CMD_FILTER` | `C18.1`, `R20.2`, `R21.1`, `U5.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `/LASER_IR/FB` | `C19.1`, `Q1.2` `S`, `R18.1`, `R19.1`, `U5.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_IR/GATE` | `Q1.1` `G`, `R17.2` | AO3400A gate node after TLV9001 output resistor. |
| `/LASER_IR/LOUT` | `C19.2`, `R17.1`, `U5.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_RED/CMD_FILTER` | `C21.1`, `R25.2`, `R26.1`, `U6.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `/LASER_RED/FB` | `C22.1`, `Q2.2` `S`, `R23.1`, `R24.1`, `U6.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_RED/GATE` | `Q2.1` `G`, `R22.2` | AO3400A gate node after TLV9001 output resistor. |
| `/LASER_RED/LOUT` | `C22.2`, `R22.1`, `U6.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/MCU_ESP32-S3/AUTO_BOOT_BASE` | `Q6.1` `B`, `R51.2` | Copied CP2102N DTR transistor base-drive node for ESP32 GPIO0/BOOT auto-reset sequencing. |
| `/MCU_ESP32-S3/AUTO_EN_BASE` | `Q5.1` `B`, `R50.2` | Copied CP2102N RTS transistor base-drive node for ESP32 EN auto-reset sequencing. |
| `/MCU_ESP32-S3/CP2102_RST` | `R57.2`, `U10.9` `~{RST}` | CP2102N reset pin pull-up node on the copied MCU sheet. |
| `/MCU_ESP32-S3/CP2102_SUSPEND_N` | `R58.1`, `U10.11` `~{SUSPEND}` | CP2102N active-low suspend status pull network on the copied MCU sheet. |
| `/MCU_ESP32-S3/CP2102_VBUS` | `C45.1`, `R55.1`, `R56.2`, `U10.8` `VBUS` | CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet. |
| `/MCU_ESP32-S3/D+` | `D8.2` `A2`, `J1.3` `D+`, `U10.4` `D+` | CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge. |
| `/MCU_ESP32-S3/D-` | `D7.2` `A2`, `J1.2` `D-`, `U10.5` `D-` | CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge. |
| `/MCU_ESP32-S3/DTR` | `Q6.3` `C`, `R50.1`, `U10.28` `~{DTR}` | CP2102N DTR output feeding the copied auto-boot/reset transistor network. |
| `/MCU_ESP32-S3/EN` | `C44.1`, `Q5.3` `C`, `R54.2`, `SW1.1` `1`, `U9.3` `EN` | ESP32-S3 EN reset net with 10 k pull-up, reset button, POR capacitor, and CP2102 auto-reset transistor. |
| `/MCU_ESP32-S3/FACT` | `R52.2`, `SW3.1` `1`, `U9.39` `GPIO1/TOUCH1/ADC1_CH0` | Copied access-controller factory button net on ESP32-S3 GPIO1 with 10 k pull-up. |
| `/MCU_ESP32-S3/IO13` | `R60.1`, `U9.21` `GPIO13/TOUCH13/ADC2_CH2/FSPIQ/FSPIIO7/SUBSPIQ` | Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up. |
| `/MCU_ESP32-S3/IO14` | `R59.2`, `U9.22` `GPIO14/TOUCH14/ADC2_CH3/FSPIWP/FSPIDQS/SUBSPIWP` | Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up. |
| `/MCU_ESP32-S3/IO19` | `D12.2` `A2`, `J2.2` `D-`, `U9.13` `GPIO19/U1RTS/ADC2_CH8/CLK_OUT2/USB_D-` | ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp. |
| `/MCU_ESP32-S3/IO20` | `D11.2` `A2`, `J2.3` `D+`, `U9.14` `GPIO20/U1CTS/ADC2_CH9/CLK_OUT1/USB_D+` | ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp. |
| `/MCU_ESP32-S3/IO43` | `U10.25` `RXD`, `U9.37` `U0TXD/GPIO43/CLK_OUT1` | ESP32-S3 UART0 TX into CP2102N RXD for USB-UART console/programming. |
| `/MCU_ESP32-S3/IO44` | `U10.26` `TXD`, `U9.36` `U0RXD/GPIO44/CLK_OUT2` | CP2102N TXD into ESP32-S3 UART0 RX for USB-UART console/programming. |
| `/MCU_ESP32-S3/PROG` | `C46.1`, `Q6.2` `E`, `R53.2`, `SW2.1` `1`, `U9.27` `GPIO0/BOOT` | ESP32-S3 GPIO0/BOOT program-mode net with pull-up, program button, POR capacitor, and CP2102 auto-boot transistor. |
| `/MCU_ESP32-S3/RTS` | `Q5.2` `E`, `R51.1`, `U10.24` `~{RTS}` | CP2102N RTS output feeding the copied auto-reset transistor network. |
| `/MCU_ESP32-S3/USB_NATIVE_CONN_VBUS` | `D13.2` `A`, `J2.1` `VBUS` | Copied MCU-sheet Mini-B connector VBUS before 1N5819HW isolation diode into the board VBUS_5V net. |
| `/MCU_ESP32-S3/USB_UART_CONN_VBUS` | `D10.2` `A`, `J1.1` `VBUS` | Copied MCU-sheet Mini-B connector VBUS before 1N5819HW isolation diode into the board VBUS_5V net. |
| `/POWER_IO/ADC_CREFIN` | `C59.1`, `U14.42` `REFIN/REFOUT` | AD7606-4 internal/reference output decoupling node at REFIN/REFOUT. |
| `/POWER_IO/ADC_CREG1` | `C57.1`, `U14.36` `REGCAP` | AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin. |
| `/POWER_IO/ADC_CREG2` | `C58.1`, `U14.39` `REGCAP` | AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin. |
| `/POWER_IO/ADC_REFCAP` | `C60.1`, `U14.44` `REFCAPA`, `U14.45` `REFCAPB` | AD7606-4 reference-buffer decoupling node tying REFCAPA and REFCAPB to the local reference capacitor. |
| `/POWER_IO/BUCK5_BST` | `C63.2`, `U15.6` `BST` | AP63205 bootstrap node between U15 BST and the 100 nF capacitor to the switch node. |
| `/POWER_IO/BUCK5_SW` | `C63.1`, `L1.1` `1`, `U15.5` `SW` | AP63205 switch node: U15 SW pin, L1 switch-side pin, and the BST capacitor switch-side plate; keep this copper compact. |
| `/POWER_IO/BUCK_5V` | `C64.1`, `C65.1`, `D6.1` `A`, `L1.2` `2`, `U15.1` `FB` | AP63205 fixed 5 V buck output after L1 and output capacitors, before D6 OR-ing into the board +5 V rail. |
| `/POWER_IO/LASER_BUCK_BST` | `C66.2`, `U16.6` `BST` | AP63200 bootstrap node between U16 BST and the 100 nF capacitor to the laser-buck switch node. |
| `/POWER_IO/LASER_BUCK_FB` | `C69.2`, `R61.2`, `R62.1`, `U16.1` `FB` | AP63200 laser-buck feedback node set by the 237k/22.1k divider and 100 pF feed-forward capacitor for about 9.3 V LASER_VP. |
| `/POWER_IO/LASER_BUCK_SW` | `C66.1`, `L2.1` `1`, `U16.5` `SW` | AP63200 laser-buck switch node: U16 SW pin, L2 switch-side pin, and the BST capacitor switch-side plate; keep away from MPD/TIA nodes. |
| `/POWER_IO/MPD_AMP1` | `R43.1`, `U12.1` `OUT1` | INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter. |
| `/POWER_IO/MPD_AMP2` | `R45.1`, `U12.7` `OUT2` | INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter. |
| `/POWER_IO/MPD_AMP3` | `R47.1`, `U12.8` `OUT3` | INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter. |
| `/POWER_IO/MPD_AMP4` | `R49.1`, `U12.14` `OUT4` | INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter. |
| `/POWER_IO/MPD_BIAS` | `C36.2`, `R41.1`, `R42.2`, `R44.2`, `R46.2`, `R48.2`, `U12.13` `IN-4`, `U12.2` `IN-1`, `U12.6` `IN-2`, `U12.9` `IN-3`, `U13.2` `A`, `U13.3` `*` | LM4040-derived monitor-PD anode bias node; holds LASER_V+ to MPD_BIAS near 5 V. |
| `/POWER_IO/RJ45_LED_CONTACT` | `J6.12`, `R64.2` | RJ45 LED/contact node copied from the access-controller RJ45 convention: J6 pin 12 current-limited to +3V3 through R64. |
| `/POWER_IO/RJ45_PWR_DETECT` | `J6.10`, `R63.2` | RJ45 LED/contact node copied from the access-controller RJ45 convention: J6 pin 10 current-limited to VIN_24V through R63. |
| `/TIA_BLUE/PD_ANODE` | `C13.1`, `D4.2` `A`, `RV8.1`, `U4.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `/TIA_BLUE/PD_CATHODE` | `C15.1`, `D4.1` `K`, `R14.2` | SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor. |
| `/TIA_BLUE/VBIAS` | `C16.1`, `R15.2`, `U4.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `/TIA_BLUE/VBIAS_TOP` | `R16.2`, `RV4.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `/TIA_BLUE/VBIAS_WIPER` | `R15.1`, `RV4.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `/TIA_GREEN/PD_ANODE` | `C9.1`, `D3.2` `A`, `RV7.1`, `U3.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `/TIA_GREEN/PD_CATHODE` | `C11.1`, `D3.1` `K`, `R10.2` | SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor. |
| `/TIA_GREEN/VBIAS` | `C12.1`, `R11.2`, `U3.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `/TIA_GREEN/VBIAS_TOP` | `R12.2`, `RV3.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `/TIA_GREEN/VBIAS_WIPER` | `R11.1`, `RV3.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `/TIA_IR/PD_ANODE` | `C1.1`, `D1.2` `A`, `RV5.1`, `U1.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `/TIA_IR/PD_CATHODE` | `C3.1`, `D1.1` `K`, `R2.2` | SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor. |
| `/TIA_IR/VBIAS` | `C4.1`, `R3.2`, `U1.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `/TIA_IR/VBIAS_TOP` | `R4.2`, `RV1.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `/TIA_IR/VBIAS_WIPER` | `R3.1`, `RV1.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `/TIA_RED/PD_ANODE` | `C5.1`, `D2.2` `A`, `RV6.1`, `U2.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `/TIA_RED/PD_CATHODE` | `C7.1`, `D2.1` `K`, `R6.2` | SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor. |
| `/TIA_RED/VBIAS` | `C8.1`, `R7.2`, `U2.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `/TIA_RED/VBIAS_TOP` | `R8.2`, `RV2.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `/TIA_RED/VBIAS_WIPER` | `R7.1`, `RV2.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `ADC_BUSY` | `U14.14` `BUSY`, `U9.24` `GPIO47/SPICLK_P/SUBSPICLK_P_DIFF` | On-board AD7606-4 BUSY status output into ESP32 GPIO47. |
| `ADC_CS` | `U14.13` `CS`, `U9.11` `GPIO18/U1RXD/ADC2_CH7/CLK_OUT3` | ESP32 GPIO18 chip-select output into the on-board AD7606-4 CS pin. |
| `ADC_MISO_A` | `U14.24` `DB7/DOUTA`, `U9.23` `GPIO21` | On-board AD7606-4 DOUTA serial data output into ESP32 GPIO21. |
| `ADC_MISO_B` | `U14.25` `DB8/DOUTB`, `U9.31` `GPIO38/FSPIWP/SUBSPIWP` | On-board AD7606-4 DOUTB serial data output into ESP32 GPIO38. |
| `ADC_RESET` | `U14.11` `RESET`, `U9.25` `GPIO48/SPICLK_N/SUBSPICLK_N_DIFF` | ESP32 GPIO48 reset output into the on-board AD7606-4 RESET pin. |
| `ADC_SCLK` | `U14.12` `RD/SCLK`, `U9.10` `GPIO17/U1TXD/ADC2_CH6` | ESP32 GPIO17 serial clock into the on-board AD7606-4 RD/SCLK pin. |
| `CONVST` | `U14.10` `CONVSTB`, `U14.9` `CONVSTA`, `U9.8` `GPIO15/U0RTS/ADC2_CH4/XTAL_32K_P` | ESP32 GPIO15 conversion-start output to the on-board AD7606-4 CONVSTA/CONVSTB pins. |
| `GND` | `C10.2`, `C11.2`, `C12.2`, `C14.2`, `C15.2`, `C16.2`, `C17.2`, `C18.2`, `C2.2`, `C20.2`, `C21.2`, `C23.2`, `C24.2`, `C26.2`, `C27.2`, `C3.2`, `C34.2`, `C35.2`, `C37.2`, `C38.2`, `C39.2`, `C4.2`, `C40.2`, `C41.2`, `C42.2`, `C43.2`, `C44.2`, `C45.2`, `C46.2`, `C47.2`, `C48.2`, `C49.2`, `C50.2`, `C51.2`, `C52.2`, `C53.2`, `C54.2`, `C55.2`, `C56.2`, `C57.2`, `C58.2`, `C59.2`, `C6.2`, `C60.2`, `C61.2`, `C62.2`, `C64.2`, `C65.2`, `C67.2`, `C68.2`, `C7.2`, `C70.2` `-`, `C8.2`, `D11.1` `A1`, `D12.1` `A1`, `D14.1` `A1`, `D7.1` `A1`, `D8.1` `A1`, `D9.1` `A1`, `H1.1` `1`, `H2.1` `1`, `J1.5` `GND`, `J1.6` `GND`, `J2.5` `GND`, `J2.6` `GND`, `J5.2` `2`, `J5.3` `3`, `J6.11`, `J6.7`, `J6.8`, `J6.9`, `J7.1` `GND`, `J7.2` `GND`, `R18.2`, `R21.2`, `R23.2`, `R26.2`, `R28.2`, `R31.2`, `R33.2`, `R36.2`, `R41.2`, `R56.1`, `R58.2`, `R62.2`, `RV1.3`, `RV2.3`, `RV3.3`, `RV4.3`, `SW1.2` `2`, `SW2.2` `2`, `SW3.2` `2`, `U1.4` `V-`, `U10.29` `GND`, `U10.3` `GND`, `U11.2` `GND`, `U12.11` `GND`, `U14.16` `DB0`, `U14.17` `DB1`, `U14.18` `DB2`, `U14.19` `DB3`, `U14.2` `AGND`, `U14.20` `DB4`, `U14.21` `DB5`, `U14.22` `DB6`, `U14.26` `AGND`, `U14.27` `DB9`, `U14.28` `DB10`, `U14.29` `DB11`, `U14.3` `OS0`, `U14.30` `DB12`, `U14.31` `DB13`, `U14.32` `DB14/HBEN`, `U14.33` `DB15/BYTE_SEL`, `U14.35` `AGND`, `U14.4` `OS1`, `U14.40` `AGND`, `U14.41` `AGND`, `U14.43` `REFGND`, `U14.46` `REFGND`, `U14.47` `AGND`, `U14.5` `OS2`, `U14.50` `V1GND`, `U14.52` `V2GND`, `U14.53` `AGND`, `U14.54` `AGND`, `U14.55` `AGND`, `U14.56` `AGND`, `U14.58` `V3GND`, `U14.60` `V4GND`, `U14.61` `AGND`, `U14.62` `AGND`, `U14.63` `AGND`, `U14.64` `AGND`, `U14.8` `RANGE`, `U15.4` `GND`, `U16.4` `GND`, `U2.4` `V-`, `U3.4` `V-`, `U4.4` `V-`, `U5.2` `V-`, `U6.2` `V-`, `U7.2` `V-`, `U8.2` `V-`, `U9.1` `GND`, `U9.40` `GND`, `U9.41` `GND` | Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `ISENSE1` | `R19.2`, `U9.4` `GPIO4/TOUCH4/ADC1_CH3` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE2` | `R24.2`, `U9.5` `GPIO5/TOUCH5/ADC1_CH4` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE3` | `R29.2`, `U9.6` `GPIO6/TOUCH6/ADC1_CH5` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE4` | `R34.2`, `U9.7` `GPIO7/TOUCH7/ADC1_CH6` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `LASER_N1` | `LD1.1` `LD_K`, `Q1.3` `D` | Laser cathode sink path from the direct LDx footprint to AO3400A drain. |
| `LASER_N2` | `LD2.1` `LD_K`, `Q2.3` `D` | Laser cathode sink path from the direct LDx footprint to AO3400A drain. |
| `LASER_N3` | `LD3.1` `LD_K`, `Q3.3` `D` | Laser cathode sink path from the direct LDx footprint to AO3400A drain. |
| `LASER_N4` | `LD4.3` `LD_K`, `Q4.3` `D` | Laser cathode sink path from the direct LDx footprint to AO3400A drain. |
| `LASER_VP` | `C36.1`, `C67.1`, `C68.1`, `C69.1`, `L2.2` `2`, `LD1.2` `LD_A/PD_K/CASE`, `LD2.2` `LD_A/PD_K/CASE`, `LD3.2` `LD_A/PD_K/CASE`, `LD4.1` `LD_A`, `R61.1`, `U13.1` `K` | AP63200-generated shared bench laser anode / monitor-PD cathode rail to the direct LDx footprints and LM4040 monitor-bias front end. |
| `MPD1` | `C37.1`, `R43.2`, `U9.38` `GPIO2/TOUCH2/ADC1_CH1` | Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC. |
| `MPD2` | `C38.1`, `R45.2`, `U9.15` `GPIO3/TOUCH3/ADC1_CH2` | Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC. |
| `MPD3` | `C39.1`, `R47.2`, `U9.12` `GPIO8/TOUCH8/ADC1_CH7/SUBSPICS1` | Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC. |
| `MPD4` | `C40.1`, `R49.2`, `U9.17` `GPIO9/TOUCH9/ADC1_CH8/FSPIHD/SUBSPIHD` | Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC. |
| `MPD_RAW1` | `LD1.3` `PD_A`, `R42.1`, `U12.3` `IN+1` | Raw internal monitor-photodiode anode node from the direct LDx footprint into the 240 ohm high-side sense resistor and INA4180 IN+ pin. |
| `MPD_RAW2` | `LD2.3` `PD_A`, `R44.1`, `U12.5` `IN+2` | Raw internal monitor-photodiode anode node from the direct LDx footprint into the 240 ohm high-side sense resistor and INA4180 IN+ pin. |
| `MPD_RAW3` | `LD3.3` `PD_A`, `R46.1`, `U12.10` `IN+3` | Raw internal monitor-photodiode anode node from the direct LDx footprint into the 240 ohm high-side sense resistor and INA4180 IN+ pin. |
| `MPD_RAW4` | `R48.1`, `U12.12` `IN+4` | Spare/open blue-channel monitor input at INA4180 channel 4; PLT5 450GB has no monitor photodiode. |
| `PWM1` | `R20.1`, `U9.18` `GPIO10/TOUCH10/ADC1_CH9/FSPICS0/FSPIIO4/SUBSPICS0` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM2` | `R25.1`, `U9.19` `GPIO11/TOUCH11/ADC2_CH0/FSPID/FSPIIO5/SUBSPID` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM3` | `R30.1`, `U9.20` `GPIO12/TOUCH12/ADC2_CH1/FSPICLK/FSPIIO6/SUBSPICLK` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM4` | `R35.1`, `U9.9` `GPIO16/U0CTS/ADC2_CH5/XTAL_32K_N` | ESP32 PWM command into one laser-driver input resistor. |
| `VBUS_5V` | `C41.1`, `C42.1`, `D10.1` `K`, `D13.1` `K`, `D14.2` `A2`, `D5.1` `A`, `D9.2` `A2`, `R55.2` | Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing. |
| `VIN_24V` | `C61.1`, `C62.1`, `C70.1` `+`, `J5.1` `1`, `J6.4`, `J6.5`, `J7.7` `VIN_24V`, `J7.8` `VIN_24V`, `R63.1`, `U15.2` `EN`, `U15.3` `IN`, `U16.2` `EN`, `U16.3` `IN` | 24 V center-positive barrel/RJ45 input after J5/J6, feeding the AP63205 +5 V buck and AP63200 laser buck input pins and local input capacitors. |
| `VOUT1` | `C1.2`, `RV5.2` `W`, `RV5.3`, `U1.6`, `U14.49` `V1` | OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `VOUT2` | `C5.2`, `RV6.2` `W`, `RV6.3`, `U14.51` `V2`, `U2.6` | OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `VOUT3` | `C9.2`, `RV7.2` `W`, `RV7.3`, `U14.57` `V3`, `U3.6` | OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `VOUT4` | `C13.2`, `RV8.2` `W`, `RV8.3`, `U14.59` `V4`, `U4.6` | OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `unconnected-(J1-ID-Pad4)` | `J1.4` `ID` | Intentional no-connect from generated schematic. |
| `unconnected-(J2-ID-Pad4)` | `J2.4` `ID` | Intentional no-connect from generated schematic. |
| `unconnected-(J6-Pad1)` | `J6.1` | Intentional no-connect from generated schematic. |
| `unconnected-(J6-Pad2)` | `J6.2` | Intentional no-connect from generated schematic. |
| `unconnected-(J6-Pad3)` | `J6.3` | Intentional no-connect from generated schematic. |
| `unconnected-(J6-Pad6)` | `J6.6` | Intentional no-connect from generated schematic. |
| `unconnected-(LD4-CASE-Pad2)` | `LD4.2` `CASE` | Intentional no-connect from generated schematic. |
| `unconnected-(U1-NC-Pad1)` | `U1.1` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U1-NC-Pad5)` | `U1.5` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U1-NC-Pad8)` | `U1.8` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-CHR0-Pad15)` | `U10.15` `CHR0` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-CHR1-Pad14)` | `U10.14` `CHR1` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-CHREN-Pad13)` | `U10.13` `CHREN` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-GPIO.4-Pad22)` | `U10.22` `GPIO.4` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-GPIO.5-Pad21)` | `U10.21` `GPIO.5` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-GPIO.6-Pad20)` | `U10.20` `GPIO.6` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-NC-Pad10)` | `U10.10` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-RS485{slash}GPIO.2-Pad17)` | `U10.17` `RS485/GPIO.2` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-SUSPEND-Pad12)` | `U10.12` `SUSPEND` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-~{CTS}-Pad23)` | `U10.23` `~{CTS}` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-~{DCD}-Pad1)` | `U10.1` `~{DCD}` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-~{DSR}-Pad27)` | `U10.27` `~{DSR}` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-~{RI}{slash}CLK-Pad2)` | `U10.2` `~{RI}/CLK` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-~{RXT}{slash}GPIO.1-Pad18)` | `U10.18` `~{RXT}/GPIO.1` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-~{TXT}{slash}GPIO.0-Pad19)` | `U10.19` `~{TXT}/GPIO.0` | Intentional no-connect from generated schematic. |
| `unconnected-(U10-~{WAKEUP}{slash}GPIO.3-Pad16)` | `U10.16` `~{WAKEUP}/GPIO.3` | Intentional no-connect from generated schematic. |
| `unconnected-(U11-NC-Pad4)` | `U11.4` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U14-FRSTDATA-Pad15)` | `U14.15` `FRSTDATA` | Intentional no-connect from generated schematic. |
| `unconnected-(U2-NC-Pad1)` | `U2.1` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U2-NC-Pad5)` | `U2.5` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U2-NC-Pad8)` | `U2.8` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U3-NC-Pad1)` | `U3.1` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U3-NC-Pad5)` | `U3.5` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U3-NC-Pad8)` | `U3.8` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U4-NC-Pad1)` | `U4.1` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U4-NC-Pad5)` | `U4.5` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U4-NC-Pad8)` | `U4.8` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO45-Pad26)` | `U9.26` `GPIO45` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO46-Pad16)` | `U9.16` `GPIO46` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-MTCK{slash}GPIO39{slash}CLK_OUT3{slash}SUBSPICS1-Pad32)` | `U9.32` `MTCK/GPIO39/CLK_OUT3/SUBSPICS1` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-MTDI{slash}GPIO41{slash}CLK_OUT1-Pad34)` | `U9.34` `MTDI/GPIO41/CLK_OUT1` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-MTDO{slash}GPIO40{slash}CLK_OUT2-Pad33)` | `U9.33` `MTDO/GPIO40/CLK_OUT2` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-MTMS{slash}GPIO42-Pad35)` | `U9.35` `MTMS/GPIO42` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-SPIDQS{slash}GPIO37{slash}FSPIQ{slash}SUBSPIQ-Pad30)` | `U9.30` `SPIDQS/GPIO37/FSPIQ/SUBSPIQ` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-SPIIO6{slash}GPIO35{slash}FSPID{slash}SUBSPID-Pad28)` | `U9.28` `SPIIO6/GPIO35/FSPID/SUBSPID` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-SPIIO7{slash}GPIO36{slash}FSPICLK{slash}SUBSPICLK-Pad29)` | `U9.29` `SPIIO7/GPIO36/FSPICLK/SUBSPICLK` | Intentional no-connect from generated schematic. |

## Component Instance Inventory

Total schematic components: **181**.

| Ref | Sheet | Value | Footprint | LCSC | MPN |
|---|---|---|---|---|---|
| `H1` | `/` | M3 | `MountingHole:MountingHole_3.2mm_M3` |  |  |
| `H2` | `/` | M3 | `MountingHole:MountingHole_3.2mm_M3` |  |  |
| `C26` | `/LASER_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C27` | `/LASER_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C28` | `/LASER_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `LD4` | `/LASER_BLUE/` | PLT5 450GB TO56 LASER CASE | `OptoDevice:LaserDiode_TO56-3` |  | `PLT5 450GB` |
| `Q4` | `/LASER_BLUE/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R32` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R33` | `/LASER_BLUE/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R34` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R35` | `/LASER_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R36` | `/LASER_BLUE/` | 4.7k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C23162` | `0603WAF4701T5E` |
| `U8` | `/LASER_BLUE/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `C398363` | `TLV9001IDBVR` |
| `C23` | `/LASER_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C24` | `/LASER_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C25` | `/LASER_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `LD3` | `/LASER_GREEN/` | PLT5 520EB_P TO56 LASER+MPD | `OptoDevice:LaserDiode_TO56-3` |  | `PLT5 520EB_P` |
| `Q3` | `/LASER_GREEN/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R27` | `/LASER_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R28` | `/LASER_GREEN/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R29` | `/LASER_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R30` | `/LASER_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R31` | `/LASER_GREEN/` | 3k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C4211` | `0603WAF3001T5E` |
| `U7` | `/LASER_GREEN/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `C398363` | `TLV9001IDBVR` |
| `C17` | `/LASER_IR/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C18` | `/LASER_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C19` | `/LASER_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `LD1` | `/LASER_IR/` | D7805I 780nm TO18 STYLE-A LASER+MPD | `OptoDevice:LaserDiode_TO18-D5.6-3` |  | `D7805I` |
| `Q1` | `/LASER_IR/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R17` | `/LASER_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R18` | `/LASER_IR/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R19` | `/LASER_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R20` | `/LASER_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R21` | `/LASER_IR/` | 1.3k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22767` | `0603WAF1301T5E` |
| `U5` | `/LASER_IR/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `C398363` | `TLV9001IDBVR` |
| `C20` | `/LASER_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C21` | `/LASER_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C22` | `/LASER_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `LD2` | `/LASER_RED/` | D6505I 650nm TO18 STYLE-A LASER+MPD | `OptoDevice:LaserDiode_TO18-D5.6-3` |  | `D6505I` |
| `Q2` | `/LASER_RED/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R22` | `/LASER_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R23` | `/LASER_RED/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R24` | `/LASER_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R25` | `/LASER_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R26` | `/LASER_RED/` | 750R LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C23241` | `0603WAF7500T5E` |
| `U6` | `/LASER_RED/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `C398363` | `TLV9001IDBVR` |
| `C41` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `C42` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `C43` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C44` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C45` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C46` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C47` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `D10` | `/MCU_ESP32-S3/` | D_1N5819HW | `Diode_SMD:D_SOD-123` | `C82544` | `1N5819HW-7-F` |
| `D11` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `C5199850` | `LESD5D5.0CT1G(UMW)` |
| `D12` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `C5199850` | `LESD5D5.0CT1G(UMW)` |
| `D13` | `/MCU_ESP32-S3/` | D_1N5819HW | `Diode_SMD:D_SOD-123` | `C82544` | `1N5819HW-7-F` |
| `D14` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `C5199850` | `LESD5D5.0CT1G(UMW)` |
| `D7` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `C5199850` | `LESD5D5.0CT1G(UMW)` |
| `D8` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `C5199850` | `LESD5D5.0CT1G(UMW)` |
| `D9` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `C5199850` | `LESD5D5.0CT1G(UMW)` |
| `J1` | `/MCU_ESP32-S3/` | USB_MINI_B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `C5120592` | `65100516121` |
| `J2` | `/MCU_ESP32-S3/` | USB_MINI_B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `C5120592` | `65100516121` |
| `J7` | `/MCU_ESP32-S3/` | C192300 | `Open_Automation:PinHeader_2x04_P2.54mm_SMD_Vertical_C192300` | `C192300` | `2.54-2*4P` |
| `Q5` | `/MCU_ESP32-S3/` | Q_L8050QLT1G | `Package_TO_SOT_SMD:SOT-23` | `C49581` | `L8050QLT1G` |
| `Q6` | `/MCU_ESP32-S3/` | Q_L8550HQLT1G | `Package_TO_SOT_SMD:SOT-23` | `C39282` | `L8550HQLT1G` |
| `R50` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C191123` | `ERJ2RKF1002X` |
| `R51` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C191123` | `ERJ2RKF1002X` |
| `R52` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C191123` | `ERJ2RKF1002X` |
| `R53` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C191123` | `ERJ2RKF1002X` |
| `R54` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C191123` | `ERJ2RKF1002X` |
| `R55` | `/MCU_ESP32-S3/` | 22.1K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C2929993` | `FRC0402F2212TS` |
| `R56` | `/MCU_ESP32-S3/` | 47.5K | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C23061` | `0603WAF4752T5E` |
| `R57` | `/MCU_ESP32-S3/` | 1K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C852624` | `RT0402BRD071KL` |
| `R58` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C191123` | `ERJ2RKF1002X` |
| `R59` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C191123` | `ERJ2RKF1002X` |
| `R60` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C191123` | `ERJ2RKF1002X` |
| `SW1` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `C127509` | `K2-1102SP-C4SC-04` |
| `SW2` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `C127509` | `K2-1102SP-C4SC-04` |
| `SW3` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `C127509` | `K2-1102SP-C4SC-04` |
| `U10` | `/MCU_ESP32-S3/` | CP2102N-Axx-xQFN28 | `Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm` | `C964632` | `CP2102N-A02-GQFN28R` |
| `U9` | `/MCU_ESP32-S3/` | ESP32-S3-WROOM-1 | `Espressif:ESP32-S3-WROOM-1` | `C2913199` | `ESP32-S3-WROOM-1-N16` |
| `C34` | `/POWER_IO/` | 10uF +5V bulk | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `C35` | `/POWER_IO/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C36` | `/POWER_IO/` | 100nF MPD bias | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C37` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C38` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C39` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C40` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C48` | `/POWER_IO/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C49` | `/POWER_IO/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C50` | `/POWER_IO/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `C51` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C52` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C53` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C54` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C55` | `/POWER_IO/` | 100nF ADC VDRIVE | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C56` | `/POWER_IO/` | 10uF ADC AVCC | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `C57` | `/POWER_IO/` | 1uF ADC REGCAP | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C58` | `/POWER_IO/` | 1uF ADC REGCAP | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C59` | `/POWER_IO/` | 10uF ADC REF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `C60` | `/POWER_IO/` | 10uF ADC REFCAP | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `C61` | `/POWER_IO/` | 10uF 50V | `Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder` | `C89632` | `CL31B106KBHNNNE` |
| `C62` | `/POWER_IO/` | 10uF 50V | `Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder` | `C89632` | `CL31B106KBHNNNE` |
| `C63` | `/POWER_IO/` | 100nF BST | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C64` | `/POWER_IO/` | 22uF 5V buck | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C45783` | `CL21A226MAQNNNE` |
| `C65` | `/POWER_IO/` | 22uF 5V buck | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C45783` | `CL21A226MAQNNNE` |
| `C66` | `/POWER_IO/` | 100nF BST | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C67` | `/POWER_IO/` | 22uF laser buck | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C45783` | `CL21A226MAQNNNE` |
| `C68` | `/POWER_IO/` | 22uF laser buck | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C45783` | `CL21A226MAQNNNE` |
| `C69` | `/POWER_IO/` | 100pF FF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1546` | `0402CG101J500NT` |
| `C70` | `/POWER_IO/` | 22uF 100V | `Capacitor_SMD:C_Elec_8x10.2` | `C242011` | `100CE22FS+P` |
| `D5` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `C2480` | `SS14` |
| `D6` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `C2480` | `SS14` |
| `J5` | `/POWER_IO/` | 24V DC IN | `Open_Automation:BarrelJack_OD5.5_ID2.5` | `C194407` | `DC-470-2.1GP` |
| `J6` | `/POWER_IO/` | CONN_RJ45 | `Connector_RJ:RJ45_Amphenol_RJHSE538X` | `C386757` | `R-RJ45R08P-C000` |
| `L1` | `/POWER_IO/` | 4.7uH | `Open_Automation:L_5.4x5.3_H3` | `C408410` | `MWSA0503S-4R7MT` |
| `L2` | `/POWER_IO/` | 10uH | `Open_Automation:L_4x4` | `C98364` | `WPN4020H100MT` |
| `R41` | `/POWER_IO/` | 2.49k MPD bias | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C103460` | `RTT032491FTP` |
| `R42` | `/POWER_IO/` | 240R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C103446` | `RTT032400FTP` |
| `R43` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R44` | `/POWER_IO/` | 240R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C103446` | `RTT032400FTP` |
| `R45` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R46` | `/POWER_IO/` | 240R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C103446` | `RTT032400FTP` |
| `R47` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R48` | `/POWER_IO/` | 240R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C103446` | `RTT032400FTP` |
| `R49` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R61` | `/POWER_IO/` | 237k FB | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2998117` | `FRC0603F2373TS` |
| `R62` | `/POWER_IO/` | 22.1K FB | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `C2929993` | `FRC0402F2212TS` |
| `R63` | `/POWER_IO/` | 10K | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R64` | `/POWER_IO/` | 10K | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `U11` | `/POWER_IO/` | AP2112K-3.3 | `Package_TO_SOT_SMD:SOT-23-5` | `C51118` | `AP2112K-3.3TRG1` |
| `U12` | `/POWER_IO/` | INA4180A1 | `Package_SO:TSSOP-14_4.4x5mm_P0.65mm` | `C2057528` | `INA4180A1IPWR` |
| `U13` | `/POWER_IO/` | LM4040C50 5V | `Package_TO_SOT_SMD:SOT-23` | `C69316` | `LM4040C50IDBZR` |
| `U14` | `/POWER_IO/` | AD7606BSTZ-4 | `Package_QFP:LQFP-64_10x10mm_P0.5mm` | `C51512` | `AD7606BSTZ-4RL` |
| `U15` | `/POWER_IO/` | AP63205WU-7 5V BUCK | `Package_TO_SOT_SMD:TSOT-23-6` | `C2071056` | `AP63205WU-7` |
| `U16` | `/POWER_IO/` | AP63200WU-7 9.3V BUCK | `Package_TO_SOT_SMD:TSOT-23-6` | `C2071868` | `AP63200WU-7` |
| `C13` | `/TIA_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `C14` | `/TIA_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C15` | `/TIA_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C16` | `/TIA_BLUE/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `D4` | `/TIA_BLUE/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `C2900216` | `SFH2201` |
| `R14` | `/TIA_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R15` | `/TIA_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R16` | `/TIA_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `RV4` | `/TIA_BLUE/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C81348` | `3224W-1-103E` |
| `RV8` | `/TIA_BLUE/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C116323` | `3224W-1-205E` |
| `U4` | `/TIA_BLUE/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `C201677` | `OPA380AID` |
| `C10` | `/TIA_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C11` | `/TIA_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C12` | `/TIA_GREEN/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `C9` | `/TIA_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `D3` | `/TIA_GREEN/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `C2900216` | `SFH2201` |
| `R10` | `/TIA_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R11` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R12` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `RV3` | `/TIA_GREEN/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C81348` | `3224W-1-103E` |
| `RV7` | `/TIA_GREEN/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C116323` | `3224W-1-205E` |
| `U3` | `/TIA_GREEN/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `C201677` | `OPA380AID` |
| `C1` | `/TIA_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `C2` | `/TIA_IR/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C3` | `/TIA_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C4` | `/TIA_IR/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `D1` | `/TIA_IR/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `C2900216` | `SFH2201` |
| `R2` | `/TIA_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R3` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R4` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `RV1` | `/TIA_IR/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C81348` | `3224W-1-103E` |
| `RV5` | `/TIA_IR/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C116323` | `3224W-1-205E` |
| `U1` | `/TIA_IR/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `C201677` | `OPA380AID` |
| `C5` | `/TIA_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `C6` | `/TIA_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C7` | `/TIA_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C8` | `/TIA_RED/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
| `D2` | `/TIA_RED/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `C2900216` | `SFH2201` |
| `R6` | `/TIA_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R7` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R8` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `RV2` | `/TIA_RED/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C81348` | `3224W-1-103E` |
| `RV6` | `/TIA_RED/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C116323` | `3224W-1-205E` |
| `U2` | `/TIA_RED/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `C201677` | `OPA380AID` |

## Pin Coverage By Physical Reference

Each row is a globally unique schematic/PCB designator. No repeated hierarchical local references are expected in the exported netlist.

| Ref | Sheet | Value(s) | Footprint(s) | Pin Nets | Pin Intent |
|---|---|---|---|---|---|
| `C1` | `/TIA_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/TIA_IR/PD_ANODE`<br>`2` -> `VOUT1` | `1` / `/TIA_IR/PD_ANODE`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT1`: Capacitor pin participating in: OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `C10` | `/TIA_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C11` | `/TIA_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/TIA_GREEN/PD_CATHODE`<br>`2` -> `GND` | `1` / `/TIA_GREEN/PD_CATHODE`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C12` | `/TIA_GREEN/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `/TIA_GREEN/VBIAS`<br>`2` -> `GND` | `1` / `/TIA_GREEN/VBIAS`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C13` | `/TIA_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/TIA_BLUE/PD_ANODE`<br>`2` -> `VOUT4` | `1` / `/TIA_BLUE/PD_ANODE`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT4`: Capacitor pin participating in: OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `C14` | `/TIA_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C15` | `/TIA_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/TIA_BLUE/PD_CATHODE`<br>`2` -> `GND` | `1` / `/TIA_BLUE/PD_CATHODE`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C16` | `/TIA_BLUE/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `/TIA_BLUE/VBIAS`<br>`2` -> `GND` | `1` / `/TIA_BLUE/VBIAS`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C17` | `/LASER_IR/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C18` | `/LASER_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/LASER_IR/CMD_FILTER`<br>`2` -> `GND` | `1` / `/LASER_IR/CMD_FILTER`: Capacitor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C19` | `/LASER_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/LASER_IR/FB`<br>`2` -> `/LASER_IR/LOUT` | `1` / `/LASER_IR/FB`: Capacitor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `/LASER_IR/LOUT`: Capacitor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `C2` | `/TIA_IR/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C20` | `/LASER_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C21` | `/LASER_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/LASER_RED/CMD_FILTER`<br>`2` -> `GND` | `1` / `/LASER_RED/CMD_FILTER`: Capacitor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C22` | `/LASER_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/LASER_RED/FB`<br>`2` -> `/LASER_RED/LOUT` | `1` / `/LASER_RED/FB`: Capacitor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `/LASER_RED/LOUT`: Capacitor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `C23` | `/LASER_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C24` | `/LASER_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/LASER_GREEN/CMD_FILTER`<br>`2` -> `GND` | `1` / `/LASER_GREEN/CMD_FILTER`: Capacitor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C25` | `/LASER_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/LASER_GREEN/FB`<br>`2` -> `/LASER_GREEN/LOUT` | `1` / `/LASER_GREEN/FB`: Capacitor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `/LASER_GREEN/LOUT`: Capacitor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `C26` | `/LASER_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C27` | `/LASER_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/LASER_BLUE/CMD_FILTER`<br>`2` -> `GND` | `1` / `/LASER_BLUE/CMD_FILTER`: Capacitor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C28` | `/LASER_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/LASER_BLUE/FB`<br>`2` -> `/LASER_BLUE/LOUT` | `1` / `/LASER_BLUE/FB`: Capacitor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `/LASER_BLUE/LOUT`: Capacitor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `C3` | `/TIA_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/TIA_IR/PD_CATHODE`<br>`2` -> `GND` | `1` / `/TIA_IR/PD_CATHODE`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C34` | `/POWER_IO/` | 10uF +5V bulk | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C35` | `/POWER_IO/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C36` | `/POWER_IO/` | 100nF MPD bias | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `LASER_VP`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `LASER_VP`: Monitor-PD bias-reference capacitor participating in the 5V LASER_V+ to MPD_BIAS shunt reference.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD bias-reference capacitor participating in the 5V LASER_V+ to MPD_BIAS shunt reference. |
| `C37` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `MPD1`<br>`2` -> `GND` | `1` / `MPD1`: Monitor-PD ADC filter capacitor ADC side.<br>`2` / `GND`: Monitor-PD ADC filter capacitor ground return. |
| `C38` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `MPD2`<br>`2` -> `GND` | `1` / `MPD2`: Monitor-PD ADC filter capacitor ADC side.<br>`2` / `GND`: Monitor-PD ADC filter capacitor ground return. |
| `C39` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `MPD3`<br>`2` -> `GND` | `1` / `MPD3`: Monitor-PD ADC filter capacitor ADC side.<br>`2` / `GND`: Monitor-PD ADC filter capacitor ground return. |
| `C4` | `/TIA_IR/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `/TIA_IR/VBIAS`<br>`2` -> `GND` | `1` / `/TIA_IR/VBIAS`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C40` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `MPD4`<br>`2` -> `GND` | `1` / `MPD4`: Monitor-PD ADC filter capacitor ADC side.<br>`2` / `GND`: Monitor-PD ADC filter capacitor ground return. |
| `C41` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `VBUS_5V`<br>`2` -> `GND` | `1` / `VBUS_5V`: Capacitor pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C42` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `VBUS_5V`<br>`2` -> `GND` | `1` / `VBUS_5V`: Capacitor pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C43` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C44` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/MCU_ESP32-S3/EN`<br>`2` -> `GND` | `1` / `/MCU_ESP32-S3/EN`: Capacitor pin participating in: ESP32-S3 EN reset net with 10 k pull-up, reset button, POR capacitor, and CP2102 auto-reset transistor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C45` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/MCU_ESP32-S3/CP2102_VBUS`<br>`2` -> `GND` | `1` / `/MCU_ESP32-S3/CP2102_VBUS`: Capacitor pin participating in: CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C46` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/MCU_ESP32-S3/PROG`<br>`2` -> `GND` | `1` / `/MCU_ESP32-S3/PROG`: Capacitor pin participating in: ESP32-S3 GPIO0/BOOT program-mode net with pull-up, program button, POR capacitor, and CP2102 auto-boot transistor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C47` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C48` | `/POWER_IO/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C49` | `/POWER_IO/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C5` | `/TIA_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/TIA_RED/PD_ANODE`<br>`2` -> `VOUT2` | `1` / `/TIA_RED/PD_ANODE`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT2`: Capacitor pin participating in: OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `C50` | `/POWER_IO/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C51` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C52` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C53` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C54` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C55` | `/POWER_IO/` | 100nF ADC VDRIVE | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C56` | `/POWER_IO/` | 10uF ADC AVCC | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C57` | `/POWER_IO/` | 1uF ADC REGCAP | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/POWER_IO/ADC_CREG1`<br>`2` -> `GND` | `1` / `/POWER_IO/ADC_CREG1`: Capacitor pin participating in: AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C58` | `/POWER_IO/` | 1uF ADC REGCAP | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/POWER_IO/ADC_CREG2`<br>`2` -> `GND` | `1` / `/POWER_IO/ADC_CREG2`: Capacitor pin participating in: AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C59` | `/POWER_IO/` | 10uF ADC REF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `/POWER_IO/ADC_CREFIN`<br>`2` -> `GND` | `1` / `/POWER_IO/ADC_CREFIN`: Capacitor pin participating in: AD7606-4 internal/reference output decoupling node at REFIN/REFOUT.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C6` | `/TIA_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C60` | `/POWER_IO/` | 10uF ADC REFCAP | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `/POWER_IO/ADC_REFCAP`<br>`2` -> `GND` | `1` / `/POWER_IO/ADC_REFCAP`: Capacitor pin participating in: AD7606-4 reference-buffer decoupling node tying REFCAPA and REFCAPB to the local reference capacitor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C61` | `/POWER_IO/` | 10uF 50V | `Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder` | `1` -> `VIN_24V`<br>`2` -> `GND` | `1` / `VIN_24V`: Capacitor pin participating in: 24 V center-positive barrel/RJ45 input after J5/J6, feeding the AP63205 +5 V buck and AP63200 laser buck input pins and local input capacitors.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C62` | `/POWER_IO/` | 10uF 50V | `Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder` | `1` -> `VIN_24V`<br>`2` -> `GND` | `1` / `VIN_24V`: Capacitor pin participating in: 24 V center-positive barrel/RJ45 input after J5/J6, feeding the AP63205 +5 V buck and AP63200 laser buck input pins and local input capacitors.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C63` | `/POWER_IO/` | 100nF BST | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/POWER_IO/BUCK5_SW`<br>`2` -> `/POWER_IO/BUCK5_BST` | `1` / `/POWER_IO/BUCK5_SW`: Power-supply capacitor pin participating in: AP63205 switch node: U15 SW pin, L1 switch-side pin, and the BST capacitor switch-side plate; keep this copper compact.<br>`2` / `/POWER_IO/BUCK5_BST`: Power-supply capacitor pin participating in: AP63205 bootstrap node between U15 BST and the 100 nF capacitor to the switch node. |
| `C64` | `/POWER_IO/` | 22uF 5V buck | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `/POWER_IO/BUCK_5V`<br>`2` -> `GND` | `1` / `/POWER_IO/BUCK_5V`: Capacitor pin participating in: AP63205 fixed 5 V buck output after L1 and output capacitors, before D6 OR-ing into the board +5 V rail.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C65` | `/POWER_IO/` | 22uF 5V buck | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `/POWER_IO/BUCK_5V`<br>`2` -> `GND` | `1` / `/POWER_IO/BUCK_5V`: Capacitor pin participating in: AP63205 fixed 5 V buck output after L1 and output capacitors, before D6 OR-ing into the board +5 V rail.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C66` | `/POWER_IO/` | 100nF BST | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/POWER_IO/LASER_BUCK_SW`<br>`2` -> `/POWER_IO/LASER_BUCK_BST` | `1` / `/POWER_IO/LASER_BUCK_SW`: Power-supply capacitor pin participating in: AP63200 laser-buck switch node: U16 SW pin, L2 switch-side pin, and the BST capacitor switch-side plate; keep away from MPD/TIA nodes.<br>`2` / `/POWER_IO/LASER_BUCK_BST`: Power-supply capacitor pin participating in: AP63200 bootstrap node between U16 BST and the 100 nF capacitor to the laser-buck switch node. |
| `C67` | `/POWER_IO/` | 22uF laser buck | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `LASER_VP`<br>`2` -> `GND` | `1` / `LASER_VP`: Capacitor pin participating in: AP63200-generated shared bench laser anode / monitor-PD cathode rail to the direct LDx footprints and LM4040 monitor-bias front end.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C68` | `/POWER_IO/` | 22uF laser buck | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `LASER_VP`<br>`2` -> `GND` | `1` / `LASER_VP`: Capacitor pin participating in: AP63200-generated shared bench laser anode / monitor-PD cathode rail to the direct LDx footprints and LM4040 monitor-bias front end.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C69` | `/POWER_IO/` | 100pF FF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `LASER_VP`<br>`2` -> `/POWER_IO/LASER_BUCK_FB` | `1` / `LASER_VP`: Power-supply capacitor pin participating in: AP63200-generated shared bench laser anode / monitor-PD cathode rail to the direct LDx footprints and LM4040 monitor-bias front end.<br>`2` / `/POWER_IO/LASER_BUCK_FB`: Power-supply capacitor pin participating in: AP63200 laser-buck feedback node set by the 237k/22.1k divider and 100 pF feed-forward capacitor for about 9.3 V LASER_VP. |
| `C7` | `/TIA_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/TIA_RED/PD_CATHODE`<br>`2` -> `GND` | `1` / `/TIA_RED/PD_CATHODE`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C70` | `/POWER_IO/` | 22uF 100V | `Capacitor_SMD:C_Elec_8x10.2` | `1` `+` -> `VIN_24V`<br>`2` `-` -> `GND` | `1` / `VIN_24V`: Capacitor pin participating in: 24 V center-positive barrel/RJ45 input after J5/J6, feeding the AP63205 +5 V buck and AP63200 laser buck input pins and local input capacitors.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C8` | `/TIA_RED/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `/TIA_RED/VBIAS`<br>`2` -> `GND` | `1` / `/TIA_RED/VBIAS`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `C9` | `/TIA_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/TIA_GREEN/PD_ANODE`<br>`2` -> `VOUT3` | `1` / `/TIA_GREEN/PD_ANODE`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT3`: Capacitor pin participating in: OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `D1` | `/TIA_IR/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `/TIA_IR/PD_CATHODE`<br>`2` `A` -> `/TIA_IR/PD_ANODE` | `1` / `/TIA_IR/PD_CATHODE`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `/TIA_IR/PD_ANODE`: SFH2201 anode into the OPA380 summing node. |
| `D10` | `/MCU_ESP32-S3/` | D_1N5819HW | `Diode_SMD:D_SOD-123` | `1` `K` -> `VBUS_5V`<br>`2` `A` -> `/MCU_ESP32-S3/USB_UART_CONN_VBUS` | `1` / `VBUS_5V`: 1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path.<br>`2` / `/MCU_ESP32-S3/USB_UART_CONN_VBUS`: 1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path. |
| `D11` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `/MCU_ESP32-S3/IO20` | `1` / `GND`: Diode pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/IO20`: Diode pin participating in: ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp. |
| `D12` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `/MCU_ESP32-S3/IO19` | `1` / `GND`: Diode pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/IO19`: Diode pin participating in: ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp. |
| `D13` | `/MCU_ESP32-S3/` | D_1N5819HW | `Diode_SMD:D_SOD-123` | `1` `K` -> `VBUS_5V`<br>`2` `A` -> `/MCU_ESP32-S3/USB_NATIVE_CONN_VBUS` | `1` / `VBUS_5V`: 1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path.<br>`2` / `/MCU_ESP32-S3/USB_NATIVE_CONN_VBUS`: 1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path. |
| `D14` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `VBUS_5V` | `1` / `GND`: Diode pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `VBUS_5V`: Diode pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing. |
| `D2` | `/TIA_RED/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `/TIA_RED/PD_CATHODE`<br>`2` `A` -> `/TIA_RED/PD_ANODE` | `1` / `/TIA_RED/PD_CATHODE`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `/TIA_RED/PD_ANODE`: SFH2201 anode into the OPA380 summing node. |
| `D3` | `/TIA_GREEN/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `/TIA_GREEN/PD_CATHODE`<br>`2` `A` -> `/TIA_GREEN/PD_ANODE` | `1` / `/TIA_GREEN/PD_CATHODE`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `/TIA_GREEN/PD_ANODE`: SFH2201 anode into the OPA380 summing node. |
| `D4` | `/TIA_BLUE/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `/TIA_BLUE/PD_CATHODE`<br>`2` `A` -> `/TIA_BLUE/PD_ANODE` | `1` / `/TIA_BLUE/PD_CATHODE`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `/TIA_BLUE/PD_ANODE`: SFH2201 anode into the OPA380 summing node. |
| `D5` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `1` `A` -> `VBUS_5V`<br>`2` `K` -> `+5V` | `1` / `VBUS_5V`: SS14 anode receives one pre-OR 5V source.<br>`2` / `+5V`: SS14 cathode feeds the post-OR +5V rail. |
| `D6` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `1` `A` -> `/POWER_IO/BUCK_5V`<br>`2` `K` -> `+5V` | `1` / `/POWER_IO/BUCK_5V`: SS14 anode receives one pre-OR 5V source.<br>`2` / `+5V`: SS14 cathode feeds the post-OR +5V rail. |
| `D7` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `/MCU_ESP32-S3/D-` | `1` / `GND`: Diode pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/D-`: Diode pin participating in: CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge. |
| `D8` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `/MCU_ESP32-S3/D+` | `1` / `GND`: Diode pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/D+`: Diode pin participating in: CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge. |
| `D9` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `VBUS_5V` | `1` / `GND`: Diode pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `VBUS_5V`: Diode pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing. |
| `H1` | `/` | M3 | `MountingHole:MountingHole_3.2mm_M3` | `1` `1` -> `GND` | `1` / `GND`: Grounded M3 mounting-hole pad for mechanical mounting and board return reference. |
| `H2` | `/` | M3 | `MountingHole:MountingHole_3.2mm_M3` | `1` `1` -> `GND` | `1` / `GND`: Grounded M3 mounting-hole pad for mechanical mounting and board return reference. |
| `J1` | `/MCU_ESP32-S3/` | USB_MINI_B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `1` `VBUS` -> `/MCU_ESP32-S3/USB_UART_CONN_VBUS`<br>`2` `D-` -> `/MCU_ESP32-S3/D-`<br>`3` `D+` -> `/MCU_ESP32-S3/D+`<br>`4` `ID` -> `unconnected-(J1-ID-Pad4)`<br>`5` `GND` -> `GND`<br>`6` `GND` -> `GND` | `1` / `/MCU_ESP32-S3/USB_UART_CONN_VBUS`: USB Mini-B VBUS entry into copied MCU-sheet VBUS isolation.<br>`2` / `/MCU_ESP32-S3/D-`: USB Mini-B D- connector pin into the copied USB data path.<br>`3` / `/MCU_ESP32-S3/D+`: USB Mini-B D+ connector pin into the copied USB data path.<br>`4` / `unconnected-(J1-ID-Pad4)`: Intentional no-connect for USB_MINI_B pin 4 `ID`.<br>`5` / `GND`: USB Mini-B signal ground.<br>`6` / `GND`: USB Mini-B shield tied to board GND. |
| `J2` | `/MCU_ESP32-S3/` | USB_MINI_B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `1` `VBUS` -> `/MCU_ESP32-S3/USB_NATIVE_CONN_VBUS`<br>`2` `D-` -> `/MCU_ESP32-S3/IO19`<br>`3` `D+` -> `/MCU_ESP32-S3/IO20`<br>`4` `ID` -> `unconnected-(J2-ID-Pad4)`<br>`5` `GND` -> `GND`<br>`6` `GND` -> `GND` | `1` / `/MCU_ESP32-S3/USB_NATIVE_CONN_VBUS`: USB Mini-B VBUS entry into copied MCU-sheet VBUS isolation.<br>`2` / `/MCU_ESP32-S3/IO19`: USB Mini-B D- connector pin into the copied USB data path.<br>`3` / `/MCU_ESP32-S3/IO20`: USB Mini-B D+ connector pin into the copied USB data path.<br>`4` / `unconnected-(J2-ID-Pad4)`: Intentional no-connect for USB_MINI_B pin 4 `ID`.<br>`5` / `GND`: USB Mini-B signal ground.<br>`6` / `GND`: USB Mini-B shield tied to board GND. |
| `J5` | `/POWER_IO/` | 24V DC IN | `Open_Automation:BarrelJack_OD5.5_ID2.5` | `1` `1` -> `VIN_24V`<br>`2` `2` -> `GND`<br>`3` `3` -> `GND` | `1` / `VIN_24V`: Center-positive barrel input pin feeding VIN_24V.<br>`2` / `GND`: Barrel sleeve ground return.<br>`3` / `GND`: Barrel jack switch/sleeve contact tied to board ground, matching the access-controller footprint convention. |
| `J6` | `/POWER_IO/` | CONN_RJ45 | `Connector_RJ:RJ45_Amphenol_RJHSE538X` | `1` -> `unconnected-(J6-Pad1)`<br>`10` -> `/POWER_IO/RJ45_PWR_DETECT`<br>`11` -> `GND`<br>`12` -> `/POWER_IO/RJ45_LED_CONTACT`<br>`2` -> `unconnected-(J6-Pad2)`<br>`3` -> `unconnected-(J6-Pad3)`<br>`4` -> `VIN_24V`<br>`5` -> `VIN_24V`<br>`6` -> `unconnected-(J6-Pad6)`<br>`7` -> `GND`<br>`8` -> `GND`<br>`9` -> `GND` | `1` / `unconnected-(J6-Pad1)`: Intentional no-connect for CONN_RJ45 pin 1.<br>`10` / `/POWER_IO/RJ45_PWR_DETECT`: RJ45 LED/contact pin current-limited to VIN_24V through R63, matching the access-controller RJ45 LED-resistor convention.<br>`11` / `GND`: RJ45 return/shield-related contact tied to GND, copied from the access-controller return convention.<br>`12` / `/POWER_IO/RJ45_LED_CONTACT`: RJ45 LED/contact pin current-limited to +3V3 through R64, matching the access-controller RJ45 LED-resistor convention.<br>`2` / `unconnected-(J6-Pad2)`: Intentional no-connect for CONN_RJ45 pin 2.<br>`3` / `unconnected-(J6-Pad3)`: Intentional no-connect for CONN_RJ45 pin 3.<br>`4` / `VIN_24V`: RJ45 power contact feeding VIN_24V, copied from the access-controller POWER convention.<br>`5` / `VIN_24V`: RJ45 power contact feeding VIN_24V, copied from the access-controller POWER convention.<br>`6` / `unconnected-(J6-Pad6)`: Intentional no-connect for CONN_RJ45 pin 6.<br>`7` / `GND`: RJ45 return contact tied to GND, copied from the access-controller return convention.<br>`8` / `GND`: RJ45 return contact tied to GND, copied from the access-controller return convention.<br>`9` / `GND`: RJ45 return/shield-related contact tied to GND, copied from the access-controller return convention. |
| `J7` | `/MCU_ESP32-S3/` | C192300 | `Open_Automation:PinHeader_2x04_P2.54mm_SMD_Vertical_C192300` | `1` `GND` -> `GND`<br>`2` `GND` -> `GND`<br>`3` `+3V3` -> `+3V3`<br>`4` `+3V3` -> `+3V3`<br>`5` `+5V` -> `+5V`<br>`6` `+5V` -> `+5V`<br>`7` `VIN_24V` -> `VIN_24V`<br>`8` `VIN_24V` -> `VIN_24V` | `1` / `GND`: J7 4x2 SMT utility header ground pin 1.<br>`2` / `GND`: J7 4x2 SMT utility header ground pin 2.<br>`3` / `+3V3`: J7 4x2 SMT utility header +3V3 pin 3.<br>`4` / `+3V3`: J7 4x2 SMT utility header +3V3 pin 4.<br>`5` / `+5V`: J7 4x2 SMT utility header +5V pin 5.<br>`6` / `+5V`: J7 4x2 SMT utility header +5V pin 6.<br>`7` / `VIN_24V`: J7 4x2 SMT utility header VIN_24V pin 7.<br>`8` / `VIN_24V`: J7 4x2 SMT utility header VIN_24V pin 8. |
| `L1` | `/POWER_IO/` | 4.7uH | `Open_Automation:L_5.4x5.3_H3` | `1` `1` -> `/POWER_IO/BUCK5_SW`<br>`2` `2` -> `/POWER_IO/BUCK_5V` | `1` / `/POWER_IO/BUCK5_SW`: 4.7uH buck inductor switch-side pin.<br>`2` / `/POWER_IO/BUCK_5V`: 4.7uH AP63205 output inductor regulated-output side feeding BUCK_5V. |
| `L2` | `/POWER_IO/` | 10uH | `Open_Automation:L_4x4` | `1` `1` -> `/POWER_IO/LASER_BUCK_SW`<br>`2` `2` -> `LASER_VP` | `1` / `/POWER_IO/LASER_BUCK_SW`: 10uH buck inductor switch-side pin.<br>`2` / `LASER_VP`: 10uH buck inductor pin. |
| `LD1` | `/LASER_IR/` | D7805I 780nm TO18 STYLE-A LASER+MPD | `OptoDevice:LaserDiode_TO18-D5.6-3` | `1` `LD_K` -> `LASER_N1`<br>`2` `LD_A/PD_K/CASE` -> `LASER_VP`<br>`3` `PD_A` -> `MPD_RAW1` | `1` / `LASER_N1`: Direct TO-can laser diode cathode tied to the board low-side current-sink net LASER_Nx.<br>`2` / `LASER_VP`: Direct TO-can common laser anode / monitor-PD cathode / case tied to LASER_V+ for PLT/A-code cans.<br>`3` / `MPD_RAW1`: Direct TO-can internal monitor-PD anode exported as MPD_RAWx into the INA4180/LM4040 monitor front end. |
| `LD2` | `/LASER_RED/` | D6505I 650nm TO18 STYLE-A LASER+MPD | `OptoDevice:LaserDiode_TO18-D5.6-3` | `1` `LD_K` -> `LASER_N2`<br>`2` `LD_A/PD_K/CASE` -> `LASER_VP`<br>`3` `PD_A` -> `MPD_RAW2` | `1` / `LASER_N2`: Direct TO-can laser diode cathode tied to the board low-side current-sink net LASER_Nx.<br>`2` / `LASER_VP`: Direct TO-can common laser anode / monitor-PD cathode / case tied to LASER_V+ for PLT/A-code cans.<br>`3` / `MPD_RAW2`: Direct TO-can internal monitor-PD anode exported as MPD_RAWx into the INA4180/LM4040 monitor front end. |
| `LD3` | `/LASER_GREEN/` | PLT5 520EB_P TO56 LASER+MPD | `OptoDevice:LaserDiode_TO56-3` | `1` `LD_K` -> `LASER_N3`<br>`2` `LD_A/PD_K/CASE` -> `LASER_VP`<br>`3` `PD_A` -> `MPD_RAW3` | `1` / `LASER_N3`: Direct TO-can laser diode cathode tied to the board low-side current-sink net LASER_Nx.<br>`2` / `LASER_VP`: Direct TO-can common laser anode / monitor-PD cathode / case tied to LASER_V+ for PLT/A-code cans.<br>`3` / `MPD_RAW3`: Direct TO-can internal monitor-PD anode exported as MPD_RAWx into the INA4180/LM4040 monitor front end. |
| `LD4` | `/LASER_BLUE/` | PLT5 450GB TO56 LASER CASE | `OptoDevice:LaserDiode_TO56-3` | `1` `LD_A` -> `LASER_VP`<br>`2` `CASE` -> `unconnected-(LD4-CASE-Pad2)`<br>`3` `LD_K` -> `LASER_N4` | `1` / `LASER_VP`: Direct TO-can PLT5 450GB laser anode tied to LASER_V+.<br>`2` / `unconnected-(LD4-CASE-Pad2)`: Intentional no-connect for PLT5 450GB TO56 LASER CASE pin 2 `CASE`.<br>`3` / `LASER_N4`: Direct TO-can PLT5 450GB laser cathode tied to the board low-side current-sink net LASER_N4. |
| `Q1` | `/LASER_IR/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `/LASER_IR/GATE`<br>`2` `S` -> `/LASER_IR/FB`<br>`3` `D` -> `LASER_N1` | `1` / `/LASER_IR/GATE`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_IR/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N1`: AO3400A drain as low-side laser cathode sink. |
| `Q2` | `/LASER_RED/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `/LASER_RED/GATE`<br>`2` `S` -> `/LASER_RED/FB`<br>`3` `D` -> `LASER_N2` | `1` / `/LASER_RED/GATE`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_RED/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N2`: AO3400A drain as low-side laser cathode sink. |
| `Q3` | `/LASER_GREEN/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `/LASER_GREEN/GATE`<br>`2` `S` -> `/LASER_GREEN/FB`<br>`3` `D` -> `LASER_N3` | `1` / `/LASER_GREEN/GATE`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_GREEN/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N3`: AO3400A drain as low-side laser cathode sink. |
| `Q4` | `/LASER_BLUE/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `/LASER_BLUE/GATE`<br>`2` `S` -> `/LASER_BLUE/FB`<br>`3` `D` -> `LASER_N4` | `1` / `/LASER_BLUE/GATE`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_BLUE/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N4`: AO3400A drain as low-side laser cathode sink. |
| `Q5` | `/MCU_ESP32-S3/` | Q_L8050QLT1G | `Package_TO_SOT_SMD:SOT-23` | `1` `B` -> `/MCU_ESP32-S3/AUTO_EN_BASE`<br>`2` `E` -> `/MCU_ESP32-S3/RTS`<br>`3` `C` -> `/MCU_ESP32-S3/EN` | `1` / `/MCU_ESP32-S3/AUTO_EN_BASE`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing.<br>`2` / `/MCU_ESP32-S3/RTS`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing.<br>`3` / `/MCU_ESP32-S3/EN`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing. |
| `Q6` | `/MCU_ESP32-S3/` | Q_L8550HQLT1G | `Package_TO_SOT_SMD:SOT-23` | `1` `B` -> `/MCU_ESP32-S3/AUTO_BOOT_BASE`<br>`2` `E` -> `/MCU_ESP32-S3/PROG`<br>`3` `C` -> `/MCU_ESP32-S3/DTR` | `1` / `/MCU_ESP32-S3/AUTO_BOOT_BASE`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing.<br>`2` / `/MCU_ESP32-S3/PROG`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing.<br>`3` / `/MCU_ESP32-S3/DTR`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing. |
| `R10` | `/TIA_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `/TIA_GREEN/PD_CATHODE` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `/TIA_GREEN/PD_CATHODE`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor. |
| `R11` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/TIA_GREEN/VBIAS_WIPER`<br>`2` -> `/TIA_GREEN/VBIAS` | `1` / `/TIA_GREEN/VBIAS_WIPER`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `/TIA_GREEN/VBIAS`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R12` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `/TIA_GREEN/VBIAS_TOP` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `/TIA_GREEN/VBIAS_TOP`: Resistor pin participating in: TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `R14` | `/TIA_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `/TIA_BLUE/PD_CATHODE` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `/TIA_BLUE/PD_CATHODE`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor. |
| `R15` | `/TIA_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/TIA_BLUE/VBIAS_WIPER`<br>`2` -> `/TIA_BLUE/VBIAS` | `1` / `/TIA_BLUE/VBIAS_WIPER`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `/TIA_BLUE/VBIAS`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R16` | `/TIA_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `/TIA_BLUE/VBIAS_TOP` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `/TIA_BLUE/VBIAS_TOP`: Resistor pin participating in: TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `R17` | `/LASER_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_IR/LOUT`<br>`2` -> `/LASER_IR/GATE` | `1` / `/LASER_IR/LOUT`: Resistor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor.<br>`2` / `/LASER_IR/GATE`: Resistor pin participating in: AO3400A gate node after TLV9001 output resistor. |
| `R18` | `/LASER_IR/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `1` -> `/LASER_IR/FB`<br>`2` -> `GND` | `1` / `/LASER_IR/FB`: Laser current-sense resistor high side.<br>`2` / `GND`: Laser current-sense resistor low-side GND return. |
| `R19` | `/LASER_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_IR/FB`<br>`2` -> `ISENSE1` | `1` / `/LASER_IR/FB`: Resistor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `ISENSE1`: Resistor pin participating in: Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `R2` | `/TIA_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `/TIA_IR/PD_CATHODE` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `/TIA_IR/PD_CATHODE`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor. |
| `R20` | `/LASER_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `PWM1`<br>`2` -> `/LASER_IR/CMD_FILTER` | `1` / `PWM1`: Resistor pin participating in: ESP32 PWM command into one laser-driver input resistor.<br>`2` / `/LASER_IR/CMD_FILTER`: Resistor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input. |
| `R21` | `/LASER_IR/` | 1.3k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_IR/CMD_FILTER`<br>`2` -> `GND` | `1` / `/LASER_IR/CMD_FILTER`: PWM command limiter ground leg.<br>`2` / `GND`: PWM command limiter ground leg. |
| `R22` | `/LASER_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_RED/LOUT`<br>`2` -> `/LASER_RED/GATE` | `1` / `/LASER_RED/LOUT`: Resistor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor.<br>`2` / `/LASER_RED/GATE`: Resistor pin participating in: AO3400A gate node after TLV9001 output resistor. |
| `R23` | `/LASER_RED/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `1` -> `/LASER_RED/FB`<br>`2` -> `GND` | `1` / `/LASER_RED/FB`: Laser current-sense resistor high side.<br>`2` / `GND`: Laser current-sense resistor low-side GND return. |
| `R24` | `/LASER_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_RED/FB`<br>`2` -> `ISENSE2` | `1` / `/LASER_RED/FB`: Resistor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `ISENSE2`: Resistor pin participating in: Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `R25` | `/LASER_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `PWM2`<br>`2` -> `/LASER_RED/CMD_FILTER` | `1` / `PWM2`: Resistor pin participating in: ESP32 PWM command into one laser-driver input resistor.<br>`2` / `/LASER_RED/CMD_FILTER`: Resistor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input. |
| `R26` | `/LASER_RED/` | 750R LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_RED/CMD_FILTER`<br>`2` -> `GND` | `1` / `/LASER_RED/CMD_FILTER`: PWM command limiter ground leg.<br>`2` / `GND`: PWM command limiter ground leg. |
| `R27` | `/LASER_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_GREEN/LOUT`<br>`2` -> `/LASER_GREEN/GATE` | `1` / `/LASER_GREEN/LOUT`: Resistor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor.<br>`2` / `/LASER_GREEN/GATE`: Resistor pin participating in: AO3400A gate node after TLV9001 output resistor. |
| `R28` | `/LASER_GREEN/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `1` -> `/LASER_GREEN/FB`<br>`2` -> `GND` | `1` / `/LASER_GREEN/FB`: Laser current-sense resistor high side.<br>`2` / `GND`: Laser current-sense resistor low-side GND return. |
| `R29` | `/LASER_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_GREEN/FB`<br>`2` -> `ISENSE3` | `1` / `/LASER_GREEN/FB`: Resistor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `ISENSE3`: Resistor pin participating in: Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `R3` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/TIA_IR/VBIAS_WIPER`<br>`2` -> `/TIA_IR/VBIAS` | `1` / `/TIA_IR/VBIAS_WIPER`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `/TIA_IR/VBIAS`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R30` | `/LASER_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `PWM3`<br>`2` -> `/LASER_GREEN/CMD_FILTER` | `1` / `PWM3`: Resistor pin participating in: ESP32 PWM command into one laser-driver input resistor.<br>`2` / `/LASER_GREEN/CMD_FILTER`: Resistor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input. |
| `R31` | `/LASER_GREEN/` | 3k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_GREEN/CMD_FILTER`<br>`2` -> `GND` | `1` / `/LASER_GREEN/CMD_FILTER`: PWM command limiter ground leg.<br>`2` / `GND`: PWM command limiter ground leg. |
| `R32` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_BLUE/LOUT`<br>`2` -> `/LASER_BLUE/GATE` | `1` / `/LASER_BLUE/LOUT`: Resistor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor.<br>`2` / `/LASER_BLUE/GATE`: Resistor pin participating in: AO3400A gate node after TLV9001 output resistor. |
| `R33` | `/LASER_BLUE/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `1` -> `/LASER_BLUE/FB`<br>`2` -> `GND` | `1` / `/LASER_BLUE/FB`: Laser current-sense resistor high side.<br>`2` / `GND`: Laser current-sense resistor low-side GND return. |
| `R34` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_BLUE/FB`<br>`2` -> `ISENSE4` | `1` / `/LASER_BLUE/FB`: Resistor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `ISENSE4`: Resistor pin participating in: Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `R35` | `/LASER_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `PWM4`<br>`2` -> `/LASER_BLUE/CMD_FILTER` | `1` / `PWM4`: Resistor pin participating in: ESP32 PWM command into one laser-driver input resistor.<br>`2` / `/LASER_BLUE/CMD_FILTER`: Resistor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input. |
| `R36` | `/LASER_BLUE/` | 4.7k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_BLUE/CMD_FILTER`<br>`2` -> `GND` | `1` / `/LASER_BLUE/CMD_FILTER`: PWM command limiter ground leg.<br>`2` / `GND`: PWM command limiter ground leg. |
| `R4` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `/TIA_IR/VBIAS_TOP` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `/TIA_IR/VBIAS_TOP`: Resistor pin participating in: TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `R41` | `/POWER_IO/` | 2.49k MPD bias | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_BIAS`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_BIAS`: MPD_BIAS sink resistor high side.<br>`2` / `GND`: MPD_BIAS sink resistor ground return. |
| `R42` | `/POWER_IO/` | 240R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD_RAW1`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `MPD_RAW1`: Monitor-PD sense resistor raw direct-laser side.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD sense resistor MPD_BIAS side. |
| `R43` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_AMP1`<br>`2` -> `MPD1` | `1` / `/POWER_IO/MPD_AMP1`: Monitor-PD ADC isolation resistor INA4180 output side.<br>`2` / `MPD1`: Monitor-PD ADC isolation resistor filtered ADC side. |
| `R44` | `/POWER_IO/` | 240R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD_RAW2`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `MPD_RAW2`: Monitor-PD sense resistor raw direct-laser side.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD sense resistor MPD_BIAS side. |
| `R45` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_AMP2`<br>`2` -> `MPD2` | `1` / `/POWER_IO/MPD_AMP2`: Monitor-PD ADC isolation resistor INA4180 output side.<br>`2` / `MPD2`: Monitor-PD ADC isolation resistor filtered ADC side. |
| `R46` | `/POWER_IO/` | 240R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD_RAW3`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `MPD_RAW3`: Monitor-PD sense resistor raw direct-laser side.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD sense resistor MPD_BIAS side. |
| `R47` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_AMP3`<br>`2` -> `MPD3` | `1` / `/POWER_IO/MPD_AMP3`: Monitor-PD ADC isolation resistor INA4180 output side.<br>`2` / `MPD3`: Monitor-PD ADC isolation resistor filtered ADC side. |
| `R48` | `/POWER_IO/` | 240R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD_RAW4`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `MPD_RAW4`: Monitor-PD sense resistor raw direct-laser side.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD sense resistor MPD_BIAS side. |
| `R49` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_AMP4`<br>`2` -> `MPD4` | `1` / `/POWER_IO/MPD_AMP4`: Monitor-PD ADC isolation resistor INA4180 output side.<br>`2` / `MPD4`: Monitor-PD ADC isolation resistor filtered ADC side. |
| `R50` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/MCU_ESP32-S3/DTR`<br>`2` -> `/MCU_ESP32-S3/AUTO_EN_BASE` | `1` / `/MCU_ESP32-S3/DTR`: Resistor pin participating in: CP2102N DTR output feeding the copied auto-boot/reset transistor network.<br>`2` / `/MCU_ESP32-S3/AUTO_EN_BASE`: Resistor pin participating in: Copied CP2102N RTS transistor base-drive node for ESP32 EN auto-reset sequencing. |
| `R51` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/MCU_ESP32-S3/RTS`<br>`2` -> `/MCU_ESP32-S3/AUTO_BOOT_BASE` | `1` / `/MCU_ESP32-S3/RTS`: Resistor pin participating in: CP2102N RTS output feeding the copied auto-reset transistor network.<br>`2` / `/MCU_ESP32-S3/AUTO_BOOT_BASE`: Resistor pin participating in: Copied CP2102N DTR transistor base-drive node for ESP32 GPIO0/BOOT auto-reset sequencing. |
| `R52` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/FACT` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/FACT`: Resistor pin participating in: Copied access-controller factory button net on ESP32-S3 GPIO1 with 10 k pull-up. |
| `R53` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/PROG` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/PROG`: Resistor pin participating in: ESP32-S3 GPIO0/BOOT program-mode net with pull-up, program button, POR capacitor, and CP2102 auto-boot transistor. |
| `R54` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/EN` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/EN`: Resistor pin participating in: ESP32-S3 EN reset net with 10 k pull-up, reset button, POR capacitor, and CP2102 auto-reset transistor. |
| `R55` | `/MCU_ESP32-S3/` | 22.1K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/MCU_ESP32-S3/CP2102_VBUS`<br>`2` -> `VBUS_5V` | `1` / `/MCU_ESP32-S3/CP2102_VBUS`: Resistor pin participating in: CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet.<br>`2` / `VBUS_5V`: Resistor pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing. |
| `R56` | `/MCU_ESP32-S3/` | 47.5K | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `GND`<br>`2` -> `/MCU_ESP32-S3/CP2102_VBUS` | `1` / `GND`: Resistor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/CP2102_VBUS`: Resistor pin participating in: CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet. |
| `R57` | `/MCU_ESP32-S3/` | 1K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/CP2102_RST` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/CP2102_RST`: Resistor pin participating in: CP2102N reset pin pull-up node on the copied MCU sheet. |
| `R58` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/MCU_ESP32-S3/CP2102_SUSPEND_N`<br>`2` -> `GND` | `1` / `/MCU_ESP32-S3/CP2102_SUSPEND_N`: Resistor pin participating in: CP2102N active-low suspend status pull network on the copied MCU sheet.<br>`2` / `GND`: Resistor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `R59` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/IO14` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/IO14`: Resistor pin participating in: Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up. |
| `R6` | `/TIA_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `/TIA_RED/PD_CATHODE` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `/TIA_RED/PD_CATHODE`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through the bias resistor and local bypass capacitor. |
| `R60` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/MCU_ESP32-S3/IO13`<br>`2` -> `+3V3` | `1` / `/MCU_ESP32-S3/IO13`: Resistor pin participating in: Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up.<br>`2` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling. |
| `R61` | `/POWER_IO/` | 237k FB | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `LASER_VP`<br>`2` -> `/POWER_IO/LASER_BUCK_FB` | `1` / `LASER_VP`: AP63200 laser-buck feedback resistor pin participating in: AP63200-generated shared bench laser anode / monitor-PD cathode rail to the direct LDx footprints and LM4040 monitor-bias front end.<br>`2` / `/POWER_IO/LASER_BUCK_FB`: AP63200 laser-buck feedback resistor pin participating in: AP63200 laser-buck feedback node set by the 237k/22.1k divider and 100 pF feed-forward capacitor for about 9.3 V LASER_VP. |
| `R62` | `/POWER_IO/` | 22.1K FB | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/POWER_IO/LASER_BUCK_FB`<br>`2` -> `GND` | `1` / `/POWER_IO/LASER_BUCK_FB`: AP63200 laser-buck feedback resistor pin participating in: AP63200 laser-buck feedback node set by the 237k/22.1k divider and 100 pF feed-forward capacitor for about 9.3 V LASER_VP.<br>`2` / `GND`: AP63200 laser-buck feedback resistor pin participating in: Common board return. The 2026-07-04 return-path signoff covers the current layout; reroutes must keep high-current laser returns away from TIA summing-node return paths. |
| `R63` | `/POWER_IO/` | 10K | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `VIN_24V`<br>`2` -> `/POWER_IO/RJ45_PWR_DETECT` | `1` / `VIN_24V`: Resistor pin participating in: 24 V center-positive barrel/RJ45 input after J5/J6, feeding the AP63205 +5 V buck and AP63200 laser buck input pins and local input capacitors.<br>`2` / `/POWER_IO/RJ45_PWR_DETECT`: Resistor pin participating in: RJ45 LED/contact node copied from the access-controller RJ45 convention: J6 pin 10 current-limited to VIN_24V through R63. |
| `R64` | `/POWER_IO/` | 10K | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/POWER_IO/RJ45_LED_CONTACT` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/POWER_IO/RJ45_LED_CONTACT`: Resistor pin participating in: RJ45 LED/contact node copied from the access-controller RJ45 convention: J6 pin 12 current-limited to +3V3 through R64. |
| `R7` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/TIA_RED/VBIAS_WIPER`<br>`2` -> `/TIA_RED/VBIAS` | `1` / `/TIA_RED/VBIAS_WIPER`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `/TIA_RED/VBIAS`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R8` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `/TIA_RED/VBIAS_TOP` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/AP63205 Schottky OR-ing; feeds analog, laser-driver op amps, AD7606 AVCC, and 3V3 LDO input.<br>`2` / `/TIA_RED/VBIAS_TOP`: Resistor pin participating in: TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `RV1` | `/TIA_IR/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `/TIA_IR/VBIAS_TOP`<br>`2` `W` -> `/TIA_IR/VBIAS_WIPER`<br>`3` -> `GND` | `1` / `/TIA_IR/VBIAS_TOP`: Bourns trimmer high-side VBIAS adjustment node.<br>`2` / `/TIA_IR/VBIAS_WIPER`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV2` | `/TIA_RED/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `/TIA_RED/VBIAS_TOP`<br>`2` `W` -> `/TIA_RED/VBIAS_WIPER`<br>`3` -> `GND` | `1` / `/TIA_RED/VBIAS_TOP`: Bourns trimmer high-side VBIAS adjustment node.<br>`2` / `/TIA_RED/VBIAS_WIPER`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV3` | `/TIA_GREEN/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `/TIA_GREEN/VBIAS_TOP`<br>`2` `W` -> `/TIA_GREEN/VBIAS_WIPER`<br>`3` -> `GND` | `1` / `/TIA_GREEN/VBIAS_TOP`: Bourns trimmer high-side VBIAS adjustment node.<br>`2` / `/TIA_GREEN/VBIAS_WIPER`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV4` | `/TIA_BLUE/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `/TIA_BLUE/VBIAS_TOP`<br>`2` `W` -> `/TIA_BLUE/VBIAS_WIPER`<br>`3` -> `GND` | `1` / `/TIA_BLUE/VBIAS_TOP`: Bourns trimmer high-side VBIAS adjustment node.<br>`2` / `/TIA_BLUE/VBIAS_WIPER`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV5` | `/TIA_IR/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `/TIA_IR/PD_ANODE`<br>`2` `W` -> `VOUT1`<br>`3` -> `VOUT1` | `1` / `/TIA_IR/PD_ANODE`: Bourns feedback trimmer low side tied to the OPA380 summing node.<br>`2` / `VOUT1`: Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.<br>`3` / `VOUT1`: Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input. |
| `RV6` | `/TIA_RED/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `/TIA_RED/PD_ANODE`<br>`2` `W` -> `VOUT2`<br>`3` -> `VOUT2` | `1` / `/TIA_RED/PD_ANODE`: Bourns feedback trimmer low side tied to the OPA380 summing node.<br>`2` / `VOUT2`: Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.<br>`3` / `VOUT2`: Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input. |
| `RV7` | `/TIA_GREEN/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `/TIA_GREEN/PD_ANODE`<br>`2` `W` -> `VOUT3`<br>`3` -> `VOUT3` | `1` / `/TIA_GREEN/PD_ANODE`: Bourns feedback trimmer low side tied to the OPA380 summing node.<br>`2` / `VOUT3`: Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.<br>`3` / `VOUT3`: Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input. |
| `RV8` | `/TIA_BLUE/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `/TIA_BLUE/PD_ANODE`<br>`2` `W` -> `VOUT4`<br>`3` -> `VOUT4` | `1` / `/TIA_BLUE/PD_ANODE`: Bourns feedback trimmer low side tied to the OPA380 summing node.<br>`2` / `VOUT4`: Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.<br>`3` / `VOUT4`: Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input. |
| `SW1` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `1` `1` -> `/MCU_ESP32-S3/EN`<br>`2` `2` -> `GND` | `1` / `/MCU_ESP32-S3/EN`: Copied MCU pushbutton signal contact.<br>`2` / `GND`: Copied MCU pushbutton ground contact. |
| `SW2` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `1` `1` -> `/MCU_ESP32-S3/PROG`<br>`2` `2` -> `GND` | `1` / `/MCU_ESP32-S3/PROG`: Copied MCU pushbutton signal contact.<br>`2` / `GND`: Copied MCU pushbutton ground contact. |
| `SW3` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `1` `1` -> `/MCU_ESP32-S3/FACT`<br>`2` `2` -> `GND` | `1` / `/MCU_ESP32-S3/FACT`: Copied MCU pushbutton signal contact.<br>`2` / `GND`: Copied MCU pushbutton ground contact. |
| `U1` | `/TIA_IR/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U1-NC-Pad1)`<br>`2` `-` -> `/TIA_IR/PD_ANODE`<br>`3` `+` -> `/TIA_IR/VBIAS`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U1-NC-Pad5)`<br>`6` -> `VOUT1`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U1-NC-Pad8)` | `1` / `unconnected-(U1-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `/TIA_IR/PD_ANODE`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `/TIA_IR/VBIAS`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U1-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT1`: OPA380 TIA output to feedback high side and on-board AD7606 input.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U1-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U10` | `/MCU_ESP32-S3/` | CP2102N-Axx-xQFN28 | `Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm` | `1` `~{DCD}` -> `unconnected-(U10-~{DCD}-Pad1)`<br>`10` `NC` -> `unconnected-(U10-NC-Pad10)`<br>`11` `~{SUSPEND}` -> `/MCU_ESP32-S3/CP2102_SUSPEND_N`<br>`12` `SUSPEND` -> `unconnected-(U10-SUSPEND-Pad12)`<br>`13` `CHREN` -> `unconnected-(U10-CHREN-Pad13)`<br>`14` `CHR1` -> `unconnected-(U10-CHR1-Pad14)`<br>`15` `CHR0` -> `unconnected-(U10-CHR0-Pad15)`<br>`16` `~{WAKEUP}/GPIO.3` -> `unconnected-(U10-~{WAKEUP}{slash}GPIO.3-Pad16)`<br>`17` `RS485/GPIO.2` -> `unconnected-(U10-RS485{slash}GPIO.2-Pad17)`<br>`18` `~{RXT}/GPIO.1` -> `unconnected-(U10-~{RXT}{slash}GPIO.1-Pad18)`<br>`19` `~{TXT}/GPIO.0` -> `unconnected-(U10-~{TXT}{slash}GPIO.0-Pad19)`<br>`2` `~{RI}/CLK` -> `unconnected-(U10-~{RI}{slash}CLK-Pad2)`<br>`20` `GPIO.6` -> `unconnected-(U10-GPIO.6-Pad20)`<br>`21` `GPIO.5` -> `unconnected-(U10-GPIO.5-Pad21)`<br>`22` `GPIO.4` -> `unconnected-(U10-GPIO.4-Pad22)`<br>`23` `~{CTS}` -> `unconnected-(U10-~{CTS}-Pad23)`<br>`24` `~{RTS}` -> `/MCU_ESP32-S3/RTS`<br>`25` `RXD` -> `/MCU_ESP32-S3/IO43`<br>`26` `TXD` -> `/MCU_ESP32-S3/IO44`<br>`27` `~{DSR}` -> `unconnected-(U10-~{DSR}-Pad27)`<br>`28` `~{DTR}` -> `/MCU_ESP32-S3/DTR`<br>`29` `GND` -> `GND`<br>`3` `GND` -> `GND`<br>`4` `D+` -> `/MCU_ESP32-S3/D+`<br>`5` `D-` -> `/MCU_ESP32-S3/D-`<br>`6` `VDD` -> `+3V3`<br>`7` `VREGIN` -> `+3V3`<br>`8` `VBUS` -> `/MCU_ESP32-S3/CP2102_VBUS`<br>`9` `~{RST}` -> `/MCU_ESP32-S3/CP2102_RST` | `1` / `unconnected-(U10-~{DCD}-Pad1)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 1 `~{DCD}`.<br>`10` / `unconnected-(U10-NC-Pad10)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 10 `NC`.<br>`11` / `/MCU_ESP32-S3/CP2102_SUSPEND_N`: CP2102N active-low suspend status output with pull network.<br>`12` / `unconnected-(U10-SUSPEND-Pad12)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 12 `SUSPEND`.<br>`13` / `unconnected-(U10-CHREN-Pad13)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 13 `CHREN`.<br>`14` / `unconnected-(U10-CHR1-Pad14)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 14 `CHR1`.<br>`15` / `unconnected-(U10-CHR0-Pad15)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 15 `CHR0`.<br>`16` / `unconnected-(U10-~{WAKEUP}{slash}GPIO.3-Pad16)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 16 `~{WAKEUP}/GPIO.3`.<br>`17` / `unconnected-(U10-RS485{slash}GPIO.2-Pad17)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 17 `RS485/GPIO.2`.<br>`18` / `unconnected-(U10-~{RXT}{slash}GPIO.1-Pad18)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 18 `~{RXT}/GPIO.1`.<br>`19` / `unconnected-(U10-~{TXT}{slash}GPIO.0-Pad19)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 19 `~{TXT}/GPIO.0`.<br>`2` / `unconnected-(U10-~{RI}{slash}CLK-Pad2)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 2 `~{RI}/CLK`.<br>`20` / `unconnected-(U10-GPIO.6-Pad20)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 20 `GPIO.6`.<br>`21` / `unconnected-(U10-GPIO.5-Pad21)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 21 `GPIO.5`.<br>`22` / `unconnected-(U10-GPIO.4-Pad22)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 22 `GPIO.4`.<br>`23` / `unconnected-(U10-~{CTS}-Pad23)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 23 `~{CTS}`.<br>`24` / `/MCU_ESP32-S3/RTS`: CP2102N RTS output into the ESP32 auto-reset transistor network.<br>`25` / `/MCU_ESP32-S3/IO43`: CP2102N RXD input from ESP32 UART0 TX.<br>`26` / `/MCU_ESP32-S3/IO44`: CP2102N TXD output into ESP32 UART0 RX.<br>`27` / `unconnected-(U10-~{DSR}-Pad27)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 27 `~{DSR}`.<br>`28` / `/MCU_ESP32-S3/DTR`: CP2102N DTR output into the ESP32 auto-boot/reset transistor network.<br>`29` / `GND`: CP2102N exposed-pad ground.<br>`3` / `GND`: CP2102N ground pin.<br>`4` / `/MCU_ESP32-S3/D+`: CP2102N USB D+ pin on the copied Mini-B USB bridge path.<br>`5` / `/MCU_ESP32-S3/D-`: CP2102N USB D- pin on the copied Mini-B USB bridge path.<br>`6` / `+3V3`: CP2102N VDD supply tied to board +3V3.<br>`7` / `+3V3`: CP2102N VREGIN tied to board +3V3 for self-powered operation.<br>`8` / `/MCU_ESP32-S3/CP2102_VBUS`: CP2102N VBUS sense input from the copied USB VBUS divider/bypass node.<br>`9` / `/MCU_ESP32-S3/CP2102_RST`: CP2102N reset input with pull-up. |
| `U11` | `/POWER_IO/` | AP2112K-3.3 | `Package_TO_SOT_SMD:SOT-23-5` | `1` `VIN` -> `+5V`<br>`2` `GND` -> `GND`<br>`3` `EN` -> `+5V`<br>`4` `NC` -> `unconnected-(U11-NC-Pad4)`<br>`5` `VOUT` -> `+3V3` | `1` / `+5V`: AP2112 VIN from post-OR +5V rail.<br>`2` / `GND`: AP2112 ground return.<br>`3` / `+5V`: AP2112 enable tied high to +5V for always-on bench 3V3.<br>`4` / `unconnected-(U11-NC-Pad4)`: Intentional no-connect for AP2112K-3.3 pin 4 `NC`.<br>`5` / `+3V3`: AP2112 regulated +3V3 output. |
| `U12` | `/POWER_IO/` | INA4180A1 | `Package_SO:TSSOP-14_4.4x5mm_P0.65mm` | `1` `OUT1` -> `/POWER_IO/MPD_AMP1`<br>`10` `IN+3` -> `MPD_RAW3`<br>`11` `GND` -> `GND`<br>`12` `IN+4` -> `MPD_RAW4`<br>`13` `IN-4` -> `/POWER_IO/MPD_BIAS`<br>`14` `OUT4` -> `/POWER_IO/MPD_AMP4`<br>`2` `IN-1` -> `/POWER_IO/MPD_BIAS`<br>`3` `IN+1` -> `MPD_RAW1`<br>`4` `VS` -> `+3V3`<br>`5` `IN+2` -> `MPD_RAW2`<br>`6` `IN-2` -> `/POWER_IO/MPD_BIAS`<br>`7` `OUT2` -> `/POWER_IO/MPD_AMP2`<br>`8` `OUT3` -> `/POWER_IO/MPD_AMP3`<br>`9` `IN-3` -> `/POWER_IO/MPD_BIAS` | `1` / `/POWER_IO/MPD_AMP1`: INA4180 channel 1 output to the MPD1 ADC RC filter.<br>`10` / `MPD_RAW3`: INA4180 channel 3 positive input on MPD_RAW3.<br>`11` / `GND`: INA4180 ground reference for ADC output accuracy.<br>`12` / `MPD_RAW4`: INA4180 channel 4 positive input on spare/open MPD_RAW4.<br>`13` / `/POWER_IO/MPD_BIAS`: INA4180 channel 4 negative input on MPD_BIAS.<br>`14` / `/POWER_IO/MPD_AMP4`: INA4180 channel 4 output to the MPD4 ADC RC filter.<br>`2` / `/POWER_IO/MPD_BIAS`: INA4180 channel 1 negative input on MPD_BIAS, the load side of the monitor sense resistor.<br>`3` / `MPD_RAW1`: INA4180 channel 1 positive input on MPD_RAW1, the laser monitor-PD anode side of the sense resistor.<br>`4` / `+3V3`: INA4180 3.3 V supply.<br>`5` / `MPD_RAW2`: INA4180 channel 2 positive input on MPD_RAW2.<br>`6` / `/POWER_IO/MPD_BIAS`: INA4180 channel 2 negative input on MPD_BIAS.<br>`7` / `/POWER_IO/MPD_AMP2`: INA4180 channel 2 output to the MPD2 ADC RC filter.<br>`8` / `/POWER_IO/MPD_AMP3`: INA4180 channel 3 output to the MPD3 ADC RC filter.<br>`9` / `/POWER_IO/MPD_BIAS`: INA4180 channel 3 negative input on MPD_BIAS. |
| `U13` | `/POWER_IO/` | LM4040C50 5V | `Package_TO_SOT_SMD:SOT-23` | `1` `K` -> `LASER_VP`<br>`2` `A` -> `/POWER_IO/MPD_BIAS`<br>`3` `*` -> `/POWER_IO/MPD_BIAS` | `1` / `LASER_VP`: LM4040 cathode tied to LASER_V+ so the reference clamps the high-side monitor-bias drop.<br>`2` / `/POWER_IO/MPD_BIAS`: LM4040 anode tied to MPD_BIAS.<br>`3` / `/POWER_IO/MPD_BIAS`: LM4040 star pin tied to anode/MPD_BIAS per TI guidance for noisy environments. |
| `U14` | `/POWER_IO/` | AD7606BSTZ-4 | `Package_QFP:LQFP-64_10x10mm_P0.5mm` | `1` `AVCC` -> `+5V`<br>`10` `CONVSTB` -> `CONVST`<br>`11` `RESET` -> `ADC_RESET`<br>`12` `RD/SCLK` -> `ADC_SCLK`<br>`13` `CS` -> `ADC_CS`<br>`14` `BUSY` -> `ADC_BUSY`<br>`15` `FRSTDATA` -> `unconnected-(U14-FRSTDATA-Pad15)`<br>`16` `DB0` -> `GND`<br>`17` `DB1` -> `GND`<br>`18` `DB2` -> `GND`<br>`19` `DB3` -> `GND`<br>`2` `AGND` -> `GND`<br>`20` `DB4` -> `GND`<br>`21` `DB5` -> `GND`<br>`22` `DB6` -> `GND`<br>`23` `VDRIVE` -> `+3V3`<br>`24` `DB7/DOUTA` -> `ADC_MISO_A`<br>`25` `DB8/DOUTB` -> `ADC_MISO_B`<br>`26` `AGND` -> `GND`<br>`27` `DB9` -> `GND`<br>`28` `DB10` -> `GND`<br>`29` `DB11` -> `GND`<br>`3` `OS0` -> `GND`<br>`30` `DB12` -> `GND`<br>`31` `DB13` -> `GND`<br>`32` `DB14/HBEN` -> `GND`<br>`33` `DB15/BYTE_SEL` -> `GND`<br>`34` `REF_SELECT` -> `+3V3`<br>`35` `AGND` -> `GND`<br>`36` `REGCAP` -> `/POWER_IO/ADC_CREG1`<br>`37` `AVCC` -> `+5V`<br>`38` `AVCC` -> `+5V`<br>`39` `REGCAP` -> `/POWER_IO/ADC_CREG2`<br>`4` `OS1` -> `GND`<br>`40` `AGND` -> `GND`<br>`41` `AGND` -> `GND`<br>`42` `REFIN/REFOUT` -> `/POWER_IO/ADC_CREFIN`<br>`43` `REFGND` -> `GND`<br>`44` `REFCAPA` -> `/POWER_IO/ADC_REFCAP`<br>`45` `REFCAPB` -> `/POWER_IO/ADC_REFCAP`<br>`46` `REFGND` -> `GND`<br>`47` `AGND` -> `GND`<br>`48` `AVCC` -> `+5V`<br>`49` `V1` -> `VOUT1`<br>`5` `OS2` -> `GND`<br>`50` `V1GND` -> `GND`<br>`51` `V2` -> `VOUT2`<br>`52` `V2GND` -> `GND`<br>`53` `AGND` -> `GND`<br>`54` `AGND` -> `GND`<br>`55` `AGND` -> `GND`<br>`56` `AGND` -> `GND`<br>`57` `V3` -> `VOUT3`<br>`58` `V3GND` -> `GND`<br>`59` `V4` -> `VOUT4`<br>`6` `PAR/SER/BYTE_SEL` -> `+3V3`<br>`60` `V4GND` -> `GND`<br>`61` `AGND` -> `GND`<br>`62` `AGND` -> `GND`<br>`63` `AGND` -> `GND`<br>`64` `AGND` -> `GND`<br>`7` `STBY` -> `+3V3`<br>`8` `RANGE` -> `GND`<br>`9` `CONVSTA` -> `CONVST` | `1` / `+5V`: AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling.<br>`10` / `CONVST`: AD7606-4 conversion-start input; CONVSTA and CONVSTB are tied together for simultaneous sampling.<br>`11` / `ADC_RESET`: AD7606-4 RESET input from ESP32 GPIO48.<br>`12` / `ADC_SCLK`: AD7606-4 RD/SCLK serial clock input from ESP32 GPIO17.<br>`13` / `ADC_CS`: AD7606-4 chip-select input from ESP32 GPIO18.<br>`14` / `ADC_BUSY`: AD7606-4 BUSY conversion-status output to ESP32 GPIO47.<br>`15` / `unconnected-(U14-FRSTDATA-Pad15)`: Intentional no-connect for AD7606BSTZ-4 pin 15 `FRSTDATA`.<br>`16` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`17` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`18` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`19` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`2` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`20` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`21` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`22` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`23` / `+3V3`: AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain.<br>`24` / `ADC_MISO_A`: AD7606-4 DOUTA serial data output to ESP32 GPIO21.<br>`25` / `ADC_MISO_B`: AD7606-4 DOUTB serial data output to ESP32 GPIO38.<br>`26` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`27` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`28` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`29` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`3` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`30` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`31` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`32` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`33` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`34` / `+3V3`: AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain.<br>`35` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`36` / `/POWER_IO/ADC_CREG1`: AD7606-4 internal regulator capacitor pin.<br>`37` / `+5V`: AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling.<br>`38` / `+5V`: AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling.<br>`39` / `/POWER_IO/ADC_CREG2`: AD7606-4 internal regulator capacitor pin.<br>`4` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`40` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`41` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`42` / `/POWER_IO/ADC_CREFIN`: AD7606-4 internal/reference output pin decoupled by the local reference capacitor.<br>`43` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`44` / `/POWER_IO/ADC_REFCAP`: AD7606-4 reference-buffer capacitor pin.<br>`45` / `/POWER_IO/ADC_REFCAP`: AD7606-4 reference-buffer capacitor pin.<br>`46` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`47` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`48` / `+5V`: AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling.<br>`49` / `VOUT1`: AD7606-4 analog input pin for one OPA380 TIA output channel.<br>`5` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`50` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`51` / `VOUT2`: AD7606-4 analog input pin for one OPA380 TIA output channel.<br>`52` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`53` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`54` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`55` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`56` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`57` / `VOUT3`: AD7606-4 analog input pin for one OPA380 TIA output channel.<br>`58` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`59` / `VOUT4`: AD7606-4 analog input pin for one OPA380 TIA output channel.<br>`6` / `+3V3`: AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain.<br>`60` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`61` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`62` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`63` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`64` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`7` / `+3V3`: AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain.<br>`8` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`9` / `CONVST`: AD7606-4 conversion-start input; CONVSTA and CONVSTB are tied together for simultaneous sampling. |
| `U15` | `/POWER_IO/` | AP63205WU-7 5V BUCK | `Package_TO_SOT_SMD:TSOT-23-6` | `1` `FB` -> `/POWER_IO/BUCK_5V`<br>`2` `EN` -> `VIN_24V`<br>`3` `IN` -> `VIN_24V`<br>`4` `GND` -> `GND`<br>`5` `SW` -> `/POWER_IO/BUCK5_SW`<br>`6` `BST` -> `/POWER_IO/BUCK5_BST` | `1` / `/POWER_IO/BUCK_5V`: AP63205 fixed-output FB pin tied to the BUCK_5V output node after L1.<br>`2` / `VIN_24V`: AP63205 EN tied to VIN_24V for always-on 5 V buck operation when the barrel/RJ45 input is present.<br>`3` / `VIN_24V`: AP63205 VIN from the protected 24 V barrel/RJ45 input.<br>`4` / `GND`: AP63205 ground return.<br>`5` / `/POWER_IO/BUCK5_SW`: AP63205 SW switch node into L1 and the bootstrap capacitor.<br>`6` / `/POWER_IO/BUCK5_BST`: AP63205 BST bootstrap pin with 100 nF to SW. |
| `U16` | `/POWER_IO/` | AP63200WU-7 9.3V BUCK | `Package_TO_SOT_SMD:TSOT-23-6` | `1` `FB` -> `/POWER_IO/LASER_BUCK_FB`<br>`2` `EN` -> `VIN_24V`<br>`3` `IN` -> `VIN_24V`<br>`4` `GND` -> `GND`<br>`5` `SW` -> `/POWER_IO/LASER_BUCK_SW`<br>`6` `BST` -> `/POWER_IO/LASER_BUCK_BST` | `1` / `/POWER_IO/LASER_BUCK_FB`: AP63200 feedback pin at the 237k/22.1k divider midpoint for the 9.3 V laser rail.<br>`2` / `VIN_24V`: AP63200 EN tied to VIN_24V for always-on laser buck operation when the barrel/RJ45 input is present.<br>`3` / `VIN_24V`: AP63200 VIN from the protected 24 V barrel/RJ45 input.<br>`4` / `GND`: AP63200 ground return.<br>`5` / `/POWER_IO/LASER_BUCK_SW`: AP63200 SW switch node into L2 and the bootstrap capacitor.<br>`6` / `/POWER_IO/LASER_BUCK_BST`: AP63200 BST bootstrap pin with 100 nF to SW. |
| `U2` | `/TIA_RED/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U2-NC-Pad1)`<br>`2` `-` -> `/TIA_RED/PD_ANODE`<br>`3` `+` -> `/TIA_RED/VBIAS`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U2-NC-Pad5)`<br>`6` -> `VOUT2`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U2-NC-Pad8)` | `1` / `unconnected-(U2-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `/TIA_RED/PD_ANODE`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `/TIA_RED/VBIAS`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U2-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT2`: OPA380 TIA output to feedback high side and on-board AD7606 input.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U2-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U3` | `/TIA_GREEN/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U3-NC-Pad1)`<br>`2` `-` -> `/TIA_GREEN/PD_ANODE`<br>`3` `+` -> `/TIA_GREEN/VBIAS`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U3-NC-Pad5)`<br>`6` -> `VOUT3`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U3-NC-Pad8)` | `1` / `unconnected-(U3-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `/TIA_GREEN/PD_ANODE`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `/TIA_GREEN/VBIAS`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U3-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT3`: OPA380 TIA output to feedback high side and on-board AD7606 input.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U3-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U4` | `/TIA_BLUE/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U4-NC-Pad1)`<br>`2` `-` -> `/TIA_BLUE/PD_ANODE`<br>`3` `+` -> `/TIA_BLUE/VBIAS`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U4-NC-Pad5)`<br>`6` -> `VOUT4`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U4-NC-Pad8)` | `1` / `unconnected-(U4-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `/TIA_BLUE/PD_ANODE`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `/TIA_BLUE/VBIAS`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U4-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT4`: OPA380 TIA output to feedback high side and on-board AD7606 input.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U4-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U5` | `/LASER_IR/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_IR/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `/LASER_IR/CMD_FILTER`<br>`4` `-` -> `/LASER_IR/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_IR/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `/LASER_IR/CMD_FILTER`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_IR/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U6` | `/LASER_RED/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_RED/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `/LASER_RED/CMD_FILTER`<br>`4` `-` -> `/LASER_RED/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_RED/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `/LASER_RED/CMD_FILTER`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_RED/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U7` | `/LASER_GREEN/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_GREEN/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `/LASER_GREEN/CMD_FILTER`<br>`4` `-` -> `/LASER_GREEN/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_GREEN/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `/LASER_GREEN/CMD_FILTER`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_GREEN/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U8` | `/LASER_BLUE/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_BLUE/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `/LASER_BLUE/CMD_FILTER`<br>`4` `-` -> `/LASER_BLUE/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_BLUE/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `/LASER_BLUE/CMD_FILTER`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_BLUE/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U9` | `/MCU_ESP32-S3/` | ESP32-S3-WROOM-1 | `Espressif:ESP32-S3-WROOM-1` | `1` `GND` -> `GND`<br>`10` `GPIO17/U1TXD/ADC2_CH6` -> `ADC_SCLK`<br>`11` `GPIO18/U1RXD/ADC2_CH7/CLK_OUT3` -> `ADC_CS`<br>`12` `GPIO8/TOUCH8/ADC1_CH7/SUBSPICS1` -> `MPD3`<br>`13` `GPIO19/U1RTS/ADC2_CH8/CLK_OUT2/USB_D-` -> `/MCU_ESP32-S3/IO19`<br>`14` `GPIO20/U1CTS/ADC2_CH9/CLK_OUT1/USB_D+` -> `/MCU_ESP32-S3/IO20`<br>`15` `GPIO3/TOUCH3/ADC1_CH2` -> `MPD2`<br>`16` `GPIO46` -> `unconnected-(U9-GPIO46-Pad16)`<br>`17` `GPIO9/TOUCH9/ADC1_CH8/FSPIHD/SUBSPIHD` -> `MPD4`<br>`18` `GPIO10/TOUCH10/ADC1_CH9/FSPICS0/FSPIIO4/SUBSPICS0` -> `PWM1`<br>`19` `GPIO11/TOUCH11/ADC2_CH0/FSPID/FSPIIO5/SUBSPID` -> `PWM2`<br>`2` `3V3` -> `+3V3`<br>`20` `GPIO12/TOUCH12/ADC2_CH1/FSPICLK/FSPIIO6/SUBSPICLK` -> `PWM3`<br>`21` `GPIO13/TOUCH13/ADC2_CH2/FSPIQ/FSPIIO7/SUBSPIQ` -> `/MCU_ESP32-S3/IO13`<br>`22` `GPIO14/TOUCH14/ADC2_CH3/FSPIWP/FSPIDQS/SUBSPIWP` -> `/MCU_ESP32-S3/IO14`<br>`23` `GPIO21` -> `ADC_MISO_A`<br>`24` `GPIO47/SPICLK_P/SUBSPICLK_P_DIFF` -> `ADC_BUSY`<br>`25` `GPIO48/SPICLK_N/SUBSPICLK_N_DIFF` -> `ADC_RESET`<br>`26` `GPIO45` -> `unconnected-(U9-GPIO45-Pad26)`<br>`27` `GPIO0/BOOT` -> `/MCU_ESP32-S3/PROG`<br>`28` `SPIIO6/GPIO35/FSPID/SUBSPID` -> `unconnected-(U9-SPIIO6{slash}GPIO35{slash}FSPID{slash}SUBSPID-Pad28)`<br>`29` `SPIIO7/GPIO36/FSPICLK/SUBSPICLK` -> `unconnected-(U9-SPIIO7{slash}GPIO36{slash}FSPICLK{slash}SUBSPICLK-Pad29)`<br>`3` `EN` -> `/MCU_ESP32-S3/EN`<br>`30` `SPIDQS/GPIO37/FSPIQ/SUBSPIQ` -> `unconnected-(U9-SPIDQS{slash}GPIO37{slash}FSPIQ{slash}SUBSPIQ-Pad30)`<br>`31` `GPIO38/FSPIWP/SUBSPIWP` -> `ADC_MISO_B`<br>`32` `MTCK/GPIO39/CLK_OUT3/SUBSPICS1` -> `unconnected-(U9-MTCK{slash}GPIO39{slash}CLK_OUT3{slash}SUBSPICS1-Pad32)`<br>`33` `MTDO/GPIO40/CLK_OUT2` -> `unconnected-(U9-MTDO{slash}GPIO40{slash}CLK_OUT2-Pad33)`<br>`34` `MTDI/GPIO41/CLK_OUT1` -> `unconnected-(U9-MTDI{slash}GPIO41{slash}CLK_OUT1-Pad34)`<br>`35` `MTMS/GPIO42` -> `unconnected-(U9-MTMS{slash}GPIO42-Pad35)`<br>`36` `U0RXD/GPIO44/CLK_OUT2` -> `/MCU_ESP32-S3/IO44`<br>`37` `U0TXD/GPIO43/CLK_OUT1` -> `/MCU_ESP32-S3/IO43`<br>`38` `GPIO2/TOUCH2/ADC1_CH1` -> `MPD1`<br>`39` `GPIO1/TOUCH1/ADC1_CH0` -> `/MCU_ESP32-S3/FACT`<br>`4` `GPIO4/TOUCH4/ADC1_CH3` -> `ISENSE1`<br>`40` `GND` -> `GND`<br>`41` `GND` -> `GND`<br>`5` `GPIO5/TOUCH5/ADC1_CH4` -> `ISENSE2`<br>`6` `GPIO6/TOUCH6/ADC1_CH5` -> `ISENSE3`<br>`7` `GPIO7/TOUCH7/ADC1_CH6` -> `ISENSE4`<br>`8` `GPIO15/U0RTS/ADC2_CH4/XTAL_32K_P` -> `CONVST`<br>`9` `GPIO16/U0CTS/ADC2_CH5/XTAL_32K_N` -> `PWM4` | `1` / `GND`: ESP32-S3 module ground/return pin.<br>`10` / `ADC_SCLK`: ESP32-S3 GPIO17 output used as the AD7606-4 serial clock.<br>`11` / `ADC_CS`: ESP32-S3 GPIO18 output used as the AD7606-4 chip select.<br>`12` / `MPD3`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`13` / `/MCU_ESP32-S3/IO19`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`14` / `/MCU_ESP32-S3/IO20`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`15` / `MPD2`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`16` / `unconnected-(U9-GPIO46-Pad16)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 16 `GPIO46`.<br>`17` / `MPD4`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`18` / `PWM1`: ESP32-S3 PWM output for one laser current command channel.<br>`19` / `PWM2`: ESP32-S3 PWM output for one laser current command channel.<br>`2` / `+3V3`: ESP32-S3 module 3V3 supply input.<br>`20` / `PWM3`: ESP32-S3 PWM output for one laser current command channel.<br>`21` / `/MCU_ESP32-S3/IO13`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`22` / `/MCU_ESP32-S3/IO14`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`23` / `ADC_MISO_A`: ESP32-S3 GPIO21 input reading AD7606-4 DOUTA.<br>`24` / `ADC_BUSY`: ESP32-S3 GPIO47 input reading AD7606-4 BUSY.<br>`25` / `ADC_RESET`: ESP32-S3 GPIO48 output driving AD7606-4 RESET.<br>`26` / `unconnected-(U9-GPIO45-Pad26)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 26 `GPIO45`.<br>`27` / `/MCU_ESP32-S3/PROG`: ESP32-S3 GPIO0/BOOT pin in the copied access-controller program/reset network.<br>`28` / `unconnected-(U9-SPIIO6{slash}GPIO35{slash}FSPID{slash}SUBSPID-Pad28)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 28 `SPIIO6/GPIO35/FSPID/SUBSPID`.<br>`29` / `unconnected-(U9-SPIIO7{slash}GPIO36{slash}FSPICLK{slash}SUBSPICLK-Pad29)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 29 `SPIIO7/GPIO36/FSPICLK/SUBSPICLK`.<br>`3` / `/MCU_ESP32-S3/EN`: ESP32-S3 EN/CHIP_PU reset pin in the copied access-controller reset network.<br>`30` / `unconnected-(U9-SPIDQS{slash}GPIO37{slash}FSPIQ{slash}SUBSPIQ-Pad30)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 30 `SPIDQS/GPIO37/FSPIQ/SUBSPIQ`.<br>`31` / `ADC_MISO_B`: ESP32-S3 GPIO38 input reading AD7606-4 DOUTB.<br>`32` / `unconnected-(U9-MTCK{slash}GPIO39{slash}CLK_OUT3{slash}SUBSPICS1-Pad32)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 32 `MTCK/GPIO39/CLK_OUT3/SUBSPICS1`.<br>`33` / `unconnected-(U9-MTDO{slash}GPIO40{slash}CLK_OUT2-Pad33)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 33 `MTDO/GPIO40/CLK_OUT2`.<br>`34` / `unconnected-(U9-MTDI{slash}GPIO41{slash}CLK_OUT1-Pad34)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 34 `MTDI/GPIO41/CLK_OUT1`.<br>`35` / `unconnected-(U9-MTMS{slash}GPIO42-Pad35)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 35 `MTMS/GPIO42`.<br>`36` / `/MCU_ESP32-S3/IO44`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`37` / `/MCU_ESP32-S3/IO43`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`38` / `MPD1`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`39` / `/MCU_ESP32-S3/FACT`: ESP32-S3 GPIO1 factory button input from the copied access-controller sheet.<br>`4` / `ISENSE1`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`40` / `GND`: ESP32-S3 module ground/return pin.<br>`41` / `GND`: ESP32-S3 module ground/return pin.<br>`5` / `ISENSE2`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`6` / `ISENSE3`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`7` / `ISENSE4`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`8` / `CONVST`: ESP32-S3 GPIO15 output for the on-board AD7606-4 conversion-start line.<br>`9` / `PWM4`: ESP32-S3 PWM output for one laser current command channel. |
