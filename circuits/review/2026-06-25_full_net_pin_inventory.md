# Laser Controller Full Net/Pin Inventory

Generated from KiCad exported netlist and the current generated PCB artifact.

Schematic references are generated globally unique before KiCad netlist export. Logical route names such as `LASER_GREEN/R12` are resolved through `circuit_designators.py`; physical net nodes use unique refs such as `R29` and `Q3`.

## PCB Trace State

| Metric | Value |
|---|---:|
| `footprint_objects` | 121 |
| `referenced_footprints` | 117 |
| `unique_references` | 117 |
| `copper_layers` | 4 |
| `segments` | 1260 |
| `vias` | 141 |
| `zones` | 2 |
| `pad_net_lines` | 326 |
| `net_table_entries` | 78 |
| `keepout_zones` | 1 |
| `gnd_reference_zone_defs` | 1 |
| `net_classes` | 8 |
| `classified_nets` | 77 |
| `placement_proximity_checks` | 109/109 PASS |
| `intentional_unnetted_pad_instances` | 59 |
| `connected_critical_local_route_links` | 109/109 |
| `multi_pad_nets` | 77 |
| `explicitly_routed_multi_pad_nets` | 75 |
| `unrouted_multi_pad_nets` | 0 |
| `zone_or_rail_pending_multi_pad_nets` | 2 |

| Net Class | Nets |
|---|---:|
| `Laser_Current` | 9 |
| `Power_Rails` | 5 |
| `USB` | 6 |
| `TIA_Sensitive` | 24 |
| `Monitor_ADC` | 12 |
| `Laser_Control` | 16 |
| `Digital_Control` | 5 |
| `Default` | 0 |

### Routed Copper Geometry By Net Class

This table reports the generated routed copper that exists in the current PCB artifact. It does not waive KiCad zone refill, DRC, or manual current-path review.

| Net Class | Segment Widths | Via Size/Drill |
|---|---|---|
| `Laser_Current` | 0.20mm x44, 0.60mm x41, 0.80mm x12 | 0.60/0.30mm x6 |
| `Power_Rails` | 0.20mm x194, 0.25mm x251, 0.35mm x12, 0.50mm x35, 0.60mm x29 | 0.45/0.20mm x60, 0.60/0.30mm x35 |
| `USB` | 0.25mm x27 | - |
| `TIA_Sensitive` | 0.20mm x220, 0.25mm x4 | 0.60/0.30mm x12 |
| `Monitor_ADC` | 0.20mm x152 | 0.60/0.30mm x16 |
| `Laser_Control` | 0.20mm x159 | 0.60/0.30mm x6 |
| `Digital_Control` | 0.20mm x80 | 0.60/0.30mm x6 |

### USB Route Detail

Native ESP32-S3 USB is checked as the connector-to-USBLC6, USBLC6-to-series, and series-to-module routed copper chain for each D+/D- leg. The PCB checker fails if either chain exceeds the generated-board length limit, uses vias, leaves F.Cu, changes width, or exceeds the pair-skew limit.

Pair routed-copper skew: 1.79 mm. PASS: USB generated-board route quality gate passed

| Chain | Section | Net | Segments | Length | Geometry | Status |
|---|---|---|---:|---:|---|---|
| `D-` | connector to USBLC6 | `/MCU_ESP32-S3/USB_DM_CONN` | 4 | 8.58 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `D-` | USBLC6 to 22R | `/MCU_ESP32-S3/USB_DM_ESD` | 5 | 9.15 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `D-` | 22R to ESP32 GPIO19 | `/MCU_ESP32-S3/USB_DM` | 4 | 4.52 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `D-` | total | `-` | 13 | 22.26 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured chain is inside generated-board USB limits |
| `D+` | connector to USBLC6 | `/MCU_ESP32-S3/USB_DP_CONN` | 6 | 12.19 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `D+` | USBLC6 to 22R | `/MCU_ESP32-S3/USB_DP_ESD` | 5 | 9.97 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `D+` | 22R to ESP32 GPIO20 | `/MCU_ESP32-S3/USB_DP` | 3 | 1.90 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured route section is present |
| `D+` | total | `-` | 14 | 24.05 mm | F.Cu; widths 0.25 mm; vias 0 | PASS: measured chain is inside generated-board USB limits |

### Laser Current Trace Detail

This table separates the high-current laser cathode/load paths from source-sense feedback copper. Any `BLOCKER` row is routed connectivity evidence only; it is not accepted current-path layout.

