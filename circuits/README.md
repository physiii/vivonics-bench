# Laser Controller — 1ch × 4λ: on-board SFH2201 PD → 4ch TIA + monitor-PD feedback + ESP32-S3 + 4× laser drivers

Bench controller for the bR index/phase read. **One optical channel, four wavelengths**
(IR / RED / GREEN / BLUE). Each wavelength has a precision **constant-current laser sink**
(with current-sense feedback) and one **on-board Osram SFH2201 clear Si PIN photodiode**
reverse-biased into an **OPA380 transimpedance amp**. The four TIA outputs go to the
on-board **AD7606BSTZ-4**. An **ESP32-S3-WROOM-1** real-time co-processor drives the 4 PWM laser
controls, reads the 4 current-sense voltages and 4 internal laser monitor-photodiode
voltages on its own ADC pins, issues hardware-timed **CONVST** to the AD7606, clocks the
AD7606 serial outputs, is programmed
and powered over **native USB (Mini-B)**, and talks to the Raspberry Pi over **UART**.

**Why a single PD per wavelength (not a quad/centroid PD):** the production reader is a
Gpixel line sensor doing a *per-pixel intensity* read, and the bench's dual-pinhole
interferometer is also a single-PD intensity read — so one broadband PD per beam is the
faithful, JLCPCB-assemblable proxy. Beam-deflection/centroid sensing (the quad-PD's only
unique capability) is a fallback the production engine deliberately engineers out. Rationale:
`../../docs/program/DUAL_PINHOLE_PHASE_READ_EXPERIMENT_DESIGN_2026-06-22.md`,
`SZEGED_BR_SWITCHING_LINEAGE_AND_INDEX_READ_FINDINGS_2026-06-22.md`,
`INDEX_READ_PRODUCTION_ARCHITECTURE_2026-06-02.md` (parent repo).

## Files

All sheets are **code-generated** from `gen_laser_controller.py`. The MCU sheet uses the
copied access-controller ESP32-S3 page with the real
`Espressif:ESP32-S3-WROOM-1` symbol, CP2102N USB-UART, two USB Mini-B entries,
discrete ESD/VBUS support, and reset/program/factory buttons. **Do not
hand-edit the generated `.kicad_sch` files**; edit the generator or copied-source
adapter flow deliberately and re-run:

```
python3 gen_laser_controller.py
```

