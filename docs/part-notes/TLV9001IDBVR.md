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

Layout notes:
- Keep source-sense feedback short and quiet.
- Keep TLV9001 output/gate path away from OPA380 summing nodes.

Checker evidence:
- Netlist checker asserts TLV9001 package pins, command-limiter nets, feedback
  nets, output/gate nets, and +5 V/GND membership.
- PCB checker enforces gate/sense/control/compensation proximity.