| Net | Layer | Width | Segments | Total Length | Role | Status |
|---|---|---:|---:|---:|---|---|
| `/LASER_BLUE/FB` | `F.Cu` | 0.20 mm | 11 | 8.37 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_BLUE/FB` | `F.Cu` | 0.60 mm | 4 | 2.51 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_GREEN/FB` | `F.Cu` | 0.20 mm | 11 | 8.37 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_GREEN/FB` | `F.Cu` | 0.60 mm | 4 | 2.51 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_IR/FB` | `F.Cu` | 0.20 mm | 11 | 8.37 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_IR/FB` | `F.Cu` | 0.60 mm | 4 | 2.51 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_RED/FB` | `F.Cu` | 0.20 mm | 11 | 8.37 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `/LASER_RED/FB` | `F.Cu` | 0.60 mm | 4 | 2.51 mm | source-sense feedback node | REVIEW: contains AO3400A source/sense current path plus low-current feedback/telemetry stubs |
| `LASER_N1` | `F.Cu` | 0.60 mm | 3 | 5.50 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N1` | `In2.Cu` | 0.60 mm | 7 | 57.06 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N2` | `B.Cu` | 0.60 mm | 4 | 34.07 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N2` | `F.Cu` | 0.60 mm | 3 | 5.50 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N3` | `F.Cu` | 0.60 mm | 1 | 0.94 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N3` | `In2.Cu` | 0.60 mm | 3 | 39.34 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N4` | `F.Cu` | 0.60 mm | 1 | 2.19 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_N4` | `In2.Cu` | 0.60 mm | 3 | 43.51 mm | laser cathode load path | PASS: generated cathode route meets current width/length limits |
| `LASER_V+` | `F.Cu` | 0.80 mm | 8 | 5.07 mm | laser anode supply path | PASS: generated laser-anode rail meets current width/length limits |
| `LASER_V+` | `In2.Cu` | 0.80 mm | 4 | 26.92 mm | laser anode supply path | PASS: generated laser-anode rail meets current width/length limits |

### Laser Sense Return Detail

Each 10 ohm 2512 source-sense resistor must return into the GND reference plane through a distinct high-current 0.60/0.30 mm via within 6.0 mm of routed GND copper.

| Channel | Sense GND Pad | Routed GND Path | Via | Via Size/Drill | Status |
|---|---|---:|---|---|---|
| `LASER_IR` | `R18.2` | 1.68 mm | `(50.90, 19.35)` | 0.60/0.30 mm | PASS: routed sense return reaches an assigned high-current GND via |
| `LASER_RED` | `R23.2` | 1.20 mm | `(51.25, 26.50)` | 0.60/0.30 mm | PASS: routed sense return reaches an assigned high-current GND via |
| `LASER_GREEN` | `R28.2` | 1.20 mm | `(51.25, 34.50)` | 0.60/0.30 mm | PASS: routed sense return reaches an assigned high-current GND via |
| `LASER_BLUE` | `R33.2` | 1.20 mm | `(51.25, 42.50)` | 0.60/0.30 mm | PASS: routed sense return reaches an assigned high-current GND via |

PCB has explicit pad-net assignments and generated copper for bounded critical-local routes plus selected low-speed board-level routes, but the current artifact is not fully connected by explicit copper. Unrouted signal/control nets: none. Rail/zone pending nets: `+5V`, `GND`. Full-board release still requires routing fixes, KiCad zone refill, DRC, and visual return-path review.

### Reviewed Rail/Zone Pending Nets

These are the only multi-pad nets currently allowed to remain split by explicit routed copper. The PCB checker fails if a different rail or any signal/control net enters this state.

| Net | Pads | Copper Components | Review Status | Required Release Action | Component Groups |
|---|---:|---:|---|---|---|
| `+5V` | 30 | 2 | REVIEWED_PENDING | Route or pour the post-OR board 5 V rail to every analog, laser-driver, and LDO input load; verify diode drop and current. | U1.7, C2.1, R2.1, R4.1, U2.7, C6.1, R6.1, R8.1 ... \| U5.5, C17.1, U6.5, C20.1, U7.5, C23.1, U8.5, C26.1 |
| `GND` | 81 | 6 | REVIEWED_PENDING | Refill the In1.Cu GND zone, inspect islands/stitching, and keep laser-current return paths out of TIA summing-node returns. | U1.4, C2.2, C3.2, C4.2, RV1.3, U2.4, C6.2, C7.2 ... \| C17.2 \| C20.2 \| C23.2 \| C26.2 \| C33.2 |

### Placement Proximity Checks

These generated-board checks keep USB protection, ESP32-S3 support parts, AP2112 decoupling, every TIA input/feedback/decoupling/bias cluster, every laser gate/sense/control/compensation cluster, and every monitor-PD burden/filter/ADC-isolation cluster close to the pins they serve.

| Check | Actual | Limit | Status |
|---|---:|---:|---|
| USB D- connector to USBLC6 | 7.48 mm | 7.50 mm | PASS |
| USB D+ connector to USBLC6 | 9.27 mm | 9.50 mm | PASS |
| USBLC6 D- to 22R series | 5.94 mm | 10.00 mm | PASS |
| USBLC6 D+ to 22R series | 7.55 mm | 10.00 mm | PASS |
| USB D- series to ESP32 GPIO19 | 3.18 mm | 4.50 mm | PASS |
| USB D+ series to ESP32 GPIO20 | 1.66 mm | 4.50 mm | PASS |
| AP2112 input cap at VIN | 1.90 mm | 4.00 mm | PASS |
| AP2112 100n output cap at VOUT | 1.52 mm | 4.00 mm | PASS |
| AP2112 bulk output cap at VOUT | 2.75 mm | 4.00 mm | PASS |
| ESP32 local 3V3 decap | 2.82 mm | 3.00 mm | PASS |
| ESP32 EN capacitor | 3.32 mm | 4.00 mm | PASS |
| ESP32 EN pull-up | 3.84 mm | 5.00 mm | PASS |
| ESP32 BOOT pull-up | 1.84 mm | 4.00 mm | PASS |
| TIA_IR photodiode anode to OPA380 -IN | 4.81 mm | 5.50 mm | PASS |
| TIA_IR feedback resistor at OPA380 -IN | 2.43 mm | 3.50 mm | PASS |
| TIA_IR feedback capacitor at OPA380 -IN | 1.73 mm | 2.50 mm | PASS |
| TIA_IR feedback resistor at OPA380 OUT | 3.50 mm | 4.50 mm | PASS |
| TIA_IR feedback capacitor at OPA380 OUT | 1.73 mm | 2.50 mm | PASS |
| TIA_IR OPA380 supply decoupling | 1.11 mm | 2.50 mm | PASS |
| TIA_IR PD bias resistor at cathode | 0.93 mm | 4.50 mm | PASS |
| TIA_IR PD cathode bypass at cathode | 2.07 mm | 3.00 mm | PASS |
| TIA_IR VBIAS resistor at OPA380 +IN | 4.25 mm | 5.00 mm | PASS |
| TIA_IR VBIAS capacitor at OPA380 +IN | 2.29 mm | 4.00 mm | PASS |
| TIA_RED photodiode anode to OPA380 -IN | 4.81 mm | 5.50 mm | PASS |
| TIA_RED feedback resistor at OPA380 -IN | 2.43 mm | 3.50 mm | PASS |
| TIA_RED feedback capacitor at OPA380 -IN | 1.73 mm | 2.50 mm | PASS |
| TIA_RED feedback resistor at OPA380 OUT | 3.50 mm | 4.50 mm | PASS |
| TIA_RED feedback capacitor at OPA380 OUT | 1.73 mm | 2.50 mm | PASS |
| TIA_RED OPA380 supply decoupling | 1.11 mm | 2.50 mm | PASS |
| TIA_RED PD bias resistor at cathode | 0.93 mm | 4.50 mm | PASS |
| TIA_RED PD cathode bypass at cathode | 2.07 mm | 3.00 mm | PASS |
| TIA_RED VBIAS resistor at OPA380 +IN | 4.25 mm | 5.00 mm | PASS |
| TIA_RED VBIAS capacitor at OPA380 +IN | 2.29 mm | 4.00 mm | PASS |
| TIA_GREEN photodiode anode to OPA380 -IN | 4.81 mm | 5.50 mm | PASS |
| TIA_GREEN feedback resistor at OPA380 -IN | 2.43 mm | 3.50 mm | PASS |
| TIA_GREEN feedback capacitor at OPA380 -IN | 1.73 mm | 2.50 mm | PASS |
| TIA_GREEN feedback resistor at OPA380 OUT | 3.50 mm | 4.50 mm | PASS |
| TIA_GREEN feedback capacitor at OPA380 OUT | 1.73 mm | 2.50 mm | PASS |
| TIA_GREEN OPA380 supply decoupling | 1.11 mm | 2.50 mm | PASS |
| TIA_GREEN PD bias resistor at cathode | 0.93 mm | 4.50 mm | PASS |
| TIA_GREEN PD cathode bypass at cathode | 2.07 mm | 3.00 mm | PASS |
| TIA_GREEN VBIAS resistor at OPA380 +IN | 4.25 mm | 5.00 mm | PASS |
| TIA_GREEN VBIAS capacitor at OPA380 +IN | 2.29 mm | 4.00 mm | PASS |
| TIA_BLUE photodiode anode to OPA380 -IN | 4.81 mm | 5.50 mm | PASS |
| TIA_BLUE feedback resistor at OPA380 -IN | 2.43 mm | 3.50 mm | PASS |
| TIA_BLUE feedback capacitor at OPA380 -IN | 1.73 mm | 2.50 mm | PASS |
| TIA_BLUE feedback resistor at OPA380 OUT | 3.50 mm | 4.50 mm | PASS |
| TIA_BLUE feedback capacitor at OPA380 OUT | 1.73 mm | 2.50 mm | PASS |
| TIA_BLUE OPA380 supply decoupling | 1.11 mm | 2.50 mm | PASS |
| TIA_BLUE PD bias resistor at cathode | 0.93 mm | 4.50 mm | PASS |
| TIA_BLUE PD cathode bypass at cathode | 2.07 mm | 3.00 mm | PASS |
| TIA_BLUE VBIAS resistor at OPA380 +IN | 4.25 mm | 5.00 mm | PASS |
| TIA_BLUE VBIAS capacitor at OPA380 +IN | 2.29 mm | 4.00 mm | PASS |
| LASER_IR TLV9001 OUT to gate resistor | 2.69 mm | 3.50 mm | PASS |
| LASER_IR gate resistor to AO3400A gate | 1.46 mm | 2.50 mm | PASS |
| LASER_IR AO3400A source to sense resistor | 1.79 mm | 2.20 mm | PASS |
| LASER_IR sense feedback to TLV9001 -IN | 3.66 mm | 6.00 mm | PASS |
| LASER_IR isolated ISENSE tap at sense resistor | 1.63 mm | 3.50 mm | PASS |
| LASER_IR TLV9001 supply decoupling | 0.75 mm | 2.50 mm | PASS |
| LASER_IR PWM input resistor at TLV9001 +IN | 1.79 mm | 2.50 mm | PASS |
| LASER_IR command limiter at TLV9001 +IN | 2.17 mm | 3.00 mm | PASS |
| LASER_IR command filter cap at TLV9001 +IN | 2.21 mm | 3.00 mm | PASS |
| LASER_IR compensation cap at TLV9001 -IN | 1.14 mm | 2.50 mm | PASS |
| LASER_IR compensation cap at TLV9001 OUT | 1.14 mm | 3.00 mm | PASS |
| LASER_RED TLV9001 OUT to gate resistor | 2.69 mm | 3.50 mm | PASS |
| LASER_RED gate resistor to AO3400A gate | 1.46 mm | 2.50 mm | PASS |
| LASER_RED AO3400A source to sense resistor | 1.79 mm | 2.20 mm | PASS |
| LASER_RED sense feedback to TLV9001 -IN | 3.66 mm | 6.00 mm | PASS |
| LASER_RED isolated ISENSE tap at sense resistor | 1.63 mm | 3.50 mm | PASS |
| LASER_RED TLV9001 supply decoupling | 0.75 mm | 2.50 mm | PASS |
| LASER_RED PWM input resistor at TLV9001 +IN | 1.56 mm | 2.50 mm | PASS |
| LASER_RED command limiter at TLV9001 +IN | 2.17 mm | 3.00 mm | PASS |
| LASER_RED command filter cap at TLV9001 +IN | 2.38 mm | 3.00 mm | PASS |
| LASER_RED compensation cap at TLV9001 -IN | 1.14 mm | 2.50 mm | PASS |
| LASER_RED compensation cap at TLV9001 OUT | 1.14 mm | 3.00 mm | PASS |
| LASER_GREEN TLV9001 OUT to gate resistor | 2.69 mm | 3.50 mm | PASS |
| LASER_GREEN gate resistor to AO3400A gate | 1.46 mm | 2.50 mm | PASS |
| LASER_GREEN AO3400A source to sense resistor | 1.79 mm | 2.20 mm | PASS |
| LASER_GREEN sense feedback to TLV9001 -IN | 3.66 mm | 6.00 mm | PASS |
| LASER_GREEN isolated ISENSE tap at sense resistor | 1.63 mm | 3.50 mm | PASS |
| LASER_GREEN TLV9001 supply decoupling | 0.75 mm | 2.50 mm | PASS |
| LASER_GREEN PWM input resistor at TLV9001 +IN | 1.79 mm | 2.50 mm | PASS |
| LASER_GREEN command limiter at TLV9001 +IN | 2.17 mm | 3.00 mm | PASS |
| LASER_GREEN command filter cap at TLV9001 +IN | 2.21 mm | 3.00 mm | PASS |
| LASER_GREEN compensation cap at TLV9001 -IN | 1.14 mm | 2.50 mm | PASS |
| LASER_GREEN compensation cap at TLV9001 OUT | 1.14 mm | 3.00 mm | PASS |
| LASER_BLUE TLV9001 OUT to gate resistor | 2.69 mm | 3.50 mm | PASS |
| LASER_BLUE gate resistor to AO3400A gate | 1.46 mm | 2.50 mm | PASS |
| LASER_BLUE AO3400A source to sense resistor | 1.79 mm | 2.20 mm | PASS |
| LASER_BLUE sense feedback to TLV9001 -IN | 3.66 mm | 6.00 mm | PASS |
| LASER_BLUE isolated ISENSE tap at sense resistor | 1.63 mm | 3.50 mm | PASS |
| LASER_BLUE TLV9001 supply decoupling | 0.75 mm | 2.50 mm | PASS |
| LASER_BLUE PWM input resistor at TLV9001 +IN | 1.79 mm | 2.50 mm | PASS |
| LASER_BLUE command limiter at TLV9001 +IN | 2.17 mm | 3.00 mm | PASS |
| LASER_BLUE command filter cap at TLV9001 +IN | 2.21 mm | 3.00 mm | PASS |
| LASER_BLUE compensation cap at TLV9001 -IN | 1.14 mm | 2.50 mm | PASS |
| LASER_BLUE compensation cap at TLV9001 OUT | 1.14 mm | 3.00 mm | PASS |
| MPD_RAW1 burden resistor at J4 | 2.70 mm | 4.00 mm | PASS |
| MPD_RAW1 filter capacitor at J4 | 1.40 mm | 2.50 mm | PASS |
| MPD_RAW1 ADC isolation resistor at J4 | 3.00 mm | 4.00 mm | PASS |
| MPD_RAW2 burden resistor at J4 | 2.70 mm | 4.00 mm | PASS |
| MPD_RAW2 filter capacitor at J4 | 1.40 mm | 2.50 mm | PASS |
| MPD_RAW2 ADC isolation resistor at J4 | 3.00 mm | 4.00 mm | PASS |
| MPD_RAW3 burden resistor at J4 | 2.70 mm | 4.00 mm | PASS |
| MPD_RAW3 filter capacitor at J4 | 1.40 mm | 2.50 mm | PASS |
| MPD_RAW3 ADC isolation resistor at J4 | 3.54 mm | 4.00 mm | PASS |
| MPD_RAW4 burden resistor at J4 | 2.71 mm | 4.00 mm | PASS |
| MPD_RAW4 filter capacitor at J4 | 1.41 mm | 2.50 mm | PASS |
| MPD_RAW4 ADC isolation resistor at J4 | 3.50 mm | 4.00 mm | PASS |

### Critical Local Route Connectivity

These are generated F.Cu route-link connectivity checks for the same local clusters. Any `UNROUTED` entries are the next routing targets; they are not waived.

| Route Link | Status |
|---|---|
| USB D- connector to USBLC6 | ROUTED |
| USB D+ connector to USBLC6 | ROUTED |
| USBLC6 D- to 22R series | ROUTED |
| USBLC6 D+ to 22R series | ROUTED |
| USB D- series to ESP32 GPIO19 | ROUTED |
| USB D+ series to ESP32 GPIO20 | ROUTED |
| AP2112 input cap at VIN | ROUTED |
| AP2112 100n output cap at VOUT | ROUTED |
| AP2112 bulk output cap at VOUT | ROUTED |
| ESP32 local 3V3 decap | ROUTED |
| ESP32 EN capacitor | ROUTED |
| ESP32 EN pull-up | ROUTED |
| ESP32 BOOT pull-up | ROUTED |
| TIA_IR photodiode anode to OPA380 -IN | ROUTED |
| TIA_IR feedback resistor at OPA380 -IN | ROUTED |
| TIA_IR feedback capacitor at OPA380 -IN | ROUTED |
| TIA_IR feedback resistor at OPA380 OUT | ROUTED |
| TIA_IR feedback capacitor at OPA380 OUT | ROUTED |
| TIA_IR OPA380 supply decoupling | ROUTED |
| TIA_IR PD bias resistor at cathode | ROUTED |
| TIA_IR PD cathode bypass at cathode | ROUTED |
| TIA_IR VBIAS resistor at OPA380 +IN | ROUTED |
| TIA_IR VBIAS capacitor at OPA380 +IN | ROUTED |
| TIA_RED photodiode anode to OPA380 -IN | ROUTED |
| TIA_RED feedback resistor at OPA380 -IN | ROUTED |
| TIA_RED feedback capacitor at OPA380 -IN | ROUTED |
| TIA_RED feedback resistor at OPA380 OUT | ROUTED |
| TIA_RED feedback capacitor at OPA380 OUT | ROUTED |
| TIA_RED OPA380 supply decoupling | ROUTED |
| TIA_RED PD bias resistor at cathode | ROUTED |
| TIA_RED PD cathode bypass at cathode | ROUTED |
| TIA_RED VBIAS resistor at OPA380 +IN | ROUTED |
| TIA_RED VBIAS capacitor at OPA380 +IN | ROUTED |
| TIA_GREEN photodiode anode to OPA380 -IN | ROUTED |
| TIA_GREEN feedback resistor at OPA380 -IN | ROUTED |
| TIA_GREEN feedback capacitor at OPA380 -IN | ROUTED |
| TIA_GREEN feedback resistor at OPA380 OUT | ROUTED |
| TIA_GREEN feedback capacitor at OPA380 OUT | ROUTED |
| TIA_GREEN OPA380 supply decoupling | ROUTED |
| TIA_GREEN PD bias resistor at cathode | ROUTED |
| TIA_GREEN PD cathode bypass at cathode | ROUTED |
| TIA_GREEN VBIAS resistor at OPA380 +IN | ROUTED |
| TIA_GREEN VBIAS capacitor at OPA380 +IN | ROUTED |
| TIA_BLUE photodiode anode to OPA380 -IN | ROUTED |
| TIA_BLUE feedback resistor at OPA380 -IN | ROUTED |
| TIA_BLUE feedback capacitor at OPA380 -IN | ROUTED |
| TIA_BLUE feedback resistor at OPA380 OUT | ROUTED |
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
| MPD_RAW1 burden resistor at J4 | ROUTED |
| MPD_RAW1 filter capacitor at J4 | ROUTED |
| MPD_RAW1 ADC isolation resistor at J4 | ROUTED |
| MPD_RAW2 burden resistor at J4 | ROUTED |
| MPD_RAW2 filter capacitor at J4 | ROUTED |
| MPD_RAW2 ADC isolation resistor at J4 | ROUTED |
| MPD_RAW3 burden resistor at J4 | ROUTED |
| MPD_RAW3 filter capacitor at J4 | ROUTED |
| MPD_RAW3 ADC isolation resistor at J4 | ROUTED |
| MPD_RAW4 burden resistor at J4 | ROUTED |
| MPD_RAW4 filter capacitor at J4 | ROUTED |
| MPD_RAW4 ADC isolation resistor at J4 | ROUTED |

### Whole-Board Explicit Route Connectivity

This table checks whether every pad on each multi-pad PCB net is connected by explicit routed copper segments. `ZONE_OR_RAIL_PENDING` nets are expected to rely on planes/zones or rail trunks that still require KiCad refill/DRC. `UNROUTED` nets still need board-level routing; critical local links passing does not waive these.

| Net | Pads | Copper Components | Status | Component Groups |
|---|---:|---:|---|---|
| `+5V` | 30 | 2 | ZONE_OR_RAIL_PENDING | U1.7, C2.1, R2.1, R4.1, U2.7, C6.1, R6.1, R8.1 ... \| U5.5, C17.1, U6.5, C20.1, U7.5, C23.1, U8.5, C26.1 |
| `GND` | 81 | 6 | ZONE_OR_RAIL_PENDING | U1.4, C2.2, C3.2, C4.2, RV1.3, U2.4, C6.2, C7.2 ... \| C17.2 \| C20.2 \| C23.2 \| C26.2 \| C33.2 |
| `+3V3` | 7 | 1 | EXPLICITLY_ROUTED | U9.2, U11.5, C30.1, C31.1, C32.1, R39.1, R40.1 |
| `/LASER_BLUE/FB` | 5 | 1 | EXPLICITLY_ROUTED | U8.4, Q4.2, R33.1, R34.1, C28.1 |
| `/LASER_BLUE/LOUT` | 3 | 1 | EXPLICITLY_ROUTED | U8.1, R32.1, C28.2 |
| `/LASER_GREEN/FB` | 5 | 1 | EXPLICITLY_ROUTED | U7.4, Q3.2, R28.1, R29.1, C25.1 |
| `/LASER_GREEN/LOUT` | 3 | 1 | EXPLICITLY_ROUTED | U7.1, R27.1, C25.2 |
| `/LASER_IR/FB` | 5 | 1 | EXPLICITLY_ROUTED | U5.4, Q1.2, R18.1, R19.1, C19.1 |
| `/LASER_IR/LOUT` | 3 | 1 | EXPLICITLY_ROUTED | U5.1, R17.1, C19.2 |
| `/LASER_RED/FB` | 5 | 1 | EXPLICITLY_ROUTED | U6.4, Q2.2, R23.1, R24.1, C22.1 |
| `/LASER_RED/LOUT` | 3 | 1 | EXPLICITLY_ROUTED | U6.1, R22.1, C22.2 |
| `/MCU_ESP32-S3/ESP_BOOT` | 3 | 1 | EXPLICITLY_ROUTED | J2.4, U9.27, R40.2 |
| `/MCU_ESP32-S3/ESP_EN` | 4 | 1 | EXPLICITLY_ROUTED | J2.3, U9.3, C33.1, R39.2 |
| `/MCU_ESP32-S3/ESP_RX` | 2 | 1 | EXPLICITLY_ROUTED | J2.2, U9.36 |
| `/MCU_ESP32-S3/ESP_TX` | 2 | 1 | EXPLICITLY_ROUTED | J2.1, U9.37 |
| `/MCU_ESP32-S3/USB_DM` | 2 | 1 | EXPLICITLY_ROUTED | U9.13, R37.2 |
| `/MCU_ESP32-S3/USB_DM_CONN` | 2 | 1 | EXPLICITLY_ROUTED | J1.2, U10.1 |
| `/MCU_ESP32-S3/USB_DM_ESD` | 2 | 1 | EXPLICITLY_ROUTED | U10.6, R37.1 |
| `/MCU_ESP32-S3/USB_DP` | 2 | 1 | EXPLICITLY_ROUTED | U9.14, R38.2 |
| `/MCU_ESP32-S3/USB_DP_CONN` | 2 | 1 | EXPLICITLY_ROUTED | J1.3, U10.3 |
| `/MCU_ESP32-S3/USB_DP_ESD` | 2 | 1 | EXPLICITLY_ROUTED | U10.4, R38.1 |
| `/POWER_IO/EXT5V` | 2 | 1 | EXPLICITLY_ROUTED | J6.1, D6.1 |
| `/POWER_IO/MPD_RAW1` | 4 | 1 | EXPLICITLY_ROUTED | J4.2, R41.1, C35.1, R42.2 |
| `/POWER_IO/MPD_RAW2` | 4 | 1 | EXPLICITLY_ROUTED | J4.4, R43.1, C36.1, R44.2 |
| `/POWER_IO/MPD_RAW3` | 4 | 1 | EXPLICITLY_ROUTED | J4.6, R45.1, C37.1, R46.2 |
| `/POWER_IO/MPD_RAW4` | 4 | 1 | EXPLICITLY_ROUTED | J4.8, R47.1, C38.1, R48.2 |
| `CONVST` | 2 | 1 | EXPLICITLY_ROUTED | U9.10, J3.5 |
| `ISENSE1` | 2 | 1 | EXPLICITLY_ROUTED | R19.2, U9.4 |
| `ISENSE2` | 2 | 1 | EXPLICITLY_ROUTED | R24.2, U9.5 |
| `ISENSE3` | 2 | 1 | EXPLICITLY_ROUTED | R29.2, U9.6 |
| `ISENSE4` | 2 | 1 | EXPLICITLY_ROUTED | R34.2, U9.7 |
| `LASER_N1` | 2 | 1 | EXPLICITLY_ROUTED | Q1.3, J4.1 |
| `LASER_N2` | 2 | 1 | EXPLICITLY_ROUTED | Q2.3, J4.3 |
| `LASER_N3` | 2 | 1 | EXPLICITLY_ROUTED | Q3.3, J4.5 |
| `LASER_N4` | 2 | 1 | EXPLICITLY_ROUTED | Q4.3, J4.7 |
| `LASER_V+` | 2 | 1 | EXPLICITLY_ROUTED | J4.9, J5.1 |
| `MPD1` | 2 | 1 | EXPLICITLY_ROUTED | U9.38, R42.1 |
| `MPD2` | 2 | 1 | EXPLICITLY_ROUTED | U9.39, R44.1 |
| `MPD3` | 2 | 1 | EXPLICITLY_ROUTED | U9.12, R46.1 |
| `MPD4` | 2 | 1 | EXPLICITLY_ROUTED | U9.17, R48.1 |
| `Net-(D1-A)` | 4 | 1 | EXPLICITLY_ROUTED | D1.2, U1.2, R1.1, C1.1 |
| `Net-(D1-K)` | 3 | 1 | EXPLICITLY_ROUTED | D1.1, R2.2, C3.1 |
| `Net-(D2-A)` | 4 | 1 | EXPLICITLY_ROUTED | D2.2, U2.2, R5.1, C5.1 |
| `Net-(D2-K)` | 3 | 1 | EXPLICITLY_ROUTED | D2.1, R6.2, C7.1 |
| `Net-(D3-A)` | 4 | 1 | EXPLICITLY_ROUTED | D3.2, U3.2, R9.1, C9.1 |
| `Net-(D3-K)` | 3 | 1 | EXPLICITLY_ROUTED | D3.1, R10.2, C11.1 |
| `Net-(D4-A)` | 4 | 1 | EXPLICITLY_ROUTED | D4.2, U4.2, R13.1, C13.1 |
| `Net-(D4-K)` | 3 | 1 | EXPLICITLY_ROUTED | D4.1, R14.2, C15.1 |
| `Net-(Q1-G)` | 2 | 1 | EXPLICITLY_ROUTED | R17.2, Q1.1 |
| `Net-(Q2-G)` | 2 | 1 | EXPLICITLY_ROUTED | R22.2, Q2.1 |
| `Net-(Q3-G)` | 2 | 1 | EXPLICITLY_ROUTED | R27.2, Q3.1 |
| `Net-(Q4-G)` | 2 | 1 | EXPLICITLY_ROUTED | R32.2, Q4.1 |
| `Net-(R12-Pad2)` | 2 | 1 | EXPLICITLY_ROUTED | RV3.1, R12.2 |
| `Net-(R16-Pad2)` | 2 | 1 | EXPLICITLY_ROUTED | RV4.1, R16.2 |
| `Net-(R4-Pad2)` | 2 | 1 | EXPLICITLY_ROUTED | RV1.1, R4.2 |
| `Net-(R8-Pad2)` | 2 | 1 | EXPLICITLY_ROUTED | RV2.1, R8.2 |
| `Net-(RV1-W)` | 2 | 1 | EXPLICITLY_ROUTED | R3.1, RV1.2 |
| `Net-(RV2-W)` | 2 | 1 | EXPLICITLY_ROUTED | R7.1, RV2.2 |
| `Net-(RV3-W)` | 2 | 1 | EXPLICITLY_ROUTED | R11.1, RV3.2 |
| `Net-(RV4-W)` | 2 | 1 | EXPLICITLY_ROUTED | R15.1, RV4.2 |
| `Net-(U1-+)` | 3 | 1 | EXPLICITLY_ROUTED | U1.3, R3.2, C4.1 |
| `Net-(U2-+)` | 3 | 1 | EXPLICITLY_ROUTED | U2.3, R7.2, C8.1 |
| `Net-(U3-+)` | 3 | 1 | EXPLICITLY_ROUTED | U3.3, R11.2, C12.1 |
| `Net-(U4-+)` | 3 | 1 | EXPLICITLY_ROUTED | U4.3, R15.2, C16.1 |
| `Net-(U5-+)` | 4 | 1 | EXPLICITLY_ROUTED | U5.3, R20.2, R21.1, C18.1 |
| `Net-(U6-+)` | 4 | 1 | EXPLICITLY_ROUTED | U6.3, R25.2, R26.1, C21.1 |
| `Net-(U7-+)` | 4 | 1 | EXPLICITLY_ROUTED | U7.3, R30.2, R31.1, C24.1 |
| `Net-(U8-+)` | 4 | 1 | EXPLICITLY_ROUTED | U8.3, R35.2, R36.1, C27.1 |
| `PWM1` | 2 | 1 | EXPLICITLY_ROUTED | R20.1, U9.9 |
| `PWM2` | 2 | 1 | EXPLICITLY_ROUTED | R25.1, U9.31 |
| `PWM3` | 2 | 1 | EXPLICITLY_ROUTED | R30.1, U9.21 |
| `PWM4` | 2 | 1 | EXPLICITLY_ROUTED | R35.1, U9.22 |
| `VBUS_5V` | 3 | 1 | EXPLICITLY_ROUTED | J1.1, U10.5, D5.1 |
| `VOUT1` | 4 | 1 | EXPLICITLY_ROUTED | U1.6, R1.2, C1.2, J3.1 |
| `VOUT2` | 4 | 1 | EXPLICITLY_ROUTED | U2.6, R5.2, C5.2, J3.2 |
| `VOUT3` | 4 | 1 | EXPLICITLY_ROUTED | U3.6, R9.2, C9.2, J3.3 |
| `VOUT4` | 4 | 1 | EXPLICITLY_ROUTED | U4.6, R13.2, C13.2, J3.4 |

## Pin Intent Coverage

Every exported netlist node is assigned a component-pin-level role. This is stricter than net-level intent: it explains why each specific pin belongs on its net.

| Metric | Value |
|---|---:|
| `exported_netlist_nodes` | 343 |
| `pin_intent_roles` | 343 |
| `missing_pin_intent_roles` | 0 |

## Net Inventory

Total exported nets: **109**.

| Net | Nodes | Intent / Review Note |
|---|---|---|
| `+3V3` | `C30.1`, `C31.1`, `C32.1`, `R39.1`, `R40.1`, `U11.5` `VOUT`, `U9.2` `3V3` | ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling. |
| `+5V` | `C10.1`, `C14.1`, `C17.1`, `C2.1`, `C20.1`, `C23.1`, `C26.1`, `C29.1`, `C34.1`, `C6.1`, `D5.2` `K`, `D6.2` `K`, `R10.1`, `R12.1`, `R14.1`, `R16.1`, `R2.1`, `R4.1`, `R6.1`, `R8.1`, `U1.7` `V+`, `U11.1` `VIN`, `U11.3` `EN`, `U2.7` `V+`, `U3.7` `V+`, `U4.7` `V+`, `U5.5` `V+`, `U6.5` `V+`, `U7.5` `V+`, `U8.5` `V+` | Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input. |
| `/LASER_BLUE/FB` | `C28.1`, `Q4.2` `S`, `R33.1`, `R34.1`, `U8.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_BLUE/LOUT` | `C28.2`, `R32.1`, `U8.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_GREEN/FB` | `C25.1`, `Q3.2` `S`, `R28.1`, `R29.1`, `U7.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_GREEN/LOUT` | `C25.2`, `R27.1`, `U7.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_IR/FB` | `C19.1`, `Q1.2` `S`, `R18.1`, `R19.1`, `U5.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_IR/LOUT` | `C19.2`, `R17.1`, `U5.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_RED/FB` | `C22.1`, `Q2.2` `S`, `R23.1`, `R24.1`, `U6.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_RED/LOUT` | `C22.2`, `R22.1`, `U6.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/MCU_ESP32-S3/ESP_BOOT` | `J2.4` `4`, `R40.2`, `U9.27` `GPIO0/BOOT` | ESP32 GPIO0 boot-mode net: header, 10 k pull-up, MCU GPIO0 pin. |
| `/MCU_ESP32-S3/ESP_EN` | `C33.1`, `J2.3` `3`, `R39.2`, `U9.3` `EN` | ESP32 EN / CHIP_PU reset net: header, 10 k pull-up, POR capacitor, MCU EN pin. |
| `/MCU_ESP32-S3/ESP_RX` | `J2.2` `2`, `U9.36` `U0RXD/GPIO44/CLK_OUT2` | ESP32 UART0 RX from Raspberry Pi / bring-up header. |
| `/MCU_ESP32-S3/ESP_TX` | `J2.1` `1`, `U9.37` `U0TXD/GPIO43/CLK_OUT1` | ESP32 UART0 TX to Raspberry Pi / bring-up header. |
| `/MCU_ESP32-S3/USB_DM` | `R37.2`, `U9.13` `GPIO19/U1RTS/ADC2_CH8/CLK_OUT2/USB_D-` | USB D- after 22 ohm series resistor to ESP32-S3 GPIO19 / module pin 13. |
| `/MCU_ESP32-S3/USB_DM_CONN` | `J1.2` `D-`, `U10.1` `IO1` | USB D- connector side into USBLC6 ESD device. |
| `/MCU_ESP32-S3/USB_DM_ESD` | `R37.1`, `U10.6` `IO1` | Protected USB D- node between USBLC6 and 22 ohm series resistor. |
| `/MCU_ESP32-S3/USB_DP` | `R38.2`, `U9.14` `GPIO20/U1CTS/ADC2_CH9/CLK_OUT1/USB_D+` | USB D+ after 22 ohm series resistor to ESP32-S3 GPIO20 / module pin 14. |
| `/MCU_ESP32-S3/USB_DP_CONN` | `J1.3` `D+`, `U10.3` `IO2` | USB D+ connector side into USBLC6 ESD device. |
| `/MCU_ESP32-S3/USB_DP_ESD` | `R38.1`, `U10.4` `IO2` | Protected USB D+ node between USBLC6 and 22 ohm series resistor. |
| `/POWER_IO/EXT5V` | `D6.1` `A`, `J6.1` `1` | External 5 V input from J6 pin 1 to D6 anode into +5V OR-ing. |
| `/POWER_IO/MPD_RAW1` | `C35.1`, `J4.2` `2`, `R41.1`, `R42.2` | Raw internal monitor-photodiode anode node: J4 pin, 10 k burden, 100 nF filter, and ADC isolation resistor. |
| `/POWER_IO/MPD_RAW2` | `C36.1`, `J4.4` `4`, `R43.1`, `R44.2` | Raw internal monitor-photodiode anode node: J4 pin, 10 k burden, 100 nF filter, and ADC isolation resistor. |
| `/POWER_IO/MPD_RAW3` | `C37.1`, `J4.6` `6`, `R45.1`, `R46.2` | Raw internal monitor-photodiode anode node: J4 pin, 10 k burden, 100 nF filter, and ADC isolation resistor. |
| `/POWER_IO/MPD_RAW4` | `C38.1`, `J4.8` `8`, `R47.1`, `R48.2` | Raw internal monitor-photodiode anode node: J4 pin, 10 k burden, 100 nF filter, and ADC isolation resistor. |
| `CONVST` | `J3.5` `5`, `U9.10` `GPIO17/U1TXD/ADC2_CH6` | ESP32 GPIO17 conversion-start output to external AD7606 header. |
| `GND` | `C10.2`, `C11.2`, `C12.2`, `C14.2`, `C15.2`, `C16.2`, `C17.2`, `C18.2`, `C2.2`, `C20.2`, `C21.2`, `C23.2`, `C24.2`, `C26.2`, `C27.2`, `C29.2`, `C3.2`, `C30.2`, `C31.2`, `C32.2`, `C33.2`, `C34.2`, `C35.2`, `C36.2`, `C37.2`, `C38.2`, `C4.2`, `C6.2`, `C7.2`, `C8.2`, `J1.5` `GND`, `J1.6` `SHLD`, `J2.5` `5`, `J3.6` `6`, `J4.10` `10`, `J5.2` `2`, `J6.2` `2`, `R18.2`, `R21.2`, `R23.2`, `R26.2`, `R28.2`, `R31.2`, `R33.2`, `R36.2`, `R41.2`, `R43.2`, `R45.2`, `R47.2`, `RV1.3`, `RV2.3`, `RV3.3`, `RV4.3`, `U1.4` `V-`, `U10.2` `GND`, `U11.2` `GND`, `U2.4` `V-`, `U3.4` `V-`, `U4.4` `V-`, `U5.2` `V-`, `U6.2` `V-`, `U7.2` `V-`, `U8.2` `V-`, `U9.1` `GND`, `U9.40` `GND`, `U9.41` `GND` | Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `ISENSE1` | `R19.2`, `U9.4` `GPIO4/TOUCH4/ADC1_CH3` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE2` | `R24.2`, `U9.5` `GPIO5/TOUCH5/ADC1_CH4` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE3` | `R29.2`, `U9.6` `GPIO6/TOUCH6/ADC1_CH5` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE4` | `R34.2`, `U9.7` `GPIO7/TOUCH7/ADC1_CH6` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `LASER_N1` | `J4.1` `1`, `Q1.3` `D` | Laser cathode sink path from harness J4 to AO3400A drain. |
| `LASER_N2` | `J4.3` `3`, `Q2.3` `D` | Laser cathode sink path from harness J4 to AO3400A drain. |
| `LASER_N3` | `J4.5` `5`, `Q3.3` `D` | Laser cathode sink path from harness J4 to AO3400A drain. |
| `LASER_N4` | `J4.7` `7`, `Q4.3` `D` | Laser cathode sink path from harness J4 to AO3400A drain. |
| `LASER_V+` | `J4.9` `9`, `J5.1` `1` | External laser anode / monitor-PD cathode common supply from J5 to laser harness J4. |
| `MPD1` | `R42.1`, `U9.38` `GPIO2/TOUCH2/ADC1_CH1` | Filtered internal laser monitor-photodiode telemetry into ESP32 ADC. |
| `MPD2` | `R44.1`, `U9.39` `GPIO1/TOUCH1/ADC1_CH0` | Filtered internal laser monitor-photodiode telemetry into ESP32 ADC. |
| `MPD3` | `R46.1`, `U9.12` `GPIO8/TOUCH8/ADC1_CH7/SUBSPICS1` | Filtered internal laser monitor-photodiode telemetry into ESP32 ADC. |
| `MPD4` | `R48.1`, `U9.17` `GPIO9/TOUCH9/ADC1_CH8/FSPIHD/SUBSPIHD` | Filtered internal laser monitor-photodiode telemetry into ESP32 ADC. |
| `Net-(D1-A)` | `C1.1`, `D1.2` `A`, `R1.1`, `U1.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `Net-(D1-K)` | `C3.1`, `D1.1` `K`, `R2.2` | SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `Net-(D2-A)` | `C5.1`, `D2.2` `A`, `R5.1`, `U2.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `Net-(D2-K)` | `C7.1`, `D2.1` `K`, `R6.2` | SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `Net-(D3-A)` | `C9.1`, `D3.2` `A`, `R9.1`, `U3.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `Net-(D3-K)` | `C11.1`, `D3.1` `K`, `R10.2` | SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `Net-(D4-A)` | `C13.1`, `D4.2` `A`, `R13.1`, `U4.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `Net-(D4-K)` | `C15.1`, `D4.1` `K`, `R14.2` | SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `Net-(Q1-G)` | `Q1.1` `G`, `R17.2` | AO3400A gate node after TLV9001 output resistor. |
| `Net-(Q2-G)` | `Q2.1` `G`, `R22.2` | AO3400A gate node after TLV9001 output resistor. |
| `Net-(Q3-G)` | `Q3.1` `G`, `R27.2` | AO3400A gate node after TLV9001 output resistor. |
| `Net-(Q4-G)` | `Q4.1` `G`, `R32.2` | AO3400A gate node after TLV9001 output resistor. |
| `Net-(R12-Pad2)` | `R12.2`, `RV3.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `Net-(R16-Pad2)` | `R16.2`, `RV4.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `Net-(R4-Pad2)` | `R4.2`, `RV1.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `Net-(R8-Pad2)` | `R8.2`, `RV2.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `Net-(RV1-W)` | `R3.1`, `RV1.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `Net-(RV2-W)` | `R7.1`, `RV2.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `Net-(RV3-W)` | `R11.1`, `RV3.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `Net-(RV4-W)` | `R15.1`, `RV4.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `Net-(U1-+)` | `C4.1`, `R3.2`, `U1.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `Net-(U2-+)` | `C8.1`, `R7.2`, `U2.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `Net-(U3-+)` | `C12.1`, `R11.2`, `U3.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `Net-(U4-+)` | `C16.1`, `R15.2`, `U4.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `Net-(U5-+)` | `C18.1`, `R20.2`, `R21.1`, `U5.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `Net-(U6-+)` | `C21.1`, `R25.2`, `R26.1`, `U6.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `Net-(U7-+)` | `C24.1`, `R30.2`, `R31.1`, `U7.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `Net-(U8-+)` | `C27.1`, `R35.2`, `R36.1`, `U8.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `PWM1` | `R20.1`, `U9.9` `GPIO16/U0CTS/ADC2_CH5/XTAL_32K_N` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM2` | `R25.1`, `U9.31` `GPIO38/FSPIWP/SUBSPIWP` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM3` | `R30.1`, `U9.21` `GPIO13/TOUCH13/ADC2_CH2/FSPIQ/FSPIIO7/SUBSPIQ` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM4` | `R35.1`, `U9.22` `GPIO14/TOUCH14/ADC2_CH3/FSPIWP/FSPIDQS/SUBSPIWP` | ESP32 PWM command into one laser-driver input resistor. |
| `VBUS_5V` | `D5.1` `A`, `J1.1` `VBUS`, `U10.5` `VBUS` | USB connector VBUS, USBLC6 VBUS clamp reference, and D5 anode into +5V OR-ing. |
| `VOUT1` | `C1.2`, `J3.1` `1`, `R1.2`, `U1.6` | OPA380 TIA output and feedback high side to external AD7606 header. |
| `VOUT2` | `C5.2`, `J3.2` `2`, `R5.2`, `U2.6` | OPA380 TIA output and feedback high side to external AD7606 header. |
| `VOUT3` | `C9.2`, `J3.3` `3`, `R9.2`, `U3.6` | OPA380 TIA output and feedback high side to external AD7606 header. |
| `VOUT4` | `C13.2`, `J3.4` `4`, `R13.2`, `U4.6` | OPA380 TIA output and feedback high side to external AD7606 header. |
| `unconnected-(J1-ID-Pad4)` | `J1.4` `ID` | Intentional no-connect from generated schematic. |
| `unconnected-(U1-NC-Pad1)` | `U1.1` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U1-NC-Pad5)` | `U1.5` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U1-NC-Pad8)` | `U1.8` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U11-NC-Pad4)` | `U11.4` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U2-NC-Pad1)` | `U2.1` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U2-NC-Pad5)` | `U2.5` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U2-NC-Pad8)` | `U2.8` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U3-NC-Pad1)` | `U3.1` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U3-NC-Pad5)` | `U3.5` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U3-NC-Pad8)` | `U3.8` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U4-NC-Pad1)` | `U4.1` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U4-NC-Pad5)` | `U4.5` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U4-NC-Pad8)` | `U4.8` `NC` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO10{slash}TOUCH10{slash}ADC1_CH9{slash}FSPICS0{slash}FSPIIO4{slash}SUBSPICS0-Pad18)` | `U9.18` `GPIO10/TOUCH10/ADC1_CH9/FSPICS0/FSPIIO4/SUBSPICS0` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO11{slash}TOUCH11{slash}ADC2_CH0{slash}FSPID{slash}FSPIIO5{slash}SUBSPID-Pad19)` | `U9.19` `GPIO11/TOUCH11/ADC2_CH0/FSPID/FSPIIO5/SUBSPID` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO12{slash}TOUCH12{slash}ADC2_CH1{slash}FSPICLK{slash}FSPIIO6{slash}SUBSPICLK-Pad20)` | `U9.20` `GPIO12/TOUCH12/ADC2_CH1/FSPICLK/FSPIIO6/SUBSPICLK` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO15{slash}U0RTS{slash}ADC2_CH4{slash}XTAL_32K_P-Pad8)` | `U9.8` `GPIO15/U0RTS/ADC2_CH4/XTAL_32K_P` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO18{slash}U1RXD{slash}ADC2_CH7{slash}CLK_OUT3-Pad11)` | `U9.11` `GPIO18/U1RXD/ADC2_CH7/CLK_OUT3` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO21-Pad23)` | `U9.23` `GPIO21` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO3{slash}TOUCH3{slash}ADC1_CH2-Pad15)` | `U9.15` `GPIO3/TOUCH3/ADC1_CH2` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO45-Pad26)` | `U9.26` `GPIO45` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO46-Pad16)` | `U9.16` `GPIO46` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO47{slash}SPICLK_P{slash}SUBSPICLK_P_DIFF-Pad24)` | `U9.24` `GPIO47/SPICLK_P/SUBSPICLK_P_DIFF` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-GPIO48{slash}SPICLK_N{slash}SUBSPICLK_N_DIFF-Pad25)` | `U9.25` `GPIO48/SPICLK_N/SUBSPICLK_N_DIFF` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-MTCK{slash}GPIO39{slash}CLK_OUT3{slash}SUBSPICS1-Pad32)` | `U9.32` `MTCK/GPIO39/CLK_OUT3/SUBSPICS1` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-MTDI{slash}GPIO41{slash}CLK_OUT1-Pad34)` | `U9.34` `MTDI/GPIO41/CLK_OUT1` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-MTDO{slash}GPIO40{slash}CLK_OUT2-Pad33)` | `U9.33` `MTDO/GPIO40/CLK_OUT2` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-MTMS{slash}GPIO42-Pad35)` | `U9.35` `MTMS/GPIO42` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-SPIDQS{slash}GPIO37{slash}FSPIQ{slash}SUBSPIQ-Pad30)` | `U9.30` `SPIDQS/GPIO37/FSPIQ/SUBSPIQ` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-SPIIO6{slash}GPIO35{slash}FSPID{slash}SUBSPID-Pad28)` | `U9.28` `SPIIO6/GPIO35/FSPID/SUBSPID` | Intentional no-connect from generated schematic. |
| `unconnected-(U9-SPIIO7{slash}GPIO36{slash}FSPICLK{slash}SUBSPICLK-Pad29)` | `U9.29` `SPIIO7/GPIO36/FSPICLK/SUBSPICLK` | Intentional no-connect from generated schematic. |

