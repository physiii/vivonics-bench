# Bench Laser Controller Power Tree

Generated design state: 2026-06-30.

This is the rail and power-path review for `laser_controller.kicad_sch` and
`laser_controller.kicad_pcb`. It complements the netlist/PCB checkers; it does
not replace GUI ERC, schematic parity, native KiCad PCB DRC, or bench
measurements.

## First-Article Finding — 2026-07-26

The 24 V input is intended to be the only external power source needed for the
board: U15 generates `/POWER_IO/BUCK_5V`, D6 feeds the board `+5V` rail, U11
then generates `+3V3`, and U16 independently generates `LASER_V+`. USB VBUS is
only an alternate diode-OR source through D5; it is not a required second rail.

The assembled first article measured only `4.3 V` and later `4.6 V` at U14
AD7606 pin 1 before an external post-OR `+5V` injection raised that point to
`5.2 V`. The AD7606 AVCC operating range is `4.75 V` to `5.25 V`. A fixed
`5.0 V` U15 output followed by D6's forward drop therefore has insufficient
guaranteed margin and explains the under-voltage observation. The same topology
exists on the USB path through D5, so connecting USB must not be treated as the
corrective action for AD7606 AVCC.

This is an open first-article power-design defect, not a missing-user-supply
requirement. Before relying on the ADC, measure D6 anode (`BUCK_5V`) and cathode
(`+5V`) simultaneously under load. Rework the source/OR topology so the
post-OR rail remains inside every downstream load's limits and the AD7606 sees
at least `4.75 V`; candidate fixes require an electrical review and include a
higher regulated pre-OR voltage, an ideal-diode path, or an approved bypass of
the unnecessary drop. Do not connect an uncontrolled second 5 V source or
assume two diode-OR inputs will raise the rail.
The PCB's copper planes follow the `~/projects/access-controller` reference
pattern: a single full-board `GND` flood on `In1.Cu` (no outer-layer `GND`
fill -- `F.Cu`/`B.Cu` are pure signal layers), and `In2.Cu` split into
exactly two simple, non-overlapping regions, `+3V3` over the MCU cluster
and `+5V` over the TIA/laser-driver clusters, satisfying
`check_laser_controller_pcb.REQUIRED_PLANE_ZONES`. `LASER_V+` and
`VIN_24V` have no dedicated zone; delivery to their loads (and delivery
from the `+3V3`/`+5V` zone edges to any load outside their region, e.g.
the `POWER_IO` buck/ADC/monitor cluster sitting in the gap between the two
regions) is meant to be explicit trunk-trace routing, not a wide flood -- see
`PCB_LAYOUT.md` for why. The current PCB artifact has filled zone definitions,
1611 routed copper segments, 236 vias, and passes the custom PCB and
generated-copper release gates. `check_schematic_pcb_parity.py` passes the
headless exported-netlist-to-current-PCB pad-net comparison. A 2026-07-04 GUI
DRC screenshot captures refilled-zone DRC with zero violations and zero
unconnected items, but native schematic parity was not run in that dialog. The
2026-07-04 return-path layout signoff captures the current
GND/via/sensitive-route review for this routed PCB.
KiCad GUI ERC and native schematic-parity evidence remain separate release
requirements.

## Rail Table

