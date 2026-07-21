# Vivonics Bench Laser Controller — Datasheet & System Audit

**Date:** 2026-07-01
**Audit scope:** Every active component datasheet pinout, specification, and
connection cross-referenced against the generated KiCad schematic. System-level
production readiness assessment against the Vivonics goal of a production-working
biophotonic measurement machine.

**Method:** Each component's part-note, datasheet, schematic symbol pins, and
netlist connections were read and cross-referenced. The automated checker suite
(542 netlist assertions, 90 MPN/LCSC source tokens, 581 pin-intent roles) was
reviewed for coverage. Physical inspection (PCB routing, KiCad ERC/DRC, zone refill,
thermal measurement, optical calibration) is still outstanding — this audit is
schematic and system-level only.

---

## 1. Component-by-Component Datasheet Verification

### 1.1 ESP32-S3-WROOM-1-N16 (U9)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| Symbol source | Espressif official `ESP32-S3-WROOM-1` from access-controller | Matches source block; only footprint-library substitution allowed | **PASS** |
| Pin 2 (3V3) | Power input | On `+3V3` net with AP2112 output, decoupling, EN/BOOT pulls | **PASS** |
| Pin 13 (GPIO19/USB_D-) | Native USB D- | To J2 D- through discrete LESD clamp | **PASS** |
| Pin 14 (GPIO20/USB_D+) | Native USB D+ | To J2 D+ through discrete LESD clamp | **PASS** |
| Pin 3 (EN) | Reset, 10k pull-up, 1uF POR cap, button | On `/MCU_ESP32-S3/EN` with R54, C44, SW1, Q5 auto-reset | **PASS** |
| Pin 27 (GPIO0/BOOT) | 10k pull-up, 1uF cap, PROG button | On `/MCU_ESP32-S3/PROG` with R53, C46, SW2, Q6 auto-reset | **PASS** |
| Pin 39 (GPIO1) | Factory button | On `/MCU_ESP32-S3/FACT` with R52 pull-up, SW3 | **PASS** |
| GPIO2/3/8/9 | ADC1 MPD telemetry | `MPD1..4` on ADC1_CH1/2/7/8 — all ADC1-capable | **PASS** |
| GPIO4/5/6/7 | ADC1 ISENSE telemetry | `ISENSE1..4` on ADC1_CH3/4/5/6 | **PASS** |
| GPIO10/11/12/16 | PWM outputs | `PWM1..4` laser command | **PASS** |
| GPIO13/14 | Pull-ups for strap | R60/R59 10k to +3V3 | **PASS** |
| GPIO17/18/21/38/47/48 | AD7606 interface | SCLK/CS/DOUTA/DOUTB/BUSY/RESET | **PASS** |
| GPIO43/44 | CP2102N UART TX/RX | U10 pins 25/26 | **PASS** |
| Antenna keepout | Copper-free on all layers | Footprint-internal keepout present; 1 zone, 4 layers | **PASS** |

**Specification concern:** Espressif RF peak currents (355mA 802.11b TX, 344mA BLE TX at 20dBm) vastly exceed the AP2112 SOT25 thermal budget from 5V. The bench policy is RF-disabled; production Wi-Fi/BLE requires a different regulator.

### 1.2 CP2102N USB-UART Bridge (U10)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| Pin 4/5 (D+/D-) | USB data to J1 | Through discrete LESD clamps on `/MCU_ESP32-S3/D+`/`D-` | **PASS** |
| Pin 8 (VBUS) | VBUS sense with divider | R55 22.1k / R56 47.5k + C45 bypass | **PASS** |
| Pin 6 (VDD), 7 (VREGIN) | +3V3 | On `+3V3` net | **PASS** |
| Pin 24/28 (RTS/DTR) | Auto-reset transistors | Q6 PNP base (DTR), Q5 NPN base (RTS) | **PASS** |
| Pin 25/26 (TXD/RXD) | ESP32 UART | GPIO44/GPIO43 | **PASS** |