## Component Instance Inventory

Total schematic components: **117**.

| Ref | Sheet | Value | Footprint | LCSC | MPN |
|---|---|---|---|---|---|
| `C26` | `/LASER_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C27` | `/LASER_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C28` | `/LASER_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `Q4` | `/LASER_BLUE/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R32` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R33` | `/LASER_BLUE/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R34` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R35` | `/LASER_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R36` | `/LASER_BLUE/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22984` | `0603WAF3002T5E` |
| `U8` | `/LASER_BLUE/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `C398363` | `TLV9001IDBVR` |
| `C23` | `/LASER_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C24` | `/LASER_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C25` | `/LASER_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `Q3` | `/LASER_GREEN/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R27` | `/LASER_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R28` | `/LASER_GREEN/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R29` | `/LASER_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R30` | `/LASER_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R31` | `/LASER_GREEN/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22984` | `0603WAF3002T5E` |
| `U7` | `/LASER_GREEN/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `C398363` | `TLV9001IDBVR` |
| `C17` | `/LASER_IR/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C18` | `/LASER_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C19` | `/LASER_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `Q1` | `/LASER_IR/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R17` | `/LASER_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R18` | `/LASER_IR/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R19` | `/LASER_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R20` | `/LASER_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R21` | `/LASER_IR/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22984` | `0603WAF3002T5E` |
| `U5` | `/LASER_IR/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `C398363` | `TLV9001IDBVR` |
| `C20` | `/LASER_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C21` | `/LASER_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C22` | `/LASER_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `Q2` | `/LASER_RED/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R22` | `/LASER_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R23` | `/LASER_RED/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R24` | `/LASER_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R25` | `/LASER_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R26` | `/LASER_RED/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22984` | `0603WAF3002T5E` |
| `U6` | `/LASER_RED/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `C398363` | `TLV9001IDBVR` |
| `C29` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C30` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C31` | `/MCU_ESP32-S3/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C15850` | `CL21A106KAYNNNE` |
| `C32` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C33` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `J1` | `/MCU_ESP32-S3/` | USB Mini-B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `C5120592` | `65100516121` |
| `J2` | `/MCU_ESP32-S3/` | UART->Pi | `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical` |  |  |
| `R37` | `/MCU_ESP32-S3/` | 22R USB | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C23345` | `0603WAF220JT5E` |
| `R38` | `/MCU_ESP32-S3/` | 22R USB | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C23345` | `0603WAF220JT5E` |
| `R39` | `/MCU_ESP32-S3/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `RMC060310KFN` |
| `R40` | `/MCU_ESP32-S3/` | 10k BOOT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `RMC060310KFN` |
| `U10` | `/MCU_ESP32-S3/` | USBLC6 | `Package_TO_SOT_SMD:SOT-23-6` | `C7519` | `USBLC6-2SC6` |
| `U11` | `/MCU_ESP32-S3/` | AP2112K-3.3 | `Package_TO_SOT_SMD:SOT-23-5` | `C51118` | `AP2112K-3.3TRG1` |
| `U9` | `/MCU_ESP32-S3/` | ESP32-S3-WROOM-1 | `RF_Module:ESP32-S3-WROOM-1` | `C2913199` | `ESP32-S3-WROOM-1-N16R8` |
| `C34` | `/POWER_IO/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C15850` | `CL21A106KAYNNNE` |
| `C35` | `/POWER_IO/` | 100nF MPD | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C36` | `/POWER_IO/` | 100nF MPD | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C37` | `/POWER_IO/` | 100nF MPD | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C38` | `/POWER_IO/` | 100nF MPD | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `D5` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `C2480` | `SS14` |
| `D6` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `C2480` | `SS14` |
| `J3` | `/POWER_IO/` | AD7606 out | `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` |  |  |
| `J4` | `/POWER_IO/` | LASER+MPD out | `Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical` |  |  |
| `J5` | `/POWER_IO/` | LASER PSU | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |  |  |
| `J6` | `/POWER_IO/` | EXT 5V | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |  |  |
| `R41` | `/POWER_IO/` | 10k MPD | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R42` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R43` | `/POWER_IO/` | 10k MPD | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R44` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R45` | `/POWER_IO/` | 10k MPD | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R46` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R47` | `/POWER_IO/` | 10k MPD | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R48` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `C13` | `/TIA_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `C14` | `/TIA_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C15` | `/TIA_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C16` | `/TIA_BLUE/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C15850` | `CL21A106KAYNNNE` |
| `D4` | `/TIA_BLUE/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `C2900216` | `SFH2201` |
| `R13` | `/TIA_BLUE/` | 10M | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C57129` | `0603WAF1005T5E` |
| `R14` | `/TIA_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R15` | `/TIA_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R16` | `/TIA_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `RV4` | `/TIA_BLUE/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C81348` | `3224W-1-103E` |
| `U4` | `/TIA_BLUE/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `C201677` | `OPA380AID` |
| `C10` | `/TIA_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C11` | `/TIA_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C12` | `/TIA_GREEN/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C15850` | `CL21A106KAYNNNE` |
| `C9` | `/TIA_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `D3` | `/TIA_GREEN/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `C2900216` | `SFH2201` |
| `R10` | `/TIA_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R11` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R12` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R9` | `/TIA_GREEN/` | 10M | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C57129` | `0603WAF1005T5E` |
| `RV3` | `/TIA_GREEN/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C81348` | `3224W-1-103E` |
| `U3` | `/TIA_GREEN/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `C201677` | `OPA380AID` |
| `C1` | `/TIA_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `C2` | `/TIA_IR/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C3` | `/TIA_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C4` | `/TIA_IR/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C15850` | `CL21A106KAYNNNE` |
| `D1` | `/TIA_IR/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `C2900216` | `SFH2201` |
| `R1` | `/TIA_IR/` | 10M | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C57129` | `0603WAF1005T5E` |
| `R2` | `/TIA_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R3` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R4` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `RV1` | `/TIA_IR/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C81348` | `3224W-1-103E` |
| `U1` | `/TIA_IR/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `C201677` | `OPA380AID` |
| `C5` | `/TIA_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `C6` | `/TIA_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C1525` | `CL05B104KO5NNNC` |
| `C7` | `/TIA_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C52923` | `CL05A105KA5NQNC` |
| `C8` | `/TIA_RED/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C15850` | `CL21A106KAYNNNE` |
| `D2` | `/TIA_RED/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `C2900216` | `SFH2201` |
| `R5` | `/TIA_RED/` | 10M | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C57129` | `0603WAF1005T5E` |
| `R6` | `/TIA_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C21190` | `0603WAF1001T5E` |
| `R7` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `R8` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C269701` | `0603WAF1002T5E` |
| `RV2` | `/TIA_RED/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `C81348` | `3224W-1-103E` |
| `U2` | `/TIA_RED/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `C201677` | `OPA380AID` |

