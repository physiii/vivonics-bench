# USBLC6-2SC6 Part Note

Source:
- ST USBLC6-2 datasheet: `https://www.st.com/resource/en/datasheet/usblc6-2.pdf`

Pin checklist:
- Pins 1 and 6 are IO1 line pair.
- Pin 2 is GND.
- Pins 3 and 4 are IO2 line pair.
- Pin 5 is VBUS clamp reference.

Current design:
- USB Mini-B D- enters U10 IO1 and leaves through the 22 ohm D- series resistor
  to ESP32-S3 GPIO19.
- USB Mini-B D+ enters U10 IO2 and leaves through the 22 ohm D+ series resistor
  to ESP32-S3 GPIO20.
- VBUS is explicitly routed from J1 pin 1 to U10 pin 5 and D5 anode.

Layout notes:
- Keep USBLC6 near the connector.
- Keep the ground path to the GND reference low impedance during final zone
  refill/review.

Checker evidence:
- Netlist checker asserts USBLC6 pin functions and exact USB chain.
- PCB checker enforces connector/USBLC6/series-resistor proximity and explicit
  VBUS routing.