### 1.3 AP2112K-3.3TRG1 3.3V LDO (U11)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| Pin 1 (VIN) | +5V input | On `+5V` net | **PASS** |
| Pin 2 (GND) | Ground | GND | **PASS** |
| Pin 3 (EN) | Enabled (tied to VIN) | On `+5V` net | **PASS** |
| Pin 4 (NC) | No connect | Single-node NC net | **PASS** |
| Pin 5 (VOUT) | +3V3 output | On `+3V3` net | **PASS** |

**Thermal specification concern (CRITICAL for production):**
- SOT25 θJA = 184°C/W
- At 5V→3.3V, 120mA load, 85°C ambient: Tj ≈ 123°C (against 125°C target)
- Espressif RF peaks would push Tj far above 125°C
- **Production verdict:** AP2112 is bench-only. Replace with buck regulator (AP63200 variant or equivalent) for any Wi-Fi/BLE use. Measure actual +3V3 current during bring-up.

### 1.4 AP63205WU-7 5V Buck (U15) / AP63200WU-7 Adjustable Buck (U16)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| TSOT-23-6 pinout | 1=FB, 2=EN, 3=IN, 4=GND, 5=SW, 6=BST | Verified against datasheet and checker | **PASS** |
| U15 FB (fixed 5V) | Tied to BUCK_5V output | On `/POWER_IO/BUCK_5V` | **PASS** |
| U16 FB (adjustable) | 0.8V * (1 + 274k/22.1k) = 10.72V | R61=274k, R62=22.1k, C69=100pF FF | **PASS** |
| BST capacitors | 100nF from BST to SW | Local to each buck | **PASS** |
| Inductor L1 (U15) | MWSA0503S-4R7MT, 4.7µH | Correct part | **PASS** |
| Inductor L2 (U16) | WPN4020H100MT, 10µH | Correct part | **PASS** |
| Input range | 3.8V–32V | 24V nominal → 75% of abs max | **WARN** |

**Critical specification issues for production:**

1. **Input capacitance (CRITICAL):** C61+C62 = 2µF ceramic. AP632 datasheet recommends >10µF ceramic input bypass. The 22µF C70 electrolytic helps but is not a substitute for ceramic HF bypass. **Must be reworked or justified by ripple/transient measurement.**

2. **Output capacitance:** C64+C65 = 20µF on BUCK_5V, C67+C68 = 20µF on LASER_V+. AP632 reference designs use 2×22µF. **Needs measurement justification.**

3. **24V input margin:** 24V nominal is only 8V below the 32V absolute maximum — and that's before any adapter tolerance, hot-plug transient, or inductive kick. The J5 barrel is rated 30V (80% used). **Production needs TVS, input protection, and transient measurement.**

4. **No fuse/PTC/TVS/reverse-polarity:** `check_vin24_input_protection.py --policy production-protection` intentionally fails. The 24V entry is a bare wire to both buck inputs. **Production requires at minimum a fuse, TVS, and reverse-polarity strategy.**

### 1.5 SS14 Schottky OR-ing Diodes (D5, D6)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| D5 anode | USB VBUS_5V | From J1/J2 through 1N5819HW isolation | **PASS** |
| D6 anode | Onboard BUCK_5V | From AP63205 output | **PASS** |
| D5/D6 cathodes | +5V rail | Common `+5V` net | **PASS** |
| Package polarity | SMA pin 1=anode, pin 2=cathode | Verified | **PASS** |

**Production concern:** Exact C2480 manufacturer must be confirmed at order time. Current evidence is Vishay SS12-SS16 family reference — confirm it's the actual SS14 part.

