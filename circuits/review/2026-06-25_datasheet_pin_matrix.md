# Bench Laser Controller Datasheet Pin Matrix

Historical note: this dated pin matrix records the package-pin decisions, but
some numeric counts and PCB-route descriptions may lag the current copied-MCU
schematic and staged PCB. Use `review/generated/laser_controller_review_gate.md`,
`review/2026-06-25_full_net_pin_inventory.md`, `docs/source-register.md`, and
the live checker commands for current counts and release state.

Generated audit date: 2026-06-25.

This file records the package-pin decisions that are intentionally encoded in
`gen_laser_controller.py`, asserted by `check_laser_controller_netlist.py`, and
reflected in `review/2026-06-25_full_net_pin_inventory.md`. It is a pinout
audit, not a manufacturing release.

`check_laser_controller_pcb.py` also inventories physical PCB pad instances:
every netted pad must match the exported schematic netlist, and every unnetted
pad must be one of the explicit NC/unused package pads or paste/mechanical pads
listed by the generated whitelist.
It also checks routed copper and vias for board-boundary compliance and fails
unsupported dangling same-net segment endpoints or vias, so a route stub cannot
hide behind an otherwise connected net.
Route-layer policy is also checked: `In1.Cu` is kept as a ground/reference
plane with no routed segments, and sensitive local USB/MPD/TIA/laser-control
nets are constrained to the intended layer set.
Route-width policy is checked for every generated segment as well, so a net
cannot silently become narrower or wider than the documented route class/local
exception.
Sensitive local-route length policy is also checked for the monitor PD raw nodes,
OPA380 input/bias nodes, trim wipers, TLV9001 laser-control nodes, laser
sense-feedback loops, and AO3400A gate-drive nodes, so the generated board cannot
keep the right pin names while moving those nets out of their local blocks.
`check_schematic_hierarchy_labels.py` verifies that the root sheet pins and
directions match the child sheet hierarchical labels and label shapes, that the
44 root global labels are exactly the intended board-level interconnect
whitelist, and that no child sheet carries an accidental global label.
`check_laser_controller_netlist.py` also allowlists every one-node exported net,
so USB ID, AP2112 NC, OPA380 NC pins, and unused ESP32 pads are deliberate and a
new floating pin is not accepted silently.

The source register and compact package-sensitive part notes are now tracked in
`docs/source-register.md` and `docs/part-notes/`. Those files record which
datasheet/manufacturer source backs each package or behavioral assumption.

## Source Set

External source URLs are now rechecked by `check_source_documents.py`, and the
generated KiCad artifact is checked against the local access-controller MCU
sheet and package-sensitive KiCad footprint files.

| Area | Primary source used |
|---|---|
| ESP32-S3 module and USB pins | Espressif ESP32-S3-WROOM-1/WROOM-1U datasheet: https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf; ESP32-S3 series datasheet for native USB behavior: https://documentation.espressif.com/esp32-s3_datasheet_en.pdf; repo source: `~/projects/access-controller/circuits/controller/microcontroller.kicad_sch` |
| ESP32 ADC channel use | Espressif ESP-IDF ESP32-S3 ADC guide plus ESP32-S3 module datasheet pin names. |
| Selected laser pin-code compatibility | Digikey cart parts and datasheets: D7805I, D6505I, PLT5 520EB_P, and PLT5 450GB; bench compatibility note `docs/part-notes/laser-harness-pin-code-compatibility.md`. |
| External signal photodiode | ams OSRAM SFH 2201 A01 datasheet: https://look.ams-osram.com/m/151c0967b1d4864e/original/SFH-2201-A01.pdf |
| TIA op amp | TI OPA380 datasheet: https://www.ti.com/lit/ds/symlink/opa380.pdf |
| Laser current-loop op amp | TI TLV9001 datasheet: https://www.ti.com/lit/ds/symlink/tlv9001.pdf |
| 3.3 V LDO | Diodes AP2112 product/datasheet family: https://www.diodes.com/part/view/AP2112; thermal budget: `circuits/POWER_THERMAL_BUDGET.md` |
| Copied MCU USB/VBUS support | Access-controller MCU sheet and local `~/circuits` libraries: discrete `LESD5D5.0CT1G` USB/VBUS clamps plus `1N5819HW` USB VBUS isolation diodes. |
| Laser current sink MOSFET | Alpha & Omega AO3400A datasheet: https://www.aosmd.com/res/data_sheets/AO3400A.pdf |
| Laser current-loop thermal budget | AO3400A datasheet, JLCPCB C5123624 2512 2 W resistor listing, and high-forward-voltage green reference case: `circuits/LASER_CURRENT_THERMAL_BUDGET.md` |
| Power OR-ing diodes | LCSC/MDD SS14 data for C2480 plus Vishay SS12-SS16 SMA family reference: https://www.vishay.com/doc/?88746= |
| USB connector | Wuerth Elektronik 65100516121 product data and local KiCad footprint `Connector_USB:USB_Mini-B_Wuerth_65100516121_Horizontal`. |
| Trim pot | Bourns 3224 datasheet: https://www.bourns.com/pdfs/3224.pdf |

