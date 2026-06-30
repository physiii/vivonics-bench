# Bench Laser Controller Power Tree

Generated design state: 2026-06-30.

This is the rail and power-path review for `laser_controller.kicad_sch` and
`laser_controller.kicad_pcb`. It complements the netlist/PCB checkers; it does
not replace GUI ERC, zone refill, PCB DRC, or visual return-path review.
The current PCB artifact has recovered hand-placement coordinates and explicit
pad nets, but it has no board-level routed segments, vias, or filled zones. The
custom release gate therefore currently fails on every signal/control route,
every rail/zone trunk, the laser-anode supply copper, and the high-current laser
sense returns.
KiCad GUI ERC, zone refill, PCB DRC, and visual return-path review are still
separate release requirements.

## Rail Table

| Rail | Source | Main Loads | Current / Stress Notes | Current PCB State | Release Action |
|---|---|---|---|---|---|
| `VIN_12V` | J5 center-positive barrel jack | U15 AP63205 input, U16 AP63200 input, input capacitors | The copied access-controller barrel jack is rated 30 V / 500 mA, so this is a bench adapter input for controlled duty/current. It is not a release waiver for all lasers at maximum continuous current. | Schematic/netlist path is correct, but current PCB copper is unrouted and split across recovered placement. | Select the adapter current limit, add protection/fusing if needed for production, route protected 12 V copper to both buck input loops, then refill zones and run DRC. |
| `VBUS_5V` | J1/J2 Mini-B VBUS through copied MCU-sheet isolation diodes | D5 anode, CP2102N VBUS-sense divider, VBUS ESD clamps | USB input current limit depends on host/source and firmware power behavior. D5 must carry board +5 V load when USB powered. | Schematic/netlist path is correct through the copied 1N5819HW isolation diodes, but PCB copper is currently unrouted and split across the recovered placement. | Route protected USB power-entry copper from the copied isolation diodes to D5 anode; verify USB entry current limit, D5 current/temperature, connector shield return, and ESD return during final DRC/visual review. |
| `/POWER_IO/BUCK_5V` | U15 AP63205 buck output through L1/C64/C65 | D6 anode | This is the onboard 5 V source from `VIN_12V`. The AP63205 switch loop and diode-OR path must stay compact and away from analog inputs. | Schematic/netlist path is correct, but current PCB copper is unrouted. | Place/route U15, L1, C61-C65, and D6 as a compact buck-plus-OR path; verify switch-loop area, current width, and diode temperature. |
| `+5V` | D5/D6 cathode OR output | OPA380s, TLV9001s, AP2112 input, TIA bias branches, local decoupling | Analog/load rail after Schottky OR-ing. D5/D6 cathodes carry board +5 V load; TLV9001/OPA380 supply branches are low-current distribution only. | Netlist membership is correct, but current PCB copper is split across the recovered placement with no routed trunk or pour. | Route or pour the post-OR +5 V rail to every analog, laser-driver, and LDO input load; then refill zones and run DRC. |
| `+3V3` | U11 AP2112K-3.3 | ESP32-S3-WROOM-1, EN/BOOT pulls, local caps | AP2112K is pin-correct and electrically rated for 600 mA, but SOT25 thermal resistance is the real limit from a 5 V source. The accepted bench policy is RF disabled and <=120 mA continuous +3V3 load. | Netlist membership is correct, but AP2112 output, ESP32 3V3, straps, and decoupling are not connected by current PCB copper. | Route the AP2112 output rail to ESP32-S3 and strap/decoupling loads; `check_power_thermal_budget.py --policy bench-uart-usb` must pass. Sustained Wi-Fi/BLE requires a buck regulator, larger thermal package, or measured duty-cycle proof. |
| `LASER_V+` | U16 AP63200 adjustable buck output through L2/C67/C68 | LD1-LD4 common laser anode / monitor-PD cathode rail | The bench rail is set near 10.72 V, not raw 12 V. Actual stress still depends on diode MPNs, forward voltage, current clamp, and duty cycle. A common high rail can overheat low-Vf red/IR channels through the AO3400A linear sinks. | Requires final PCB routing/zone review from U16/L2 to the direct laser footprints and monitor-bias front end. | `check_laser_current_budget.py` must pass for each selected diode/supply assumption. Verify buck layout, width/current/temperature rise, duty cycle, and board stackup; keep final review away from TIA summing nodes and MPD_RAW traces. |
| `GND` | J1/J2 shield/GND, J5 barrel return, IC grounds | Entire board return | Mixed analog, digital, USB ESD, buck-switching, and laser-current returns share this net; layout must control return paths. | Netlist membership is correct, but current PCB has no board-level GND routes, vias, or filled `In1.Cu` reference plane. | Add/refill the GND reference zone, route required returns and stitching, inspect for islands/stitching, keep buck hot-loop returns tight, and keep laser current return out of TIA summing-node return path. |

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
- AP63205 generates the onboard 5 V source from `VIN_12V`; AP63200 generates the
  shared bench `LASER_V+` rail from `VIN_12V`. Raw 12 V is not tied to the laser
  anodes.