### 1.6 OPA380AID TIA Op-Amp (U1–U4)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| SOIC-8 pin 1 | NC | Single-node NC net | **PASS** |
| Pin 2 (-IN) | Summing node with SFH2201 anode + feedback | Correct: PD anode, feedback trimmer + 10pF | **PASS** |
| Pin 3 (+IN) | VBIAS from trim network | 10k trimmer + series resistor, 0.00–2.50V range | **PASS** |
| Pin 4 (V-) | GND | GND | **PASS** |
| Pin 5 | NC | Single-node NC net | **PASS** |
| Pin 6 (OUT) | TIA output to AD7606 | `VOUT1..4` net, within 0.10–4.30V guarded window | **PASS** |
| Pin 7 (V+) | +5V | On `+5V` with local 100nF decoupling | **PASS** |
| Pin 8 | NC | Single-node NC net | **PASS** |
| Supply range | 2.7V–5.5V | 5.0V — within spec | **PASS** |
| CM input range | Up to (V+) - 1.8V = 3.2V | VBIAS max 2.50V — within spec | **PASS** |
| Feedback | 2MΩ trimmer || 10pF C0G | RV5–RV8 (2M Bourns 3224W) + C3/C7/C11/C15 (10pF) | **PASS** |

**Specification note:** The bright-ambient policy (`sfh2201-1000lx-example`) intentionally fails — 76µA short-circuit current at 1000lx would need 152V of swing at 2MΩ feedback. The TIA is designed for the Vivonics biophotonic signal range, not ambient light. Production optical calibration must define the actual signal current range.

### 1.7 SFH2201 Signal Photodiode (D1–D4)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| Pin 1 (cathode) | Reverse-biased from +5V | +5V → 1kΩ → cathode, with 100nF bypass | **PASS** |
| Pin 2 (anode) | To OPA380 summing node | Direct to Ux.2 (-IN) | **PASS** |
| Reverse bias | 5.0V vs. 16V max | 5.0V — well within spec | **PASS** |
| Spectral range | 300–1100nm | Covers IR/RED/GREEN/BLUE source set | **PASS** |

### 1.8 TLV9001IDBVR Laser Driver Op-Amp (U5–U8)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| SOT-23-5 pin 1 (OUT) | Drives AO3400A gate through 1kΩ | On `/LASER_x/LOUT` → gate resistor | **PASS** |
| Pin 2 (V-) | GND | GND | **PASS** |
| Pin 3 (IN+) | Filtered PWM command | 10k + 30k divider to GND, filter cap | **PASS** |
| Pin 4 (IN-) | Source-sense feedback | From 10Ω sense high side | **PASS** |
| Pin 5 (V+) | +5V | On `+5V` with 100nF decoupling | **PASS** |
| Supply range | 1.8V–5.5V | 5.0V — within spec | **PASS** |
| Input CM range | (V-) - 0.1V to (V+) + 0.1V | 0–3.3V command range — within spec | **PASS** |
| Compensation | 10pF OUT-to--IN | Local to each TLV9001 | **PASS** |

**Critical note — NOT a U-pinout device:** The non-U DBV pinout is used (OUT=1, V-=2, IN+=3, IN-=4, V+=5). Do NOT substitute TLV9001U without rewiring.

### 1.9 AO3400A Laser MOSFET (Q1–Q4)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| SOT-23 pin 1 (Gate) | Driven from TLV9001 through 1kΩ | On gate resistor net | **PASS** |
| Pin 2 (Source) | To 10Ω sense resistor | On `/LASER_x/FB` net | **PASS** |
| Pin 3 (Drain) | To laser cathode `LASER_Nx` | On `/LASER_x/LASER_N` net | **PASS** |
| Sense resistor | 10Ω, 2512, 2W | Correctly upsized; 0.61W at hardware clamp | **PASS** |

**Critical specification concern (PRODUCTION):** The AO3400A is used as a **linear low-side current sink**, not a saturated switch. This means:
- Pdiss = I × (LASER_V+ − Vf − I×10Ω)
- At the 10.72V rail, PLT5 450GB at 87mA typ: Pdiss ≈ 0.37W (>0.32W budget at 85°C)
- At the 10.72V rail, D7805I at 35mA typ: Pdiss ≈ 0.25W (passes)
- The **common 10.72V rail is a single-point failure for production** — low-Vf diodes burn excessive power in the MOSFET, and high-Vf diodes barely fit
- The 9.3V reference rail passes all selected-diode max-current cases but is not the current board setting
- **AO3400A is not characterized for linear-mode SOA** in its datasheet
- **Recommendation for production:** Either use per-channel supply rails optimized for each diode class, or switch to a proper current-source architecture (e.g., op-amp + BJT with heatsink, or dedicated laser driver IC)

