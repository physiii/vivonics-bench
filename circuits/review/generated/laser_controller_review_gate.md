# Laser Controller Review Gate

Generated: 2026-06-26T15:42:02+00:00

This is a generated local audit artifact. It proves only the checks listed below.
Fabrication remains blocked if any row is `FAIL` or `BLOCKED`.

Overall release status: BLOCKED

| Status | Step | Return | Command |
|---|---|---:|---|
| PASS | Python compile | 0 | `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_laser_controller_release_gate.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_power_thermal_budget.py circuits/check_laser_current_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py` |
| PASS | Generate schematic/BOM | 0 | `python3 circuits/gen_laser_controller.py` |
| PASS | Export schematic netlist | 0 | `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net` |
| PASS | Netlist assertions | 0 | `python3 circuits/check_laser_controller_netlist.py /tmp/lc.net` |
| PASS | Schematic hierarchy/label assertions | 0 | `python3 circuits/check_schematic_hierarchy_labels.py circuits/laser_controller.kicad_sch` |
| PASS | Source-register assertions | 0 | `python3 circuits/check_laser_controller_sources.py /tmp/lc.net` |
| PASS | Part-note completeness assertions | 0 | `python3 circuits/check_part_notes_completeness.py` |
| PASS | Source-document evidence | 0 | `python3 circuits/check_source_documents.py` |
| PASS | Passive derating assertions | 0 | `python3 circuits/check_passive_derating.py` |
| PASS | Generate PCB | 0 | `env LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 circuits/gen_pcb.py` |
| PASS | PCB assertions | 0 | `python3 circuits/check_laser_controller_pcb.py circuits/laser_controller.kicad_pcb /tmp/lc.net` |
| BLOCKED | Generated-copper release gate | 1 | `python3 circuits/check_laser_controller_release_gate.py circuits/laser_controller.kicad_pcb /tmp/lc.net` |
| PASS | AP2112 bench thermal policy | 0 | `python3 circuits/check_power_thermal_budget.py --policy bench-uart-usb` |
| PASS | AP2112 sustained Wi-Fi expected fail | 1 | `python3 circuits/check_power_thermal_budget.py --policy wifi-tx-100-duty` |
| PASS | PLT5 green laser-current policy | 0 | `python3 circuits/check_laser_current_budget.py --policy plt5-520b-green-10v5` |
| PASS | PLT5 12V laser-current expected fail | 1 | `python3 circuits/check_laser_current_budget.py --policy plt5-520b-green-12v` |
| PASS | Low-Vf diode on green rail expected fail | 1 | `python3 circuits/check_laser_current_budget.py --policy low-vf-diode-on-10v5` |
| BLOCKED | Open fabrication/release blockers | 2 | `python3 circuits/check_laser_controller_release_readiness.py` |
| PASS | Regenerate audit inventory | 0 | `python3 circuits/generate_laser_controller_audit_tables.py /tmp/lc.net circuits/laser_controller.kicad_pcb circuits/review/2026-06-25_full_net_pin_inventory.md` |
| PASS | Export placement | 0 | `kicad-cli pcb export pos circuits/laser_controller.kicad_pcb -o /tmp/lc_pos.csv` |
| BLOCKED | KiCad ERC availability | 1 | `kicad-cli sch erc circuits/laser_controller.kicad_sch -o /tmp/lc_erc.rpt` |
| BLOCKED | KiCad DRC availability | 1 | `kicad-cli pcb drc circuits/laser_controller.kicad_pcb -o /tmp/lc_drc.rpt` |
| PASS | Git diff whitespace | 0 | `git diff --check` |
| PASS | Trailing whitespace scan | 1 | `rg -n [ \t]+$ circuits docs -g *.md -g *.py -g *.kicad_sch -g *.kicad_pcb` |

## PASS: Python compile

Command: `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_laser_controller_release_gate.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_power_thermal_budget.py circuits/check_laser_current_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py`

## PASS: Generate schematic/BOM

Command: `python3 circuits/gen_laser_controller.py`