| File | Role |
|---|---|
| `gen_laser_controller.py` | Generator for root, TIA, laser-driver, MCU, power/IO sheets + BOM. |
| `adapt_mcu.py` | Compatibility wrapper for older flows; it verifies the imported MCU sheet exists and does not overwrite the copied access-controller page. |
| `gen_pcb.py` | Placement-staging generator: keeps only the 90 x 50 mm board outline, stages schematic footprints outside the outline, and assigns PCB pad nets for manual placement/ratsnest work. |
| `check_laser_controller_pcb.py` | Board-level guardrail: verifies generated PCB pad nets against the exported schematic netlist. |
| `check_schematic_hierarchy_labels.py` | Schematic hierarchy/label guardrail: verifies root sheet pins, pin directions, child hierarchical label shapes, and intentional root global-label whitelist. |
| `check_schematic_presentation.py` | Schematic presentation guardrail: verifies generated net labels clear symbols/text/other labels, generated wires do not enter symbol bodies, and symbol pin anchors/strokes touch their glyphs. |
| `check_laser_controller_sources.py` | Source/register guardrail: verifies every exported MPN/LCSC token is represented in the source register or part notes, every exported net has a specific electrical-intent mapping, and every exported component pin has a component-pin-level role. |
| `check_part_notes_completeness.py` | Part-note guardrail: verifies critical datasheet notes still carry pinout, layout, risk, and checker-evidence phrases. |
| `check_source_documents.py` | Source-document guardrail: verifies required datasheet/manufacturer URLs and required local source/footprint artifacts are present; reports secondary/distributor source risks and vendor-CDN probe failures as warnings. |
| `check_laser_controller_release_gate.py` | Generated-copper fabrication gate: fails on split signal/control nets, unacceptable laser cathode/anode current routes, or missing laser sense-return GND vias; poured rail/zone connectivity is checked by KiCad refill/DRC. |
| `check_layout_review_geometry.py` | Focused layout-geometry gate for buck local loops, USB ESD placement, OPA380 summing-node loops, monitor-PD raw paths, and laser-current sense loops. |
| `check_laser_controller_release_readiness.py` | Open first-article/production blocker gate: keeps calibration, firmware, thermal, protection, procurement, and measured bring-up blockers visible in the review wrapper. |
| `check_jlcpcb_order_package.py` | JLCPCB prototype order-package gate: verifies Gerber/drill zip contents, BOM/POS designator match, J7 C192300 2x4 SMD header metadata, required board labels, and the flat transfer archive. |
| `check_power_thermal_budget.py` | AP2112 `+3V3` thermal guardrail for bench/no-RF versus sustained RF policies. |
| `check_power_bringup_template.py` | First-article power/input bring-up measurement-template guardrail for J5/VIN24, AP632 rails, post-OR +5V, LASER_V+, and AP2112 +3V3 rows. |
| `check_vin24_input_protection.py` | VIN_24V bench-topology and production input-protection guardrail for J5/J6, adapter/harness limit, fuse/TVS/reverse-protection decisions. |
| `check_laser_driver_control_loop.py` | Laser-driver control-loop guardrail for PWM divider topology, TLV9001 input/output range, AO3400A gate drive, and the hardware-clamp gate-margin expected fail. |
| `check_laser_driver_package_pcb.py` | Laser-driver package/PCB guardrail: verifies U5-U8 TLV9001 and Q1-Q4 AO3400A schematic pin nets, local sense/command/gate/compensation component identities, current PCB pad nets, and KiCad SOT-23-5/SOT-23/2512/0603/0402/0603-cap geometry. |
| `check_laser_diode_footprints.py` | Direct LD1-LD4 TO-can guardrail: verifies selected diode MPN/footprint identities, schematic pin nets, current PCB pad nets, LD4 case no-connect, `MPD_RAW4` spare/open, and installed KiCad TO18/TO56 pad geometry. |
| `check_monitor_pd_package_pcb.py` | Monitor-PD package/PCB guardrail: verifies U12 INA4180/U13 LM4040 pin nets, local 240 ohm sense, 1 k / 100 nF ADC filters, R41/C35/C36 support parts, current PCB pad nets, LD4 case no-connect, and KiCad TSSOP-14/SOT-23/0603/0402 geometry. |
| `check_laser_current_budget.py` | Laser current-loop guardrail for the PWM clamp, selected laser-diode current limits, sense resistor, AO3400A heat, and `LASER_V+` headroom. |
| `check_laser_bringup_template.py` | First-article laser bring-up measurement-template guardrail for LD1-LD4 current-limit, safety-fixture, optical-output, temperature, and firmware-shutoff rows. |
| `check_tia_readout_budget.py` | SFH2201/OPA380 signal-PD TIA guardrail: exact topology into AD7606, VBIAS/common-mode bound, OPA380 output headroom, and bright-ambient expected-fail range check. |
| `check_optical_calibration_template.py` | First-article optical/readout calibration-template guardrail for LD1-LD4 monitor-PD handling, D1-D4 signal-PD calibration, and U14 V1-V4 AD7606 known-input readback rows. |
| `check_firmware_validation_template.py` | First-article AD7606 firmware/readback validation-template guardrail for timing, both DOUT lines, scaling, channel order, and known-input rows. |
| `check_ad7606_package_pcb.py` | AD7606 package/PCB guardrail: verifies U14 schematic pin nets, C51-C60 AVCC/VDRIVE/REGCAP/reference capacitor identities and pad nets, current PCB pad nets, FRSTDATA no-connect, and installed KiCad LQFP-64 pad geometry. |
| `check_ap6320x_package_pcb.py` | AP63205/AP63200 package/PCB guardrail: verifies U15/U16 schematic pin nets, current PCB pad nets, KiCad TSOT-23-6 pad geometry, and local L1/L2 inductor footprint geometry. |
| `check_passive_derating.py` | Passive voltage/power guardrail for every assembled capacitor, resistor, and SMD trimmer MPN in the exported netlist. |
| `check_procurement_release_template.py` | Quote-time procurement and production-derating template guardrail for BOM/POS quote acceptance, substitutions, pulse/surge derating, board-temperature evidence, and order archive linkage. |
| `check_first_article_release_evidence.py` | First-article release evidence ledger guardrail: requires explicit closure rows for all deferred blocker categories and keeps them open until linked measurement/procurement/firmware evidence exists. |
| `run_laser_controller_review.py` | One-command review wrapper for available gates, JLCPCB order status, deferred first-article/production blockers, and KiCad ERC/DRC/parity reporting. |
| `laser_controller.kicad_sch` | Root sheet — sheet symbols + global-label interconnect (A2). |
| `tia_ir.kicad_sch`, `tia_red.kicad_sch`, `tia_green.kicad_sch`, `tia_blue.kicad_sch` | Four on-board PD + OPA380 TIA sheets with globally unique designators. |
| `laser_ir.kicad_sch`, `laser_red.kicad_sch`, `laser_green.kicad_sch`, `laser_blue.kicad_sch` | Four constant-current laser sink sheets with globally unique designators; each sheet has a direct through-hole TO-can footprint so `LD_K`, common `LD_A/PD_K/case`, and `PD_A -> MPD_RAW` are visible. |
| `mcu.kicad_sch` | ESP32-S3-WROOM-1 + CP2102N USB-UART + two USB Mini-B connectors + discrete USB/VBUS ESD + reset/program/factory buttons. |
| `power_io.kicad_sch` | 5V OR-ing, laser supply, on-board AD7606-4 signal ADC, and shared INA4180/LM4040 monitor-PD front end. |
| `laser_controller_bom_jlcpcb.csv` | JLCPCB SMT assembly CSV (Comment, Designator, Footprint, LCSC); hand-add headers and direct laser cans are listed separately. |
| `fab/laser_controller_pos.csv` | JLCPCB SMT CPL/POS CSV generated from the current PCB; designators match the JLCPCB BOM. |
| `laser_controller_gerbers.zip` | Current PCB Gerber/drill zip for JLCPCB PCB fabrication upload. |
| `laser_controller_jlcpcb_package.zip` | Flat review/transfer archive containing Gerber/drill files plus BOM and POS. |
| `laser_controller.kicad_pro` | KiCad 7 project file. |
| `LASER_MONITOR_PD_FEEDBACK.md` | Design note for the internal laser monitor photodiode feedback path and production APC implications. |
| `LASER_CURRENT_THERMAL_BUDGET.md` | Laser current-loop thermal budget and common-rail bench limitation. |
| `POWER_TREE.md` | Rail/source/load review and release gates for 24 V barrel/RJ45 input, USB VBUS, BUCK_5V, +5V, +3V3, LASER_V+, and GND. |
| `POWER_THERMAL_BUDGET.md` | AP2112/ESP32-S3 thermal budget and bench-vs-production regulator decision. |
| `../docs/source-register.md` | Datasheet/source register for active components, passives, manufacturing capability, and open source gaps. |
| `../docs/part-notes/` | Compact datasheet notes for package-sensitive and behavior-sensitive parts. |