Local footprint pads were spot-checked in:
`/usr/share/kicad/footprints/OptoDevice.pretty/Osram_SFH2201.kicad_mod`,
`/usr/share/kicad/footprints/RF_Module.pretty/ESP32-S3-WROOM-1.kicad_mod`,
`/usr/share/kicad/footprints/Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod`,
`/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23.kicad_mod`,
`/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23-5.kicad_mod`,
`/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23-6.kicad_mod`,
`/usr/share/kicad/footprints/Diode_SMD.pretty/D_SMA.kicad_mod`,
`/usr/share/kicad/footprints/Connector_USB.pretty/USB_Mini-B_Wuerth_65100516121_Horizontal.kicad_mod`,
and `/usr/share/kicad/footprints/Potentiometer_SMD.pretty/Potentiometer_Bourns_3224W_Vertical.kicad_mod`.

## Pinout Decisions

| Component | Package pins checked | Bench net/use | Guardrail |
|---|---|---|---|
| ESP32-S3-WROOM-1 `U9` | Pin 2 `3V3`; pins 1/40/41 `GND`; pin 3 `EN`; pin 13 `GPIO19/USB_D-`; pin 14 `GPIO20/USB_D+`; pin 27 `GPIO0/BOOT`; pins 36/37 UART; selected GPIO pins below; all other unused pads intentional no-connects. | Native USB Serial/JTAG, UART bring-up, laser PWM, current telemetry, monitor-PD telemetry, `CONVST`. | Exact pin names/types and deliberate no-connect pads asserted in netlist checker; checker also compares the generated MCU sheet's `Espressif:ESP32-S3-WROOM-1` symbol block against the access-controller source symbol with only the footprint-library substitution allowed. |
| ESP32 ADC telemetry | `MPD1..4`: GPIO2 pin 38, GPIO3 pin 15, GPIO8 pin 12, GPIO9 pin 17. `ISENSE1..4`: GPIO4 pin 4, GPIO5 pin 5, GPIO6 pin 6, GPIO7 pin 7. GPIO1 pin 39 is the copied factory-button net, not monitor telemetry. | All eight analog telemetry inputs stay on ADC1 pins. | Netlist checker asserts every telemetry net has exactly one ESP32 ADC node and the intended front-end resistor node. |
| ESP32 control pins | `PWM1..4`: GPIO10 pin 18, GPIO11 pin 19, GPIO12 pin 20, GPIO16 pin 9. `CONVST`: GPIO15 pin 8. | PWM drives the slow command RC/limiter into TLV9001 loops; `CONVST` triggers the on-board AD7606-4. | Netlist checker asserts exact one-to-one GPIO membership. |
| USB Mini-B `J1` / `J2` | Pin 1 `VBUS`; pin 2 `D-`; pin 3 `D+`; pin 4 `ID` no-connect; pin 5 `GND`; shield pad 6 to `GND`. | J1 feeds CP2102N USB-UART through copied discrete ESD; J2 feeds ESP32 native USB on GPIO19/GPIO20 through copied discrete ESD. J1/J2 VBUS pass through copied `1N5819HW` isolation diodes before `VBUS_5V`. | Package pin-function assertions and exact copied-MCU USB chain assertions. |
| Copied MCU USB/VBUS support `D7..D14` | `LESD5D5.0CT1G` data/VBUS clamps and `1N5819HW` VBUS isolation diodes from the copied MCU sheet. | Discrete protection/isolation for J1 CP2102N USB-UART and J2 ESP32 native USB; no USBLC6 array or 22 ohm USB series resistors are present in the active copied MCU sheet. | Source/register and netlist guardrails assert the copied designators and reject stale USBLC6 documentation. |
| AP2112K-3.3 `U11` | Pin 1 `VIN`; pin 2 `GND`; pin 3 `EN`; pin 4 `NC`; pin 5 `VOUT`. | `VIN` and `EN` tied to `+5V`; `VOUT` makes `+3V3`; pin 4 deliberate no-connect. Bench policy is RF disabled and <=120 mA continuous +3V3 load. | Exact pin-function and rail-membership assertions; `check_power_thermal_budget.py` enforces the accepted AP2112 thermal policy and intentionally fails sustained RF load cases. |
| OPA380AID `U1..U4` | SOIC-8: pins 1/5/8 `NC`; pin 2 `IN-`; pin 3 `IN+`; pin 4 `V-`; pin 6 `OUT`; pin 7 `V+`. | External/sample photodiode TIA: SFH2201 anode to pin 2 summing node, VBIAS to pin 3, output to `VOUTx`, `V+` to `+5V`, `V-` to `GND`. | Exact pin-function assertions now include pins 1/5/8 as `passive+no_connect`; TIA net signatures assert every summing node and output node. |
| SFH2201 `D1..D4` | Pin 1 `K`; pin 2 `A`. | Cathode reverse-biased from `+5V` through `RB` and bypassed by `CB`; anode goes to OPA380 pin 2 summing node. | Pin-function and exact TIA photodiode net assertions. |
| TLV9001IDBVR `U5..U8` | Non-U DBV SOT-23-5: pin 1 `OUT`; pin 2 `V-`; pin 3 `IN+`; pin 4 `IN-`; pin 5 `V+`. Do not substitute the TLV9001U DBV pinout without rewiring. | Laser current loop amplifier: `IN+` gets filtered/limited PWM command; `IN-` senses MOSFET source resistor high side; output drives AO3400A gate resistor. | Exact pin-function, `FB`, `LOUT`, and command-limiter net assertions. |
| AO3400A `Q1..Q4` | SOT-23: pin 1 `G`; pin 2 `S`; pin 3 `D`. | Low-side laser current sink: gate from TLV9001 through `R31`; source through 10 ohm 2 W sense resistor; drain to `LASER_Nx`. Linear-pass heat depends on `LASER_V+`, diode `Vf`, current, and duty cycle. | Pin-function and exact `LASER_Nx`, gate, and source/sense net assertions; `check_laser_current_budget.py` must pass for each selected diode/supply assumption. |
| D7805I IR laser diode | Style-A 5.6 mm can: pin 1 laser cathode; pin 2 common case; pin 3 monitor diode anode. | Direct `LD1` footprint: pin 1 to `LASER_N1`, pin 2/common to `LASER_V+`, pin 3 to `MPD_RAW1`. | `LD1` uses `OptoDevice:LaserDiode_TO18-D5.6-3`; J5 remains the external laser supply input. |
| D6505I red laser diode | Style-A 5.6 mm can: pin 1 laser cathode; pin 2 common case; pin 3 monitor diode anode. | Direct `LD2` footprint: pin 1 to `LASER_N2`, pin 2/common to `LASER_V+`, pin 3 to `MPD_RAW2`. | `LD2` uses `OptoDevice:LaserDiode_TO18-D5.6-3`; no laser/MPD harness header remains. |
| PLT5 520EB_P green laser diode | 5.6 mm TO56 can with monitor PD: pin 1 LD cathode; pin 2 LD anode + monitor-PD cathode + case; pin 3 monitor-PD anode. | Direct `LD3` footprint: pin 1 to `LASER_N3`, pin 2/common to `LASER_V+`, pin 3 to `MPD_RAW3`. | `LD3` uses `OptoDevice:LaserDiode_TO56-3`; monitor front-end policy checks the 150 uA, VRPD=5 V datasheet reference case. |
| PLT5 450GB blue laser diode | 5.6 mm TO56 laser-only can: pin 1 LD anode; pin 2 case; pin 3 LD cathode. | Direct `LD4` footprint: pin 1 to `LASER_V+`, pin 3 to `LASER_N4`, pin 2 case no-connect. `MPD_RAW4` remains spare/open at the INA4180 front end. | `LD4` uses `OptoDevice:LaserDiode_TO56-3`; do not wire case to `MPD_RAW4`. |
| Monitor PD front end | `MPD_RAWx` to 750 ohm sense resistor, then `MPD_BIAS`; INA4180A1 gain 20 drives `MPD_AMPx -> 1k/100 nF -> MPDx`; LM4040C50 holds `LASER_V+ - MPD_BIAS` near 5 V. | Internal laser monitor PD current becomes slow ESP32 ADC telemetry for normalization/APC experiments. PLT5 520EB_P typical monitor current maps to about 2.25 V at the ADC and about 4.89 V monitor-PD reverse bias at `LASER_V+ = 10.5 V`; D6505I and D7805I must be verified against their monitor reverse-bias limits during bring-up. | Exact `MPD_RAWx`, `MPD_BIAS`, `MPD_AMPx`, and `MPDx` net assertions; `check_laser_monitor_pd_budget.py` verifies the PLT5 520EB_P 10.5 V high-side monitor-bias policy; PCB checker enforces direct-laser-to-monitor-front-end placement proximity. |
| SS14 `D5/D6` | Pin 1 anode; pin 2 cathode. | USB `VBUS_5V` and external `/POWER_IO/EXT5V` OR into `+5V`. | Pin-function, source/cathode net assertions, and explicit D5/D6 cathode route to bulk cap. |
| Bourns 3224 trim pots `RV1..RV4` | 3-terminal pot, wiper pin 2. | VBIAS trim for OPA380 non-inverting input; series resistor bounds the adjustment. | VBIAS net signature and placement proximity checks. |
| Headers J5/J6 | Pin order defined in generated schematic and README. | J5 is the external laser-anode supply input; J6 is the external 5 V input. USB/UART/reset/program buttons, the AD7606, and laser cans are on-board. | Exact connector net assertions and full inventory rows. |

## Remaining Release Blockers

- Run KiCad GUI ERC on the regenerated schematic.
- Refill zones and run KiCad PCB DRC with schematic parity.
- Finish/reroute the current recovered-placement PCB: the live checker reports
  final board-boundary/proximity issues, zero board-level routed segments, zero
  vias, no filled `In1.Cu` `GND` reference zone, and missing USB/laser/analog
  routes.
- Accept and measure AP2112 bench/no-RF thermal margin, or replace it with a buck regulator
  or larger proven supply before sustained Wi-Fi/BLE use.
- Confirm each actual laser MPN pin table and can/common-node polarity before
  soldering into the direct `LDx` footprint. In particular, keep the PLT5 450GB
  case isolated/no-connect unless the mechanical design intentionally bonds the
  can elsewhere.
- Review laser-current thermal/SOA for actual `LASER_V+`, diode forward voltage, duty cycle, and current clamp.