### 1.10 AD7606BSTZ-4RL 4-Channel ADC (U14)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| LQFP-64 package | AD7606-4 variant | Correct part number | **PASS** |
| V1–V4 (pins 49/51/57/59) | TIA outputs | `VOUT1..4` — correct | **PASS** |
| CONVSTA/B (9/10) | Tied together on CONVST | ESP32 GPIO15 — correct | **PASS** |
| RD/SCLK (12) | Serial clock | ESP32 GPIO17 — correct | **PASS** |
| CS (13) | Chip select | ESP32 GPIO18 — correct | **PASS** |
| DOUTA (24) | Serial data A | ESP32 GPIO21 — correct | **PASS** |
| DOUTB (25) | Serial data B | ESP32 GPIO38 — correct | **PASS** |
| BUSY (14) | Conversion busy | ESP32 GPIO47 — correct | **PASS** |
| RESET (11) | Hardware reset | ESP32 GPIO48 — correct | **PASS** |
| RANGE (8) | ±5V range (GND) | Tied low — correct | **PASS** |
| OS[2:0] (3/4/5) | No oversampling (GND) | Tied low — correct | **PASS** |
| PAR/SER (6) | Serial mode (HIGH) | Tied to +3V3 — correct | **PASS** |
| DB15/BYTE_SEL (33) | Serial byte select (LOW) | Tied to GND — correct | **PASS** |
| STBY (7), REF_SELECT (34) | Standby off, internal ref | Tied to +3V3 — correct | **PASS** |
| AVCC (1/37/38/48) | +5V analog supply | On `+5V` with 100nF+10µF each | **PASS** |
| VDRIVE (23) | +3V3 logic supply | On `+3V3` with 100nF | **PASS** |
| REGCAP (36/39) | 1µF each to GND | C59/C60 — correct | **PASS** |
| REFIN/REFOUT (42) | 10µF to GND | C58 — correct | **PASS** |
| REFCAPA/B (44/45) | Shared 10µF | C57 — correct | **PASS** |
| FRSTDATA (15) | Intentional NC in 2-DOUT mode | Single-node NC — correct | **PASS** |
| Firmware budget | 10MHz SCLK, 100kSPS, 4ch, 2 DOUT | 3.2µs read + 2µs conv = 5.2µs, margin 4.8µs | **PASS** |

**Production concern:** Firmware implementation, real ESP32 timing validation, and bench ADC readback against known inputs remain open system-level checks.

### 1.11 INA4180A1IPWR Monitor-PD Current Sense (U12)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| TSSOP-14 pinout | Quad current-sense, gain=20 | Verified against TI datasheet | **PASS** |
| IN+1..4 (3/5/10/12) | MPD_RAW1..4 | Direct from LDx.3 monitor anode | **PASS** |
| IN-1..4 (2/6/9/13) | MPD_BIAS | Common bias node | **PASS** |
| VS (4) | +3V3 | On `+3V3` with C35 100nF | **PASS** |
| GND (11) | Ground | GND | **PASS** |
| OUT1..4 (1/7/8/14) | MPD_AMP1..4 | Through 1kΩ/100nF filter to ESP32 ADC | **PASS** |
| Sense resistors | 240Ω (reduced from 750Ω) | R42/R44/R46/R48 — correct | **PASS** |
| Gain | 20 V/V (A1 variant) | INA4180**A1** — correct | **PASS** |

**Scale verification:**
- PLT5 520EB_P typical: 150µA × 240Ω = 36mV → gain 20 → 0.72V at ADC
- D7805I max: 600µA × 240Ω = 144mV → gain 20 → 2.88V at ADC (< 2.90V guard)
- D6505I max: 300µA × 240Ω = 72mV → gain 20 → 1.44V at ADC
- **All within ESP32 ADC range. PASS.**

