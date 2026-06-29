# Laser Controller Full Net/Pin Inventory

Generated from KiCad exported netlist and the current generated PCB artifact.

Schematic references are generated globally unique before KiCad netlist export. Logical route names such as `LASER_GREEN/R12` are resolved through `circuit_designators.py`; physical net nodes use unique refs such as `R29` and `Q3`.

## PCB Trace State

| Metric | Value |
|---|---:|
| `footprint_objects` | 160 |
| `referenced_footprints` | 160 |
| `unique_references` | 160 |
| `copper_layers` | 4 |
| `segments` | 0 |
| `vias` | 0 |
| `zones` | 1 |
| `pad_net_lines` | 515 |
| `net_table_entries` | 112 |
| `keepout_zones` | 1 |
| `gnd_reference_zone_defs` | 0 |
| `net_classes` | 8 |
| `classified_nets` | 111 |
| `placement_proximity_checks` | 4/111 PASS |
| `intentional_unnetted_pad_instances` | 62 |
| `connected_critical_local_route_links` | 0/111 |
| `multi_pad_nets` | 102 |
| `explicitly_routed_multi_pad_nets` | 0 |
| `unrouted_multi_pad_nets` | 96 |
| `zone_or_rail_pending_multi_pad_nets` | 6 |

| Net Class | Nets |
|---|---:|
| `Laser_Current` | 9 |
| `Power_Rails` | 7 |
| `USB` | 4 |
| `TIA_Sensitive` | 24 |
| `Monitor_ADC` | 21 |
| `Laser_Control` | 16 |
| `Digital_Control` | 30 |
| `Default` | 0 |

### USB Route Detail

USB is checked as the copied MCU-sheet connector-to-endpoint routed copper chain for each D+/D- leg. The PCB checker fails if either chain exceeds the generated-board length limit, uses vias, leaves F.Cu, changes width, or exceeds the pair-skew limit.

Pair routed-copper skew: 0.00 mm. BLOCKER: USB-UART D- USB section is unrouted: J1 D- to CP2102N D- /MCU_ESP32-S3/D-; USB-UART D- USB route layers mismatch: expected ['F.Cu'] got []; USB-UART D- USB route widths mismatch: expected 0.25 mm got []; USB-UART D+ USB section is unrouted: J1 D+ to CP2102N D+ /MCU_ESP32-S3/D+; USB-UART D+ USB route layers mismatch: expected ['F.Cu'] got []; USB-UART D+ USB route widths mismatch: expected 0.25 mm got []; Native USB D- USB section is unrouted: J2 D- to ESP32 GPIO19 /MCU_ESP32-S3/IO19; Native USB D- USB route layers mismatch: expected ['F.Cu'] got []; Native USB D- USB route widths mismatch: expected 0.25 mm got []; Native USB D+ USB section is unrouted: J2 D+ to ESP32 GPIO20 /MCU_ESP32-S3/IO20; Native USB D+ USB route layers mismatch: expected ['F.Cu'] got []; Native USB D+ USB route widths mismatch: expected 0.25 mm got []

| Chain | Section | Net | Segments | Length | Geometry | Status |
|---|---|---|---:|---:|---|---|
| `USB-UART D-` | J1 D- to CP2102N D- | `/MCU_ESP32-S3/D-` | 0 | 0.00 mm | -; widths -; vias 0 | BLOCKER: USB route section is missing |
| `USB-UART D-` | total | `-` | 0 | 0.00 mm | -; widths -; vias 0 | PASS: measured chain is inside generated-board USB limits |
| `USB-UART D+` | J1 D+ to CP2102N D+ | `/MCU_ESP32-S3/D+` | 0 | 0.00 mm | -; widths -; vias 0 | BLOCKER: USB route section is missing |
| `USB-UART D+` | total | `-` | 0 | 0.00 mm | -; widths -; vias 0 | PASS: measured chain is inside generated-board USB limits |
| `Native USB D-` | J2 D- to ESP32 GPIO19 | `/MCU_ESP32-S3/IO19` | 0 | 0.00 mm | -; widths -; vias 0 | BLOCKER: USB route section is missing |
| `Native USB D-` | total | `-` | 0 | 0.00 mm | -; widths -; vias 0 | PASS: measured chain is inside generated-board USB limits |
| `Native USB D+` | J2 D+ to ESP32 GPIO20 | `/MCU_ESP32-S3/IO20` | 0 | 0.00 mm | -; widths -; vias 0 | BLOCKER: USB route section is missing |
| `Native USB D+` | total | `-` | 0 | 0.00 mm | -; widths -; vias 0 | PASS: measured chain is inside generated-board USB limits |

PCB pad-net assignment, stackup, net classes, and footprint-internal keepouts are present and auditable, but trace-level electrical review is still blocked until placement, routing, board-level zones, and KiCad DRC exist. Current board evidence has no routed segments, no vias, and no board-level zones.

### Reviewed Rail/Zone Pending Nets

These are the only multi-pad nets currently allowed to remain route/zone pending in the current unrouted PCB. The PCB checker fails if a different rail or any signal/control net enters this state.

| Net | Pads | Copper Components | Review Status | Required Release Action | Component Groups |
|---|---:|---:|---|---|---|
| `+3V3` | 21 | 21 | REVIEWED_PENDING | Route the AP2112 output rail to ESP32-S3 and strap/decoupling loads; verify LDO thermal margin under radio bursts. | U9.2 \| C43.1 \| R54.1 \| R59.1 \| R60.2 \| R52.1 \| R53.1 \| U10.6 \| ... 13 more |
| `+5V` | 39 | 39 | REVIEWED_PENDING | Route or pour the post-OR board 5 V rail to every analog, laser-driver, and LDO input load; verify diode drop and current. | R2.1 \| U1.7 \| C2.1 \| R4.1 \| R6.1 \| U2.7 \| C6.1 \| R8.1 \| ... 31 more |
| `/POWER_IO/EXT5V` | 2 | 2 | REVIEWED_PENDING | Route J6 pin 1 to D6 anode; if this appears pending, treat it as an open external-5V input route. | D6.1 \| J6.1 |
| `GND` | 148 | 146 | REVIEWED_PENDING | Refill the In1.Cu GND zone, inspect islands/stitching, and keep laser-current return paths out of TIA summing-node returns. | C3.2 \| U1.4 \| C2.2 \| RV1.3 \| C4.2 \| C7.2 \| U2.4 \| C6.2 \| ... 138 more |
| `LASER_V+` | 7 | 7 | REVIEWED_PENDING | Manual wide laser-anode rail from J5 to the direct LDx footprints; size for actual laser current and keep away from TIA/MPD analog nodes. | LD1.2 \| LD2.2 \| LD3.2 \| LD4.1 \| J5.1 \| U13.1 \| C36.1 |
| `VBUS_5V` | 8 | 8 | REVIEWED_PENDING | Route protected USB power-entry copper from the copied MCU-sheet VBUS isolation diodes to D5 anode; keep ESD return short. | C41.1 \| C42.1 \| R55.2 \| D9.2 \| D10.1 \| D13.1 \| D14.2 \| D5.1 |

### Placement Proximity Checks

These generated-board checks keep USB protection, ESP32-S3 support parts, AP2112 decoupling, every TIA input/feedback/decoupling/bias cluster, every laser gate/sense/control/compensation cluster, and every monitor-PD sense/reference/ADC-isolation cluster close to the pins they serve.

| Check | Actual | Limit | Status |
|---|---:|---:|---|
| USB UART D- connector to ESD | 22.76 mm | 7.50 mm | FAIL |
| USB UART D+ connector to ESD | 25.30 mm | 9.50 mm | FAIL |
| USB UART D- ESD to CP2102N | 23.15 mm | 10.00 mm | FAIL |
| USB UART D+ ESD to CP2102N | 22.44 mm | 10.00 mm | FAIL |
| Native USB D- connector to ESD | 20.78 mm | 7.50 mm | FAIL |
| Native USB D+ connector to ESD | 18.52 mm | 9.50 mm | FAIL |
| Native USB D- ESD to ESP32 GPIO19 | 24.28 mm | 4.50 mm | FAIL |
| Native USB D+ ESD to ESP32 GPIO20 | 22.83 mm | 4.50 mm | FAIL |
| AP2112 input cap at VIN | 18.20 mm | 4.00 mm | FAIL |
| AP2112 100n output cap at VOUT | 21.17 mm | 4.00 mm | FAIL |
| AP2112 bulk output cap at VOUT | 21.82 mm | 4.00 mm | FAIL |
| ESP32 local 3V3 decap | 42.65 mm | 3.00 mm | FAIL |
| ESP32 EN capacitor | 42.90 mm | 4.00 mm | FAIL |
| ESP32 EN pull-up | 33.02 mm | 5.00 mm | FAIL |
| ESP32 BOOT pull-up | 9.36 mm | 4.00 mm | FAIL |
| TIA_IR photodiode anode to OPA380 -IN | 10.67 mm | 5.50 mm | FAIL |
| TIA_IR feedback trimmer at OPA380 -IN | 6.13 mm | 3.50 mm | FAIL |
| TIA_IR feedback capacitor at OPA380 -IN | 5.13 mm | 2.50 mm | FAIL |
| TIA_IR feedback trimmer at OPA380 OUT | 11.84 mm | 4.50 mm | FAIL |
| TIA_IR feedback capacitor at OPA380 OUT | 5.31 mm | 2.50 mm | FAIL |
| TIA_IR OPA380 supply decoupling | 15.87 mm | 2.50 mm | FAIL |
| TIA_IR PD bias resistor at cathode | 2.67 mm | 4.50 mm | PASS |
| TIA_IR PD cathode bypass at cathode | 12.28 mm | 3.00 mm | FAIL |
| TIA_IR VBIAS resistor at OPA380 +IN | 8.97 mm | 5.00 mm | FAIL |
| TIA_IR VBIAS capacitor at OPA380 +IN | 10.43 mm | 4.00 mm | FAIL |
| TIA_RED photodiode anode to OPA380 -IN | 10.67 mm | 5.50 mm | FAIL |
| TIA_RED feedback trimmer at OPA380 -IN | 6.13 mm | 3.50 mm | FAIL |
| TIA_RED feedback capacitor at OPA380 -IN | 5.13 mm | 2.50 mm | FAIL |
| TIA_RED feedback trimmer at OPA380 OUT | 11.84 mm | 4.50 mm | FAIL |
| TIA_RED feedback capacitor at OPA380 OUT | 5.31 mm | 2.50 mm | FAIL |
| TIA_RED OPA380 supply decoupling | 15.87 mm | 2.50 mm | FAIL |
| TIA_RED PD bias resistor at cathode | 2.67 mm | 4.50 mm | PASS |
| TIA_RED PD cathode bypass at cathode | 12.28 mm | 3.00 mm | FAIL |
| TIA_RED VBIAS resistor at OPA380 +IN | 8.97 mm | 5.00 mm | FAIL |
| TIA_RED VBIAS capacitor at OPA380 +IN | 10.43 mm | 4.00 mm | FAIL |
| TIA_GREEN photodiode anode to OPA380 -IN | 10.67 mm | 5.50 mm | FAIL |
| TIA_GREEN feedback trimmer at OPA380 -IN | 6.13 mm | 3.50 mm | FAIL |
| TIA_GREEN feedback capacitor at OPA380 -IN | 5.13 mm | 2.50 mm | FAIL |
| TIA_GREEN feedback trimmer at OPA380 OUT | 11.84 mm | 4.50 mm | FAIL |
| TIA_GREEN feedback capacitor at OPA380 OUT | 5.31 mm | 2.50 mm | FAIL |
| TIA_GREEN OPA380 supply decoupling | 15.87 mm | 2.50 mm | FAIL |
| TIA_GREEN PD bias resistor at cathode | 2.67 mm | 4.50 mm | PASS |
| TIA_GREEN PD cathode bypass at cathode | 12.28 mm | 3.00 mm | FAIL |
| TIA_GREEN VBIAS resistor at OPA380 +IN | 8.97 mm | 5.00 mm | FAIL |
| TIA_GREEN VBIAS capacitor at OPA380 +IN | 10.43 mm | 4.00 mm | FAIL |
| TIA_BLUE photodiode anode to OPA380 -IN | 10.67 mm | 5.50 mm | FAIL |
| TIA_BLUE feedback trimmer at OPA380 -IN | 6.13 mm | 3.50 mm | FAIL |
| TIA_BLUE feedback capacitor at OPA380 -IN | 5.13 mm | 2.50 mm | FAIL |
| TIA_BLUE feedback trimmer at OPA380 OUT | 11.84 mm | 4.50 mm | FAIL |
| TIA_BLUE feedback capacitor at OPA380 OUT | 5.31 mm | 2.50 mm | FAIL |
| TIA_BLUE OPA380 supply decoupling | 15.87 mm | 2.50 mm | FAIL |
| TIA_BLUE PD bias resistor at cathode | 2.67 mm | 4.50 mm | PASS |
| TIA_BLUE PD cathode bypass at cathode | 12.28 mm | 3.00 mm | FAIL |
| TIA_BLUE VBIAS resistor at OPA380 +IN | 8.97 mm | 5.00 mm | FAIL |
| TIA_BLUE VBIAS capacitor at OPA380 +IN | 10.43 mm | 4.00 mm | FAIL |
| LASER_IR TLV9001 OUT to gate resistor | 12.23 mm | 3.50 mm | FAIL |
| LASER_IR gate resistor to AO3400A gate | 12.48 mm | 2.50 mm | FAIL |
| LASER_IR AO3400A source to sense resistor | 12.81 mm | 2.20 mm | FAIL |
| LASER_IR sense feedback to TLV9001 -IN | 11.27 mm | 6.00 mm | FAIL |
| LASER_IR isolated ISENSE tap at sense resistor | 5.96 mm | 3.50 mm | FAIL |
| LASER_IR TLV9001 supply decoupling | 5.46 mm | 2.50 mm | FAIL |
| LASER_IR PWM input resistor at TLV9001 +IN | 10.14 mm | 2.50 mm | FAIL |
| LASER_IR command limiter at TLV9001 +IN | 12.34 mm | 3.00 mm | FAIL |
| LASER_IR command filter cap at TLV9001 +IN | 5.42 mm | 3.00 mm | FAIL |
| LASER_IR compensation cap at TLV9001 -IN | 15.81 mm | 2.50 mm | FAIL |
| LASER_IR compensation cap at TLV9001 OUT | 11.38 mm | 3.00 mm | FAIL |
| LASER_RED TLV9001 OUT to gate resistor | 12.23 mm | 3.50 mm | FAIL |
| LASER_RED gate resistor to AO3400A gate | 12.48 mm | 2.50 mm | FAIL |
| LASER_RED AO3400A source to sense resistor | 12.81 mm | 2.20 mm | FAIL |
| LASER_RED sense feedback to TLV9001 -IN | 11.27 mm | 6.00 mm | FAIL |
| LASER_RED isolated ISENSE tap at sense resistor | 5.96 mm | 3.50 mm | FAIL |
| LASER_RED TLV9001 supply decoupling | 5.46 mm | 2.50 mm | FAIL |
| LASER_RED PWM input resistor at TLV9001 +IN | 10.14 mm | 2.50 mm | FAIL |
| LASER_RED command limiter at TLV9001 +IN | 12.34 mm | 3.00 mm | FAIL |
| LASER_RED command filter cap at TLV9001 +IN | 5.42 mm | 3.00 mm | FAIL |
| LASER_RED compensation cap at TLV9001 -IN | 15.81 mm | 2.50 mm | FAIL |
| LASER_RED compensation cap at TLV9001 OUT | 11.38 mm | 3.00 mm | FAIL |
| LASER_GREEN TLV9001 OUT to gate resistor | 12.73 mm | 3.50 mm | FAIL |
| LASER_GREEN gate resistor to AO3400A gate | 12.90 mm | 2.50 mm | FAIL |
| LASER_GREEN AO3400A source to sense resistor | 13.12 mm | 2.20 mm | FAIL |
| LASER_GREEN sense feedback to TLV9001 -IN | 11.71 mm | 6.00 mm | FAIL |
| LASER_GREEN isolated ISENSE tap at sense resistor | 5.96 mm | 3.50 mm | FAIL |
| LASER_GREEN TLV9001 supply decoupling | 5.58 mm | 2.50 mm | FAIL |
| LASER_GREEN PWM input resistor at TLV9001 +IN | 10.65 mm | 2.50 mm | FAIL |
| LASER_GREEN command limiter at TLV9001 +IN | 12.83 mm | 3.00 mm | FAIL |
| LASER_GREEN command filter cap at TLV9001 +IN | 5.33 mm | 3.00 mm | FAIL |
| LASER_GREEN compensation cap at TLV9001 -IN | 16.27 mm | 2.50 mm | FAIL |
| LASER_GREEN compensation cap at TLV9001 OUT | 11.84 mm | 3.00 mm | FAIL |
| LASER_BLUE TLV9001 OUT to gate resistor | 12.73 mm | 3.50 mm | FAIL |
| LASER_BLUE gate resistor to AO3400A gate | 12.90 mm | 2.50 mm | FAIL |
| LASER_BLUE AO3400A source to sense resistor | 13.12 mm | 2.20 mm | FAIL |
| LASER_BLUE sense feedback to TLV9001 -IN | 11.71 mm | 6.00 mm | FAIL |
| LASER_BLUE isolated ISENSE tap at sense resistor | 5.96 mm | 3.50 mm | FAIL |
| LASER_BLUE TLV9001 supply decoupling | 5.58 mm | 2.50 mm | FAIL |
| LASER_BLUE PWM input resistor at TLV9001 +IN | 10.65 mm | 2.50 mm | FAIL |
| LASER_BLUE command limiter at TLV9001 +IN | 12.83 mm | 3.00 mm | FAIL |
| LASER_BLUE command filter cap at TLV9001 +IN | 5.33 mm | 3.00 mm | FAIL |
| LASER_BLUE compensation cap at TLV9001 -IN | 16.27 mm | 2.50 mm | FAIL |
| LASER_BLUE compensation cap at TLV9001 OUT | 11.84 mm | 3.00 mm | FAIL |
| MPD_RAW1 direct LD monitor to sense resistor | 68.11 mm | 4.00 mm | FAIL |
| MPD_RAW1 sense resistor to INA input | 26.86 mm | 4.00 mm | FAIL |
| MPD1 ADC resistor to filter capacitor | 14.91 mm | 2.50 mm | FAIL |
| MPD_RAW2 direct LD monitor to sense resistor | 73.14 mm | 4.00 mm | FAIL |
| MPD_RAW2 sense resistor to INA input | 23.41 mm | 4.00 mm | FAIL |
| MPD2 ADC resistor to filter capacitor | 12.31 mm | 2.50 mm | FAIL |
| MPD_RAW3 direct LD monitor to sense resistor | 56.18 mm | 4.00 mm | FAIL |
| MPD_RAW3 sense resistor to INA input | 22.33 mm | 4.00 mm | FAIL |
| MPD3 ADC resistor to filter capacitor | 9.98 mm | 2.50 mm | FAIL |
| MPD_RAW4 spare sense resistor to INA input | 18.19 mm | 4.00 mm | FAIL |
| MPD_AMP4 INA output to ADC resistor | 16.39 mm | 4.00 mm | FAIL |
| MPD4 ADC resistor to filter capacitor | 8.13 mm | 2.50 mm | FAIL |