## Pin Coverage By Physical Reference

Each row is a globally unique schematic/PCB designator. No repeated hierarchical local references are expected in the exported netlist.

| Ref | Sheet | Value(s) | Footprint(s) | Pin Nets | Pin Intent |
|---|---|---|---|---|---|
| `C1` | `/TIA_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `Net-(D1-A)`<br>`2` -> `VOUT1` | `1` / `Net-(D1-A)`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT1`: Capacitor pin participating in: OPA380 TIA output and feedback high side to external AD7606 header. |
| `C10` | `/TIA_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C11` | `/TIA_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(D3-K)`<br>`2` -> `GND` | `1` / `Net-(D3-K)`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C12` | `/TIA_GREEN/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U3-+)`<br>`2` -> `GND` | `1` / `Net-(U3-+)`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C13` | `/TIA_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `Net-(D4-A)`<br>`2` -> `VOUT4` | `1` / `Net-(D4-A)`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT4`: Capacitor pin participating in: OPA380 TIA output and feedback high side to external AD7606 header. |
| `C14` | `/TIA_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C15` | `/TIA_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(D4-K)`<br>`2` -> `GND` | `1` / `Net-(D4-K)`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C16` | `/TIA_BLUE/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U4-+)`<br>`2` -> `GND` | `1` / `Net-(U4-+)`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C17` | `/LASER_IR/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C18` | `/LASER_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(U5-+)`<br>`2` -> `GND` | `1` / `Net-(U5-+)`: Capacitor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C19` | `/LASER_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/LASER_IR/FB`<br>`2` -> `/LASER_IR/LOUT` | `1` / `/LASER_IR/FB`: Capacitor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `/LASER_IR/LOUT`: Capacitor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `C2` | `/TIA_IR/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C20` | `/LASER_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C21` | `/LASER_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(U6-+)`<br>`2` -> `GND` | `1` / `Net-(U6-+)`: Capacitor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C22` | `/LASER_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/LASER_RED/FB`<br>`2` -> `/LASER_RED/LOUT` | `1` / `/LASER_RED/FB`: Capacitor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `/LASER_RED/LOUT`: Capacitor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `C23` | `/LASER_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C24` | `/LASER_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(U7-+)`<br>`2` -> `GND` | `1` / `Net-(U7-+)`: Capacitor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C25` | `/LASER_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/LASER_GREEN/FB`<br>`2` -> `/LASER_GREEN/LOUT` | `1` / `/LASER_GREEN/FB`: Capacitor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `/LASER_GREEN/LOUT`: Capacitor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `C26` | `/LASER_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C27` | `/LASER_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(U8-+)`<br>`2` -> `GND` | `1` / `Net-(U8-+)`: Capacitor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C28` | `/LASER_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `/LASER_BLUE/FB`<br>`2` -> `/LASER_BLUE/LOUT` | `1` / `/LASER_BLUE/FB`: Capacitor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `/LASER_BLUE/LOUT`: Capacitor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `C29` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C3` | `/TIA_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(D1-K)`<br>`2` -> `GND` | `1` / `Net-(D1-K)`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C30` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C31` | `/MCU_ESP32-S3/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C32` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C33` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/MCU_ESP32-S3/ESP_EN`<br>`2` -> `GND` | `1` / `/MCU_ESP32-S3/ESP_EN`: Capacitor pin participating in: ESP32 EN / CHIP_PU reset net: header, 10 k pull-up, POR capacitor, MCU EN pin.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C34` | `/POWER_IO/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C35` | `/POWER_IO/` | 100nF MPD | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/POWER_IO/MPD_RAW1`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_RAW1`: Capacitor pin participating in: Raw internal monitor-photodiode anode node: J4 pin, 10 k burden, 100 nF filter, and ADC isolation resistor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C36` | `/POWER_IO/` | 100nF MPD | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/POWER_IO/MPD_RAW2`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_RAW2`: Capacitor pin participating in: Raw internal monitor-photodiode anode node: J4 pin, 10 k burden, 100 nF filter, and ADC isolation resistor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C37` | `/POWER_IO/` | 100nF MPD | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/POWER_IO/MPD_RAW3`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_RAW3`: Capacitor pin participating in: Raw internal monitor-photodiode anode node: J4 pin, 10 k burden, 100 nF filter, and ADC isolation resistor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C38` | `/POWER_IO/` | 100nF MPD | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/POWER_IO/MPD_RAW4`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_RAW4`: Capacitor pin participating in: Raw internal monitor-photodiode anode node: J4 pin, 10 k burden, 100 nF filter, and ADC isolation resistor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C4` | `/TIA_IR/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U1-+)`<br>`2` -> `GND` | `1` / `Net-(U1-+)`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C5` | `/TIA_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `Net-(D2-A)`<br>`2` -> `VOUT2` | `1` / `Net-(D2-A)`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT2`: Capacitor pin participating in: OPA380 TIA output and feedback high side to external AD7606 header. |
| `C6` | `/TIA_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C7` | `/TIA_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(D2-K)`<br>`2` -> `GND` | `1` / `Net-(D2-K)`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C8` | `/TIA_RED/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U2-+)`<br>`2` -> `GND` | `1` / `Net-(U2-+)`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C9` | `/TIA_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `Net-(D3-A)`<br>`2` -> `VOUT3` | `1` / `Net-(D3-A)`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT3`: Capacitor pin participating in: OPA380 TIA output and feedback high side to external AD7606 header. |
| `D1` | `/TIA_IR/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `Net-(D1-K)`<br>`2` `A` -> `Net-(D1-A)` | `1` / `Net-(D1-K)`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `Net-(D1-A)`: SFH2201 anode into the OPA380 summing node. |
| `D2` | `/TIA_RED/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `Net-(D2-K)`<br>`2` `A` -> `Net-(D2-A)` | `1` / `Net-(D2-K)`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `Net-(D2-A)`: SFH2201 anode into the OPA380 summing node. |
| `D3` | `/TIA_GREEN/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `Net-(D3-K)`<br>`2` `A` -> `Net-(D3-A)` | `1` / `Net-(D3-K)`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `Net-(D3-A)`: SFH2201 anode into the OPA380 summing node. |
| `D4` | `/TIA_BLUE/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `Net-(D4-K)`<br>`2` `A` -> `Net-(D4-A)` | `1` / `Net-(D4-K)`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `Net-(D4-A)`: SFH2201 anode into the OPA380 summing node. |
| `D5` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `1` `A` -> `VBUS_5V`<br>`2` `K` -> `+5V` | `1` / `VBUS_5V`: SS14 anode receives one pre-OR 5V source.<br>`2` / `+5V`: SS14 cathode feeds the post-OR +5V rail. |
| `D6` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `1` `A` -> `/POWER_IO/EXT5V`<br>`2` `K` -> `+5V` | `1` / `/POWER_IO/EXT5V`: SS14 anode receives one pre-OR 5V source.<br>`2` / `+5V`: SS14 cathode feeds the post-OR +5V rail. |
| `J1` | `/MCU_ESP32-S3/` | USB Mini-B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `1` `VBUS` -> `VBUS_5V`<br>`2` `D-` -> `/MCU_ESP32-S3/USB_DM_CONN`<br>`3` `D+` -> `/MCU_ESP32-S3/USB_DP_CONN`<br>`4` `ID` -> `unconnected-(J1-ID-Pad4)`<br>`5` `GND` -> `GND`<br>`6` `SHLD` -> `GND` | `1` / `VBUS_5V`: USB Mini-B VBUS entry into VBUS_5V.<br>`2` / `/MCU_ESP32-S3/USB_DM_CONN`: USB Mini-B D- connector pin into USBLC6 IO1.<br>`3` / `/MCU_ESP32-S3/USB_DP_CONN`: USB Mini-B D+ connector pin into USBLC6 IO2.<br>`4` / `unconnected-(J1-ID-Pad4)`: Intentional no-connect for USB Mini-B pin 4 `ID`.<br>`5` / `GND`: USB Mini-B signal ground.<br>`6` / `GND`: USB Mini-B shield tied to board GND. |
| `J2` | `/MCU_ESP32-S3/` | UART->Pi | `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical` | `1` `1` -> `/MCU_ESP32-S3/ESP_TX`<br>`2` `2` -> `/MCU_ESP32-S3/ESP_RX`<br>`3` `3` -> `/MCU_ESP32-S3/ESP_EN`<br>`4` `4` -> `/MCU_ESP32-S3/ESP_BOOT`<br>`5` `5` -> `GND` | `1` / `/MCU_ESP32-S3/ESP_TX`: Bring-up header ESP32 UART TX.<br>`2` / `/MCU_ESP32-S3/ESP_RX`: Bring-up header ESP32 UART RX.<br>`3` / `/MCU_ESP32-S3/ESP_EN`: Bring-up header ESP32 EN/reset access.<br>`4` / `/MCU_ESP32-S3/ESP_BOOT`: Bring-up header ESP32 GPIO0/BOOT access.<br>`5` / `GND`: Bring-up header ground reference. |
| `J3` | `/POWER_IO/` | AD7606 out | `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` | `1` `1` -> `VOUT1`<br>`2` `2` -> `VOUT2`<br>`3` `3` -> `VOUT3`<br>`4` `4` -> `VOUT4`<br>`5` `5` -> `CONVST`<br>`6` `6` -> `GND` | `1` / `VOUT1`: External ADC header pin carrying one OPA380 TIA output.<br>`2` / `VOUT2`: External ADC header pin carrying one OPA380 TIA output.<br>`3` / `VOUT3`: External ADC header pin carrying one OPA380 TIA output.<br>`4` / `VOUT4`: External ADC header pin carrying one OPA380 TIA output.<br>`5` / `CONVST`: External ADC header conversion-start control pin.<br>`6` / `GND`: External ADC header ground reference. |
| `J4` | `/POWER_IO/` | LASER+MPD out | `Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical` | `1` `1` -> `LASER_N1`<br>`10` `10` -> `GND`<br>`2` `2` -> `/POWER_IO/MPD_RAW1`<br>`3` `3` -> `LASER_N2`<br>`4` `4` -> `/POWER_IO/MPD_RAW2`<br>`5` `5` -> `LASER_N3`<br>`6` `6` -> `/POWER_IO/MPD_RAW3`<br>`7` `7` -> `LASER_N4`<br>`8` `8` -> `/POWER_IO/MPD_RAW4`<br>`9` `9` -> `LASER_V+` | `1` / `LASER_N1`: Laser harness cathode sink output for one channel.<br>`10` / `GND`: Laser harness shield/return ground.<br>`2` / `/POWER_IO/MPD_RAW1`: Laser harness internal monitor-PD anode input for one channel.<br>`3` / `LASER_N2`: Laser harness cathode sink output for one channel.<br>`4` / `/POWER_IO/MPD_RAW2`: Laser harness internal monitor-PD anode input for one channel.<br>`5` / `LASER_N3`: Laser harness cathode sink output for one channel.<br>`6` / `/POWER_IO/MPD_RAW3`: Laser harness internal monitor-PD anode input for one channel.<br>`7` / `LASER_N4`: Laser harness cathode sink output for one channel.<br>`8` / `/POWER_IO/MPD_RAW4`: Laser harness internal monitor-PD anode input for one channel.<br>`9` / `LASER_V+`: Laser harness common laser anode / monitor-PD cathode supply. |
| `J5` | `/POWER_IO/` | LASER PSU | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | `1` `1` -> `LASER_V+`<br>`2` `2` -> `GND` | `1` / `LASER_V+`: External laser-anode supply input.<br>`2` / `GND`: Laser supply connector return ground. |
| `J6` | `/POWER_IO/` | EXT 5V | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | `1` `1` -> `/POWER_IO/EXT5V`<br>`2` `2` -> `GND` | `1` / `/POWER_IO/EXT5V`: External 5V input before OR-ing diode.<br>`2` / `GND`: External 5V connector ground. |
| `Q1` | `/LASER_IR/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `Net-(Q1-G)`<br>`2` `S` -> `/LASER_IR/FB`<br>`3` `D` -> `LASER_N1` | `1` / `Net-(Q1-G)`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_IR/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N1`: AO3400A drain as low-side laser cathode sink. |
| `Q2` | `/LASER_RED/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `Net-(Q2-G)`<br>`2` `S` -> `/LASER_RED/FB`<br>`3` `D` -> `LASER_N2` | `1` / `Net-(Q2-G)`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_RED/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N2`: AO3400A drain as low-side laser cathode sink. |
| `Q3` | `/LASER_GREEN/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `Net-(Q3-G)`<br>`2` `S` -> `/LASER_GREEN/FB`<br>`3` `D` -> `LASER_N3` | `1` / `Net-(Q3-G)`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_GREEN/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N3`: AO3400A drain as low-side laser cathode sink. |
| `Q4` | `/LASER_BLUE/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `Net-(Q4-G)`<br>`2` `S` -> `/LASER_BLUE/FB`<br>`3` `D` -> `LASER_N4` | `1` / `Net-(Q4-G)`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_BLUE/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N4`: AO3400A drain as low-side laser cathode sink. |
| `R1` | `/TIA_IR/` | 10M | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(D1-A)`<br>`2` -> `VOUT1` | `1` / `Net-(D1-A)`: Resistor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT1`: Resistor pin participating in: OPA380 TIA output and feedback high side to external AD7606 header. |
| `R10` | `/TIA_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(D3-K)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(D3-K)`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `R11` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(RV3-W)`<br>`2` -> `Net-(U3-+)` | `1` / `Net-(RV3-W)`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `Net-(U3-+)`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R12` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(R12-Pad2)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(R12-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side. |
| `R13` | `/TIA_BLUE/` | 10M | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(D4-A)`<br>`2` -> `VOUT4` | `1` / `Net-(D4-A)`: Resistor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT4`: Resistor pin participating in: OPA380 TIA output and feedback high side to external AD7606 header. |
| `R14` | `/TIA_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(D4-K)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(D4-K)`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `R15` | `/TIA_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(RV4-W)`<br>`2` -> `Net-(U4-+)` | `1` / `Net-(RV4-W)`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `Net-(U4-+)`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R16` | `/TIA_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(R16-Pad2)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(R16-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side. |
| `R17` | `/LASER_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_IR/LOUT`<br>`2` -> `Net-(Q1-G)` | `1` / `/LASER_IR/LOUT`: Resistor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor.<br>`2` / `Net-(Q1-G)`: Resistor pin participating in: AO3400A gate node after TLV9001 output resistor. |
| `R18` | `/LASER_IR/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `1` -> `/LASER_IR/FB`<br>`2` -> `GND` | `1` / `/LASER_IR/FB`: Laser current-sense resistor high side.<br>`2` / `GND`: Laser current-sense resistor low-side GND return. |
| `R19` | `/LASER_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_IR/FB`<br>`2` -> `ISENSE1` | `1` / `/LASER_IR/FB`: Resistor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `ISENSE1`: Resistor pin participating in: Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `R2` | `/TIA_IR/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(D1-K)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(D1-K)`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `R20` | `/LASER_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `PWM1`<br>`2` -> `Net-(U5-+)` | `1` / `PWM1`: Resistor pin participating in: ESP32 PWM command into one laser-driver input resistor.<br>`2` / `Net-(U5-+)`: Resistor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input. |
| `R21` | `/LASER_IR/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(U5-+)`<br>`2` -> `GND` | `1` / `Net-(U5-+)`: PWM command limiter node.<br>`2` / `GND`: PWM command limiter ground leg. |
| `R22` | `/LASER_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_RED/LOUT`<br>`2` -> `Net-(Q2-G)` | `1` / `/LASER_RED/LOUT`: Resistor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor.<br>`2` / `Net-(Q2-G)`: Resistor pin participating in: AO3400A gate node after TLV9001 output resistor. |
| `R23` | `/LASER_RED/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `1` -> `/LASER_RED/FB`<br>`2` -> `GND` | `1` / `/LASER_RED/FB`: Laser current-sense resistor high side.<br>`2` / `GND`: Laser current-sense resistor low-side GND return. |
| `R24` | `/LASER_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_RED/FB`<br>`2` -> `ISENSE2` | `1` / `/LASER_RED/FB`: Resistor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `ISENSE2`: Resistor pin participating in: Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `R25` | `/LASER_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `PWM2`<br>`2` -> `Net-(U6-+)` | `1` / `PWM2`: Resistor pin participating in: ESP32 PWM command into one laser-driver input resistor.<br>`2` / `Net-(U6-+)`: Resistor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input. |
| `R26` | `/LASER_RED/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(U6-+)`<br>`2` -> `GND` | `1` / `Net-(U6-+)`: PWM command limiter node.<br>`2` / `GND`: PWM command limiter ground leg. |
| `R27` | `/LASER_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_GREEN/LOUT`<br>`2` -> `Net-(Q3-G)` | `1` / `/LASER_GREEN/LOUT`: Resistor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor.<br>`2` / `Net-(Q3-G)`: Resistor pin participating in: AO3400A gate node after TLV9001 output resistor. |
| `R28` | `/LASER_GREEN/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `1` -> `/LASER_GREEN/FB`<br>`2` -> `GND` | `1` / `/LASER_GREEN/FB`: Laser current-sense resistor high side.<br>`2` / `GND`: Laser current-sense resistor low-side GND return. |
| `R29` | `/LASER_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_GREEN/FB`<br>`2` -> `ISENSE3` | `1` / `/LASER_GREEN/FB`: Resistor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `ISENSE3`: Resistor pin participating in: Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `R3` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(RV1-W)`<br>`2` -> `Net-(U1-+)` | `1` / `Net-(RV1-W)`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `Net-(U1-+)`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R30` | `/LASER_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `PWM3`<br>`2` -> `Net-(U7-+)` | `1` / `PWM3`: Resistor pin participating in: ESP32 PWM command into one laser-driver input resistor.<br>`2` / `Net-(U7-+)`: Resistor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input. |
| `R31` | `/LASER_GREEN/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(U7-+)`<br>`2` -> `GND` | `1` / `Net-(U7-+)`: PWM command limiter node.<br>`2` / `GND`: PWM command limiter ground leg. |
| `R32` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_BLUE/LOUT`<br>`2` -> `Net-(Q4-G)` | `1` / `/LASER_BLUE/LOUT`: Resistor pin participating in: TLV9001 output and compensation node before the 1 k MOSFET gate resistor.<br>`2` / `Net-(Q4-G)`: Resistor pin participating in: AO3400A gate node after TLV9001 output resistor. |
| `R33` | `/LASER_BLUE/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `1` -> `/LASER_BLUE/FB`<br>`2` -> `GND` | `1` / `/LASER_BLUE/FB`: Laser current-sense resistor high side.<br>`2` / `GND`: Laser current-sense resistor low-side GND return. |
| `R34` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/LASER_BLUE/FB`<br>`2` -> `ISENSE4` | `1` / `/LASER_BLUE/FB`: Resistor pin participating in: Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input.<br>`2` / `ISENSE4`: Resistor pin participating in: Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `R35` | `/LASER_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `PWM4`<br>`2` -> `Net-(U8-+)` | `1` / `PWM4`: Resistor pin participating in: ESP32 PWM command into one laser-driver input resistor.<br>`2` / `Net-(U8-+)`: Resistor pin participating in: Laser command filter/limiter node into TLV9001 non-inverting input. |
| `R36` | `/LASER_BLUE/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(U8-+)`<br>`2` -> `GND` | `1` / `Net-(U8-+)`: PWM command limiter node.<br>`2` / `GND`: PWM command limiter ground leg. |
| `R37` | `/MCU_ESP32-S3/` | 22R USB | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/MCU_ESP32-S3/USB_DM_ESD`<br>`2` -> `/MCU_ESP32-S3/USB_DM` | `1` / `/MCU_ESP32-S3/USB_DM_ESD`: USB series resistor connector/ESD side.<br>`2` / `/MCU_ESP32-S3/USB_DM`: USB series resistor ESP32 module side. |
| `R38` | `/MCU_ESP32-S3/` | 22R USB | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/MCU_ESP32-S3/USB_DP_ESD`<br>`2` -> `/MCU_ESP32-S3/USB_DP` | `1` / `/MCU_ESP32-S3/USB_DP_ESD`: USB series resistor connector/ESD side.<br>`2` / `/MCU_ESP32-S3/USB_DP`: USB series resistor ESP32 module side. |
| `R39` | `/MCU_ESP32-S3/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/ESP_EN` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/ESP_EN`: Resistor pin participating in: ESP32 EN / CHIP_PU reset net: header, 10 k pull-up, POR capacitor, MCU EN pin. |
| `R4` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(R4-Pad2)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(R4-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side. |
| `R40` | `/MCU_ESP32-S3/` | 10k BOOT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/ESP_BOOT` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/ESP_BOOT`: Resistor pin participating in: ESP32 GPIO0 boot-mode net: header, 10 k pull-up, MCU GPIO0 pin. |
| `R41` | `/POWER_IO/` | 10k MPD | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_RAW1`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_RAW1`: Monitor-PD burden resistor raw MPD side.<br>`2` / `GND`: Monitor-PD burden resistor ground side. |
| `R42` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD1`<br>`2` -> `/POWER_IO/MPD_RAW1` | `1` / `MPD1`: Monitor-PD ADC isolation resistor filtered ADC side.<br>`2` / `/POWER_IO/MPD_RAW1`: Monitor-PD ADC isolation resistor raw/filter side. |
| `R43` | `/POWER_IO/` | 10k MPD | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_RAW2`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_RAW2`: Monitor-PD burden resistor raw MPD side.<br>`2` / `GND`: Monitor-PD burden resistor ground side. |
| `R44` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD2`<br>`2` -> `/POWER_IO/MPD_RAW2` | `1` / `MPD2`: Monitor-PD ADC isolation resistor filtered ADC side.<br>`2` / `/POWER_IO/MPD_RAW2`: Monitor-PD ADC isolation resistor raw/filter side. |
| `R45` | `/POWER_IO/` | 10k MPD | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_RAW3`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_RAW3`: Monitor-PD burden resistor raw MPD side.<br>`2` / `GND`: Monitor-PD burden resistor ground side. |
| `R46` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD3`<br>`2` -> `/POWER_IO/MPD_RAW3` | `1` / `MPD3`: Monitor-PD ADC isolation resistor filtered ADC side.<br>`2` / `/POWER_IO/MPD_RAW3`: Monitor-PD ADC isolation resistor raw/filter side. |
| `R47` | `/POWER_IO/` | 10k MPD | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_RAW4`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_RAW4`: Monitor-PD burden resistor raw MPD side.<br>`2` / `GND`: Monitor-PD burden resistor ground side. |
| `R48` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD4`<br>`2` -> `/POWER_IO/MPD_RAW4` | `1` / `MPD4`: Monitor-PD ADC isolation resistor filtered ADC side.<br>`2` / `/POWER_IO/MPD_RAW4`: Monitor-PD ADC isolation resistor raw/filter side. |
| `R5` | `/TIA_RED/` | 10M | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(D2-A)`<br>`2` -> `VOUT2` | `1` / `Net-(D2-A)`: Resistor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT2`: Resistor pin participating in: OPA380 TIA output and feedback high side to external AD7606 header. |
| `R6` | `/TIA_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(D2-K)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(D2-K)`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `R7` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(RV2-W)`<br>`2` -> `Net-(U2-+)` | `1` / `Net-(RV2-W)`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `Net-(U2-+)`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R8` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(R8-Pad2)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(R8-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side. |
| `R9` | `/TIA_GREEN/` | 10M | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(D3-A)`<br>`2` -> `VOUT3` | `1` / `Net-(D3-A)`: Resistor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT3`: Resistor pin participating in: OPA380 TIA output and feedback high side to external AD7606 header. |
| `RV1` | `/TIA_IR/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(R4-Pad2)`<br>`2` `W` -> `Net-(RV1-W)`<br>`3` -> `GND` | `1` / `Net-(R4-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side.<br>`2` / `Net-(RV1-W)`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV2` | `/TIA_RED/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(R8-Pad2)`<br>`2` `W` -> `Net-(RV2-W)`<br>`3` -> `GND` | `1` / `Net-(R8-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side.<br>`2` / `Net-(RV2-W)`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV3` | `/TIA_GREEN/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(R12-Pad2)`<br>`2` `W` -> `Net-(RV3-W)`<br>`3` -> `GND` | `1` / `Net-(R12-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side.<br>`2` / `Net-(RV3-W)`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV4` | `/TIA_BLUE/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(R16-Pad2)`<br>`2` `W` -> `Net-(RV4-W)`<br>`3` -> `GND` | `1` / `Net-(R16-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side.<br>`2` / `Net-(RV4-W)`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `U1` | `/TIA_IR/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U1-NC-Pad1)`<br>`2` `-` -> `Net-(D1-A)`<br>`3` `+` -> `Net-(U1-+)`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U1-NC-Pad5)`<br>`6` -> `VOUT1`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U1-NC-Pad8)` | `1` / `unconnected-(U1-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `Net-(D1-A)`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `Net-(U1-+)`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U1-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT1`: OPA380 TIA output to feedback high side and AD7606 header.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U1-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U10` | `/MCU_ESP32-S3/` | USBLC6 | `Package_TO_SOT_SMD:SOT-23-6` | `1` `IO1` -> `/MCU_ESP32-S3/USB_DM_CONN`<br>`2` `GND` -> `GND`<br>`3` `IO2` -> `/MCU_ESP32-S3/USB_DP_CONN`<br>`4` `IO2` -> `/MCU_ESP32-S3/USB_DP_ESD`<br>`5` `VBUS` -> `VBUS_5V`<br>`6` `IO1` -> `/MCU_ESP32-S3/USB_DM_ESD` | `1` / `/MCU_ESP32-S3/USB_DM_CONN`: USBLC6 IO1 side of the protected USB D- path.<br>`2` / `GND`: USBLC6 ESD return pin to board GND.<br>`3` / `/MCU_ESP32-S3/USB_DP_CONN`: USBLC6 IO2 side of the protected USB D+ path.<br>`4` / `/MCU_ESP32-S3/USB_DP_ESD`: USBLC6 IO2 side of the protected USB D+ path.<br>`5` / `VBUS_5V`: USBLC6 VBUS clamp reference tied to USB VBUS.<br>`6` / `/MCU_ESP32-S3/USB_DM_ESD`: USBLC6 IO1 side of the protected USB D- path. |
| `U11` | `/MCU_ESP32-S3/` | AP2112K-3.3 | `Package_TO_SOT_SMD:SOT-23-5` | `1` `VIN` -> `+5V`<br>`2` `GND` -> `GND`<br>`3` `EN` -> `+5V`<br>`4` `NC` -> `unconnected-(U11-NC-Pad4)`<br>`5` `VOUT` -> `+3V3` | `1` / `+5V`: AP2112 VIN from post-OR +5V rail.<br>`2` / `GND`: AP2112 ground return.<br>`3` / `+5V`: AP2112 enable tied high to +5V for always-on bench 3V3.<br>`4` / `unconnected-(U11-NC-Pad4)`: Intentional no-connect for AP2112K-3.3 pin 4 `NC`.<br>`5` / `+3V3`: AP2112 regulated +3V3 output. |
| `U2` | `/TIA_RED/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U2-NC-Pad1)`<br>`2` `-` -> `Net-(D2-A)`<br>`3` `+` -> `Net-(U2-+)`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U2-NC-Pad5)`<br>`6` -> `VOUT2`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U2-NC-Pad8)` | `1` / `unconnected-(U2-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `Net-(D2-A)`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `Net-(U2-+)`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U2-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT2`: OPA380 TIA output to feedback high side and AD7606 header.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U2-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U3` | `/TIA_GREEN/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U3-NC-Pad1)`<br>`2` `-` -> `Net-(D3-A)`<br>`3` `+` -> `Net-(U3-+)`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U3-NC-Pad5)`<br>`6` -> `VOUT3`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U3-NC-Pad8)` | `1` / `unconnected-(U3-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `Net-(D3-A)`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `Net-(U3-+)`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U3-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT3`: OPA380 TIA output to feedback high side and AD7606 header.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U3-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U4` | `/TIA_BLUE/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U4-NC-Pad1)`<br>`2` `-` -> `Net-(D4-A)`<br>`3` `+` -> `Net-(U4-+)`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U4-NC-Pad5)`<br>`6` -> `VOUT4`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U4-NC-Pad8)` | `1` / `unconnected-(U4-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `Net-(D4-A)`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `Net-(U4-+)`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U4-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT4`: OPA380 TIA output to feedback high side and AD7606 header.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U4-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U5` | `/LASER_IR/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_IR/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `Net-(U5-+)`<br>`4` `-` -> `/LASER_IR/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_IR/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `Net-(U5-+)`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_IR/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U6` | `/LASER_RED/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_RED/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `Net-(U6-+)`<br>`4` `-` -> `/LASER_RED/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_RED/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `Net-(U6-+)`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_RED/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U7` | `/LASER_GREEN/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_GREEN/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `Net-(U7-+)`<br>`4` `-` -> `/LASER_GREEN/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_GREEN/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `Net-(U7-+)`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_GREEN/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U8` | `/LASER_BLUE/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_BLUE/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `Net-(U8-+)`<br>`4` `-` -> `/LASER_BLUE/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_BLUE/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `Net-(U8-+)`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_BLUE/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U9` | `/MCU_ESP32-S3/` | ESP32-S3-WROOM-1 | `RF_Module:ESP32-S3-WROOM-1` | `1` `GND` -> `GND`<br>`10` `GPIO17/U1TXD/ADC2_CH6` -> `CONVST`<br>`11` `GPIO18/U1RXD/ADC2_CH7/CLK_OUT3` -> `unconnected-(U9-GPIO18{slash}U1RXD{slash}ADC2_CH7{slash}CLK_OUT3-Pad11)`<br>`12` `GPIO8/TOUCH8/ADC1_CH7/SUBSPICS1` -> `MPD3`<br>`13` `GPIO19/U1RTS/ADC2_CH8/CLK_OUT2/USB_D-` -> `/MCU_ESP32-S3/USB_DM`<br>`14` `GPIO20/U1CTS/ADC2_CH9/CLK_OUT1/USB_D+` -> `/MCU_ESP32-S3/USB_DP`<br>`15` `GPIO3/TOUCH3/ADC1_CH2` -> `unconnected-(U9-GPIO3{slash}TOUCH3{slash}ADC1_CH2-Pad15)`<br>`16` `GPIO46` -> `unconnected-(U9-GPIO46-Pad16)`<br>`17` `GPIO9/TOUCH9/ADC1_CH8/FSPIHD/SUBSPIHD` -> `MPD4`<br>`18` `GPIO10/TOUCH10/ADC1_CH9/FSPICS0/FSPIIO4/SUBSPICS0` -> `unconnected-(U9-GPIO10{slash}TOUCH10{slash}ADC1_CH9{slash}FSPICS0{slash}FSPIIO4{slash}SUBSPICS0-Pad18)`<br>`19` `GPIO11/TOUCH11/ADC2_CH0/FSPID/FSPIIO5/SUBSPID` -> `unconnected-(U9-GPIO11{slash}TOUCH11{slash}ADC2_CH0{slash}FSPID{slash}FSPIIO5{slash}SUBSPID-Pad19)`<br>`2` `3V3` -> `+3V3`<br>`20` `GPIO12/TOUCH12/ADC2_CH1/FSPICLK/FSPIIO6/SUBSPICLK` -> `unconnected-(U9-GPIO12{slash}TOUCH12{slash}ADC2_CH1{slash}FSPICLK{slash}FSPIIO6{slash}SUBSPICLK-Pad20)`<br>`21` `GPIO13/TOUCH13/ADC2_CH2/FSPIQ/FSPIIO7/SUBSPIQ` -> `PWM3`<br>`22` `GPIO14/TOUCH14/ADC2_CH3/FSPIWP/FSPIDQS/SUBSPIWP` -> `PWM4`<br>`23` `GPIO21` -> `unconnected-(U9-GPIO21-Pad23)`<br>`24` `GPIO47/SPICLK_P/SUBSPICLK_P_DIFF` -> `unconnected-(U9-GPIO47{slash}SPICLK_P{slash}SUBSPICLK_P_DIFF-Pad24)`<br>`25` `GPIO48/SPICLK_N/SUBSPICLK_N_DIFF` -> `unconnected-(U9-GPIO48{slash}SPICLK_N{slash}SUBSPICLK_N_DIFF-Pad25)`<br>`26` `GPIO45` -> `unconnected-(U9-GPIO45-Pad26)`<br>`27` `GPIO0/BOOT` -> `/MCU_ESP32-S3/ESP_BOOT`<br>`28` `SPIIO6/GPIO35/FSPID/SUBSPID` -> `unconnected-(U9-SPIIO6{slash}GPIO35{slash}FSPID{slash}SUBSPID-Pad28)`<br>`29` `SPIIO7/GPIO36/FSPICLK/SUBSPICLK` -> `unconnected-(U9-SPIIO7{slash}GPIO36{slash}FSPICLK{slash}SUBSPICLK-Pad29)`<br>`3` `EN` -> `/MCU_ESP32-S3/ESP_EN`<br>`30` `SPIDQS/GPIO37/FSPIQ/SUBSPIQ` -> `unconnected-(U9-SPIDQS{slash}GPIO37{slash}FSPIQ{slash}SUBSPIQ-Pad30)`<br>`31` `GPIO38/FSPIWP/SUBSPIWP` -> `PWM2`<br>`32` `MTCK/GPIO39/CLK_OUT3/SUBSPICS1` -> `unconnected-(U9-MTCK{slash}GPIO39{slash}CLK_OUT3{slash}SUBSPICS1-Pad32)`<br>`33` `MTDO/GPIO40/CLK_OUT2` -> `unconnected-(U9-MTDO{slash}GPIO40{slash}CLK_OUT2-Pad33)`<br>`34` `MTDI/GPIO41/CLK_OUT1` -> `unconnected-(U9-MTDI{slash}GPIO41{slash}CLK_OUT1-Pad34)`<br>`35` `MTMS/GPIO42` -> `unconnected-(U9-MTMS{slash}GPIO42-Pad35)`<br>`36` `U0RXD/GPIO44/CLK_OUT2` -> `/MCU_ESP32-S3/ESP_RX`<br>`37` `U0TXD/GPIO43/CLK_OUT1` -> `/MCU_ESP32-S3/ESP_TX`<br>`38` `GPIO2/TOUCH2/ADC1_CH1` -> `MPD1`<br>`39` `GPIO1/TOUCH1/ADC1_CH0` -> `MPD2`<br>`4` `GPIO4/TOUCH4/ADC1_CH3` -> `ISENSE1`<br>`40` `GND` -> `GND`<br>`41` `GND` -> `GND`<br>`5` `GPIO5/TOUCH5/ADC1_CH4` -> `ISENSE2`<br>`6` `GPIO6/TOUCH6/ADC1_CH5` -> `ISENSE3`<br>`7` `GPIO7/TOUCH7/ADC1_CH6` -> `ISENSE4`<br>`8` `GPIO15/U0RTS/ADC2_CH4/XTAL_32K_P` -> `unconnected-(U9-GPIO15{slash}U0RTS{slash}ADC2_CH4{slash}XTAL_32K_P-Pad8)`<br>`9` `GPIO16/U0CTS/ADC2_CH5/XTAL_32K_N` -> `PWM1` | `1` / `GND`: ESP32-S3 module ground/return pin.<br>`10` / `CONVST`: ESP32-S3 GPIO output for the external AD7606 conversion-start line.<br>`11` / `unconnected-(U9-GPIO18{slash}U1RXD{slash}ADC2_CH7{slash}CLK_OUT3-Pad11)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 11 `GPIO18/U1RXD/ADC2_CH7/CLK_OUT3`.<br>`12` / `MPD3`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`13` / `/MCU_ESP32-S3/USB_DM`: ESP32-S3 native USB D- pin GPIO19/module pin 13.<br>`14` / `/MCU_ESP32-S3/USB_DP`: ESP32-S3 native USB D+ pin GPIO20/module pin 14.<br>`15` / `unconnected-(U9-GPIO3{slash}TOUCH3{slash}ADC1_CH2-Pad15)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 15 `GPIO3/TOUCH3/ADC1_CH2`.<br>`16` / `unconnected-(U9-GPIO46-Pad16)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 16 `GPIO46`.<br>`17` / `MPD4`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`18` / `unconnected-(U9-GPIO10{slash}TOUCH10{slash}ADC1_CH9{slash}FSPICS0{slash}FSPIIO4{slash}SUBSPICS0-Pad18)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 18 `GPIO10/TOUCH10/ADC1_CH9/FSPICS0/FSPIIO4/SUBSPICS0`.<br>`19` / `unconnected-(U9-GPIO11{slash}TOUCH11{slash}ADC2_CH0{slash}FSPID{slash}FSPIIO5{slash}SUBSPID-Pad19)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 19 `GPIO11/TOUCH11/ADC2_CH0/FSPID/FSPIIO5/SUBSPID`.<br>`2` / `+3V3`: ESP32-S3 module 3V3 supply input.<br>`20` / `unconnected-(U9-GPIO12{slash}TOUCH12{slash}ADC2_CH1{slash}FSPICLK{slash}FSPIIO6{slash}SUBSPICLK-Pad20)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 20 `GPIO12/TOUCH12/ADC2_CH1/FSPICLK/FSPIIO6/SUBSPICLK`.<br>`21` / `PWM3`: ESP32-S3 PWM output for one laser current command channel.<br>`22` / `PWM4`: ESP32-S3 PWM output for one laser current command channel.<br>`23` / `unconnected-(U9-GPIO21-Pad23)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 23 `GPIO21`.<br>`24` / `unconnected-(U9-GPIO47{slash}SPICLK_P{slash}SUBSPICLK_P_DIFF-Pad24)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 24 `GPIO47/SPICLK_P/SUBSPICLK_P_DIFF`.<br>`25` / `unconnected-(U9-GPIO48{slash}SPICLK_N{slash}SUBSPICLK_N_DIFF-Pad25)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 25 `GPIO48/SPICLK_N/SUBSPICLK_N_DIFF`.<br>`26` / `unconnected-(U9-GPIO45-Pad26)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 26 `GPIO45`.<br>`27` / `/MCU_ESP32-S3/ESP_BOOT`: ESP32-S3 GPIO0 boot strap with pull-up and header access.<br>`28` / `unconnected-(U9-SPIIO6{slash}GPIO35{slash}FSPID{slash}SUBSPID-Pad28)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 28 `SPIIO6/GPIO35/FSPID/SUBSPID`.<br>`29` / `unconnected-(U9-SPIIO7{slash}GPIO36{slash}FSPICLK{slash}SUBSPICLK-Pad29)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 29 `SPIIO7/GPIO36/FSPICLK/SUBSPICLK`.<br>`3` / `/MCU_ESP32-S3/ESP_EN`: ESP32-S3 EN/CHIP_PU reset pin with pull-up, POR cap, and header access.<br>`30` / `unconnected-(U9-SPIDQS{slash}GPIO37{slash}FSPIQ{slash}SUBSPIQ-Pad30)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 30 `SPIDQS/GPIO37/FSPIQ/SUBSPIQ`.<br>`31` / `PWM2`: ESP32-S3 PWM output for one laser current command channel.<br>`32` / `unconnected-(U9-MTCK{slash}GPIO39{slash}CLK_OUT3{slash}SUBSPICS1-Pad32)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 32 `MTCK/GPIO39/CLK_OUT3/SUBSPICS1`.<br>`33` / `unconnected-(U9-MTDO{slash}GPIO40{slash}CLK_OUT2-Pad33)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 33 `MTDO/GPIO40/CLK_OUT2`.<br>`34` / `unconnected-(U9-MTDI{slash}GPIO41{slash}CLK_OUT1-Pad34)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 34 `MTDI/GPIO41/CLK_OUT1`.<br>`35` / `unconnected-(U9-MTMS{slash}GPIO42-Pad35)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 35 `MTMS/GPIO42`.<br>`36` / `/MCU_ESP32-S3/ESP_RX`: ESP32-S3 UART0 RX brought to the bench header.<br>`37` / `/MCU_ESP32-S3/ESP_TX`: ESP32-S3 UART0 TX brought to the bench header.<br>`38` / `MPD1`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`39` / `MPD2`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`4` / `ISENSE1`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`40` / `GND`: ESP32-S3 module ground/return pin.<br>`41` / `GND`: ESP32-S3 module ground/return pin.<br>`5` / `ISENSE2`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`6` / `ISENSE3`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`7` / `ISENSE4`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`8` / `unconnected-(U9-GPIO15{slash}U0RTS{slash}ADC2_CH4{slash}XTAL_32K_P-Pad8)`: Intentional no-connect for ESP32-S3-WROOM-1 pin 8 `GPIO15/U0RTS/ADC2_CH4/XTAL_32K_P`.<br>`9` / `PWM1`: ESP32-S3 PWM output for one laser current command channel. |