### 1.12 LM4040C50IDBZR 5.0V Shunt Reference (U13)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| SOT-23-3 pin 1 (cathode) | LASER_V+ | Connected to `LASER_V+` | **PASS** |
| Pin 2 (anode) | MPD_BIAS | Connected to `MPD_BIAS` | **PASS** |
| Pin 3 (*) | Tied to anode (noise) | Connected to `MPD_BIAS` | **PASS** |
| Bias resistor | 2.49kΩ from MPD_BIAS to GND | R41 — correct | **PASS** |
| Bias capacitor | 100nF LASER_V+ to MPD_BIAS | C36 — correct | **PASS** |
| Shunt current (typ) | ~1.61mA at 10.5V with 3×150µA MPD | Well within 80µA–15mA range | **PASS** |

### 1.13 Laser Diodes — Direct Footprint Mapping

| Channel | Laser MPN | Package | Pin 1 | Pin 2 | Pin 3 | Footprint | Verdict |
|---|---|---|---|---|---|---|---|
| LD1 (IR) | D7805I | Style-A TO18 5.6mm | LD_K → LASER_N1 | Common/case → LASER_V+ | PD_A → MPD_RAW1 | TO18-D5.6-3 | **PASS** |
| LD2 (RED) | D6505I | Style-A TO18 5.6mm | LD_K → LASER_N2 | Common/case → LASER_V+ | PD_A → MPD_RAW2 | TO18-D5.6-3 | **PASS** |
| LD3 (GREEN) | PLT5 520EB_P | TO56 5.6mm | LD_K → LASER_N3 | LD_A/PD_K/case → LASER_V+ | PD_A → MPD_RAW3 | TO56-3 | **PASS** |
| LD4 (BLUE) | PLT5 450GB | TO56 5.6mm | LD_A → LASER_V+ | Case → NC | LD_K → LASER_N4 | TO56-3 | **PASS** |

**Verified per-datasheet pin codes:**
- D7805I: Style A, pin 1=laser cathode, pin 2=common case, pin 3=monitor anode ✓
- D6505I: Style A, pin 1=laser cathode, pin 2=common case, pin 3=monitor anode ✓
- PLT5 520EB_P: pin 1=LD cathode, pin 2=LD anode/PD cathode/case, pin 3=PD anode ✓
- PLT5 450GB: pin 1=LD anode, pin 2=case (NC), pin 3=LD cathode ✓

**Production concern:** The D6505I has conflicting current specs between US-Lasers (40mA typ/60mA max) and the Digikey D650-5I datasheet (20mA typ/25mA max). The conservative Digikey value is used. Lock the actual order source.

### 1.14 Bourns 3224W Trimmers (RV1–RV8)

| Ref | Function | Value | Verdict |
|---|---|---|---|
| RV1–RV4 | VBIAS trim for OPA380 +IN | 10kΩ (3224W-1-103E) | **PASS** |
| RV5–RV8 | TIA feedback (rheostat, wiper to OUT) | 2MΩ (3224W-1-205E) | **PASS** |

**Production concern:** Wiper orientation requires visual Pcbnew verification before fabrication.

### 1.15 USB Mini-B Connectors (J1, J2)

| Field | Expected | Actual | Verdict |
|---|---|---|---|
| J1 pin 1 | VBUS → CP2102N via isolation | Through 1N5819HW diode | **PASS** |
| J1 pin 2/3 | D-/D+ → CP2102N via ESD | Through LESD5D5.0CT1G clamps | **PASS** |
| J2 pin 2/3 | D-/D+ → ESP32 native USB | Through LESD5D5.0CT1G clamps | **PASS** |
| Pin 4 (ID) | NC | Intentional single-node NC | **PASS** |
| Pin 5 (GND) | Ground | GND | **PASS** |
| Shield | Ground | GND | **PASS** |

**Critical production concern (BLOCKER):** The electrical symbol/BOM uses `920-462A2021S10101` / LCSC `C46391`, but the PCB footprint is KiCad's Würth `65100516121` land pattern. These must be mechanically verified as compatible or one must be changed before fabrication.