Every SMT component carries a **hidden `LCSC` field + `Part Number` (MPN) field** — exactly
the access-controller convention, so clicking a part in Eeschema shows its LCSC number and
the JLCPCB BOM exports straight from the `LCSC` column.

## Topology

```
PD + TIA CHANNEL (×4 = IR / RED / GREEN / BLUE)  — on-board, no off-board optics header
  Osram SFH2201 clear Si PIN PD (D1):  cathode → +5V via RB(1k)+CB bypass = reverse bias
        anode → OPA380AID −IN (summing node)
  Rf = RVFB (2M feedback trim, wiper tied to output side) ∥ Cf = C1 (10pF) ;  +IN = VBIAS (RV11 10k trim + RC)
  V_OUT = VBIAS + I_pd·Rf  →  U14 AD7606BSTZ-4 on-board ADC
  check_tia_readout_budget.py passes the current topology but shows this is a high-sensitivity bench range:
  at VBIAS=1.5V and RF=2M, OPA380 headroom is about +1.40 uA / -0.70 uA before clipping.
  TIA readout range and optical calibration remain release blockers.

LASER DRIVER (×4, one per wavelength)
  PWM_IN → 10k/1µF filter with per-channel limiter pulldown → TLV9001(+) ; TLV9001 OUT →
  1k → AO3400A gate ; source → 10Ω 2512 2W sense → GND
  I_laser = V_ctrl / 10Ω ; full-scale command is per color:
  IR≈38.0mA, red≈23.0mA, green≈76.2mA, blue≈105.5mA.
  The selected max-current and per-channel analog-limit cases pass the
  TLV9001/AO3400A range checks; optical output, duty cycle, loop dynamics, and
  board temperature remain bring-up measurements.
  Sense top → FB (op-amp −) and 1k → ISENSE (isolates the ADC tap from the loop) ;
  10pF loop-comp ; AO3400A drain → LASER_N (direct LDx footprint) ; laser-can model:
  LD_K → LASER_N, common LD_A/PD_K/case → LASER_V+, PD_A → MPD_RAW
  LASER_V+ is a shared bench rail: set it from the actual diode Vf/current table so the
  AO3400A does not become the heat sink.

MCU  ESP32-S3-WROOM-1 (2.4 GHz Wi-Fi 802.11 b/g/n / Bluetooth LE / native USB)
  USB Mini-B J1 → discrete ESD → CP2102N USB-UART → ESP32 UART0/auto-reset network
  USB Mini-B J2 → discrete ESD → ESP32 native USB-Serial/JTAG
  (D+ = GPIO20 / module pin 14, D− = GPIO19 / module pin 13)
  4× PWM → laser drivers · 4× ISENSE ← laser current-sense · 4× MPD ← internal monitor PDs ·
  CONVST/SCLK/CS/RESET → AD7606 · BUSY/DOUTA/DOUTB ← AD7606
  VDD3P3 from AP2112K-3.3 LDO (bench/no-RF thermal policy only) ; EN pulled up + 1uF + reset button ;
  GPIO0/BOOT pulled up + 1uF with local PROG button ; FACT button on GPIO1

POWER / IO
  VIN_24V = J5 center-positive barrel jack + J6 RJ45 pins 4/5 copied from access-controller
  VIN_24V is presently a direct bench input: no schematic fuse/PTC/TVS/
  reverse-protection/eFuse stage sits between J5/J6 and the AP632 buck inputs.
  BUCK_5V = U15 AP63205WU-7 from VIN_24V ; D6 ORs it with USB VBUS through D5 into +5V
  +3V3 = AP2112K-3.3 from +5V
  LASER_V+ = U16 AP63200WU-7 from VIN_24V, set near 9.38V for the shared bench laser rail
  U14 AD7606BSTZ-4RL → VOUT1..4, CONVST, SCLK, CS, BUSY, RESET, DOUTA, DOUTB
  LD1..LD4 direct TO-can footprints carry LASER_N/MPD_RAW pairs + LASER_V+
  MPD_RAWx -> 240R sense -> MPD_BIAS ; INA4180A1 gain 20 -> 1k/100nF -> MPDx ESP32 ADC
  LM4040C50 holds LASER_V+ - MPD_BIAS near 5V for PLT5-style/A-code monitor diodes
```