| Rail | Source | Main Loads | Current / Stress Notes | Current PCB State | Release Action |
|---|---|---|---|---|---|
| `VIN_24V` | J5 center-positive barrel jack and J6 RJ45 pins 4/5 | U15 AP63205 input, U16 AP63200 input, C61-C62 10 uF/50 V ceramic input caps, C70 22 uF/100 V bulk input cap | The copied barrel jack is rated 30 V / 500 mA. The copied RJ45 footprint follows the access-controller convention: pins 4/5 are power and pins 7/8/9/11 are return. AP63205/AP63200 are 32 V-max input parts, so 24 V nominal leaves limited transient margin: 80 percent of the J5 voltage rating and 75 percent of the AP632 input maximum before transients. `check_vin24_input_protection.py --policy bench-topology` and `bench-external-protection` pass for first-article bench use with J5 barrel only, 24.0 V, current limit no higher than 300 mA, RJ45 power disabled, no hot-plug, and verified polarity. `production-protection` intentionally fails because J5/J6 and U15/U16 IN pins share one `VIN_24V` net with no fuse/PTC/TVS/reverse-protection/eFuse stage onboard. `check_buck_input_power_budget.py --policy bench-selected-max-9v3`, `hardware-clamp-9v3`, and `datasheet-recommended-components` now pass the selected current, all-channel analog-limit, and local AP632 capacitor-count guards. | Schematic/netlist path is correct and current PCB copper is routed for the custom checks; input protection, KiCad DRC, and visual power-entry review remain open. | Select the adapter/RJ45 harness current limit, add protection/fusing/TVS if needed for production, review protected 24 V copper to both buck input loops, then refill zones and run DRC. |
| `VBUS_5V` | J1/J2 Mini-B VBUS through copied MCU-sheet isolation diodes | D5 anode, CP2102N VBUS-sense divider, VBUS ESD clamps | USB input current limit depends on host/source and firmware power behavior. D5 must carry board +5 V load when USB powered. | Schematic/netlist path is correct through the copied 1N5819HW isolation diodes and current PCB copper is routed for the custom checks. | Verify USB entry current limit, D5 current/temperature, connector shield return, and ESD return during final DRC/visual review. |
| `/POWER_IO/BUCK_5V` | U15 AP63205 buck output through L1/C64/C65 | D6 anode | This is the onboard fixed 5 V source from `VIN_24V`. A downstream Schottky drop leaves no guaranteed AD7606 AVCC margin. The current C64+C65 bank is 44 uF nominal using 2x22 uF 25 V 0805 ceramics, matching the local AP632 reference-table capacitance guard. | Schematic/netlist connectivity is correct, but the assembled first article exposed a system-level voltage-margin defect after D6. | Measure U15 output/ripple under load and the D6 anode-to-cathode drop; approve and implement a post-OR voltage-margin rework. |
| `+5V` | D5/D6 cathode OR output | OPA380s, TLV9001s, AP2112 input, AD7606 AVCC, TIA bias branches, local decoupling | Analog/load rail after Schottky OR-ing. The first article measured `4.3-4.6 V` at AD7606 AVCC before direct rail injection, below its `4.75 V` minimum. USB also reaches this rail through a Schottky and is not a reliable voltage correction. | PCB connectivity is correct, but voltage compliance is open and ADC operation cannot be credited at the observed native rail voltage. | Keep outputs off while diagnosing. Measure D6 anode/cathode under load, then rework the topology so the loaded post-OR rail stays within all load limits and AD7606 AVCC is `4.75-5.25 V`. |
| `+3V3` | U11 AP2112K-3.3 | ESP32-S3-WROOM-1, EN/BOOT pulls, local caps | AP2112K is pin-correct and electrically rated for 600 mA, but SOT25 thermal resistance is the real limit from a 5 V source. The accepted bench policy is RF disabled and <=120 mA continuous +3V3 load. | Netlist membership is correct and current PCB copper plus the checked plane-zone definitions connect the rail for the custom checks. | `check_power_thermal_budget.py --policy bench-uart-usb` must pass. Sustained Wi-Fi/BLE requires a buck regulator, larger thermal package, or measured duty-cycle proof. |
| `LASER_V+` | U16 AP63200 adjustable buck output through L2/C67/C68 | LD1-LD4 common laser anode / monitor-PD cathode rail | The bench rail is set near 9.38 V by R61/R62, not raw 24 V. Actual stress still depends on diode MPNs, forward voltage, per-channel analog command limit, firmware clamp, and duty cycle. The selected-diode 9.3 V common-rail reference passes the selected typical-current, max-current, and per-channel analog-limit cases. The current C67+C68 bank is 44 uF nominal using 2x22 uF 25 V 0805 ceramics, matching the local AP632 reference-table capacitance guard. | Current PCB routes the common rail from U16/L2 to the direct laser footprints and monitor-bias front end with 0.80 mm copper and full-size vias for the custom release gate. | `check_laser_current_budget.py` must pass for each selected diode/supply assumption. Verify AP63200 buck layout, output capacitance/ripple/stability, width/current/temperature rise, duty cycle, and board stackup; keep final review away from TIA summing nodes and MPD_RAW traces. |
| `GND` | J1/J2 shield/GND, J5 barrel return, J6 RJ45 return pins, IC grounds | Entire board return | Mixed analog, digital, USB ESD, buck-switching, and laser-current returns share this net; layout must control return paths. | Netlist membership is correct, the current PCB has routed GND copper, 101 GND vias, and a filled `In1.Cu` GND reference-plane zone. The 2026-07-04 return-path signoff records local laser-sense and buck-return vias plus sensitive-route spacing. | Run native KiCad DRC/parity; re-open return-path review after any reroute or if bench noise/ripple measurements show coupling. |