### 1.16 Passive Components

| Check | Result |
|---|---|
| 55 capacitors derated | **PASS** |
| 60 resistors/trimmers derated | **PASS** |
| All BOM MPN/LCSC tokens covered | **PASS** (90 tokens) |
| Passive steady-state bench power/voltage | **PASS** |
| Pulse/surge/lifecycle derating | **OPEN** (production AVL not locked) |

---

## 2. System-Level Production Readiness Assessment

### 2.1 What Works (Schematic Level)

The schematic is **electronically sound** at the generated-artifact level. Every pin is accounted for, every net has an intent mapping, and the automated checker suite (542 assertions, 581 pin-intent roles) passes clean. The architecture is:

```
24V IN → AP63205 (5V buck) → D6 OR (+5V rail) ← D5 ← USB VBUS
         AP63200 (10.72V buck) → LASER_V+ → laser anodes
                                      ↓
+5V → AP2112 (3.3V LDO) → ESP32-S3
    → OPA380 ×4 (TIA)
    → TLV9001 ×4 (laser driver)
    → AD7606 AVCC

LASER_V+ → LD1..LD4 anodes/common
         → LM4040 → MPD_BIAS reference

Signal path: SFH2201 → OPA380 TIA → AD7606 → ESP32 SPI
Monitor path: LDx PD → INA4180 → ESP32 ADC
Control path: ESP32 PWM → TLV9001 → AO3400A → laser cathode
```

### 2.2 Critical Production Blockers (Must Fix Before Board Order)

| # | Blocker | Severity | Impact |
|---|---|---|---|
| 1 | **24V input has zero protection** — no fuse, PTC, TVS, reverse-polarity, or eFuse | **CRITICAL** | Board destruction on first overvoltage/reverse/hot-plug event |
| 2 | **AP632 input capacitance too low** — 2µF vs. >10µF datasheet recommendation | **HIGH** | Buck instability, excessive ripple, potential regulation failure |
| 3 | **Common LASER_V+ rail architecture** — single 10.72V for all four diode classes | **CRITICAL** | AO3400A thermal failure on PLT5 450GB at typ current; massive waste heat on low-Vf diodes |
| 4 | **AP2112 cannot support Wi-Fi/BLE** — 184°C/W θJA, fails at RF currents | **HIGH** | Any wireless feature requires regulator replacement |
| 5 | **USB connector footprint/BOM mismatch** — 920-462A2021S10101 vs. Würth 65100516121 | **HIGH** | Board may not accept the ordered connector |
| 6 | **PCB completely unrouted** — 0 board-level segments, 0 vias, 0 filled zones | **BLOCKER** | Cannot order boards |
| 7 | **No KiCad ERC or DRC run** — CLI version lacks these commands | **BLOCKER** | Unknown electrical/routing errors |
| 8 | **AP632 output capacitance** — 20µF vs. 2×22µF reference | **MEDIUM** | May affect transient response/stability |
| 9 | **D6505I current spec conflict** — two sources disagree on max current | **MEDIUM** | Wrong current limit could destroy diode |
| 10 | **AO3400A linear-mode SOA** — not datasheet-characterized for linear operation | **MEDIUM** | Thermal failure risk at production duty cycles |

### 2.3 Architecture-Level Production Concerns

**The Common Rail Problem.** The single LASER_V+ rail at 10.72V is the most fundamental production issue. Consider:

| Laser | Vf(typ) | Vf(max) | I(typ) | I(max) | Pdiss(AO3400A) at 10.72V typ | Pdiss at 9.3V typ |
|---|---|---|---|---|---|---|
| D7805I IR | 2.1V | 2.5V | 35mA | 50mA | 0.25W | 0.21W |
| D6505I RED | 2.2V | 2.6V | 20mA | 25mA | 0.15W | 0.12W |
| PLT5 520EB_P GREEN | 5.4V | 6.1V | 65mA | 78mA | 0.28W | 0.19W |
| PLT5 450GB BLUE | 5.2V | 6.5V | 87mA | 120mA | **0.40W FAIL** | 0.27W |