The third monitor-photodiode pin present on several raw laser diodes is exposed as
`MPD_RAW1..4` and converted to ESP32 ADC telemetry as `MPD1..4`. This is useful for
source-power telemetry, slow firmware optical-power correction, and production APC,
but it is not a replacement for the transmitted-light/sample photodiode path. See
[`LASER_MONITOR_PD_FEEDBACK.md`](LASER_MONITOR_PD_FEEDBACK.md) before changing diode
footprints, pin-code assumptions, or production driver selection.

The wavelength of each channel is set by the firing laser (the sheet names carry IR/RED/
GREEN/BLUE); the SFH2201 is broadband (300–1100 nm) so the same PD detects all four.

## BOM — verified LCSC numbers (2026-06-30)

`laser_controller_bom_jlcpcb.csv` is the JLCPCB SMT assembly CSV generated from
parts with populated LCSC fields. It intentionally excludes the hand-added
through-hole barrel jack and direct laser-can footprints; those are separate
procurement/assembly items listed below.

### SMT (JLCPCB assembled)

| Part | Value | LCSC | JLC tier | Notes |
|---|---|---|---|---|
| U1–U4 | OPA380AID (SOIC-8) | **C201677** | Extended | TIA op-amp; low stock + highest BOM cost — buy a buffer. |
| U5–U8 | TLV9001IDBVR (SOT-23-5) | **C398363** | Extended | laser-driver op-amp. |
| U10 | CP2102N-A02-GQFN28R (QFN-28 EP) | **C964632** | Extended | USB-UART bridge copied from the access-controller MCU sheet. |
| U11 | AP2112K-3.3 (SOT-23-5) | **C51118** | Basic | 3V3 LDO for bench USB/UART with RF disabled; sustained Wi-Fi/BLE needs a buck or measured duty-cycle proof. |
| U12 | INA4180A1IPWR (TSSOP-14) | **C2057528** | — | quad high-side monitor-PD current-sense amplifier, gain 20. |
| U13 | LM4040C50IDBZR (SOT-23-3) | **C69316** | — | 5.0 V shunt reference for `MPD_BIAS`; DBZ pin 3 tied to anode. |
| U14 | AD7606BSTZ-4RL (LQFP-64) | **C51512** | Extended | 4-channel simultaneous signal-PD ADC; `VOUT1..4` into V1/V2/V3/V4, serial readback to ESP32. |
| U9 | **ESP32-S3-WROOM-1** | **C2913199** | Extended | MCU — exact C-number used on the access-controller; native USB. |
| D1–D4 | **Osram SFH2201** photodiode | **C2900216** | Extended | on-board clear Si PIN PD, 300–1100 nm (`OptoDevice:Osram_SFH2201`). One per wavelength. |
| Q1–Q4 | AO3400A N-MOSFET (SOT-23) | **C20917** | Basic | laser low-side sink pass device. |
| D5–D6 | MDD SS14 (SMA/DO-214AC) | **C2480** | Basic | 5V OR-ing Schottky, 40V/1A. D5 = USB `VBUS_5V`, D6 = onboard `BUCK_5V`; 2026-07-04 signoff confirms C2480 identity and polarity. |
| D7-D14 | LESD5D5.0CT1G(UMW) / 1N5819HW VBUS support | **C5199850 / C82544** | — | copied MCU-sheet USB data/VBUS ESD and USB VBUS isolation. |
| U15 | AP63205WU-7 (TSOT-23-6) | **C2071056** | — | 24 V input to onboard 5 V buck; output `BUCK_5V` feeds D6. |
| U16 | AP63200WU-7 (TSOT-23-6) | **C2071868** | — | 24 V input to adjustable shared bench `LASER_V+` buck. |
| L1 | 4.7uH shielded inductor | **C408410** | — | AP63205 5 V buck inductor, copied from access-controller libraries. |
| L2 | 10uH shielded inductor | **C98364** | — | AP63200 laser buck inductor, copied from access-controller libraries. |
| RV1–RV4 | 10k SMD trimmer | **C81348** | Extended | VBIAS, Bourns **3224W-1-103E** (SMD, JLCPCB-mountable); pin 2 wiper orientation signed off on 2026-07-04. |
| RV5–RV8 | 2M SMD trimmer | **C116323** | Extended | TIA feedback trim, Bourns **3224W-1-205E**, pin 2 wiper tied to OPA380 output side; orientation signed off on 2026-07-04. |
| R (10k) | 10k 0603 1% | **C844918** | — | VBIAS / EN / BOOT pull-up resistors. |
| R (240Ω) | 240Ω 0603 1% | **C114613** | — | monitor-PD high-side sense resistors. |
| R (2.49k) | 2.49k 0603 1% | **C2099849** | — | LM4040/`MPD_BIAS` sink resistor. |
| R61/R62/C69 | 237k / 22.1k / 100pF feedback set | **C2998117 / C2929993 / C1546** | — | AP63200 feedback divider and feed-forward capacitor for about 9.38 V `LASER_V+`. |
| R (1k) | 1k 0603 1% | **C2907002** | — | gate / ISENSE-isolation / PD-bias / monitor-ADC isolation resistor. |
| R21/R26/R31/R36 | 1.3k / 750Ω / 3k / 4.7k 0603 1% | **C22767 / C23241 / C4211 / C23162** | Basic | Per-channel PWM command limiter pulldowns for IR / red / green / blue. |
| R (10Ω) | 10Ω 2512 2W 1% | **C5123624** | Basic | laser source-sense resistor. |
| C (10pF) | 10pF C0G 0603 | **C106245** | Extended | Cf / loop-comp. |
| C (1µF) | 1µF 0402 25V X5R | **C7472946** | — | PWM filter / PD-bias bypass / LDO input. |
| C61-C62 | 10µF 1206 50V X7R | **C89632** | Extended | high-voltage `VIN_24V` ceramic input capacitors for AP632 local bypass. |
| C70 | 22µF 100V SMD electrolytic | **C90264** | — | `VIN_24V` input bulk capacitor copied from access-controller PoE bulk input. |
| C (100nF) | 100nF 0402 16V X7R | **C83056** | — | decoupling and monitor-PD low-pass filters. |
| C (10µF) | 10µF 0805 25V X5R | **C318691** | — | bulk decoupling. |
| C64-C65/C67-C68 | 22µF 0805 25V X5R | **C45783** | Basic | AP63205/AP63200 buck output capacitor banks, 2x22µF per rail. |
| J1-J2 | USB Mini-B receptacle | **C5120592** | (JLC assy) | Würth `65100516121` metadata on the matching KiCad Würth land pattern. |