## Datasheet-Driven Notes

- ESP32-S3-WROOM-1 operates from a 3.3 V module rail and has RF current peaks
  well above the no-RF bench budget; the AP2112K thermal margin is the main
  `+3V3` risk.
- AP2112K SOT-23-5 pinout is `VIN=1`, `GND=2`, `EN=3`, `NC=4`, `VOUT=5`; the schematic and
  netlist checker assert this package mapping.
- AP2112K SOT25 thetaJA is 184 degC/W. With +5 V input, +3.3 V output, and
  `Iq(max)=80 uA`, the bench/no-RF 120 mA policy calculates to about 123 degC
  junction at 85 degC ambient against a 125 degC design target. Sustained
  802.11b TX at Espressif's 355 mA table value fails this regulator choice.
- SS14 diodes D5/D6 are Schottky OR-ing parts. The schematic and PCB inventory assert
  anode-to-source and cathode-to-`+5V` polarity.
- AP63205 generates the onboard 5 V source from `VIN_24V`; AP63200 generates the
  shared bench `LASER_V+` rail from `VIN_24V`. Raw 24 V is not tied to the laser
  anodes. A separate external 5 V source is not intended for normal operation.
- The AP63205 is a fixed 5 V regulator, but the board calls the rail after D6
  `+5V`. The 2026-07-26 first-article measurements show that distinction is
  electrically significant: Schottky loss can put the post-OR rail below the
  AD7606 minimum. Connecting USB adds the parallel D5 path but does not remove
  its own forward drop.
- AP63200/AP63205 datasheet review is encoded in
  `check_buck_input_power_budget.py`. The checker asserts TSOT-23-6 pins
  `FB/EN/IN/GND/SW/BST`, AP63200 feedback math
  `0.8 V * (1 + 237k/22.1k) = 9.38 V`, AP63205 fixed 5 V output, local
  100 nF bootstrap capacitors, and the L1/L2 inductor identities. It also keeps
  the production capacitor guard visible: C64+C65/C67+C68 output banks now
  provide 44 uF each with 2x22 uF 25 V ceramics. C61+C62 provide 20 uF nominal
  VIN ceramic input capacitance.
- `circuits/review/signoff/2026-07-05-ap632-first-article-buck-validation-signoff.md`
  records first-article AP632 rail verification, startup/ripple/load-step
  capture, and U15/U16/L1/L2/D6/output-cap temperature measurement requirements
  under the J5-only external-current-limit input policy.
- `check_vin24_input_protection.py` keeps the input-protection distinction
  explicit. The present bench topology is direct J5/J6-to-`VIN_24V`, while the
  production policy is an expected fail until current limiting, transient
  suppression, reverse-polarity handling, and adapter/RJ45 harness ratings are
  designed in or explicitly justified by measurement and release signoff.