### Whole-Board Explicit Route Connectivity

This table checks whether every pad on each multi-pad PCB net is connected by explicit routed copper segments. `ZONE_OR_RAIL_PENDING` nets are expected to rely on planes/zones or rail trunks that still require KiCad refill/DRC. `UNROUTED` nets still need board-level routing; critical local links passing does not waive these.

| Net | Pads | Copper Components | Status | Component Groups |
|---|---:|---:|---|---|
| `/LASER_BLUE/FB` | 5 | 5 | UNROUTED | U8.4 \| Q4.2 \| R33.1 \| R34.1 \| C28.1 |
| `/LASER_BLUE/LOUT` | 3 | 3 | UNROUTED | U8.1 \| R32.1 \| C28.2 |
| `/LASER_GREEN/FB` | 5 | 5 | UNROUTED | U7.4 \| Q3.2 \| R28.1 \| R29.1 \| C25.1 |
| `/LASER_GREEN/LOUT` | 3 | 3 | UNROUTED | U7.1 \| R27.1 \| C25.2 |
| `/LASER_IR/FB` | 5 | 5 | UNROUTED | U5.4 \| Q1.2 \| R18.1 \| R19.1 \| C19.1 |
| `/LASER_IR/LOUT` | 3 | 3 | UNROUTED | U5.1 \| R17.1 \| C19.2 |
| `/LASER_RED/FB` | 5 | 5 | UNROUTED | U6.4 \| Q2.2 \| R23.1 \| R24.1 \| C22.1 |
| `/LASER_RED/LOUT` | 3 | 3 | UNROUTED | U6.1 \| R22.1 \| C22.2 |
| `/MCU_ESP32-S3/D+` | 3 | 3 | UNROUTED | U10.4 \| J1.3 \| D8.2 |
| `/MCU_ESP32-S3/D-` | 3 | 3 | UNROUTED | U10.5 \| J1.2 \| D7.2 |
| `/MCU_ESP32-S3/DTR` | 3 | 3 | UNROUTED | Q6.3 \| R50.1 \| U10.28 |
| `/MCU_ESP32-S3/EN` | 6 | 6 | UNROUTED | U9.3 \| C44.1 \| R54.2 \| SW1.1 \| SW1.1 \| Q5.3 |
| `/MCU_ESP32-S3/FACT` | 4 | 4 | UNROUTED | U9.39 \| SW3.1 \| SW3.1 \| R52.2 |
| `/MCU_ESP32-S3/IO13` | 2 | 2 | UNROUTED | U9.21 \| R60.1 |
| `/MCU_ESP32-S3/IO14` | 2 | 2 | UNROUTED | U9.22 \| R59.2 |
| `/MCU_ESP32-S3/IO19` | 3 | 3 | UNROUTED | U9.13 \| J2.2 \| D12.2 |
| `/MCU_ESP32-S3/IO20` | 3 | 3 | UNROUTED | U9.14 \| J2.3 \| D11.2 |
| `/MCU_ESP32-S3/IO43` | 2 | 2 | UNROUTED | U9.37 \| U10.25 |
| `/MCU_ESP32-S3/IO44` | 2 | 2 | UNROUTED | U9.36 \| U10.26 |
| `/MCU_ESP32-S3/PROG` | 6 | 6 | UNROUTED | U9.27 \| SW2.1 \| SW2.1 \| Q6.2 \| R53.2 \| C46.1 |
| `/MCU_ESP32-S3/RTS` | 3 | 3 | UNROUTED | Q5.2 \| R51.1 \| U10.24 |
| `/POWER_IO/MPD_AMP1` | 2 | 2 | UNROUTED | U12.1 \| R43.1 |
| `/POWER_IO/MPD_AMP2` | 2 | 2 | UNROUTED | U12.7 \| R45.1 |
| `/POWER_IO/MPD_AMP3` | 2 | 2 | UNROUTED | U12.8 \| R47.1 |
| `/POWER_IO/MPD_AMP4` | 2 | 2 | UNROUTED | U12.14 \| R49.1 |
| `/POWER_IO/MPD_BIAS` | 12 | 12 | UNROUTED | U12.2 \| U12.6 \| U12.9 \| U12.13 \| U13.2 \| U13.3 \| C36.2 \| R41.1 \| ... 4 more |
| `ADC_BUSY` | 2 | 2 | UNROUTED | U9.24 \| U14.14 |
| `ADC_CS` | 2 | 2 | UNROUTED | U9.11 \| U14.13 |
| `ADC_MISO_A` | 2 | 2 | UNROUTED | U9.23 \| U14.24 |
| `ADC_MISO_B` | 2 | 2 | UNROUTED | U9.31 \| U14.25 |
| `ADC_RESET` | 2 | 2 | UNROUTED | U9.25 \| U14.11 |
| `ADC_SCLK` | 2 | 2 | UNROUTED | U9.10 \| U14.12 |
| `CONVST` | 3 | 3 | UNROUTED | U9.8 \| U14.9 \| U14.10 |
| `ISENSE1` | 2 | 2 | UNROUTED | R19.2 \| U9.4 |
| `ISENSE2` | 2 | 2 | UNROUTED | R24.2 \| U9.5 |
| `ISENSE3` | 2 | 2 | UNROUTED | R29.2 \| U9.6 |
| `ISENSE4` | 2 | 2 | UNROUTED | R34.2 \| U9.7 |
| `LASER_N1` | 2 | 2 | UNROUTED | Q1.3 \| LD1.1 |
| `LASER_N2` | 2 | 2 | UNROUTED | Q2.3 \| LD2.1 |
| `LASER_N3` | 2 | 2 | UNROUTED | Q3.3 \| LD3.1 |
| `LASER_N4` | 2 | 2 | UNROUTED | Q4.3 \| LD4.3 |
| `MPD1` | 3 | 3 | UNROUTED | U9.38 \| R43.2 \| C37.1 |
| `MPD2` | 3 | 3 | UNROUTED | U9.15 \| R45.2 \| C38.1 |
| `MPD3` | 3 | 3 | UNROUTED | U9.12 \| R47.2 \| C39.1 |
| `MPD4` | 3 | 3 | UNROUTED | U9.17 \| R49.2 \| C40.1 |
| `MPD_RAW1` | 3 | 3 | UNROUTED | LD1.3 \| U12.3 \| R42.1 |
| `MPD_RAW2` | 3 | 3 | UNROUTED | LD2.3 \| U12.5 \| R44.1 |
| `MPD_RAW3` | 3 | 3 | UNROUTED | LD3.3 \| U12.10 \| R46.1 |
| `MPD_RAW4` | 2 | 2 | UNROUTED | U12.12 \| R48.1 |
| `Net-(C57-Pad1)` | 2 | 2 | UNROUTED | U14.36 \| C57.1 |
| `Net-(C58-Pad1)` | 2 | 2 | UNROUTED | U14.39 \| C58.1 |
| `Net-(D1-A)` | 4 | 4 | UNROUTED | D1.2 \| U1.2 \| RV5.1 \| C1.1 |
| `Net-(D1-K)` | 3 | 3 | UNROUTED | D1.1 \| R2.2 \| C3.1 |
| `Net-(D10-A)` | 2 | 2 | UNROUTED | J1.1 \| D10.2 |
| `Net-(D13-A)` | 2 | 2 | UNROUTED | J2.1 \| D13.2 |
| `Net-(D2-A)` | 4 | 4 | UNROUTED | D2.2 \| U2.2 \| RV6.1 \| C5.1 |
| `Net-(D2-K)` | 3 | 3 | UNROUTED | D2.1 \| R6.2 \| C7.1 |
| `Net-(D3-A)` | 4 | 4 | UNROUTED | D3.2 \| U3.2 \| RV7.1 \| C9.1 |
| `Net-(D3-K)` | 3 | 3 | UNROUTED | D3.1 \| R10.2 \| C11.1 |
| `Net-(D4-A)` | 4 | 4 | UNROUTED | D4.2 \| U4.2 \| RV8.1 \| C13.1 |
| `Net-(D4-K)` | 3 | 3 | UNROUTED | D4.1 \| R14.2 \| C15.1 |
| `Net-(Q1-G)` | 2 | 2 | UNROUTED | R17.2 \| Q1.1 |
| `Net-(Q2-G)` | 2 | 2 | UNROUTED | R22.2 \| Q2.1 |
| `Net-(Q3-G)` | 2 | 2 | UNROUTED | R27.2 \| Q3.1 |
| `Net-(Q4-G)` | 2 | 2 | UNROUTED | R32.2 \| Q4.1 |
| `Net-(Q5-B)` | 2 | 2 | UNROUTED | Q5.1 \| R50.2 |
| `Net-(Q6-B)` | 2 | 2 | UNROUTED | Q6.1 \| R51.2 |
| `Net-(R12-Pad2)` | 2 | 2 | UNROUTED | R12.2 \| RV3.1 |
| `Net-(R16-Pad2)` | 2 | 2 | UNROUTED | R16.2 \| RV4.1 |
| `Net-(R4-Pad2)` | 2 | 2 | UNROUTED | R4.2 \| RV1.1 |
| `Net-(R8-Pad2)` | 2 | 2 | UNROUTED | R8.2 \| RV2.1 |
| `Net-(RV1-W)` | 2 | 2 | UNROUTED | RV1.2 \| R3.1 |
| `Net-(RV2-W)` | 2 | 2 | UNROUTED | RV2.2 \| R7.1 |
| `Net-(RV3-W)` | 2 | 2 | UNROUTED | RV3.2 \| R11.1 |
| `Net-(RV4-W)` | 2 | 2 | UNROUTED | RV4.2 \| R15.1 |
| `Net-(U1-+)` | 3 | 3 | UNROUTED | U1.3 \| R3.2 \| C4.1 |
| `Net-(U10-VBUS)` | 4 | 4 | UNROUTED | U10.8 \| R55.1 \| R56.2 \| C45.1 |
| `Net-(U10-~{RST})` | 2 | 2 | UNROUTED | U10.9 \| R57.2 |
| `Net-(U10-~{SUSPEND})` | 2 | 2 | UNROUTED | R58.1 \| U10.11 |
| `Net-(U14-REFCAPA)` | 3 | 3 | UNROUTED | U14.44 \| U14.45 \| C60.1 |
| `Net-(U14-REFIN{slash}REFOUT)` | 2 | 2 | UNROUTED | U14.42 \| C59.1 |
| `Net-(U2-+)` | 3 | 3 | UNROUTED | U2.3 \| R7.2 \| C8.1 |
| `Net-(U3-+)` | 3 | 3 | UNROUTED | U3.3 \| R11.2 \| C12.1 |
| `Net-(U4-+)` | 3 | 3 | UNROUTED | U4.3 \| R15.2 \| C16.1 |
| `Net-(U5-+)` | 4 | 4 | UNROUTED | U5.3 \| R20.2 \| R21.1 \| C18.1 |
| `Net-(U6-+)` | 4 | 4 | UNROUTED | U6.3 \| R25.2 \| R26.1 \| C21.1 |
| `Net-(U7-+)` | 4 | 4 | UNROUTED | U7.3 \| R30.2 \| R31.1 \| C24.1 |
| `Net-(U8-+)` | 4 | 4 | UNROUTED | U8.3 \| R35.2 \| R36.1 \| C27.1 |
| `PWM1` | 2 | 2 | UNROUTED | R20.1 \| U9.18 |
| `PWM2` | 2 | 2 | UNROUTED | R25.1 \| U9.19 |
| `PWM3` | 2 | 2 | UNROUTED | R30.1 \| U9.20 |
| `PWM4` | 2 | 2 | UNROUTED | R35.1 \| U9.9 |
| `VOUT1` | 5 | 5 | UNROUTED | U1.6 \| RV5.2 \| RV5.3 \| C1.2 \| U14.49 |
| `VOUT2` | 5 | 5 | UNROUTED | U2.6 \| RV6.2 \| RV6.3 \| C5.2 \| U14.51 |
| `VOUT3` | 5 | 5 | UNROUTED | U3.6 \| RV7.2 \| RV7.3 \| C9.2 \| U14.57 |
| `VOUT4` | 5 | 5 | UNROUTED | U4.6 \| RV8.2 \| RV8.3 \| C13.2 \| U14.59 |
| `+3V3` | 21 | 21 | ZONE_OR_RAIL_PENDING | U9.2 \| C43.1 \| R54.1 \| R59.1 \| R60.2 \| R52.1 \| R53.1 \| U10.6 \| ... 13 more |
| `+5V` | 39 | 39 | ZONE_OR_RAIL_PENDING | R2.1 \| U1.7 \| C2.1 \| R4.1 \| R6.1 \| U2.7 \| C6.1 \| R8.1 \| ... 31 more |
| `/POWER_IO/EXT5V` | 2 | 2 | ZONE_OR_RAIL_PENDING | D6.1 \| J6.1 |
| `GND` | 148 | 146 | ZONE_OR_RAIL_PENDING | C3.2 \| U1.4 \| C2.2 \| RV1.3 \| C4.2 \| C7.2 \| U2.4 \| C6.2 \| ... 138 more |
| `LASER_V+` | 7 | 7 | ZONE_OR_RAIL_PENDING | LD1.2 \| LD2.2 \| LD3.2 \| LD4.1 \| J5.1 \| U13.1 \| C36.1 |
| `VBUS_5V` | 8 | 8 | ZONE_OR_RAIL_PENDING | C41.1 \| C42.1 \| R55.2 \| D9.2 \| D10.1 \| D13.1 \| D14.2 \| D5.1 |