```text
wrote tia_ir.kicad_sch (34381 bytes, 549 lines)
  wrote tia_red.kicad_sch (34382 bytes, 549 lines)
  wrote tia_green.kicad_sch (34396 bytes, 549 lines)
  wrote tia_blue.kicad_sch (34399 bytes, 549 lines)
  wrote laser_ir.kicad_sch (28482 bytes, 454 lines)
  wrote laser_red.kicad_sch (28483 bytes, 454 lines)
  wrote laser_green.kicad_sch (28485 bytes, 454 lines)
  wrote laser_blue.kicad_sch (28484 bytes, 454 lines)
  wrote mcu.kicad_sch (71033 bytes, 1128 lines)
  wrote power_io.kicad_sch (62545 bytes, 991 lines)
  wrote laser_controller.kicad_sch (22728 bytes, 199 lines)
  wrote laser_controller_bom_jlcpcb.csv
```

## PASS: Export schematic netlist

Command: `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net`

## PASS: Netlist assertions

Command: `python3 circuits/check_laser_controller_netlist.py /tmp/lc.net`

```text
PASS 352 netlist assertions across 109 nets
```

## PASS: Schematic hierarchy/label assertions

Command: `python3 circuits/check_schematic_hierarchy_labels.py circuits/laser_controller.kicad_sch`

```text
PASS schematic hierarchy/label guardrails: 10 root sheets, 44 whitelisted root global labels, 44 child hierarchical labels, typed sheet pins, zero child-sheet global labels, and checked schematic annotation designators
```

## PASS: Source-register assertions

Command: `python3 circuits/check_laser_controller_sources.py /tmp/lc.net`

```text
PASS source-register coverage for 41 MPN/LCSC tokens across 117 components, intent coverage for 109 exported nets, 343 component-pin intent roles, and 4 documentation designator guard files
```

## PASS: Part-note completeness assertions

Command: `python3 circuits/check_part_notes_completeness.py`

```text
PASS part-note completeness: 13 notes, 96 required phrases, 2 stale-phrase guards
```

## PASS: Source-document evidence

Command: `python3 circuits/check_source_documents.py`

```text
WARN ST USBLC6-2 official datasheet: not reachable; Primary source, but ST/Akamai times out from this shell environment; manual release-time verification remains required. [GET failed: The read operation timed out; HEAD failed: The read operation timed out]
WARN JLCPCB via-design article: reachable; Advisory article only; JLCPCB quote capability page wins. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN Vishay SS12-SS16 family datasheet: reachable; Family reference only; exact LCSC C2480 manufacturer must be confirmed at order. [HEAD HTTP 200, type=application/pdf, length=1174123]
WARN LCSC C2480 SS14 order page: reachable; Distributor/order source, not a replacement for final order-time manufacturer confirmation. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN Wuerth Mini/Micro USB family page: reachable; Family/product page; final 65100516121 drawing still needs release verification. [HEAD HTTP 200, type=text/html; charset=UTF-8, length=1]
WARN Farnell mirror of Wuerth 65100516121 drawing: reachable; Distributor mirror used because the exact official Wuerth drawing URL was not directly reachable. [HEAD HTTP 200, type=application/pdf, length=276116]
WARN TME Royalohm 0603WAF1001T5E page: not reachable; Representative 0603WAF family evidence for commodity resistors. [GET failed: HTTP Error 403: Forbidden; HEAD failed: HTTP Error 403: Forbidden]
WARN JLCPCB C22984 30k resistor page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C269701 RMC060310KFN page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
WARN JLCPCB C5123624 10 ohm 2512 sense resistor page: reachable; Distributor/order source for passive rating evidence. [HEAD HTTP 200, type=text/html; charset=utf-8, length=unknown]
PASS source-document evidence: 16 required online sources, 13 required local artifacts, and 10 secondary/open-risk sources reviewed
```

## PASS: Passive derating assertions

Command: `python3 circuits/check_passive_derating.py`

```text
PASS passive derating: checked 38 capacitors and 52 resistors/trimmers
  max capacitor voltage utilization: 67.3% at C38 (100nF MPD)
  max resistor power utilization: 30.6% at R33 (10R 2W)
  max resistor voltage utilization: 10.0% at R39 (10k)
```