- D6505I, D7805I, and PLT5 520EB_P include internal monitor photodiodes that are
  compatible with the high-side `MPD_RAWx -> INA4180/LM4040` bench front end
  when the direct LDx footprint follows the datasheet pin map. PLT5 450GB has no monitor
  photodiode, so `MPD_RAW4` remains a spare/open monitor input. The laser current
  command path now uses per-channel limiter pulldowns: about 38.0 mA IR,
  23.0 mA red, 76.2 mA green, and 105.5 mA blue. `LASER_V+` and firmware clamps
  must still be sized for each selected diode voltage, rated current, duty
  cycle, and optical safety limit.
- The 10 ohm sense resistor worst case is now about 0.111 W at the blue
  per-channel analog command limit, below the 2512 2 W rating. The AO3400A
  linear-pass dissipation is
  `I * (LASER_V+ - Vf - I*10 ohm)`. A common `LASER_V+` rail needs per-diode review,
  especially when mixing different current/Vf diode classes. The current passing
  common-rail references are `selected-diodes-typ-9v3`,
  `selected-diodes-max-9v3`, and `selected-diodes-hardware-clamp-9v3`, matching
  the present 9.3 V-class setting and per-channel analog limiters.
- USB VBUS from J1/J2 is isolated by copied-sheet 1N5819HW diodes before `VBUS_5V`.
  It still needs a short, low-impedance path to D5 and appropriate upstream current limiting.

## Bring-Up Measurement Points

Existing connector access is enough for bench bring-up but not ideal for production:

- `VBUS_5V`: J1 pin 1 / D5 anode.
- `VIN_24V`: J5 pin 1, J6 pins 4/5, C61/C62/C70, and U15/U16 input pins.
- `/POWER_IO/BUCK_5V`: L1 output / C64-C65 / D6 anode.
- `+5V`: C34 / D5-D6 cathodes.
- `+3V3`: U11 pin 5 / C30-C31 / C32.
- `LASER_V+`: L2 output / C67-C68 / LD1-LD4 anode/common pins.
- `GND`: J1/J2 shell/GND pins, J5 barrel ground pins, or J6 RJ45 return pins; use a short probe ground for rail-noise measurement.

For the first-article voltage-margin diagnosis, record `/POWER_IO/BUCK_5V` at
D6 anode and board `+5V` at D6 cathode/U14 pin 1 at the same load state. A
post-OR reading below `4.75 V` blocks AD7606 qualification even if digital
readback appears to run.

## Release Gate

Block fabrication until:

1. GUI ERC passes on the generated unique-reference schematic.
2. Zones are refilled in KiCad.
3. PCB DRC with schematic parity passes.
4. AP2112 bench/no-RF thermal policy is accepted and measured during bring-up,
   or the regulator is replaced before sustained Wi-Fi/BLE use.
5. Received laser-can orientation is inspected against the signed-off MPN/footprint
   mapping before soldering.
6. Each selected diode and `LASER_V+` setting passes the laser current thermal budget.
7. `check_vin24_input_protection.py --policy bench-topology` and
   `bench-external-protection` pass for controlled first-article power-up, while
   the expected-fail `production-protection` policy remains open until a
   production current-limit/fuse, reverse-polarity strategy, TVS/transient
   strategy, and RJ45 harness limit are selected.
8. `check_buck_input_power_budget.py --policy bench-selected-max-9v3`,
   `hardware-clamp-9v3`, and `datasheet-recommended-components` pass for the
   current component set. AP63205/AP63200 ripple, load-step behavior,
   switch-loop temperature, and input adapter/protection assumptions still need
   first-article measurement before trusting the rails for production.

`python3 check_laser_controller_release_gate.py laser_controller.kicad_pcb /tmp/lc.net`
must pass before fabrication. It passes on the current routed artifact for
explicit multi-pad connectivity, laser cathode/anode current-copper width and
length limits, and distinct high-current GND vias for the laser sense returns.
This does not replace KiCad GUI ERC or PCB DRC with schematic parity.