### Hand-add / not in SMT assembly

| Part | Value | Notes |
|---|---|---|
| LD1 | D7805I, `OptoDevice:LaserDiode_TO18-D5.6-3` | Direct IR laser can. |
| LD2 | D6505I, `OptoDevice:LaserDiode_TO18-D5.6-3` | Direct red laser can. |
| LD3 | PLT5 520EB_P, `OptoDevice:LaserDiode_TO56-3` | Direct green laser can. |
| LD4 | PLT5 450GB, `OptoDevice:LaserDiode_TO56-3` | Direct blue laser can; case pad is intentionally no-connect and `MPD_RAW4` stays spare/open. |
| J5 | 24 V DC barrel jack, `Open_Automation:BarrelJack_OD5.5_ID2.5` | Center-positive 24 V input, GANGYUAN `DC-470-2.1GP` / LCSC **C194407**, copied from the access-controller libraries. |
| J6 | 24 V RJ45 power input, `Connector_RJ:RJ45_Amphenol_RJHSE538X` | RJ45 pins 4/5 to `VIN_24V`, pins 7/8/9/11 to GND, pins 10/12 through 10k LED/contact resistors to `VIN_24V` and `+3V3`, Ckmtw `R-RJ45R08P-C000` / LCSC **C386757**, copied from the access-controller Ethernet sheet and libraries. |

## ⚠ Before PCB layout — required pin-accuracy pass