## PASS: Generate PCB

Command: `env LC_STRICT_ROUTE_CLEARANCE=1 LC_MAX_ROUTE_SEARCH_CELLS=2500 python3 circuits/gen_pcb.py`

```text
wrote laser_controller.kicad_pcb  (1534 blocks, 117 ref instances)
  refs: 117 unique
```

## PASS: PCB assertions

Command: `python3 circuits/check_laser_controller_pcb.py circuits/laser_controller.kicad_pcb /tmp/lc.net`

```text
PASS 311 PCB pad-net assignments across 117 footprints, 77 named nets, 8 net classes, 4 copper layers, 1 GND reference-zone definition, 109 placement proximity checks, 59 intentional unnetted pad instances, 385 board-bounded pads, 2661 board-bounded copper endpoints/vias, 48260 different-net pad-overlap checks, 327596 trace-to-pad clearance checks, 1708 antenna-keepout intrusion checks, 2520 routed segment endpoints and 141 vias checked for dangling copper, 1260 routed segments checked by layer policy, 1260 routed segments checked by width policy, 40 sensitive local nets checked by length policy, 1260 routed copper segments, 97 reviewed Laser_Current segments, 6 USB route sections, sensitive-to-laser clearances [TIA_Sensitive:16376 min 15.911/2.00mm; MPD_RAW:2888 min 1.222/0.50mm; Monitor_ADC:5809 min 0.350/0.25mm], 141 vias, 46 non-power vias checked by route policy, 75/77 explicitly routed multi-pad nets, 2 zone/rail pending nets, and 109/109 connected critical local route links
```

## BLOCKED: Generated-copper release gate

Command: `python3 circuits/check_laser_controller_release_gate.py circuits/laser_controller.kicad_pcb /tmp/lc.net`

Generated signal/control copper passes the custom PCB gate; +5V/GND rail-zone signoff still requires a bulk +5V bridge into the routed laser-driver +5V trunk, KiCad refill, DRC, and return-path review before fabrication.

```text
FAIL fabrication release gate
  rail/zone multi-pad nets still require pour/trunk routing and KiCad refill/DRC: +5V, GND
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

## PASS: PLT5 green laser-current policy

Command: `python3 circuits/check_laser_current_budget.py --policy plt5-520b-green-10v5`

```text
Laser current-loop policy: plt5-520b-green-10v5
  PLT5 520B reference using datasheet max operating voltage 7.0 V and a 10.5 V laser rail.
  command clamp: 3.30V * 30k/(10k+30k) / 10.0ohm = 247.5mA
  sense resistor: drop=2.475V, power=0.613W, rating=2.0W
  laser rail=10.50V, diode Vf(max)=7.00V, AO3400A Vds=1.02V, power=0.254W
  at ambient=85.0degC and target Tj=125.0degC, AO3400A continuous power budget=0.320W
  estimated safe laser rail window at this diode Vf/current: 9.97V to 10.77V
PASS laser current-loop policy for this diode/supply assumption. Actual laser MPN and harness pinout still require release review.
```

## PASS: PLT5 12V laser-current expected fail

Command: `python3 circuits/check_laser_current_budget.py --policy plt5-520b-green-12v`

```text
Laser current-loop policy: plt5-520b-green-12v
  PLT5 520B reference at a 12 V laser rail; this is expected to fail the conservative continuous AO3400A thermal budget.
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
    Detail: The PLT5 520B pinout is only a compatible reference. The current MPD_RAWx burden directly supports PLT5-style and Thorlabs A-code common-anode / monitor-PD-cathode cans. The canonical 785 nm proof diode L785P090 is C-code, so its monitor photodiode is not compatible with this low-side monitor front end without an adapter or different driver/monitor topology. L450G2 has no monitor photodiode.
    Required action: Lock every laser diode MPN, verify its datasheet pin table and can/common polarity, then build the J4 harness from that table. For L785P090 monitor feedback, design a C-code-compatible adapter/front end or choose a compatible 785 nm diode.
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