- D6505I, D7805I, and PLT5 520EB_P include internal monitor photodiodes that are
  compatible with the high-side `MPD_RAWx -> INA4180/LM4040` bench front end
  when the direct LDx footprint follows the datasheet pin map. PLT5 450GB has no monitor
  photodiode, so `MPD_RAW4` remains a spare/open monitor input. The laser current
  command limiter targets about 248 mA nominal; `LASER_V+` and firmware clamps
  must still be sized for each selected diode voltage, rated current, duty cycle,
  and optical safety limit.
- The current 10 ohm sense resistor dissipates about 0.61 W at the 248 mA command clamp.
  The 2512 2 W part is correctly upsized, but the AO3400A linear-pass dissipation is
  `I * (LASER_V+ - Vf - I*10 ohm)`. A common `LASER_V+` rail needs per-diode review,
  especially when mixing green with low-forward-voltage red/IR diodes.
- USB VBUS from J1/J2 is isolated by copied-sheet 1N5819HW diodes before `VBUS_5V`.
  It still needs a short, low-impedance path to D5 and appropriate upstream current limiting.

## Bring-Up Measurement Points

Existing connector access is enough for bench bring-up but not ideal for production:

- `VBUS_5V`: J1 pin 1 / D5 anode.
- `VIN_12V`: J5 pin 1 and U15/U16 input capacitors.
- `/POWER_IO/BUCK_5V`: L1 output / C64-C65 / D6 anode.
- `+5V`: C34 / D5-D6 cathodes.
- `+3V3`: U11 pin 5 / C30-C31 / C32.
- `LASER_V+`: L2 output / C67-C68 / LD1-LD4 anode/common pins.
- `GND`: J1/J2 shell/GND pins or J5 barrel ground pins; use a short probe ground for rail-noise measurement.

## Release Gate

Block fabrication until:

1. GUI ERC passes on the generated unique-reference schematic.
2. Zones are refilled in KiCad.
3. PCB DRC with schematic parity passes.
4. `GND` has a visually reviewed return path after zone refill.
5. AP2112 bench/no-RF thermal policy is accepted and measured during bring-up,
   or the regulator is replaced before sustained Wi-Fi/BLE use.
6. Each actual laser MPN and direct-footprint pinout is checked against its datasheet.
7. Each selected diode and `LASER_V+` setting passes the laser current thermal budget.
8. AP63205/AP63200 buck placement, switch-loop routing, thermal behavior, and input
   adapter/protection assumptions are reviewed before ordering boards.

`python3 check_laser_controller_release_gate.py laser_controller.kicad_pcb /tmp/lc.net`
must pass before fabrication. It currently fails because signal/control
multi-pad nets are not explicitly routed, `+3V3`/`+5V`/`VIN_12V`/`BUCK_5V`/`GND`/`LASER_V+`/
`VBUS_5V` still require pours or trunks, `LASER_V+` has no routed laser-anode
copper, and the laser sense resistors lack high-current GND vias. This does not
replace KiCad GUI ERC, zone refill, PCB DRC with schematic parity, or visual
return-path review.