Connectivity is validated by KiCad **netlist export — 150 exported nets, zero unintended tied
bench signals**. The USB `ID` pin, LDO `NC` pin, OPA380 `NC` pins 1/5/8, and unused ESP32-S3
pads are deliberate no-connects; `check_laser_controller_netlist.py` now fails any single-node
exported net outside that explicit no-connect allowlist. It also asserts exact value/footprint/MPN/LCSC
identity for all 160 schematic components and package pin functions for the datasheet-sensitive
parts: OPA380, TLV9001, AP2112K, CP2102N, ESP32-S3-WROOM-1, INA4180, LM4040, AD7606, AO3400A,
SFH2201, SS14, and USB Mini-B. It also asserts exact `+5V`, `+3V3`, and `GND` rail membership so broad power
rails cannot hide a stray or missing power pin. The review file
`review/2026-06-25_datasheet_pin_matrix.md` summarizes the datasheet pin decisions and the
script guardrails that enforce them. `check_laser_controller_sources.py` also fails if any
exported net or component pin falls back to a generic "review required" intent in the full
net/pin inventory. `check_source_documents.py` separately checks required primary datasheet
URLs, the inherited access-controller ESP32-S3 source sheet, the local OPA380 datasheet copy,
and package-sensitive KiCad footprint files; secondary distributor/order sources remain
warnings rather than silent assumptions, and vendor-CDN probe failures such as ST remain
explicit manual release-time checks.
`check_usb_vbus_interface.py` separately asserts the copied USB/VBUS support
block: J1 USB-UART, J2 ESP32-S3 native USB, Mini-B pins 1-6, CP2102N QFN28
pins 4/5/8, ESP32-S3 module pins 13/14, discrete ESD clamps, 1N5819HW VBUS
isolation, D5 +5 V OR-ing, the CP2102N 22.1 k / 47.5 k VBUS divider, RST
pull-up, UART, EN/BOOT auto-reset, and USB ID no-connects. Its
`connector-source-match` policy passes only when the active metadata is
Würth `65100516121` / **C5120592** on the matching Würth land pattern.
`check_esp32_reset_boot_controls.py` separately asserts the copied reset/boot
support block: EN 10 k / 1 uF / RESET button, GPIO0 BOOT 10 k / 1 uF / PROG
button, GPIO1 FACT button, CP2102N QFN28 DTR/RTS into the Q5/Q6 auto-reset
transistor network, CP2102N RST/SUSPEND pulls, and IO13/IO14 pulls.
`check_schematic_hierarchy_labels.py` separately enforces the intended root/child-sheet
interface: 10 root sheets, typed sheet pins, the whitelisted root global labels,
matching typed child hierarchical labels, and zero child-sheet global labels.
`check_schematic_presentation.py` separately enforces reviewability of the generated sheets:
net labels must clear symbol bodies, visible reference/value text, and other labels, generated
wire segments must not pass through component bodies, and every generated wire endpoint must land
on a real connection object. It also checks that custom-symbol pin anchors/strokes touch the symbol
glyph, preventing visually disconnected parts. Generated symbol origins, wire endpoints, labels,
junctions, no-connect markers, sheet pins, and custom-symbol pin anchors must stay on the 50 mil
schematic grid.
The current PCB has explicit pad nets verified by `check_laser_controller_pcb.py` so
missing pad-net assignment on quoted/bare footprint pads is caught before routing. The same
PCB check verifies net-class membership for laser current, power rails, USB,
TIA-sensitive analog, monitor/ADC telemetry, laser control, and digital control nets,
plus the explicit four-layer stackup (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`) and
the ESP32 footprint antenna keepout. It also checks pad-to-pad placement distances
covering the USB connectors, discrete USB ESD clamps, AP2112 capacitors, ESP32
local 3V3 decoupling, EN capacitor, EN pull-up, BOOT pull-up, every TIA
photodiode/input/feedback/decoupling/bias cluster, every laser-driver
gate/sense/control/compensation cluster, and every monitor-PD
sense/reference/ADC-isolation cluster near the direct laser footprints.

The current board artifact is routed for the available custom checks: measured
evidence is 181 physical footprints, including two grounded board-only mounting
holes, 1611 routed copper segments, 236 vias, four board-level zones, and one
footprint-internal ESP32 antenna keepout. The old laser/MPD header footprint is
not present. The PCB checker verifies intentional unnetted pad instances so
OPA380 NC pads, AP2112 NC, USB ID, unused ESP32 pads, paste-only pads, and
mechanical pads are explicit rather than silent floating copper. It also verifies
copper uses named nets, positive widths, declared layers, net-class clearance,
duplicate via stacks, board-boundary compliance, unsupported dangling copper
endpoints/vias, non-power via policy, critical local-route connectivity, USB
D+/D- length/skew, and route-layer/route-width policy.
It also enforces a sensitive local-route length policy on 40 nets: raw laser
monitor-PD inputs (`MPD_RAWx`) must stay at or below 12 mm, OPA380 summing nodes
at or below 12 mm, photodiode cathode/bias stubs at or below 5 mm, local trim/
bias nodes at 9-18 mm by function, laser gate nodes at or below 3 mm, laser
op-amp output nodes at or below 7 mm, and laser sense-feedback loops at or
below 12.5 mm.
Current blocker: the custom PCB, generated-copper, focused layout-geometry, and
return-path signoff gates pass, but the board is not fabrication-released until
KiCad ERC with schematic parity evidence, native KiCad DRC/parity,
procurement/source checks, and bring-up measurement blockers are closed. A
2026-07-04 GUI DRC screenshot is
captured in `review/signoff/2026-07-04-kicad-drc-zero-violations.md` and shows
0 violations / 0 unconnected items with zone refill enabled, but schematic
parity was not run in that DRC dialog. The checker also enforces same-layer spacing
from laser-current copper to `TIA_Sensitive`, `MPD_RAWx`, and filtered
`Monitor_ADC` copper.
`check_power_thermal_budget.py` separately enforces the AP2112 `+3V3` bench/no-RF thermal
policy; it intentionally fails sustained Wi-Fi/BLE load cases on the current SOT-25 LDO.
`check_ap6320x_package_pcb.py` separately enforces the AP63205/AP63200 package
pin nets against the current PCB pads: U15/U16 `FB/EN/IN/GND/SW/BST`, L1/L2,
bootstrap caps, output caps, and U16 feedback parts. It also checks the installed
KiCad TSOT-23-6 footprint geometry and local Open_Automation L1/L2 footprints.
`check_buck_input_power_budget.py` separately enforces the AP63205/AP63200 pinout,
feedback, input-current, and inductor-stress policy. The selected-diode 9.3 V
max-current reference and all-channel per-channel analog-limit case pass the
500 mA J5 bench input rating. The same checker also keeps the AP632 production
component guard visible: C64+C65/C67+C68 now provide 44 uF per buck output with
2x22 uF 25 V ceramics, and C61+C62 are 20 uF nominal VIN ceramic input
capacitance.
`check_laser_current_budget.py` separately checks the laser command clamp, selected
LD1-LD4 current limits, sense resistor power, AO3400A heat, and safe `LASER_V+`
window for the selected diode forward voltage. The selected-diode policies show
that the present 9.3 V common-rail reference passes the selected typical-current,
max-current, and per-channel analog-limit cases. The generic high-rail
expected-fail policies remain to show why `LASER_V+` and commanded current need
per-diode review.
`check_passive_derating.py` verifies all assembled passive MPNs against explicit bench
voltage/power ratings; current worst cases are `R57` at 40.0% resistor power,
the `100nF MPD bias` capacitor at 31.6% of rating, and `R61` at 13.3% resistor voltage.
The `VIN_24V` input capacitors are at 24.0% of their 100 V rating under nominal
24 V steady-state input.
The generated inventory separately reports routed copper width/via geometry by
net class and whole-board explicit route connectivity. In the current recovered
placement PCB those route sections are empty: signal/control multi-pad nets are
not explicitly routed, `+3V3`/`+5V`/`VIN_24V`/`BUCK_5V`/`GND`/`LASER_V+`/`VBUS_5V` still need
pours or trunks, and the laser sense returns have no high-current GND vias.
Netlist export is *not* full
ERC; `PWR_FLAG`s declare externally-supplied rails, but GUI ERC still must be run and reviewed
before release. Items to
datasheet-check before routing:

1. **ESP32-S3-WROOM-1 symbol pinout.** The schematic uses the real Espressif symbol and
   `RF_Module:ESP32-S3-WROOM-1` footprint. Netlist audit confirms USB D− on GPIO19/module
   pin 13, USB D+ on GPIO20/module pin 14, GPIO0/BOOT pulled up with local PROG button, and all
   unused pads marked no-connect. Still mind strapping pins (GPIO0/3/45/46) and the antenna
   keep-out during layout.
2. **SFH2201 polarity.** `OptoDevice:Osram_SFH2201` pad 1 = cathode, pad 2 = anode (matches
   the KiCad `D_Photo` symbol convention used here). Confirm the orientation mark in bring-up.
3. **USB Mini-B land.** J1/J2 use Würth `65100516121` / **C5120592** metadata
   on the KiCad Würth 65100516121 footprint; check connector pin-1, shield pad
   6 to GND, board-edge orientation, and final JLCPCB quote acceptance.

### Design review — folded into the generator

- **LDO brownout/thermal** — AP2112K-3.3 avoids the AMS1117 dropout problem, but it is accepted
  only for the bench USB/UART no-RF policy. The SOT-25 thermal budget fails sustained
  Wi-Fi/BLE current and production wireless should use a buck regulator or larger proven supply.
- **PD reverse bias** — SFH2201 cathode → +5V via RB(1k) + CB bypass; anode → OPA380 −IN;
  `V_OUT = VBIAS + I_pd·Rf` (positive-going).
- **ERC power sources** — `PWR_FLAG`s on +5V, +3V3-source, LASER_V+, VBUS_5V.
- **Decoupling** — 100 nF at every OPA380 and TLV9001 V+.
- **VBIAS range** — series 10 k bounds the trim to ≤2.5 V, inside the OPA380 input CM.
- **Laser loop** — TLV9001 drives AO3400A gate through 1 k; 10 pF compensation cap + 1 k
  resistor isolate the ISENSE tap from the current-sense feedback node. The 30 k pulldown on
  the filtered command node limits nominal full-scale current to about 248 mA. The shared
  `LASER_V+` rail must be chosen from the actual diode forward-voltage table; too much rail
  headroom is dissipated in the AO3400A.
- **Monitor PD path** — `MPD_RAWx` feeds a 240 ohm high-side sense resistor into
  `MPD_BIAS`; INA4180A1 gain 20 drives a 1 k / 100 nF ADC-side filter into `MPDx`.
  LM4040C50 holds `LASER_V+ - MPD_BIAS` near 5 V. At `LASER_V+ = 10.5 V`, typical
  PLT5 520EB_P monitor current around 150 uA maps to about 0.72 V at the ESP32 ADC and
  about 4.96 V monitor-PD reverse bias. This front end is pin-topology compatible with
  selected `D7805I`, `D6505I`, and `PLT5 520EB_P`, and the selected high-end monitor
  currents now fit the local ADC-headroom guard: D7805I max maps to about 2.88 V and
  D6505I max maps to about 1.44 V. Selected blue diode `PLT5 450GB` has no monitor
  photodiode, so `MPD_RAW4` / `MPD4` is spare/open for that source.
- **USB programming/control** — J1 is CP2102N USB-UART; J2 is ESP32-S3 native USB on
  GPIO19/GPIO20. Both connectors use copied-sheet discrete ESD clamps and VBUS
  isolation. `check_usb_vbus_interface.py` enforces the schematic topology,
  while the PCB checker enforces USB route length/skew/layer/width policy.
- **ESP32 EN/BOOT** — EN has 10 k pull-up + 1 uF POR/reset-delay cap + reset
  button; GPIO0/BOOT has 10 k pull-up + 1 uF cap + local PROG button.

**Still verify (firmware side):** U14 straps `RANGE` low for the base AD7606 **±5 V**
input range, `REF_SELECT` high for the internal reference, and `OS0..2` low for no
oversampling. Confirm ESP32 timing, serial readback mode, and scale conversion before
trusting bench readings; keep per-laser current ≲ 250 mA so `I·10Ω` stays inside the
ESP32 ADC window.

The generator emits globally unique schematic references before KiCad netlist export. Do not
reintroduce repeated sheet-local designators; `circuit_designators.py` is the translation layer
between readable logical route names and physical component references.

## Layout notes

- The 4 **SFH2201 PDs sit on the optical (left) board edge** so each laser beam reaches its
  detector; keep the OPA380 −IN summing node tiny and guarded, directly behind the PD.
- Star ground: keep laser-driver switching return and ESP32 digital ground off the analog TIA
  return; separate trace for the laser-driver returns back to the common entry.
- Keep Q1–Q4 drain traces (`LASER_Nx`) short and direct to `LD1..LD4`, away from TIA inputs.
- Keep `MPD_RAW1..4` and `MPD_BIAS` away from laser cathode switching/current traces;
  place the 240 ohm sense resistors, INA4180, LM4040, bias sink, and ADC filters close
  near the direct laser monitor inputs or quiet ADC entry path.
- If firmware needs AD7606 oversampling, change the U14 `OS0..2` straps intentionally;
  the current schematic ties them low for no oversampling.
- ISENSE headroom: I_laser·10Ω must stay inside the ESP32 ADC range (≈0–3.1 V with 11 dB
  atten) — keep per-channel current ≲ 250 mA, or drop R_sense on a high-current channel.
- **ESP32-S3 antenna keep-out**: no copper pour / parts in the module antenna zone (toward the
  board edge).

## Review gate

Run the available local gate after any generated schematic, PCB, checker, or
source-note change:

```bash
python3 circuits/run_laser_controller_review.py
```

For first-article or production release, use release mode:

```bash
python3 circuits/run_laser_controller_review.py --release
```

In this environment, release mode is expected to fail while
`check_laser_controller_release_readiness.py` still reports deferred
first-article/production blockers. That failure is intentional: the current
JLCPCB order package can be ready while bench-use or production release remains
blocked by missing measured calibration, firmware, thermal, protection,
procurement, or bring-up evidence. Do not clear the blocker registry until the
corresponding physical/source signoffs are recorded.

See `PCB_LAYOUT.md` for the full placement + routing/Gerber workflow.
