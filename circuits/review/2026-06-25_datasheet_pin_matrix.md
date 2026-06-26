# Bench Laser Controller Datasheet Pin Matrix

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
| Internal laser monitor PD example | ams OSRAM PLT5 520B datasheet: https://look.ams-osram.com/m/200c3d8553b61059/original/PLT5-520B.pdf |
| Proof laser pin-code compatibility | Program proof-parts list `../docs/program/PROOF_LASER_PARTS_2026-06-24.md`; bench compatibility note `docs/part-notes/laser-harness-pin-code-compatibility.md`; Thorlabs diode pages for `L785P090`, `L638P040`, `L520A1`, `L450G2`, and `L405P20`. |
| External signal photodiode | ams OSRAM SFH 2201 A01 datasheet: https://look.ams-osram.com/m/151c0967b1d4864e/original/SFH-2201-A01.pdf |
| TIA op amp | TI OPA380 datasheet: https://www.ti.com/lit/ds/symlink/opa380.pdf |
| Laser current-loop op amp | TI TLV9001 datasheet: https://www.ti.com/lit/ds/symlink/tlv9001.pdf |
| 3.3 V LDO | Diodes AP2112 product/datasheet family: https://www.diodes.com/part/view/AP2112; thermal budget: `circuits/POWER_THERMAL_BUDGET.md` |
| USB ESD array | ST USBLC6-2 datasheet: https://www.st.com/resource/en/datasheet/usblc6-2.pdf |
| Laser current sink MOSFET | Alpha & Omega AO3400A datasheet: https://www.aosmd.com/res/data_sheets/AO3400A.pdf |
| Laser current-loop thermal budget | AO3400A datasheet, JLCPCB C5123624 2512 2 W resistor listing, and PLT5 520B reference diode: `circuits/LASER_CURRENT_THERMAL_BUDGET.md` |
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
| ESP32 ADC telemetry | `MPD1..4`: GPIO2 pin 38, GPIO1 pin 39, GPIO8 pin 12, GPIO9 pin 17. `ISENSE1..4`: GPIO4 pin 4, GPIO5 pin 5, GPIO6 pin 6, GPIO7 pin 7. | All eight analog telemetry inputs stay on ADC1 pins. | Netlist checker asserts every telemetry net has exactly one ESP32 ADC node and the intended front-end resistor node. |
| ESP32 control pins | `PWM1..4`: GPIO16 pin 9, GPIO38 pin 31, GPIO13 pin 21, GPIO14 pin 22. `CONVST`: GPIO17 pin 10. | PWM drives the slow command RC/limiter into TLV9001 loops; `PWM2` uses GPIO38 so the red command route stays off the GND reference plane while avoiding strapping pins. `CONVST` triggers the external AD7606 header. | Netlist checker asserts exact one-to-one GPIO membership. |
| USB Mini-B `J1` | Pin 1 `VBUS`; pin 2 `D-`; pin 3 `D+`; pin 4 `ID` no-connect; pin 5 `GND`; shield to `GND`. | USB VBUS feeds `VBUS_5V`; D-/D+ pass through USBLC6 and 22 ohm series resistors to ESP32 pins 13/14. | Package pin-function assertions and exact USB chain assertions. |
| USBLC6 `U10` | Pins 1/6 `IO1`; pin 2 `GND`; pins 3/4 `IO2`; pin 5 `VBUS`. | ESD protection at USB connector: D- through IO1 pair, D+ through IO2 pair, VBUS as clamp reference. | Exact pin-function and USB chain assertions. |
| AP2112K-3.3 `U11` | Pin 1 `VIN`; pin 2 `GND`; pin 3 `EN`; pin 4 `NC`; pin 5 `VOUT`. | `VIN` and `EN` tied to `+5V`; `VOUT` makes `+3V3`; pin 4 deliberate no-connect. Bench policy is RF disabled and <=120 mA continuous +3V3 load. | Exact pin-function and rail-membership assertions; `check_power_thermal_budget.py` enforces the accepted AP2112 thermal policy and intentionally fails sustained RF load cases. |
| OPA380AID `U1..U4` | SOIC-8: pins 1/5/8 `NC`; pin 2 `IN-`; pin 3 `IN+`; pin 4 `V-`; pin 6 `OUT`; pin 7 `V+`. | External/sample photodiode TIA: SFH2201 anode to pin 2 summing node, VBIAS to pin 3, output to `VOUTx`, `V+` to `+5V`, `V-` to `GND`. | Exact pin-function assertions now include pins 1/5/8 as `passive+no_connect`; TIA net signatures assert every summing node and output node. |
| SFH2201 `D1..D4` | Pin 1 `K`; pin 2 `A`. | Cathode reverse-biased from `+5V` through `RB` and bypassed by `CB`; anode goes to OPA380 pin 2 summing node. | Pin-function and exact TIA photodiode net assertions. |
| TLV9001IDBVR `U5..U8` | Non-U DBV SOT-23-5: pin 1 `OUT`; pin 2 `V-`; pin 3 `IN+`; pin 4 `IN-`; pin 5 `V+`. Do not substitute the TLV9001U DBV pinout without rewiring. | Laser current loop amplifier: `IN+` gets filtered/limited PWM command; `IN-` senses MOSFET source resistor high side; output drives AO3400A gate resistor. | Exact pin-function, `FB`, `LOUT`, and command-limiter net assertions. |
| AO3400A `Q1..Q4` | SOT-23: pin 1 `G`; pin 2 `S`; pin 3 `D`. | Low-side laser current sink: gate from TLV9001 through `R31`; source through 10 ohm 2 W sense resistor; drain to `LASER_Nx`. Linear-pass heat depends on `LASER_V+`, diode `Vf`, current, and duty cycle. | Pin-function and exact `LASER_Nx`, gate, and source/sense net assertions; `check_laser_current_budget.py` must pass for each selected diode/supply assumption. |
| PLT5 520B style 3-pin laser diode | Pin 1 LD cathode; pin 2 LD anode + monitor-PD cathode + case; pin 3 monitor-PD anode. | J4 harness intent for compatible packages: pin 1 to `LASER_Nx`, pin 2/common to `LASER_V+`, pin 3 to `MPD_RAWx`. The PLT5 520B forward-voltage/current class is only the green reference case for the common-rail thermal budget. | Bench board exposes `LASER_Nx`, `LASER_V+`, and `MPD_RAWx`; actual laser MPN, harness pinout, and per-diode `LASER_V+`/thermal budget remain release blockers. |
| Proof laser pin-code compatibility | Polarity-compatible: PLT5-style and Thorlabs A-code common-anode / monitor-PD-cathode cans such as `L638P040` and `L520A1`. Not direct-compatible: `L785P090` C-code monitor feedback; no monitor telemetry: `L450G2`. | The low-side current sink and high-side `MPD_RAWx -> 750R -> MPD_BIAS` front end assume monitor-PD anode on `MPD_RAWx` and monitor-PD cathode on the high common node. `L785P090` puts the monitor-PD anode on the case/common laser-cathode side and the monitor-PD cathode on the isolated monitor pin. | `check_laser_controller_release_readiness.py` keeps actual laser MPN/harness and `L785P090` monitor feedback blocked until the correct adapter/front end is designed or a compatible diode/rail policy is selected. |
| Monitor PD front end | `MPD_RAWx` to 750 ohm sense resistor, then `MPD_BIAS`; INA4180A1 gain 20 drives `MPD_AMPx -> 1k/100 nF -> MPDx`; LM4040C50 holds `LASER_V+ - MPD_BIAS` near 5 V. | Internal laser monitor PD current becomes slow ESP32 ADC telemetry for normalization/APC experiments. PLT5 520B typical monitor current maps to about 2.25 V at the ADC and about 4.89 V monitor-PD reverse bias at `LASER_V+ = 10.5 V`. | Exact `MPD_RAWx`, `MPD_BIAS`, `MPD_AMPx`, and `MPDx` net assertions; `check_laser_monitor_pd_budget.py` verifies the PLT5 10.5 V high-side monitor-bias policy; PCB checker enforces J4 monitor-front-end placement proximity. |
| SS14 `D5/D6` | Pin 1 anode; pin 2 cathode. | USB `VBUS_5V` and external `/POWER_IO/EXT5V` OR into `+5V`. | Pin-function, source/cathode net assertions, and explicit D5/D6 cathode route to bulk cap. |
| Bourns 3224 trim pots `RV1..RV4` | 3-terminal pot, wiper pin 2. | VBIAS trim for OPA380 non-inverting input; series resistor bounds the adjustment. | VBIAS net signature and placement proximity checks. |
| Headers J2/J3/J4/J5/J6 | Pin order defined in generated schematic and README. | Bring-up UART/EN/BOOT, AD7606 output header, laser/monitor harness, laser supply, external 5 V. | Exact connector net assertions and full inventory rows. |

## Remaining Release Blockers

- Run KiCad GUI ERC on the regenerated schematic.
- Refill zones and run KiCad PCB DRC with schematic parity.
- Refill the `In1.Cu` `GND` zone and visually review return paths; `VBUS_5V`,
  `+5V`, `+3V3`, `LASER_V+`, and `GND` are explicitly connected in the
  generated board but still need final visual/DRC/thermal review.
- Accept and measure AP2112 bench/no-RF thermal margin, or replace it with a buck regulator
  or larger proven supply before sustained Wi-Fi/BLE use.
- Confirm each actual laser MPN pin table and can/common-node polarity before building the J4 harness. In particular, do not wire `L785P090` directly to J4 expecting the current `MPD_RAWx` circuit to read its monitor photodiode.
- Review laser-current thermal/SOA for actual `LASER_V+`, diode forward voltage, duty cycle, and current clamp.
