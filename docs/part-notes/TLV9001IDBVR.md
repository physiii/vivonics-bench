# TLV9001IDBVR Part Note

Source:
- TI TLV9001 datasheet: `https://www.ti.com/lit/ds/symlink/tlv9001.pdf`

Pin checklist:
- This design uses the non-U DBV SOT-23-5 pinout: OUT=1, V-=2, IN+=3,
  IN-=4, V+=5.
- Do not substitute a TLV9001U DBV pinout without rewiring.

Current design:
- TLV9001 implements the slow laser-current control loop.
- IN+ receives filtered/limited PWM command.
- IN- senses the MOSFET source/sense-resistor high side.
- OUT drives the AO3400A gate through 1 kOhm.
- 10 pF compensation is used from output-side loop node to feedback node.
- It runs from the local +5 V rail. The captured datasheet guard is 1.8 V to
  5.5 V supply, common-mode input from `(V-) - 0.1 V` to `(V+) + 0.1 V`, and
  output swing close to the rails under light load.
- The present PWM divider command clamp is
  `3.3 V * 30k/(10k+30k) = 2.475 V`, or 247.5 mA through the 10 ohm sense
  resistor. That is an electrical clamp, not the selected laser operating
  current.

Layout notes:
- Keep source-sense feedback short and quiet.
- Keep TLV9001 output/gate path away from OPA380 summing nodes.
- Place a 0.1 uF ceramic bypass capacitor close to V+ and V-.
- Route IN+/IN- feedback traces away from switching rails and the output/gate
  trace where practical.

Checker evidence:
- Netlist checker asserts TLV9001 package pins, command-limiter nets, feedback
  nets, output/gate nets, and +5 V/GND membership.
- `check_laser_driver_control_loop.py` asserts the TLV9001 control loop from
  PWM divider to IN+, source-sense feedback to IN-, OUT to AO3400A gate, and the
  selected-max-current gate-drive/range budget.
- `check_laser_driver_package_pcb.py` asserts the U5-U8 TLV9001 schematic pin
  nets, current PCB pad-net assignments, local command/filter/compensation
  components, and installed KiCad `SOT-23-5` pad geometry.
- `hardware-clamp-gate-margin` is an expected-fail policy because the 247.5 mA
  clamp leaves only about 5 mV of AO3400A gate-drive margin above the 2.5 V
  RDS(on) characterization point.
- PCB checker enforces gate/sense/control/compensation proximity.