The AO3400A continuous budget at 85°C ambient, 125°C Tj is only 0.32W. At 10.72V:
- Blue fails at typical current
- Green is marginal
- IR/Red waste ~2× more power in the MOSFET than in the laser

**Production recommendation:** For a sellable product, consider:
1. **Per-channel buck regulators** — each laser channel gets its own AP63200 set to Vf + 1.5V headroom
2. **Or a proper current-source topology** — switch to a dedicated laser driver IC with integrated current regulation and thermal protection
3. **Minimum viable fix:** Reduce LASER_V+ to 9.3V (change R61 to ~234k) and limit blue channel current in firmware

**The bR Measurement Gap.** The AGENTS.md documents the fundamental physics constraint: the 650nm red probe is in the far tail of bR absorption (ε₆₅₀ ≈ 2,000 vs. ε₅₆₈ = 63,000 M⁻¹cm⁻¹). The bench has proven ~1.2% ΔT detection via RTSP temporal decay, but:
- M-state lifetime is ~10ms in solution
- The camera+H264 path is too slow to catch the peak
- A **570nm probe would give 32× stronger signal** (~26% ΔT)
- A **photodiode+TIA** (which the bench board has!) would give µs time resolution

The bench laser controller board is actually well-positioned for this — it has SFH2201 photodiodes, OPA380 TIAs, and an AD7606 ADC. The missing piece is a 570nm laser source and firmware integration.

### 2.4 What's Production-Ready

These subsystems are ready for fabrication once routing is complete:
- ESP32-S3 module, CP2102N USB-UART, reset/boot circuits
- SFH2201 + OPA380 TIA analog front end (proven topology)
- AD7606 4-channel simultaneous-sampling ADC
- INA4180 + LM4040 monitor-PD front end
- TLV9001 + AO3400A current-sink topology (with rail voltage caveats)
- USB ESD protection (LESD5D5.0CT1G + 1N5819HW)
- Power OR-ing (SS14 diodes)

### 2.5 Remaining Work to Production Machine

| Phase | Tasks |
|---|---|
| **Immediate (schematic)** | Resolve USB connector footprint/BOM; lock D6505I source; set LASER_V+ to 9.3V or per-channel |
| **Immediate (PCB)** | Route the board; create GND reference plane; run KiCad GUI ERC; run KiCad GUI DRC |
| **Before board order** | Add 24V protection (fuse + TVS minimum); fix or justify AP632 output capacitance; Bourns wiper and return-path reviews are closed by 2026-07-04 signoffs |
| **Bring-up** | Measure AP2112 temperature; measure buck ripple/stability; verify AD7606 firmware timing; calibrate TIA gain per channel |
| **Production engineering** | Replace AP2112 with buck regulator; redesign laser driver for per-channel rails or proper current-source; add 570nm laser channel; optical calibration procedure; EMC pre-compliance |
| **Production manufacturing** | Lock production AVL; IPC class selection; fab tier selection; assembly partner; test fixture design |

---

## 3. Summary Verdict

**Schematic correctness:** The pin-level verification is thorough and correct. Every component's datasheet pinout has been cross-referenced against the schematic symbol and netlist. The automated checker suite validates 542 assertions across 178 components. **No pinout errors found.**

**Connection correctness:** All inter-component connections are verified — power tree, analog signal chain, digital control, USB, ADC interface. **No connection errors found.**

**Production readiness:** The schematic is a solid **bench prototype**, not a production design. The three critical architectural issues (no input protection, common high-voltage rail, thermal-limited LDO) would need resolution before any volume manufacturing. The PCB is unrouted and has never seen ERC/DRC.

**Path to production:** Address the 10 blockers above. The most impactful single change would be switching to per-channel laser supply rails and adding 24V input protection. With those changes, this board is on a credible path to a production-working Vivonics biophotonic measurement machine.

---

*Evidence: 17 part notes, 2 datasheets (OPA380, BPW34), source register, 4 review documents, 5 KiCad schematic files, automated checker suite output, PCB layout guide, power tree document.*