## Pin Intent Coverage

Every exported netlist node is assigned a component-pin-level role. This is stricter than net-level intent: it explains why each specific pin belongs on its net.

| Metric | Value |
|---|---:|
| `exported_netlist_nodes` | 526 |
| `pin_intent_roles` | 526 |
| `missing_pin_intent_roles` | 0 |

## Net Inventory

Total exported nets: **144**.

| Net | Nodes | Intent / Review Note |
|---|---|---|
| `+3V3` | `C35.1`, `C43.1`, `C47.1`, `C49.1`, `C50.1`, `C55.1`, `R52.1`, `R53.1`, `R54.1`, `R57.1`, `R59.1`, `R60.2`, `U10.6` `VDD`, `U10.7` `VREGIN`, `U11.5` `VOUT`, `U12.4` `VS`, `U14.23` `VDRIVE`, `U14.34` `REF_SELECT`, `U14.6` `PAR/SER/BYTE_SEL`, `U14.7` `STBY`, `U9.2` `3V3` | ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling. |
| `+5V` | `C10.1`, `C14.1`, `C17.1`, `C2.1`, `C20.1`, `C23.1`, `C26.1`, `C34.1`, `C48.1`, `C51.1`, `C52.1`, `C53.1`, `C54.1`, `C56.1`, `C6.1`, `D5.2` `K`, `D6.2` `K`, `R10.1`, `R12.1`, `R14.1`, `R16.1`, `R2.1`, `R4.1`, `R6.1`, `R8.1`, `U1.7` `V+`, `U11.1` `VIN`, `U11.3` `EN`, `U14.1` `AVCC`, `U14.37` `AVCC`, `U14.38` `AVCC`, `U14.48` `AVCC`, `U2.7` `V+`, `U3.7` `V+`, `U4.7` `V+`, `U5.5` `V+`, `U6.5` `V+`, `U7.5` `V+`, `U8.5` `V+` | Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input. |
| `/LASER_BLUE/FB` | `C28.1`, `Q4.2` `S`, `R33.1`, `R34.1`, `U8.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_BLUE/LOUT` | `C28.2`, `R32.1`, `U8.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_GREEN/FB` | `C25.1`, `Q3.2` `S`, `R28.1`, `R29.1`, `U7.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_GREEN/LOUT` | `C25.2`, `R27.1`, `U7.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_IR/FB` | `C19.1`, `Q1.2` `S`, `R18.1`, `R19.1`, `U5.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_IR/LOUT` | `C19.2`, `R17.1`, `U5.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/LASER_RED/FB` | `C22.1`, `Q2.2` `S`, `R23.1`, `R24.1`, `U6.4` `-` | Laser current-loop feedback: AO3400A source / 10 ohm sense high side / TLV9001 inverting input. |
| `/LASER_RED/LOUT` | `C22.2`, `R22.1`, `U6.1` | TLV9001 output and compensation node before the 1 k MOSFET gate resistor. |
| `/MCU_ESP32-S3/D+` | `D8.2` `A2`, `J1.3` `D+`, `U10.4` `D+` | CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge. |
| `/MCU_ESP32-S3/D-` | `D7.2` `A2`, `J1.2` `D-`, `U10.5` `D-` | CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge. |
| `/MCU_ESP32-S3/DTR` | `Q6.3` `C`, `R50.1`, `U10.28` `~{DTR}` | CP2102N DTR output feeding the copied auto-boot/reset transistor network. |
| `/MCU_ESP32-S3/EN` | `C44.1`, `Q5.3` `C`, `R54.2`, `SW1.1` `1`, `U9.3` `EN` | ESP32-S3 EN reset net with 10 k pull-up, reset button, POR capacitor, and CP2102 auto-reset transistor. |
| `/MCU_ESP32-S3/FACT` | `R52.2`, `SW3.1` `1`, `U9.39` `GPIO1/TOUCH1/ADC1_CH0` | Copied access-controller factory button net on ESP32-S3 GPIO1 with 10 k pull-up. |
| `/MCU_ESP32-S3/IO13` | `R60.1`, `U9.21` `GPIO13/TOUCH13/ADC2_CH2/FSPIQ/FSPIIO7/SUBSPIQ` | Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up. |
| `/MCU_ESP32-S3/IO14` | `R59.2`, `U9.22` `GPIO14/TOUCH14/ADC2_CH3/FSPIWP/FSPIDQS/SUBSPIWP` | Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up. |
| `/MCU_ESP32-S3/IO19` | `D12.2` `A2`, `J2.2` `D-`, `U9.13` `GPIO19/U1RTS/ADC2_CH8/CLK_OUT2/USB_D-` | ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp. |
| `/MCU_ESP32-S3/IO20` | `D11.2` `A2`, `J2.3` `D+`, `U9.14` `GPIO20/U1CTS/ADC2_CH9/CLK_OUT1/USB_D+` | ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp. |
| `/MCU_ESP32-S3/IO35` | `U9.28` `SPIIO6/GPIO35/FSPID/SUBSPID` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/IO36` | `U9.29` `SPIIO7/GPIO36/FSPICLK/SUBSPICLK` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/IO37` | `U9.30` `SPIDQS/GPIO37/FSPIQ/SUBSPIQ` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/IO39` | `U9.32` `MTCK/GPIO39/CLK_OUT3/SUBSPICS1` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/IO40` | `U9.33` `MTDO/GPIO40/CLK_OUT2` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/IO41` | `U9.34` `MTDI/GPIO41/CLK_OUT1` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/IO42` | `U9.35` `MTMS/GPIO42` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/IO43` | `U10.25` `RXD`, `U9.37` `U0TXD/GPIO43/CLK_OUT1` | ESP32-S3 UART0 TX into CP2102N RXD for USB-UART console/programming. |
| `/MCU_ESP32-S3/IO44` | `U10.26` `TXD`, `U9.36` `U0RXD/GPIO44/CLK_OUT2` | CP2102N TXD into ESP32-S3 UART0 RX for USB-UART console/programming. |
| `/MCU_ESP32-S3/IO45` | `U9.26` `GPIO45` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/IO46` | `U9.16` `GPIO46` | Copied access-controller ESP32-S3 spare/local GPIO net with no bench-sheet interface. |
| `/MCU_ESP32-S3/PROG` | `C46.1`, `Q6.2` `E`, `R53.2`, `SW2.1` `1`, `U9.27` `GPIO0/BOOT` | ESP32-S3 GPIO0/BOOT program-mode net with pull-up, program button, POR capacitor, and CP2102 auto-boot transistor. |
| `/MCU_ESP32-S3/RTS` | `Q5.2` `E`, `R51.1`, `U10.24` `~{RTS}` | CP2102N RTS output feeding the copied auto-reset transistor network. |
| `/POWER_IO/EXT5V` | `D6.1` `A`, `J6.1` `1` | External 5 V input from J6 pin 1 to D6 anode into +5V OR-ing. |
| `/POWER_IO/MPD_AMP1` | `R43.1`, `U12.1` `OUT1` | INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter. |
| `/POWER_IO/MPD_AMP2` | `R45.1`, `U12.7` `OUT2` | INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter. |
| `/POWER_IO/MPD_AMP3` | `R47.1`, `U12.8` `OUT3` | INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter. |
| `/POWER_IO/MPD_AMP4` | `R49.1`, `U12.14` `OUT4` | INA4180 monitor-PD current-sense amplifier output before the 1 k / 100 nF ADC filter. |
| `/POWER_IO/MPD_BIAS` | `C36.2`, `R41.1`, `R42.2`, `R44.2`, `R46.2`, `R48.2`, `U12.13` `IN-4`, `U12.2` `IN-1`, `U12.6` `IN-2`, `U12.9` `IN-3`, `U13.2` `A`, `U13.3` `*` | LM4040-derived monitor-PD anode bias node; holds LASER_V+ to MPD_BIAS near 5 V. |
| `ADC_BUSY` | `U14.14` `BUSY`, `U9.24` `GPIO47/SPICLK_P/SUBSPICLK_P_DIFF` | On-board AD7606-4 BUSY status output into ESP32 GPIO47. |
| `ADC_CS` | `U14.13` `CS`, `U9.11` `GPIO18/U1RXD/ADC2_CH7/CLK_OUT3` | ESP32 GPIO18 chip-select output into the on-board AD7606-4 CS pin. |
| `ADC_MISO_A` | `U14.24` `DB7/DOUTA`, `U9.23` `GPIO21` | On-board AD7606-4 DOUTA serial data output into ESP32 GPIO21. |
| `ADC_MISO_B` | `U14.25` `DB8/DOUTB`, `U9.31` `GPIO38/FSPIWP/SUBSPIWP` | On-board AD7606-4 DOUTB serial data output into ESP32 GPIO38. |
| `ADC_RESET` | `U14.11` `RESET`, `U9.25` `GPIO48/SPICLK_N/SUBSPICLK_N_DIFF` | ESP32 GPIO48 reset output into the on-board AD7606-4 RESET pin. |
| `ADC_SCLK` | `U14.12` `RD/SCLK`, `U9.10` `GPIO17/U1TXD/ADC2_CH6` | ESP32 GPIO17 serial clock into the on-board AD7606-4 RD/SCLK pin. |
| `CONVST` | `U14.10` `CONVSTB`, `U14.9` `CONVSTA`, `U9.8` `GPIO15/U0RTS/ADC2_CH4/XTAL_32K_P` | ESP32 GPIO15 conversion-start output to the on-board AD7606-4 CONVSTA/CONVSTB pins. |
| `GND` | `C10.2`, `C11.2`, `C12.2`, `C14.2`, `C15.2`, `C16.2`, `C17.2`, `C18.2`, `C2.2`, `C20.2`, `C21.2`, `C23.2`, `C24.2`, `C26.2`, `C27.2`, `C3.2`, `C34.2`, `C35.2`, `C37.2`, `C38.2`, `C39.2`, `C4.2`, `C40.2`, `C41.2`, `C42.2`, `C43.2`, `C44.2`, `C45.2`, `C46.2`, `C47.2`, `C48.2`, `C49.2`, `C50.2`, `C51.2`, `C52.2`, `C53.2`, `C54.2`, `C55.2`, `C56.2`, `C57.2`, `C58.2`, `C59.2`, `C6.2`, `C60.2`, `C7.2`, `C8.2`, `D11.1` `A1`, `D12.1` `A1`, `D14.1` `A1`, `D7.1` `A1`, `D8.1` `A1`, `D9.1` `A1`, `J1.5` `GND`, `J1.6` `GND`, `J2.5` `GND`, `J2.6` `GND`, `J5.2` `2`, `J6.2` `2`, `R18.2`, `R21.2`, `R23.2`, `R26.2`, `R28.2`, `R31.2`, `R33.2`, `R36.2`, `R41.2`, `R56.1`, `R58.2`, `RV1.3`, `RV2.3`, `RV3.3`, `RV4.3`, `SW1.2` `2`, `SW2.2` `2`, `SW3.2` `2`, `U1.4` `V-`, `U10.29` `GND`, `U10.3` `GND`, `U11.2` `GND`, `U12.11` `GND`, `U14.16` `DB0`, `U14.17` `DB1`, `U14.18` `DB2`, `U14.19` `DB3`, `U14.2` `AGND`, `U14.20` `DB4`, `U14.21` `DB5`, `U14.22` `DB6`, `U14.26` `AGND`, `U14.27` `DB9`, `U14.28` `DB10`, `U14.29` `DB11`, `U14.3` `OS0`, `U14.30` `DB12`, `U14.31` `DB13`, `U14.32` `DB14/HBEN`, `U14.33` `DB15/BYTE_SEL`, `U14.35` `AGND`, `U14.4` `OS1`, `U14.40` `AGND`, `U14.41` `AGND`, `U14.43` `REFGND`, `U14.46` `REFGND`, `U14.47` `AGND`, `U14.5` `OS2`, `U14.50` `V1GND`, `U14.52` `V2GND`, `U14.53` `AGND`, `U14.54` `AGND`, `U14.55` `AGND`, `U14.56` `AGND`, `U14.58` `V3GND`, `U14.60` `V4GND`, `U14.61` `AGND`, `U14.62` `AGND`, `U14.63` `AGND`, `U14.64` `AGND`, `U14.8` `RANGE`, `U2.4` `V-`, `U3.4` `V-`, `U4.4` `V-`, `U5.2` `V-`, `U6.2` `V-`, `U7.2` `V-`, `U8.2` `V-`, `U9.1` `GND`, `U9.40` `GND`, `U9.41` `GND` | Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `ISENSE1` | `R19.2`, `U9.4` `GPIO4/TOUCH4/ADC1_CH3` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE2` | `R24.2`, `U9.5` `GPIO5/TOUCH5/ADC1_CH4` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE3` | `R29.2`, `U9.6` `GPIO6/TOUCH6/ADC1_CH5` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `ISENSE4` | `R34.2`, `U9.7` `GPIO7/TOUCH7/ADC1_CH6` | Laser source-sense telemetry through 1 k isolation into ESP32 ADC. |
| `LASER_N1` | `LD1.1` `LD_K`, `Q1.3` `D` | Laser cathode sink path from the direct LDx footprint to AO3400A drain. |
| `LASER_N2` | `LD2.1` `LD_K`, `Q2.3` `D` | Laser cathode sink path from the direct LDx footprint to AO3400A drain. |
| `LASER_N3` | `LD3.1` `LD_K`, `Q3.3` `D` | Laser cathode sink path from the direct LDx footprint to AO3400A drain. |
| `LASER_N4` | `LD4.3` `LD_K`, `Q4.3` `D` | Laser cathode sink path from the direct LDx footprint to AO3400A drain. |
| `LASER_V+` | `C36.1`, `J5.1` `1`, `LD1.2` `LD_A/PD_K/CASE`, `LD2.2` `LD_A/PD_K/CASE`, `LD3.2` `LD_A/PD_K/CASE`, `LD4.1` `LD_A`, `U13.1` `K` | External laser anode / monitor-PD cathode common supply from J5 to the direct LDx footprints. |
| `MPD1` | `C37.1`, `R43.2`, `U9.38` `GPIO2/TOUCH2/ADC1_CH1` | Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC. |
| `MPD2` | `C38.1`, `R45.2`, `U9.15` `GPIO3/TOUCH3/ADC1_CH2` | Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC. |
| `MPD3` | `C39.1`, `R47.2`, `U9.12` `GPIO8/TOUCH8/ADC1_CH7/SUBSPICS1` | Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC. |
| `MPD4` | `C40.1`, `R49.2`, `U9.17` `GPIO9/TOUCH9/ADC1_CH8/FSPIHD/SUBSPIHD` | Filtered INA4180 internal laser monitor-photodiode current telemetry into ESP32 ADC. |
| `MPD_RAW1` | `LD1.3` `PD_A`, `R42.1`, `U12.3` `IN+1` | Raw internal monitor-photodiode anode node from the direct LDx footprint into the 750 ohm high-side sense resistor and INA4180 IN+ pin. |
| `MPD_RAW2` | `LD2.3` `PD_A`, `R44.1`, `U12.5` `IN+2` | Raw internal monitor-photodiode anode node from the direct LDx footprint into the 750 ohm high-side sense resistor and INA4180 IN+ pin. |
| `MPD_RAW3` | `LD3.3` `PD_A`, `R46.1`, `U12.10` `IN+3` | Raw internal monitor-photodiode anode node from the direct LDx footprint into the 750 ohm high-side sense resistor and INA4180 IN+ pin. |
| `MPD_RAW4` | `R48.1`, `U12.12` `IN+4` | Spare/open blue-channel monitor input at INA4180 channel 4; PLT5 450GB has no monitor photodiode. |
| `Net-(C57-Pad1)` | `C57.1`, `U14.36` `REGCAP` | AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin. |
| `Net-(C58-Pad1)` | `C58.1`, `U14.39` `REGCAP` | AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin. |
| `Net-(D1-A)` | `C1.1`, `D1.2` `A`, `RV5.1`, `U1.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `Net-(D1-K)` | `C3.1`, `D1.1` `K`, `R2.2` | SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `Net-(D10-A)` | `D10.2` `A`, `J1.1` `VBUS` | Copied MCU-sheet Mini-B VBUS before 1N5819HW isolation diode into the board VBUS_5V net. |
| `Net-(D13-A)` | `D13.2` `A`, `J2.1` `VBUS` | Copied MCU-sheet Mini-B VBUS before 1N5819HW isolation diode into the board VBUS_5V net. |
| `Net-(D2-A)` | `C5.1`, `D2.2` `A`, `RV6.1`, `U2.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `Net-(D2-K)` | `C7.1`, `D2.1` `K`, `R6.2` | SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `Net-(D3-A)` | `C9.1`, `D3.2` `A`, `RV7.1`, `U3.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `Net-(D3-K)` | `C11.1`, `D3.1` `K`, `R10.2` | SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `Net-(D4-A)` | `C13.1`, `D4.2` `A`, `RV8.1`, `U4.2` `-` | TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side. |
| `Net-(D4-K)` | `C15.1`, `D4.1` `K`, `R14.2` | SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `Net-(Q1-G)` | `Q1.1` `G`, `R17.2` | AO3400A gate node after TLV9001 output resistor. |
| `Net-(Q2-G)` | `Q2.1` `G`, `R22.2` | AO3400A gate node after TLV9001 output resistor. |
| `Net-(Q3-G)` | `Q3.1` `G`, `R27.2` | AO3400A gate node after TLV9001 output resistor. |
| `Net-(Q4-G)` | `Q4.1` `G`, `R32.2` | AO3400A gate node after TLV9001 output resistor. |
| `Net-(Q5-B)` | `Q5.1` `B`, `R50.2` | Copied CP2102N RTS/DTR transistor base-drive node for ESP32 EN/GPIO0 auto-reset sequencing. |
| `Net-(Q6-B)` | `Q6.1` `B`, `R51.2` | Copied CP2102N RTS/DTR transistor base-drive node for ESP32 EN/GPIO0 auto-reset sequencing. |
| `Net-(R12-Pad2)` | `R12.2`, `RV3.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `Net-(R16-Pad2)` | `R16.2`, `RV4.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `Net-(R4-Pad2)` | `R4.2`, `RV1.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `Net-(R8-Pad2)` | `R8.2`, `RV2.1` | TIA VBIAS trim upper node between +5V limiting resistor and trimmer. |
| `Net-(RV1-W)` | `R3.1`, `RV1.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `Net-(RV2-W)` | `R7.1`, `RV2.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `Net-(RV3-W)` | `R11.1`, `RV3.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `Net-(RV4-W)` | `R15.1`, `RV4.2` `W` | TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input. |
| `Net-(U1-+)` | `C4.1`, `R3.2`, `U1.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `Net-(U10-VBUS)` | `C45.1`, `R55.1`, `R56.2`, `U10.8` `VBUS` | CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet. |
| `Net-(U10-~{RST})` | `R57.2`, `U10.9` `~{RST}` | CP2102N reset pin pull-up node on the copied MCU sheet. |
| `Net-(U10-~{SUSPEND})` | `R58.1`, `U10.11` `~{SUSPEND}` | CP2102N active-low suspend status pull network on the copied MCU sheet. |
| `Net-(U14-REFCAPA)` | `C60.1`, `U14.44` `REFCAPA`, `U14.45` `REFCAPB` | AD7606-4 reference-buffer decoupling node tying REFCAPA and REFCAPB to the local reference capacitor. |
| `Net-(U14-REFIN{slash}REFOUT)` | `C59.1`, `U14.42` `REFIN/REFOUT` | AD7606-4 internal/reference output decoupling node at REFIN/REFOUT. |
| `Net-(U2-+)` | `C8.1`, `R7.2`, `U2.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `Net-(U3-+)` | `C12.1`, `R11.2`, `U3.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `Net-(U4-+)` | `C16.1`, `R15.2`, `U4.3` `+` | OPA380 non-inverting VBIAS node after trim/filter. |
| `Net-(U5-+)` | `C18.1`, `R20.2`, `R21.1`, `U5.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `Net-(U6-+)` | `C21.1`, `R25.2`, `R26.1`, `U6.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `Net-(U7-+)` | `C24.1`, `R30.2`, `R31.1`, `U7.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `Net-(U8-+)` | `C27.1`, `R35.2`, `R36.1`, `U8.3` `+` | Laser command filter/limiter node into TLV9001 non-inverting input. |
| `PWM1` | `R20.1`, `U9.18` `GPIO10/TOUCH10/ADC1_CH9/FSPICS0/FSPIIO4/SUBSPICS0` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM2` | `R25.1`, `U9.19` `GPIO11/TOUCH11/ADC2_CH0/FSPID/FSPIIO5/SUBSPID` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM3` | `R30.1`, `U9.20` `GPIO12/TOUCH12/ADC2_CH1/FSPICLK/FSPIIO6/SUBSPICLK` | ESP32 PWM command into one laser-driver input resistor. |
| `PWM4` | `R35.1`, `U9.9` `GPIO16/U0CTS/ADC2_CH5/XTAL_32K_N` | ESP32 PWM command into one laser-driver input resistor. |
| `VBUS_5V` | `C41.1`, `C42.1`, `D10.1` `K`, `D13.1` `K`, `D14.2` `A2`, `D5.1` `A`, `D9.2` `A2`, `R55.2` | Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing. |
| `VOUT1` | `C1.2`, `RV5.2` `W`, `RV5.3`, `U1.6`, `U14.49` `V1` | OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `VOUT2` | `C5.2`, `RV6.2` `W`, `RV6.3`, `U14.51` `V2`, `U2.6` | OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `VOUT3` | `C9.2`, `RV7.2` `W`, `RV7.3`, `U14.57` `V3`, `U3.6` | OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `VOUT4` | `C13.2`, `RV8.2` `W`, `RV8.3`, `U14.59` `V4`, `U4.6` | OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `unconnected-(J1-ID-Pad4)` | `J1.4` `ID` | Intentional no-connect from generated schematic. |
| `unconnected-(J2-ID-Pad4)` | `J2.4` `ID` | Intentional no-connect from generated schematic. |
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

## Component Instance Inventory

Total schematic components: **160**.

| Ref | Sheet | Value | Footprint | LCSC | MPN |
|---|---|---|---|---|---|
| `C26` | `/LASER_BLUE/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C83056` | `0402B104K160CT` |
| `C27` | `/LASER_BLUE/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `C7472946` | `HGC0402R5105K250NTEJ` |
| `C28` | `/LASER_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `C106245` | `CC0603JRNPO9BN100` |
| `LD4` | `/LASER_BLUE/` | PLT5 450GB TO56 LASER CASE | `OptoDevice:LaserDiode_TO56-3` |  | `PLT5 450GB` |
| `Q4` | `/LASER_BLUE/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `C20917` | `AO3400A` |
| `R32` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R33` | `/LASER_BLUE/` | 10R 2W | `Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder` | `C5123624` | `HoCR2512-2W-10R-1%` |
| `R34` | `/LASER_BLUE/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R35` | `/LASER_BLUE/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C844918` | `CRCW060310K0FKEA` |
| `R36` | `/LASER_BLUE/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22984` | `0603WAF3002T5E` |
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
| `R31` | `/LASER_GREEN/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22984` | `0603WAF3002T5E` |
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
| `R21` | `/LASER_IR/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22984` | `0603WAF3002T5E` |
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
| `R26` | `/LASER_RED/` | 30k LIMIT | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C22984` | `0603WAF3002T5E` |
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
| `J1` | `/MCU_ESP32-S3/` | USB_MINI_B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `C46391` | `920-462A2021S10101` |
| `J2` | `/MCU_ESP32-S3/` | USB_MINI_B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `C46391` | `920-462A2021S10101` |
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
| `C34` | `/POWER_IO/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `C318691` | `CL21A106KAYNNNG` |
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
| `D5` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `C2480` | `SS14` |
| `D6` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `C2480` | `SS14` |
| `J5` | `/POWER_IO/` | LASER PSU | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |  |  |
| `J6` | `/POWER_IO/` | EXT 5V | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |  |  |
| `R41` | `/POWER_IO/` | 2.49k MPD bias | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2099849` | `CRCW06032K49FKEAHP` |
| `R42` | `/POWER_IO/` | 750R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C114635` | `RC0603FR-07750RL` |
| `R43` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R44` | `/POWER_IO/` | 750R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C114635` | `RC0603FR-07750RL` |
| `R45` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R46` | `/POWER_IO/` | 750R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C114635` | `RC0603FR-07750RL` |
| `R47` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `R48` | `/POWER_IO/` | 750R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C114635` | `RC0603FR-07750RL` |
| `R49` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `C2907002` | `FRC0603F1001TS` |
| `U11` | `/POWER_IO/` | AP2112K-3.3 | `Package_TO_SOT_SMD:SOT-23-5` | `C51118` | `AP2112K-3.3TRG1` |
| `U12` | `/POWER_IO/` | INA4180A1 | `Package_SO:TSSOP-14_4.4x5mm_P0.65mm` | `C2057528` | `INA4180A1IPWR` |
| `U13` | `/POWER_IO/` | LM4040C50 5V | `Package_TO_SOT_SMD:SOT-23` | `C69316` | `LM4040C50IDBZR` |
| `U14` | `/POWER_IO/` | AD7606BSTZ-4 | `Package_QFP:LQFP-64_10x10mm_P0.5mm` | `C51512` | `AD7606BSTZ-4RL` |
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
| `C1` | `/TIA_IR/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `Net-(D1-A)`<br>`2` -> `VOUT1` | `1` / `Net-(D1-A)`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT1`: Capacitor pin participating in: OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `C10` | `/TIA_GREEN/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C11` | `/TIA_GREEN/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(D3-K)`<br>`2` -> `GND` | `1` / `Net-(D3-K)`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C12` | `/TIA_GREEN/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U3-+)`<br>`2` -> `GND` | `1` / `Net-(U3-+)`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C13` | `/TIA_BLUE/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `Net-(D4-A)`<br>`2` -> `VOUT4` | `1` / `Net-(D4-A)`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT4`: Capacitor pin participating in: OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
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
| `C3` | `/TIA_IR/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(D1-K)`<br>`2` -> `GND` | `1` / `Net-(D1-K)`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C34` | `/POWER_IO/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C35` | `/POWER_IO/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C36` | `/POWER_IO/` | 100nF MPD bias | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `LASER_V+`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `LASER_V+`: Monitor-PD bias-reference capacitor participating in the 5V LASER_V+ to MPD_BIAS shunt reference.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD bias-reference capacitor participating in the 5V LASER_V+ to MPD_BIAS shunt reference. |
| `C37` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `MPD1`<br>`2` -> `GND` | `1` / `MPD1`: Monitor-PD ADC filter capacitor ADC side.<br>`2` / `GND`: Monitor-PD ADC filter capacitor ground return. |
| `C38` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `MPD2`<br>`2` -> `GND` | `1` / `MPD2`: Monitor-PD ADC filter capacitor ADC side.<br>`2` / `GND`: Monitor-PD ADC filter capacitor ground return. |
| `C39` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `MPD3`<br>`2` -> `GND` | `1` / `MPD3`: Monitor-PD ADC filter capacitor ADC side.<br>`2` / `GND`: Monitor-PD ADC filter capacitor ground return. |
| `C4` | `/TIA_IR/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U1-+)`<br>`2` -> `GND` | `1` / `Net-(U1-+)`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C40` | `/POWER_IO/` | 100nF MPD ADC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `MPD4`<br>`2` -> `GND` | `1` / `MPD4`: Monitor-PD ADC filter capacitor ADC side.<br>`2` / `GND`: Monitor-PD ADC filter capacitor ground return. |
| `C41` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `VBUS_5V`<br>`2` -> `GND` | `1` / `VBUS_5V`: Capacitor pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C42` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `VBUS_5V`<br>`2` -> `GND` | `1` / `VBUS_5V`: Capacitor pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C43` | `/MCU_ESP32-S3/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C44` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/MCU_ESP32-S3/EN`<br>`2` -> `GND` | `1` / `/MCU_ESP32-S3/EN`: Capacitor pin participating in: ESP32-S3 EN reset net with 10 k pull-up, reset button, POR capacitor, and CP2102 auto-reset transistor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C45` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(U10-VBUS)`<br>`2` -> `GND` | `1` / `Net-(U10-VBUS)`: Capacitor pin participating in: CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C46` | `/MCU_ESP32-S3/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `/MCU_ESP32-S3/PROG`<br>`2` -> `GND` | `1` / `/MCU_ESP32-S3/PROG`: Capacitor pin participating in: ESP32-S3 GPIO0/BOOT program-mode net with pull-up, program button, POR capacitor, and CP2102 auto-boot transistor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C47` | `/MCU_ESP32-S3/` | C_10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C48` | `/POWER_IO/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C49` | `/POWER_IO/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C5` | `/TIA_RED/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `Net-(D2-A)`<br>`2` -> `VOUT2` | `1` / `Net-(D2-A)`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT2`: Capacitor pin participating in: OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `C50` | `/POWER_IO/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C51` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C52` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C53` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C54` | `/POWER_IO/` | 100nF ADC AVCC | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C55` | `/POWER_IO/` | 100nF ADC VDRIVE | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `GND` | `1` / `+3V3`: Capacitor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C56` | `/POWER_IO/` | 10uF ADC AVCC | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C57` | `/POWER_IO/` | 1uF ADC REGCAP | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(C57-Pad1)`<br>`2` -> `GND` | `1` / `Net-(C57-Pad1)`: Capacitor pin participating in: AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C58` | `/POWER_IO/` | 1uF ADC REGCAP | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(C58-Pad1)`<br>`2` -> `GND` | `1` / `Net-(C58-Pad1)`: Capacitor pin participating in: AD7606-4 internal regulator decoupling capacitor node on a REGCAP pin.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C59` | `/POWER_IO/` | 10uF ADC REF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U14-REFIN{slash}REFOUT)`<br>`2` -> `GND` | `1` / `Net-(U14-REFIN{slash}REFOUT)`: Capacitor pin participating in: AD7606-4 internal/reference output decoupling node at REFIN/REFOUT.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C6` | `/TIA_RED/` | 100nF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `+5V`<br>`2` -> `GND` | `1` / `+5V`: Capacitor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C60` | `/POWER_IO/` | 10uF ADC REFCAP | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U14-REFCAPA)`<br>`2` -> `GND` | `1` / `Net-(U14-REFCAPA)`: Capacitor pin participating in: AD7606-4 reference-buffer decoupling node tying REFCAPA and REFCAPB to the local reference capacitor.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C7` | `/TIA_RED/` | 1uF | `Capacitor_SMD:C_0402_1005Metric_Pad0.74x0.62mm_HandSolder` | `1` -> `Net-(D2-K)`<br>`2` -> `GND` | `1` / `Net-(D2-K)`: Capacitor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C8` | `/TIA_RED/` | 10uF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `1` -> `Net-(U2-+)`<br>`2` -> `GND` | `1` / `Net-(U2-+)`: Capacitor pin participating in: OPA380 non-inverting VBIAS node after trim/filter.<br>`2` / `GND`: Capacitor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `C9` | `/TIA_GREEN/` | 10pF C0G | `Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder` | `1` -> `Net-(D3-A)`<br>`2` -> `VOUT3` | `1` / `Net-(D3-A)`: Capacitor pin participating in: TIA summing node: SFH2201 anode, OPA380 inverting input, feedback R/C low side.<br>`2` / `VOUT3`: Capacitor pin participating in: OPA380 TIA output and feedback high side into the on-board AD7606-4 signal ADC. |
| `D1` | `/TIA_IR/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `Net-(D1-K)`<br>`2` `A` -> `Net-(D1-A)` | `1` / `Net-(D1-K)`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `Net-(D1-A)`: SFH2201 anode into the OPA380 summing node. |
| `D10` | `/MCU_ESP32-S3/` | D_1N5819HW | `Diode_SMD:D_SOD-123` | `1` `K` -> `VBUS_5V`<br>`2` `A` -> `Net-(D10-A)` | `1` / `VBUS_5V`: 1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path.<br>`2` / `Net-(D10-A)`: 1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path. |
| `D11` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `/MCU_ESP32-S3/IO20` | `1` / `GND`: Diode pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/IO20`: Diode pin participating in: ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp. |
| `D12` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `/MCU_ESP32-S3/IO19` | `1` / `GND`: Diode pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/IO19`: Diode pin participating in: ESP32-S3 native USB D-/D+ line on the copied MCU-sheet second Mini-B connector with local ESD clamp. |
| `D13` | `/MCU_ESP32-S3/` | D_1N5819HW | `Diode_SMD:D_SOD-123` | `1` `K` -> `VBUS_5V`<br>`2` `A` -> `Net-(D13-A)` | `1` / `VBUS_5V`: 1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path.<br>`2` / `Net-(D13-A)`: 1N5819HW USB VBUS isolation diode pin participating in the copied MCU-sheet VBUS path. |
| `D14` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `VBUS_5V` | `1` / `GND`: Diode pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `VBUS_5V`: Diode pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing. |
| `D2` | `/TIA_RED/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `Net-(D2-K)`<br>`2` `A` -> `Net-(D2-A)` | `1` / `Net-(D2-K)`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `Net-(D2-A)`: SFH2201 anode into the OPA380 summing node. |
| `D3` | `/TIA_GREEN/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `Net-(D3-K)`<br>`2` `A` -> `Net-(D3-A)` | `1` / `Net-(D3-K)`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `Net-(D3-A)`: SFH2201 anode into the OPA380 summing node. |
| `D4` | `/TIA_BLUE/` | SFH2201 | `OptoDevice:Osram_SFH2201` | `1` `K` -> `Net-(D4-K)`<br>`2` `A` -> `Net-(D4-A)` | `1` / `Net-(D4-K)`: SFH2201 cathode reverse-bias node from +5V through 1k and local bypass.<br>`2` / `Net-(D4-A)`: SFH2201 anode into the OPA380 summing node. |
| `D5` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `1` `A` -> `VBUS_5V`<br>`2` `K` -> `+5V` | `1` / `VBUS_5V`: SS14 anode receives one pre-OR 5V source.<br>`2` / `+5V`: SS14 cathode feeds the post-OR +5V rail. |
| `D6` | `/POWER_IO/` | SS14 | `Diode_SMD:D_SMA` | `1` `A` -> `/POWER_IO/EXT5V`<br>`2` `K` -> `+5V` | `1` / `/POWER_IO/EXT5V`: SS14 anode receives one pre-OR 5V source.<br>`2` / `+5V`: SS14 cathode feeds the post-OR +5V rail. |
| `D7` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `/MCU_ESP32-S3/D-` | `1` / `GND`: Diode pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/D-`: Diode pin participating in: CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge. |
| `D8` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `/MCU_ESP32-S3/D+` | `1` / `GND`: Diode pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `/MCU_ESP32-S3/D+`: Diode pin participating in: CP2102 Mini-B USB data line through the copied MCU-sheet ESD protection into the CP2102N USB bridge. |
| `D9` | `/MCU_ESP32-S3/` | ESD_5V | `Diode_SMD:D_SOD-523` | `1` `A1` -> `GND`<br>`2` `A2` -> `VBUS_5V` | `1` / `GND`: Diode pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `VBUS_5V`: Diode pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing. |
| `J1` | `/MCU_ESP32-S3/` | USB_MINI_B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `1` `VBUS` -> `Net-(D10-A)`<br>`2` `D-` -> `/MCU_ESP32-S3/D-`<br>`3` `D+` -> `/MCU_ESP32-S3/D+`<br>`4` `ID` -> `unconnected-(J1-ID-Pad4)`<br>`5` `GND` -> `GND`<br>`6` `GND` -> `GND` | `1` / `Net-(D10-A)`: USB Mini-B VBUS entry into copied MCU-sheet VBUS isolation.<br>`2` / `/MCU_ESP32-S3/D-`: USB Mini-B D- connector pin into the copied USB data path.<br>`3` / `/MCU_ESP32-S3/D+`: USB Mini-B D+ connector pin into the copied USB data path.<br>`4` / `unconnected-(J1-ID-Pad4)`: Intentional no-connect for USB_MINI_B pin 4 `ID`.<br>`5` / `GND`: USB Mini-B signal ground.<br>`6` / `GND`: USB Mini-B shield tied to board GND. |
| `J2` | `/MCU_ESP32-S3/` | USB_MINI_B | `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal` | `1` `VBUS` -> `Net-(D13-A)`<br>`2` `D-` -> `/MCU_ESP32-S3/IO19`<br>`3` `D+` -> `/MCU_ESP32-S3/IO20`<br>`4` `ID` -> `unconnected-(J2-ID-Pad4)`<br>`5` `GND` -> `GND`<br>`6` `GND` -> `GND` | `1` / `Net-(D13-A)`: USB Mini-B VBUS entry into copied MCU-sheet VBUS isolation.<br>`2` / `/MCU_ESP32-S3/IO19`: USB Mini-B D- connector pin into the copied USB data path.<br>`3` / `/MCU_ESP32-S3/IO20`: USB Mini-B D+ connector pin into the copied USB data path.<br>`4` / `unconnected-(J2-ID-Pad4)`: Intentional no-connect for USB_MINI_B pin 4 `ID`.<br>`5` / `GND`: USB Mini-B signal ground.<br>`6` / `GND`: USB Mini-B shield tied to board GND. |
| `J5` | `/POWER_IO/` | LASER PSU | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | `1` `1` -> `LASER_V+`<br>`2` `2` -> `GND` | `1` / `LASER_V+`: External laser-anode supply input.<br>`2` / `GND`: Laser supply connector return ground. |
| `J6` | `/POWER_IO/` | EXT 5V | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | `1` `1` -> `/POWER_IO/EXT5V`<br>`2` `2` -> `GND` | `1` / `/POWER_IO/EXT5V`: External 5V input before OR-ing diode.<br>`2` / `GND`: External 5V connector ground. |
| `LD1` | `/LASER_IR/` | D7805I 780nm TO18 STYLE-A LASER+MPD | `OptoDevice:LaserDiode_TO18-D5.6-3` | `1` `LD_K` -> `LASER_N1`<br>`2` `LD_A/PD_K/CASE` -> `LASER_V+`<br>`3` `PD_A` -> `MPD_RAW1` | `1` / `LASER_N1`: Direct TO-can laser diode cathode tied to the board low-side current-sink net LASER_Nx.<br>`2` / `LASER_V+`: Direct TO-can common laser anode / monitor-PD cathode / case tied to LASER_V+ for PLT/A-code cans.<br>`3` / `MPD_RAW1`: Direct TO-can internal monitor-PD anode exported as MPD_RAWx into the INA4180/LM4040 monitor front end. |
| `LD2` | `/LASER_RED/` | D6505I 650nm TO18 STYLE-A LASER+MPD | `OptoDevice:LaserDiode_TO18-D5.6-3` | `1` `LD_K` -> `LASER_N2`<br>`2` `LD_A/PD_K/CASE` -> `LASER_V+`<br>`3` `PD_A` -> `MPD_RAW2` | `1` / `LASER_N2`: Direct TO-can laser diode cathode tied to the board low-side current-sink net LASER_Nx.<br>`2` / `LASER_V+`: Direct TO-can common laser anode / monitor-PD cathode / case tied to LASER_V+ for PLT/A-code cans.<br>`3` / `MPD_RAW2`: Direct TO-can internal monitor-PD anode exported as MPD_RAWx into the INA4180/LM4040 monitor front end. |
| `LD3` | `/LASER_GREEN/` | PLT5 520EB_P TO56 LASER+MPD | `OptoDevice:LaserDiode_TO56-3` | `1` `LD_K` -> `LASER_N3`<br>`2` `LD_A/PD_K/CASE` -> `LASER_V+`<br>`3` `PD_A` -> `MPD_RAW3` | `1` / `LASER_N3`: Direct TO-can laser diode cathode tied to the board low-side current-sink net LASER_Nx.<br>`2` / `LASER_V+`: Direct TO-can common laser anode / monitor-PD cathode / case tied to LASER_V+ for PLT/A-code cans.<br>`3` / `MPD_RAW3`: Direct TO-can internal monitor-PD anode exported as MPD_RAWx into the INA4180/LM4040 monitor front end. |
| `LD4` | `/LASER_BLUE/` | PLT5 450GB TO56 LASER CASE | `OptoDevice:LaserDiode_TO56-3` | `1` `LD_A` -> `LASER_V+`<br>`2` `CASE` -> `unconnected-(LD4-CASE-Pad2)`<br>`3` `LD_K` -> `LASER_N4` | `1` / `LASER_V+`: Direct TO-can PLT5 450GB laser anode tied to LASER_V+.<br>`2` / `unconnected-(LD4-CASE-Pad2)`: Intentional no-connect for PLT5 450GB TO56 LASER CASE pin 2 `CASE`.<br>`3` / `LASER_N4`: Direct TO-can PLT5 450GB laser cathode tied to the board low-side current-sink net LASER_N4. |
| `Q1` | `/LASER_IR/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `Net-(Q1-G)`<br>`2` `S` -> `/LASER_IR/FB`<br>`3` `D` -> `LASER_N1` | `1` / `Net-(Q1-G)`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_IR/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N1`: AO3400A drain as low-side laser cathode sink. |
| `Q2` | `/LASER_RED/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `Net-(Q2-G)`<br>`2` `S` -> `/LASER_RED/FB`<br>`3` `D` -> `LASER_N2` | `1` / `Net-(Q2-G)`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_RED/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N2`: AO3400A drain as low-side laser cathode sink. |
| `Q3` | `/LASER_GREEN/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `Net-(Q3-G)`<br>`2` `S` -> `/LASER_GREEN/FB`<br>`3` `D` -> `LASER_N3` | `1` / `Net-(Q3-G)`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_GREEN/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N3`: AO3400A drain as low-side laser cathode sink. |
| `Q4` | `/LASER_BLUE/` | AO3400A | `Package_TO_SOT_SMD:SOT-23` | `1` `G` -> `Net-(Q4-G)`<br>`2` `S` -> `/LASER_BLUE/FB`<br>`3` `D` -> `LASER_N4` | `1` / `Net-(Q4-G)`: AO3400A gate driven through 1k from TLV9001 loop output.<br>`2` / `/LASER_BLUE/FB`: AO3400A source at the laser current-sense feedback node.<br>`3` / `LASER_N4`: AO3400A drain as low-side laser cathode sink. |
| `Q5` | `/MCU_ESP32-S3/` | Q_L8050QLT1G | `Package_TO_SOT_SMD:SOT-23` | `1` `B` -> `Net-(Q5-B)`<br>`2` `E` -> `/MCU_ESP32-S3/RTS`<br>`3` `C` -> `/MCU_ESP32-S3/EN` | `1` / `Net-(Q5-B)`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing.<br>`2` / `/MCU_ESP32-S3/RTS`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing.<br>`3` / `/MCU_ESP32-S3/EN`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing. |
| `Q6` | `/MCU_ESP32-S3/` | Q_L8550HQLT1G | `Package_TO_SOT_SMD:SOT-23` | `1` `B` -> `Net-(Q6-B)`<br>`2` `E` -> `/MCU_ESP32-S3/PROG`<br>`3` `C` -> `/MCU_ESP32-S3/DTR` | `1` / `Net-(Q6-B)`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing.<br>`2` / `/MCU_ESP32-S3/PROG`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing.<br>`3` / `/MCU_ESP32-S3/DTR`: Copied CP2102 RTS/DTR transistor-network pin for ESP32 EN/GPIO0 sequencing. |
| `R10` | `/TIA_GREEN/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(D3-K)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(D3-K)`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `R11` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(RV3-W)`<br>`2` -> `Net-(U3-+)` | `1` / `Net-(RV3-W)`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `Net-(U3-+)`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R12` | `/TIA_GREEN/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(R12-Pad2)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(R12-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side. |
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
| `R4` | `/TIA_IR/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(R4-Pad2)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(R4-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side. |
| `R41` | `/POWER_IO/` | 2.49k MPD bias | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_BIAS`<br>`2` -> `GND` | `1` / `/POWER_IO/MPD_BIAS`: MPD_BIAS sink resistor high side.<br>`2` / `GND`: MPD_BIAS sink resistor ground return. |
| `R42` | `/POWER_IO/` | 750R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD_RAW1`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `MPD_RAW1`: Monitor-PD sense resistor raw direct-laser side.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD sense resistor MPD_BIAS side. |
| `R43` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_AMP1`<br>`2` -> `MPD1` | `1` / `/POWER_IO/MPD_AMP1`: Monitor-PD ADC isolation resistor INA4180 output side.<br>`2` / `MPD1`: Monitor-PD ADC isolation resistor filtered ADC side. |
| `R44` | `/POWER_IO/` | 750R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD_RAW2`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `MPD_RAW2`: Monitor-PD sense resistor raw direct-laser side.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD sense resistor MPD_BIAS side. |
| `R45` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_AMP2`<br>`2` -> `MPD2` | `1` / `/POWER_IO/MPD_AMP2`: Monitor-PD ADC isolation resistor INA4180 output side.<br>`2` / `MPD2`: Monitor-PD ADC isolation resistor filtered ADC side. |
| `R46` | `/POWER_IO/` | 750R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD_RAW3`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `MPD_RAW3`: Monitor-PD sense resistor raw direct-laser side.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD sense resistor MPD_BIAS side. |
| `R47` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_AMP3`<br>`2` -> `MPD3` | `1` / `/POWER_IO/MPD_AMP3`: Monitor-PD ADC isolation resistor INA4180 output side.<br>`2` / `MPD3`: Monitor-PD ADC isolation resistor filtered ADC side. |
| `R48` | `/POWER_IO/` | 750R MPD sense | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `MPD_RAW4`<br>`2` -> `/POWER_IO/MPD_BIAS` | `1` / `MPD_RAW4`: Monitor-PD sense resistor raw direct-laser side.<br>`2` / `/POWER_IO/MPD_BIAS`: Monitor-PD sense resistor MPD_BIAS side. |
| `R49` | `/POWER_IO/` | 1k ADC | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `/POWER_IO/MPD_AMP4`<br>`2` -> `MPD4` | `1` / `/POWER_IO/MPD_AMP4`: Monitor-PD ADC isolation resistor INA4180 output side.<br>`2` / `MPD4`: Monitor-PD ADC isolation resistor filtered ADC side. |
| `R50` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/MCU_ESP32-S3/DTR`<br>`2` -> `Net-(Q5-B)` | `1` / `/MCU_ESP32-S3/DTR`: Resistor pin participating in: CP2102N DTR output feeding the copied auto-boot/reset transistor network.<br>`2` / `Net-(Q5-B)`: Resistor pin participating in: Copied CP2102N RTS/DTR transistor base-drive node for ESP32 EN/GPIO0 auto-reset sequencing. |
| `R51` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/MCU_ESP32-S3/RTS`<br>`2` -> `Net-(Q6-B)` | `1` / `/MCU_ESP32-S3/RTS`: Resistor pin participating in: CP2102N RTS output feeding the copied auto-reset transistor network.<br>`2` / `Net-(Q6-B)`: Resistor pin participating in: Copied CP2102N RTS/DTR transistor base-drive node for ESP32 EN/GPIO0 auto-reset sequencing. |
| `R52` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/FACT` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/FACT`: Resistor pin participating in: Copied access-controller factory button net on ESP32-S3 GPIO1 with 10 k pull-up. |
| `R53` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/PROG` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/PROG`: Resistor pin participating in: ESP32-S3 GPIO0/BOOT program-mode net with pull-up, program button, POR capacitor, and CP2102 auto-boot transistor. |
| `R54` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/EN` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/EN`: Resistor pin participating in: ESP32-S3 EN reset net with 10 k pull-up, reset button, POR capacitor, and CP2102 auto-reset transistor. |
| `R55` | `/MCU_ESP32-S3/` | 22.1K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `Net-(U10-VBUS)`<br>`2` -> `VBUS_5V` | `1` / `Net-(U10-VBUS)`: Resistor pin participating in: CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet.<br>`2` / `VBUS_5V`: Resistor pin participating in: Joined USB VBUS after the copied MCU-sheet 1N5819HW isolation diodes, local VBUS ESD/bulk parts, and D5 anode into +5V OR-ing. |
| `R56` | `/MCU_ESP32-S3/` | 47.5K | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `GND`<br>`2` -> `Net-(U10-VBUS)` | `1` / `GND`: Resistor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths.<br>`2` / `Net-(U10-VBUS)`: Resistor pin participating in: CP2102N VBUS sense/bias node with divider and bypass capacitor on the copied MCU sheet. |
| `R57` | `/MCU_ESP32-S3/` | 1K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `Net-(U10-~{RST})` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `Net-(U10-~{RST})`: Resistor pin participating in: CP2102N reset pin pull-up node on the copied MCU sheet. |
| `R58` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `Net-(U10-~{SUSPEND})`<br>`2` -> `GND` | `1` / `Net-(U10-~{SUSPEND})`: Resistor pin participating in: CP2102N active-low suspend status pull network on the copied MCU sheet.<br>`2` / `GND`: Resistor pin participating in: Common board return. Layout still must keep high-current laser returns away from TIA summing-node return paths. |
| `R59` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `+3V3`<br>`2` -> `/MCU_ESP32-S3/IO14` | `1` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling.<br>`2` / `/MCU_ESP32-S3/IO14`: Resistor pin participating in: Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up. |
| `R6` | `/TIA_RED/` | 1k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(D2-K)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(D2-K)`: Resistor pin participating in: SFH2201 cathode reverse-bias node: +5V through RB and local bypass CB. |
| `R60` | `/MCU_ESP32-S3/` | 10K | `Resistor_SMD:R_0402_1005Metric_Pad0.72x0.64mm_HandSolder` | `1` -> `/MCU_ESP32-S3/IO13`<br>`2` -> `+3V3` | `1` / `/MCU_ESP32-S3/IO13`: Resistor pin participating in: Copied access-controller ESP32-S3 GPIO strap/support net with local 10 k pull-up.<br>`2` / `+3V3`: Resistor pin participating in: ESP32-S3 3.3 V rail from AP2112K output, plus MCU reset/boot pulls and decoupling. |
| `R7` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `Net-(RV2-W)`<br>`2` -> `Net-(U2-+)` | `1` / `Net-(RV2-W)`: Resistor pin participating in: TIA VBIAS trimmer wiper through R1 into filtered OPA380 non-inverting input.<br>`2` / `Net-(U2-+)`: Resistor pin participating in: OPA380 non-inverting VBIAS node after trim/filter. |
| `R8` | `/TIA_RED/` | 10k | `Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder` | `1` -> `+5V`<br>`2` -> `Net-(R8-Pad2)` | `1` / `+5V`: Resistor pin participating in: Board 5 V rail after USB/external Schottky OR-ing; feeds analog, laser-driver op amps, and 3V3 LDO input.<br>`2` / `Net-(R8-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side. |
| `RV1` | `/TIA_IR/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(R4-Pad2)`<br>`2` `W` -> `Net-(RV1-W)`<br>`3` -> `GND` | `1` / `Net-(R4-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side.<br>`2` / `Net-(RV1-W)`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV2` | `/TIA_RED/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(R8-Pad2)`<br>`2` `W` -> `Net-(RV2-W)`<br>`3` -> `GND` | `1` / `Net-(R8-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side.<br>`2` / `Net-(RV2-W)`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV3` | `/TIA_GREEN/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(R12-Pad2)`<br>`2` `W` -> `Net-(RV3-W)`<br>`3` -> `GND` | `1` / `Net-(R12-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side.<br>`2` / `Net-(RV3-W)`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV4` | `/TIA_BLUE/` | VBIAS 10k | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(R16-Pad2)`<br>`2` `W` -> `Net-(RV4-W)`<br>`3` -> `GND` | `1` / `Net-(R16-Pad2)`: TIA VBIAS trim upper node between the +5V limiting resistor and the Bourns trimmer high side.<br>`2` / `Net-(RV4-W)`: Bourns trimmer wiper feeding the OPA380 VBIAS resistor.<br>`3` / `GND`: Bourns trimmer low-side return to GND. |
| `RV5` | `/TIA_IR/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(D1-A)`<br>`2` `W` -> `VOUT1`<br>`3` -> `VOUT1` | `1` / `Net-(D1-A)`: Bourns feedback trimmer low side tied to the OPA380 summing node.<br>`2` / `VOUT1`: Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.<br>`3` / `VOUT1`: Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input. |
| `RV6` | `/TIA_RED/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(D2-A)`<br>`2` `W` -> `VOUT2`<br>`3` -> `VOUT2` | `1` / `Net-(D2-A)`: Bourns feedback trimmer low side tied to the OPA380 summing node.<br>`2` / `VOUT2`: Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.<br>`3` / `VOUT2`: Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input. |
| `RV7` | `/TIA_GREEN/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(D3-A)`<br>`2` `W` -> `VOUT3`<br>`3` -> `VOUT3` | `1` / `Net-(D3-A)`: Bourns feedback trimmer low side tied to the OPA380 summing node.<br>`2` / `VOUT3`: Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.<br>`3` / `VOUT3`: Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input. |
| `RV8` | `/TIA_BLUE/` | RF 2M | `Potentiometer_SMD:Potentiometer_Bourns_3224W_Vertical` | `1` -> `Net-(D4-A)`<br>`2` `W` -> `VOUT4`<br>`3` -> `VOUT4` | `1` / `Net-(D4-A)`: Bourns feedback trimmer low side tied to the OPA380 summing node.<br>`2` / `VOUT4`: Bourns feedback trimmer wiper tied to the OPA380 output side for rheostat fail-safe behavior.<br>`3` / `VOUT4`: Bourns feedback trimmer output-side terminal tied to OPA380 output and on-board AD7606 input. |
| `SW1` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `1` `1` -> `/MCU_ESP32-S3/EN`<br>`2` `2` -> `GND` | `1` / `/MCU_ESP32-S3/EN`: Copied MCU pushbutton signal contact.<br>`2` / `GND`: Copied MCU pushbutton ground contact. |
| `SW2` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `1` `1` -> `/MCU_ESP32-S3/PROG`<br>`2` `2` -> `GND` | `1` / `/MCU_ESP32-S3/PROG`: Copied MCU pushbutton signal contact.<br>`2` / `GND`: Copied MCU pushbutton ground contact. |
| `SW3` | `/MCU_ESP32-S3/` | SW_PUSH | `Button_Switch_SMD:SW_SPST_PTS645` | `1` `1` -> `/MCU_ESP32-S3/FACT`<br>`2` `2` -> `GND` | `1` / `/MCU_ESP32-S3/FACT`: Copied MCU pushbutton signal contact.<br>`2` / `GND`: Copied MCU pushbutton ground contact. |
| `U1` | `/TIA_IR/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U1-NC-Pad1)`<br>`2` `-` -> `Net-(D1-A)`<br>`3` `+` -> `Net-(U1-+)`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U1-NC-Pad5)`<br>`6` -> `VOUT1`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U1-NC-Pad8)` | `1` / `unconnected-(U1-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `Net-(D1-A)`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `Net-(U1-+)`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U1-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT1`: OPA380 TIA output to feedback high side and on-board AD7606 input.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U1-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U10` | `/MCU_ESP32-S3/` | CP2102N-Axx-xQFN28 | `Package_DFN_QFN:QFN-28-1EP_5x5mm_P0.5mm_EP3.35x3.35mm` | `1` `~{DCD}` -> `unconnected-(U10-~{DCD}-Pad1)`<br>`10` `NC` -> `unconnected-(U10-NC-Pad10)`<br>`11` `~{SUSPEND}` -> `Net-(U10-~{SUSPEND})`<br>`12` `SUSPEND` -> `unconnected-(U10-SUSPEND-Pad12)`<br>`13` `CHREN` -> `unconnected-(U10-CHREN-Pad13)`<br>`14` `CHR1` -> `unconnected-(U10-CHR1-Pad14)`<br>`15` `CHR0` -> `unconnected-(U10-CHR0-Pad15)`<br>`16` `~{WAKEUP}/GPIO.3` -> `unconnected-(U10-~{WAKEUP}{slash}GPIO.3-Pad16)`<br>`17` `RS485/GPIO.2` -> `unconnected-(U10-RS485{slash}GPIO.2-Pad17)`<br>`18` `~{RXT}/GPIO.1` -> `unconnected-(U10-~{RXT}{slash}GPIO.1-Pad18)`<br>`19` `~{TXT}/GPIO.0` -> `unconnected-(U10-~{TXT}{slash}GPIO.0-Pad19)`<br>`2` `~{RI}/CLK` -> `unconnected-(U10-~{RI}{slash}CLK-Pad2)`<br>`20` `GPIO.6` -> `unconnected-(U10-GPIO.6-Pad20)`<br>`21` `GPIO.5` -> `unconnected-(U10-GPIO.5-Pad21)`<br>`22` `GPIO.4` -> `unconnected-(U10-GPIO.4-Pad22)`<br>`23` `~{CTS}` -> `unconnected-(U10-~{CTS}-Pad23)`<br>`24` `~{RTS}` -> `/MCU_ESP32-S3/RTS`<br>`25` `RXD` -> `/MCU_ESP32-S3/IO43`<br>`26` `TXD` -> `/MCU_ESP32-S3/IO44`<br>`27` `~{DSR}` -> `unconnected-(U10-~{DSR}-Pad27)`<br>`28` `~{DTR}` -> `/MCU_ESP32-S3/DTR`<br>`29` `GND` -> `GND`<br>`3` `GND` -> `GND`<br>`4` `D+` -> `/MCU_ESP32-S3/D+`<br>`5` `D-` -> `/MCU_ESP32-S3/D-`<br>`6` `VDD` -> `+3V3`<br>`7` `VREGIN` -> `+3V3`<br>`8` `VBUS` -> `Net-(U10-VBUS)`<br>`9` `~{RST}` -> `Net-(U10-~{RST})` | `1` / `unconnected-(U10-~{DCD}-Pad1)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 1 `~{DCD}`.<br>`10` / `unconnected-(U10-NC-Pad10)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 10 `NC`.<br>`11` / `Net-(U10-~{SUSPEND})`: CP2102N active-low suspend status output with pull network.<br>`12` / `unconnected-(U10-SUSPEND-Pad12)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 12 `SUSPEND`.<br>`13` / `unconnected-(U10-CHREN-Pad13)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 13 `CHREN`.<br>`14` / `unconnected-(U10-CHR1-Pad14)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 14 `CHR1`.<br>`15` / `unconnected-(U10-CHR0-Pad15)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 15 `CHR0`.<br>`16` / `unconnected-(U10-~{WAKEUP}{slash}GPIO.3-Pad16)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 16 `~{WAKEUP}/GPIO.3`.<br>`17` / `unconnected-(U10-RS485{slash}GPIO.2-Pad17)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 17 `RS485/GPIO.2`.<br>`18` / `unconnected-(U10-~{RXT}{slash}GPIO.1-Pad18)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 18 `~{RXT}/GPIO.1`.<br>`19` / `unconnected-(U10-~{TXT}{slash}GPIO.0-Pad19)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 19 `~{TXT}/GPIO.0`.<br>`2` / `unconnected-(U10-~{RI}{slash}CLK-Pad2)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 2 `~{RI}/CLK`.<br>`20` / `unconnected-(U10-GPIO.6-Pad20)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 20 `GPIO.6`.<br>`21` / `unconnected-(U10-GPIO.5-Pad21)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 21 `GPIO.5`.<br>`22` / `unconnected-(U10-GPIO.4-Pad22)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 22 `GPIO.4`.<br>`23` / `unconnected-(U10-~{CTS}-Pad23)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 23 `~{CTS}`.<br>`24` / `/MCU_ESP32-S3/RTS`: CP2102N RTS output into the ESP32 auto-reset transistor network.<br>`25` / `/MCU_ESP32-S3/IO43`: CP2102N RXD input from ESP32 UART0 TX.<br>`26` / `/MCU_ESP32-S3/IO44`: CP2102N TXD output into ESP32 UART0 RX.<br>`27` / `unconnected-(U10-~{DSR}-Pad27)`: Intentional no-connect for CP2102N-Axx-xQFN28 pin 27 `~{DSR}`.<br>`28` / `/MCU_ESP32-S3/DTR`: CP2102N DTR output into the ESP32 auto-boot/reset transistor network.<br>`29` / `GND`: CP2102N exposed-pad ground.<br>`3` / `GND`: CP2102N ground pin.<br>`4` / `/MCU_ESP32-S3/D+`: CP2102N USB D+ pin on the copied Mini-B USB bridge path.<br>`5` / `/MCU_ESP32-S3/D-`: CP2102N USB D- pin on the copied Mini-B USB bridge path.<br>`6` / `+3V3`: CP2102N VDD supply tied to board +3V3.<br>`7` / `+3V3`: CP2102N VREGIN tied to board +3V3 for self-powered operation.<br>`8` / `Net-(U10-VBUS)`: CP2102N VBUS sense input from the copied USB VBUS divider/bypass node.<br>`9` / `Net-(U10-~{RST})`: CP2102N reset input with pull-up. |
| `U11` | `/POWER_IO/` | AP2112K-3.3 | `Package_TO_SOT_SMD:SOT-23-5` | `1` `VIN` -> `+5V`<br>`2` `GND` -> `GND`<br>`3` `EN` -> `+5V`<br>`4` `NC` -> `unconnected-(U11-NC-Pad4)`<br>`5` `VOUT` -> `+3V3` | `1` / `+5V`: AP2112 VIN from post-OR +5V rail.<br>`2` / `GND`: AP2112 ground return.<br>`3` / `+5V`: AP2112 enable tied high to +5V for always-on bench 3V3.<br>`4` / `unconnected-(U11-NC-Pad4)`: Intentional no-connect for AP2112K-3.3 pin 4 `NC`.<br>`5` / `+3V3`: AP2112 regulated +3V3 output. |
| `U12` | `/POWER_IO/` | INA4180A1 | `Package_SO:TSSOP-14_4.4x5mm_P0.65mm` | `1` `OUT1` -> `/POWER_IO/MPD_AMP1`<br>`10` `IN+3` -> `MPD_RAW3`<br>`11` `GND` -> `GND`<br>`12` `IN+4` -> `MPD_RAW4`<br>`13` `IN-4` -> `/POWER_IO/MPD_BIAS`<br>`14` `OUT4` -> `/POWER_IO/MPD_AMP4`<br>`2` `IN-1` -> `/POWER_IO/MPD_BIAS`<br>`3` `IN+1` -> `MPD_RAW1`<br>`4` `VS` -> `+3V3`<br>`5` `IN+2` -> `MPD_RAW2`<br>`6` `IN-2` -> `/POWER_IO/MPD_BIAS`<br>`7` `OUT2` -> `/POWER_IO/MPD_AMP2`<br>`8` `OUT3` -> `/POWER_IO/MPD_AMP3`<br>`9` `IN-3` -> `/POWER_IO/MPD_BIAS` | `1` / `/POWER_IO/MPD_AMP1`: INA4180 channel 1 output to the MPD1 ADC RC filter.<br>`10` / `MPD_RAW3`: INA4180 channel 3 positive input on MPD_RAW3.<br>`11` / `GND`: INA4180 ground reference for ADC output accuracy.<br>`12` / `MPD_RAW4`: INA4180 channel 4 positive input on spare/open MPD_RAW4.<br>`13` / `/POWER_IO/MPD_BIAS`: INA4180 channel 4 negative input on MPD_BIAS.<br>`14` / `/POWER_IO/MPD_AMP4`: INA4180 channel 4 output to the MPD4 ADC RC filter.<br>`2` / `/POWER_IO/MPD_BIAS`: INA4180 channel 1 negative input on MPD_BIAS, the load side of the monitor sense resistor.<br>`3` / `MPD_RAW1`: INA4180 channel 1 positive input on MPD_RAW1, the laser monitor-PD anode side of the sense resistor.<br>`4` / `+3V3`: INA4180 3.3 V supply.<br>`5` / `MPD_RAW2`: INA4180 channel 2 positive input on MPD_RAW2.<br>`6` / `/POWER_IO/MPD_BIAS`: INA4180 channel 2 negative input on MPD_BIAS.<br>`7` / `/POWER_IO/MPD_AMP2`: INA4180 channel 2 output to the MPD2 ADC RC filter.<br>`8` / `/POWER_IO/MPD_AMP3`: INA4180 channel 3 output to the MPD3 ADC RC filter.<br>`9` / `/POWER_IO/MPD_BIAS`: INA4180 channel 3 negative input on MPD_BIAS. |
| `U13` | `/POWER_IO/` | LM4040C50 5V | `Package_TO_SOT_SMD:SOT-23` | `1` `K` -> `LASER_V+`<br>`2` `A` -> `/POWER_IO/MPD_BIAS`<br>`3` `*` -> `/POWER_IO/MPD_BIAS` | `1` / `LASER_V+`: LM4040 cathode tied to LASER_V+ so the reference clamps the high-side monitor-bias drop.<br>`2` / `/POWER_IO/MPD_BIAS`: LM4040 anode tied to MPD_BIAS.<br>`3` / `/POWER_IO/MPD_BIAS`: LM4040 star pin tied to anode/MPD_BIAS per TI guidance for noisy environments. |
| `U14` | `/POWER_IO/` | AD7606BSTZ-4 | `Package_QFP:LQFP-64_10x10mm_P0.5mm` | `1` `AVCC` -> `+5V`<br>`10` `CONVSTB` -> `CONVST`<br>`11` `RESET` -> `ADC_RESET`<br>`12` `RD/SCLK` -> `ADC_SCLK`<br>`13` `CS` -> `ADC_CS`<br>`14` `BUSY` -> `ADC_BUSY`<br>`15` `FRSTDATA` -> `unconnected-(U14-FRSTDATA-Pad15)`<br>`16` `DB0` -> `GND`<br>`17` `DB1` -> `GND`<br>`18` `DB2` -> `GND`<br>`19` `DB3` -> `GND`<br>`2` `AGND` -> `GND`<br>`20` `DB4` -> `GND`<br>`21` `DB5` -> `GND`<br>`22` `DB6` -> `GND`<br>`23` `VDRIVE` -> `+3V3`<br>`24` `DB7/DOUTA` -> `ADC_MISO_A`<br>`25` `DB8/DOUTB` -> `ADC_MISO_B`<br>`26` `AGND` -> `GND`<br>`27` `DB9` -> `GND`<br>`28` `DB10` -> `GND`<br>`29` `DB11` -> `GND`<br>`3` `OS0` -> `GND`<br>`30` `DB12` -> `GND`<br>`31` `DB13` -> `GND`<br>`32` `DB14/HBEN` -> `GND`<br>`33` `DB15/BYTE_SEL` -> `GND`<br>`34` `REF_SELECT` -> `+3V3`<br>`35` `AGND` -> `GND`<br>`36` `REGCAP` -> `Net-(C57-Pad1)`<br>`37` `AVCC` -> `+5V`<br>`38` `AVCC` -> `+5V`<br>`39` `REGCAP` -> `Net-(C58-Pad1)`<br>`4` `OS1` -> `GND`<br>`40` `AGND` -> `GND`<br>`41` `AGND` -> `GND`<br>`42` `REFIN/REFOUT` -> `Net-(U14-REFIN{slash}REFOUT)`<br>`43` `REFGND` -> `GND`<br>`44` `REFCAPA` -> `Net-(U14-REFCAPA)`<br>`45` `REFCAPB` -> `Net-(U14-REFCAPA)`<br>`46` `REFGND` -> `GND`<br>`47` `AGND` -> `GND`<br>`48` `AVCC` -> `+5V`<br>`49` `V1` -> `VOUT1`<br>`5` `OS2` -> `GND`<br>`50` `V1GND` -> `GND`<br>`51` `V2` -> `VOUT2`<br>`52` `V2GND` -> `GND`<br>`53` `AGND` -> `GND`<br>`54` `AGND` -> `GND`<br>`55` `AGND` -> `GND`<br>`56` `AGND` -> `GND`<br>`57` `V3` -> `VOUT3`<br>`58` `V3GND` -> `GND`<br>`59` `V4` -> `VOUT4`<br>`6` `PAR/SER/BYTE_SEL` -> `+3V3`<br>`60` `V4GND` -> `GND`<br>`61` `AGND` -> `GND`<br>`62` `AGND` -> `GND`<br>`63` `AGND` -> `GND`<br>`64` `AGND` -> `GND`<br>`7` `STBY` -> `+3V3`<br>`8` `RANGE` -> `GND`<br>`9` `CONVSTA` -> `CONVST` | `1` / `+5V`: AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling.<br>`10` / `CONVST`: AD7606-4 conversion-start input; CONVSTA and CONVSTB are tied together for simultaneous sampling.<br>`11` / `ADC_RESET`: AD7606-4 RESET input from ESP32 GPIO48.<br>`12` / `ADC_SCLK`: AD7606-4 RD/SCLK serial clock input from ESP32 GPIO17.<br>`13` / `ADC_CS`: AD7606-4 chip-select input from ESP32 GPIO18.<br>`14` / `ADC_BUSY`: AD7606-4 BUSY conversion-status output to ESP32 GPIO47.<br>`15` / `unconnected-(U14-FRSTDATA-Pad15)`: Intentional no-connect for AD7606BSTZ-4 pin 15 `FRSTDATA`.<br>`16` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`17` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`18` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`19` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`2` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`20` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`21` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`22` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`23` / `+3V3`: AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain.<br>`24` / `ADC_MISO_A`: AD7606-4 DOUTA serial data output to ESP32 GPIO21.<br>`25` / `ADC_MISO_B`: AD7606-4 DOUTB serial data output to ESP32 GPIO38.<br>`26` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`27` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`28` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`29` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`3` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`30` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`31` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`32` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`33` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`34` / `+3V3`: AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain.<br>`35` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`36` / `Net-(C57-Pad1)`: AD7606-4 internal regulator capacitor pin.<br>`37` / `+5V`: AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling.<br>`38` / `+5V`: AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling.<br>`39` / `Net-(C58-Pad1)`: AD7606-4 internal regulator capacitor pin.<br>`4` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`40` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`41` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`42` / `Net-(U14-REFIN{slash}REFOUT)`: AD7606-4 internal/reference output pin decoupled by the local reference capacitor.<br>`43` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`44` / `Net-(U14-REFCAPA)`: AD7606-4 reference-buffer capacitor pin.<br>`45` / `Net-(U14-REFCAPA)`: AD7606-4 reference-buffer capacitor pin.<br>`46` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`47` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`48` / `+5V`: AD7606-4 AVCC analog supply pin tied to the board 5V analog rail with local decoupling.<br>`49` / `VOUT1`: AD7606-4 analog input pin for one OPA380 TIA output channel.<br>`5` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`50` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`51` / `VOUT2`: AD7606-4 analog input pin for one OPA380 TIA output channel.<br>`52` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`53` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`54` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`55` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`56` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`57` / `VOUT3`: AD7606-4 analog input pin for one OPA380 TIA output channel.<br>`58` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`59` / `VOUT4`: AD7606-4 analog input pin for one OPA380 TIA output channel.<br>`6` / `+3V3`: AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain.<br>`60` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`61` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`62` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`63` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`64` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`7` / `+3V3`: AD7606-4 VDRIVE/control strap pin tied to the ESP32 3.3V logic domain.<br>`8` / `GND`: AD7606-4 AGND/REFGND/input-ground or grounded parallel/oversampling/range strap pin.<br>`9` / `CONVST`: AD7606-4 conversion-start input; CONVSTA and CONVSTB are tied together for simultaneous sampling. |
| `U2` | `/TIA_RED/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U2-NC-Pad1)`<br>`2` `-` -> `Net-(D2-A)`<br>`3` `+` -> `Net-(U2-+)`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U2-NC-Pad5)`<br>`6` -> `VOUT2`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U2-NC-Pad8)` | `1` / `unconnected-(U2-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `Net-(D2-A)`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `Net-(U2-+)`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U2-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT2`: OPA380 TIA output to feedback high side and on-board AD7606 input.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U2-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U3` | `/TIA_GREEN/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U3-NC-Pad1)`<br>`2` `-` -> `Net-(D3-A)`<br>`3` `+` -> `Net-(U3-+)`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U3-NC-Pad5)`<br>`6` -> `VOUT3`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U3-NC-Pad8)` | `1` / `unconnected-(U3-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `Net-(D3-A)`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `Net-(U3-+)`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U3-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT3`: OPA380 TIA output to feedback high side and on-board AD7606 input.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U3-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U4` | `/TIA_BLUE/` | OPA380AID | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | `1` `NC` -> `unconnected-(U4-NC-Pad1)`<br>`2` `-` -> `Net-(D4-A)`<br>`3` `+` -> `Net-(U4-+)`<br>`4` `V-` -> `GND`<br>`5` `NC` -> `unconnected-(U4-NC-Pad5)`<br>`6` -> `VOUT4`<br>`7` `V+` -> `+5V`<br>`8` `NC` -> `unconnected-(U4-NC-Pad8)` | `1` / `unconnected-(U4-NC-Pad1)`: Intentional no-connect for OPA380AID pin 1 `NC`.<br>`2` / `Net-(D4-A)`: OPA380 inverting summing input tied to SFH2201 anode and feedback network.<br>`3` / `Net-(U4-+)`: OPA380 non-inverting VBIAS input.<br>`4` / `GND`: OPA380 negative supply tied to board GND.<br>`5` / `unconnected-(U4-NC-Pad5)`: Intentional no-connect for OPA380AID pin 5 `NC`.<br>`6` / `VOUT4`: OPA380 TIA output to feedback high side and on-board AD7606 input.<br>`7` / `+5V`: OPA380 positive supply tied to +5V with local decoupling.<br>`8` / `unconnected-(U4-NC-Pad8)`: Intentional no-connect for OPA380AID pin 8 `NC`. |
| `U5` | `/LASER_IR/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_IR/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `Net-(U5-+)`<br>`4` `-` -> `/LASER_IR/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_IR/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `Net-(U5-+)`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_IR/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U6` | `/LASER_RED/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_RED/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `Net-(U6-+)`<br>`4` `-` -> `/LASER_RED/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_RED/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `Net-(U6-+)`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_RED/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U7` | `/LASER_GREEN/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_GREEN/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `Net-(U7-+)`<br>`4` `-` -> `/LASER_GREEN/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_GREEN/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `Net-(U7-+)`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_GREEN/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U8` | `/LASER_BLUE/` | TLV9001 | `Package_TO_SOT_SMD:SOT-23-5` | `1` -> `/LASER_BLUE/LOUT`<br>`2` `V-` -> `GND`<br>`3` `+` -> `Net-(U8-+)`<br>`4` `-` -> `/LASER_BLUE/FB`<br>`5` `V+` -> `+5V` | `1` / `/LASER_BLUE/LOUT`: TLV9001 output/loop compensation node before MOSFET gate resistor.<br>`2` / `GND`: TLV9001 negative supply tied to board GND.<br>`3` / `Net-(U8-+)`: TLV9001 non-inverting command input from PWM RC/limiter.<br>`4` / `/LASER_BLUE/FB`: TLV9001 inverting source-sense feedback input.<br>`5` / `+5V`: TLV9001 positive supply tied to +5V with local decoupling. |
| `U9` | `/MCU_ESP32-S3/` | ESP32-S3-WROOM-1 | `Espressif:ESP32-S3-WROOM-1` | `1` `GND` -> `GND`<br>`10` `GPIO17/U1TXD/ADC2_CH6` -> `ADC_SCLK`<br>`11` `GPIO18/U1RXD/ADC2_CH7/CLK_OUT3` -> `ADC_CS`<br>`12` `GPIO8/TOUCH8/ADC1_CH7/SUBSPICS1` -> `MPD3`<br>`13` `GPIO19/U1RTS/ADC2_CH8/CLK_OUT2/USB_D-` -> `/MCU_ESP32-S3/IO19`<br>`14` `GPIO20/U1CTS/ADC2_CH9/CLK_OUT1/USB_D+` -> `/MCU_ESP32-S3/IO20`<br>`15` `GPIO3/TOUCH3/ADC1_CH2` -> `MPD2`<br>`16` `GPIO46` -> `/MCU_ESP32-S3/IO46`<br>`17` `GPIO9/TOUCH9/ADC1_CH8/FSPIHD/SUBSPIHD` -> `MPD4`<br>`18` `GPIO10/TOUCH10/ADC1_CH9/FSPICS0/FSPIIO4/SUBSPICS0` -> `PWM1`<br>`19` `GPIO11/TOUCH11/ADC2_CH0/FSPID/FSPIIO5/SUBSPID` -> `PWM2`<br>`2` `3V3` -> `+3V3`<br>`20` `GPIO12/TOUCH12/ADC2_CH1/FSPICLK/FSPIIO6/SUBSPICLK` -> `PWM3`<br>`21` `GPIO13/TOUCH13/ADC2_CH2/FSPIQ/FSPIIO7/SUBSPIQ` -> `/MCU_ESP32-S3/IO13`<br>`22` `GPIO14/TOUCH14/ADC2_CH3/FSPIWP/FSPIDQS/SUBSPIWP` -> `/MCU_ESP32-S3/IO14`<br>`23` `GPIO21` -> `ADC_MISO_A`<br>`24` `GPIO47/SPICLK_P/SUBSPICLK_P_DIFF` -> `ADC_BUSY`<br>`25` `GPIO48/SPICLK_N/SUBSPICLK_N_DIFF` -> `ADC_RESET`<br>`26` `GPIO45` -> `/MCU_ESP32-S3/IO45`<br>`27` `GPIO0/BOOT` -> `/MCU_ESP32-S3/PROG`<br>`28` `SPIIO6/GPIO35/FSPID/SUBSPID` -> `/MCU_ESP32-S3/IO35`<br>`29` `SPIIO7/GPIO36/FSPICLK/SUBSPICLK` -> `/MCU_ESP32-S3/IO36`<br>`3` `EN` -> `/MCU_ESP32-S3/EN`<br>`30` `SPIDQS/GPIO37/FSPIQ/SUBSPIQ` -> `/MCU_ESP32-S3/IO37`<br>`31` `GPIO38/FSPIWP/SUBSPIWP` -> `ADC_MISO_B`<br>`32` `MTCK/GPIO39/CLK_OUT3/SUBSPICS1` -> `/MCU_ESP32-S3/IO39`<br>`33` `MTDO/GPIO40/CLK_OUT2` -> `/MCU_ESP32-S3/IO40`<br>`34` `MTDI/GPIO41/CLK_OUT1` -> `/MCU_ESP32-S3/IO41`<br>`35` `MTMS/GPIO42` -> `/MCU_ESP32-S3/IO42`<br>`36` `U0RXD/GPIO44/CLK_OUT2` -> `/MCU_ESP32-S3/IO44`<br>`37` `U0TXD/GPIO43/CLK_OUT1` -> `/MCU_ESP32-S3/IO43`<br>`38` `GPIO2/TOUCH2/ADC1_CH1` -> `MPD1`<br>`39` `GPIO1/TOUCH1/ADC1_CH0` -> `/MCU_ESP32-S3/FACT`<br>`4` `GPIO4/TOUCH4/ADC1_CH3` -> `ISENSE1`<br>`40` `GND` -> `GND`<br>`41` `GND` -> `GND`<br>`5` `GPIO5/TOUCH5/ADC1_CH4` -> `ISENSE2`<br>`6` `GPIO6/TOUCH6/ADC1_CH5` -> `ISENSE3`<br>`7` `GPIO7/TOUCH7/ADC1_CH6` -> `ISENSE4`<br>`8` `GPIO15/U0RTS/ADC2_CH4/XTAL_32K_P` -> `CONVST`<br>`9` `GPIO16/U0CTS/ADC2_CH5/XTAL_32K_N` -> `PWM4` | `1` / `GND`: ESP32-S3 module ground/return pin.<br>`10` / `ADC_SCLK`: ESP32-S3 GPIO17 output used as the AD7606-4 serial clock.<br>`11` / `ADC_CS`: ESP32-S3 GPIO18 output used as the AD7606-4 chip select.<br>`12` / `MPD3`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`13` / `/MCU_ESP32-S3/IO19`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`14` / `/MCU_ESP32-S3/IO20`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`15` / `MPD2`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`16` / `/MCU_ESP32-S3/IO46`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`17` / `MPD4`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`18` / `PWM1`: ESP32-S3 PWM output for one laser current command channel.<br>`19` / `PWM2`: ESP32-S3 PWM output for one laser current command channel.<br>`2` / `+3V3`: ESP32-S3 module 3V3 supply input.<br>`20` / `PWM3`: ESP32-S3 PWM output for one laser current command channel.<br>`21` / `/MCU_ESP32-S3/IO13`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`22` / `/MCU_ESP32-S3/IO14`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`23` / `ADC_MISO_A`: ESP32-S3 GPIO21 input reading AD7606-4 DOUTA.<br>`24` / `ADC_BUSY`: ESP32-S3 GPIO47 input reading AD7606-4 BUSY.<br>`25` / `ADC_RESET`: ESP32-S3 GPIO48 output driving AD7606-4 RESET.<br>`26` / `/MCU_ESP32-S3/IO45`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`27` / `/MCU_ESP32-S3/PROG`: ESP32-S3 GPIO0/BOOT pin in the copied access-controller program/reset network.<br>`28` / `/MCU_ESP32-S3/IO35`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`29` / `/MCU_ESP32-S3/IO36`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`3` / `/MCU_ESP32-S3/EN`: ESP32-S3 EN/CHIP_PU reset pin in the copied access-controller reset network.<br>`30` / `/MCU_ESP32-S3/IO37`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`31` / `ADC_MISO_B`: ESP32-S3 GPIO38 input reading AD7606-4 DOUTB.<br>`32` / `/MCU_ESP32-S3/IO39`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`33` / `/MCU_ESP32-S3/IO40`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`34` / `/MCU_ESP32-S3/IO41`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`35` / `/MCU_ESP32-S3/IO42`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`36` / `/MCU_ESP32-S3/IO44`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`37` / `/MCU_ESP32-S3/IO43`: ESP32-S3 local GPIO pin from the copied access-controller MCU sheet.<br>`38` / `MPD1`: ESP32-S3 ADC1 input for filtered internal laser monitor-PD telemetry.<br>`39` / `/MCU_ESP32-S3/FACT`: ESP32-S3 GPIO1 factory button input from the copied access-controller sheet.<br>`4` / `ISENSE1`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`40` / `GND`: ESP32-S3 module ground/return pin.<br>`41` / `GND`: ESP32-S3 module ground/return pin.<br>`5` / `ISENSE2`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`6` / `ISENSE3`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`7` / `ISENSE4`: ESP32-S3 ADC1 input for laser source-sense telemetry.<br>`8` / `CONVST`: ESP32-S3 GPIO15 output for the on-board AD7606-4 conversion-start line.<br>`9` / `PWM4`: ESP32-S3 PWM output for one laser current command channel. |
