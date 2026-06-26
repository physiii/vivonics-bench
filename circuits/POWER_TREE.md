# Bench Laser Controller Power Tree

Generated design state: 2026-06-26.

This is the rail and power-path review for `laser_controller.kicad_sch` and
`laser_controller.kicad_pcb`. It complements the netlist/PCB checkers; it does
not replace GUI ERC, zone refill, PCB DRC, or visual return-path review.
The custom release gate currently requires every multi-pad rail and signal net
to be connected in the generated PCB artifact. KiCad GUI ERC, zone refill, PCB
DRC, and visual return-path review are still separate release requirements.

## Rail Table

| Rail | Source | Main Loads | Current / Stress Notes | Current PCB State | Release Action |
|---|---|---|---|---|---|
| `VBUS_5V` | J1 Mini-B VBUS | USBLC6 VBUS reference, D5 anode | USB input current limit depends on host/source and firmware power behavior. D5 must carry board +5 V load when USB powered. | Explicitly routed: J1 pin 1 to USBLC6 pin 5 and D5 anode, using local F.Cu escapes and a 0.50 mm B.Cu trunk so the In2.Cu power/reference layer remains available for `LASER_V+`. | Verify USB entry current limit, D5 current/temperature, and ESD return during final DRC/visual review. |
| `/POWER_IO/EXT5V` | J6 external 5 V | D6 anode | External supply must be current-limited off-board until a fuse/PTC is added. | Explicitly routed from J6 pin 1 to D6 anode. | Define off-board current limit or add board protection before production. |
| `+5V` | D5/D6 cathode OR output | OPA380s, TLV9001s, AP2112 input, TIA bias branches, local decoupling | Analog/load rail after Schottky OR-ing. D5/D6 cathodes carry board +5 V load; TLV9001/OPA380 supply branches are low-current distribution only. | Partially routed: D5/D6, C34, AP2112 VIN/EN/input cap, and all OPA380 supply/PD-bias/trim feeds are one generated-copper component. The four laser-driver TLV9001 V+ decouplers/op-amp pins are connected to each other by a 0.25 mm `In2.Cu` trunk, but that laser-driver trunk is still split from the bulk `+5V` component. | Rework the laser-driver placement or add a reviewed bulk-`+5V` to laser-driver-trunk bridge that preserves LASER_N/USB/MPD/PWM routing and antenna keepout; then refill zones and run DRC. |
| `+3V3` | U11 AP2112K-3.3 | ESP32-S3-WROOM-1, EN/BOOT pulls, local caps | AP2112K is pin-correct and electrically rated for 600 mA, but SOT25 thermal resistance is the real limit from a 5 V source. The accepted bench policy is RF disabled and <=120 mA continuous +3V3 load. | Explicitly routed: AP2112 output decoupling, ESP32 local decap, ESP32 module 3V3, EN pull-up, and BOOT pull-up are one connected rail. | `check_power_thermal_budget.py --policy bench-uart-usb` must pass. Sustained Wi-Fi/BLE requires a buck regulator, larger thermal package, or measured duty-cycle proof. |
| `LASER_V+` | J5 laser supply input | J4 pin 9 common laser anode rail | Separate external laser rail. Actual voltage and current depend on diode MPNs, forward voltage, current clamp, and duty cycle. A common high rail can overheat low-Vf red/IR channels through the AO3400A linear sinks. | Explicitly routed as a 0.80 mm `In2.Cu` laser-anode trunk from J5 pin 1 to J4 pin 9. | `check_laser_current_budget.py` must pass for each selected diode/supply assumption. Verify width/current/temperature rise against selected laser current, supply voltage, duty cycle, and board stackup; keep final review away from TIA summing nodes and MPD_RAW traces. |
| `GND` | J1 shield/GND, J2/J3/J4/J5/J6 returns, IC grounds | Entire board return | Mixed analog, digital, USB ESD, and laser-current returns share this net; layout must control return paths. | Explicitly connected in the generated route graph through local GND dogbones/fanout vias into the `In1.Cu` GND reference-zone model, including the reserved C34 bulk-cap GND via. | Refill zones in KiCad, inspect for islands/stitching, and keep laser current return out of TIA summing-node return path. |

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
- PLT5 520B has operating current up to 260 mA and monitor current around 150 uA at rated
  optical output. The laser current command limiter targets about 248 mA nominal; `LASER_V+`
  must still be sized for actual selected diode voltage, duty cycle, and current.
- The current 10 ohm sense resistor dissipates about 0.61 W at the 248 mA command clamp.
  The 2512 2 W part is correctly upsized, but the AO3400A linear-pass dissipation is
  `I * (LASER_V+ - Vf - I*10 ohm)`. A common `LASER_V+` rail needs per-diode review,
  especially when mixing green with low-forward-voltage red/IR diodes.
- USBLC6 VBUS is only the ESD clamp reference, not a power switch. USB VBUS still needs a
  short, low-impedance path to D5 and appropriate upstream current limiting.

## Bring-Up Measurement Points

Existing connector access is enough for bench bring-up but not ideal for production:

- `VBUS_5V`: J1 pin 1 / D5 anode.
- `/POWER_IO/EXT5V`: J6 pin 1 / D6 anode.
- `+5V`: C34 / D5-D6 cathodes.
- `+3V3`: U11 pin 5 / C30-C31 / C32.
- `LASER_V+`: J5 pin 1 / J4 pin 9.
- `GND`: J2/J3/J4/J5/J6 ground pins; use a short probe ground for rail-noise measurement.

## Release Gate

Block fabrication until:

1. GUI ERC passes on the generated unique-reference schematic.
2. Zones are refilled in KiCad.
3. PCB DRC with schematic parity passes.
4. `GND` has a visually reviewed return path after zone refill.
5. AP2112 bench/no-RF thermal policy is accepted and measured during bring-up,
   or the regulator is replaced before sustained Wi-Fi/BLE use.
6. Each actual laser MPN and harness pinout is checked against its datasheet.
7. Each selected diode and `LASER_V+` setting passes the laser current thermal budget.

`python3 check_laser_controller_release_gate.py laser_controller.kicad_pcb /tmp/lc.net`
must pass before fabrication. It currently fails closed on generated `+5V` and
`GND` rail/zone signoff: the laser-driver inter-channel `+5V` trunk is routed,
but bulk `+5V` is still split from that trunk. This does not replace KiCad GUI
ERC, zone refill, PCB DRC with schematic parity, or visual return-path review.
