# USBLC6-2SC6 Part Note

Status: obsolete for the current bench laser controller. The copied
access-controller MCU sheet now uses discrete LESD5D5.0CT1G USB/VBUS clamps and
1N5819HW VBUS isolation diodes; the exported bench netlist has no USBLC6
component.

Source:
- ST USBLC6-2 datasheet: `https://www.st.com/resource/en/datasheet/usblc6-2.pdf`

Pin checklist:
- Pins 1 and 6 are IO1 line pair.
- Pin 2 is GND.
- Pins 3 and 4 are IO2 line pair.
- Pin 5 is VBUS clamp reference.

Previous local-generator design, not active:
- USB Mini-B D- enters U10 IO1 and leaves through the 22 ohm D- series resistor
  to ESP32-S3 GPIO19.
- USB Mini-B D+ enters U10 IO2 and leaves through the 22 ohm D+ series resistor
  to ESP32-S3 GPIO20.
- VBUS is explicitly routed from J1 pin 1 to U10 pin 5 and D5 anode.

Layout notes:
- This note is retained only so stale USBLC6 references remain searchable.
  Current active layout work must use the copied MCU-sheet LESD/1N5819HW
  topology instead.
- Keep the ground path to the GND reference low impedance during final zone
  refill/review.

Checker evidence:
- Current netlist checker asserts the copied MCU-sheet discrete LESD5D5.0CT1G
  data/VBUS clamps and 1N5819HW VBUS isolation diodes, not USBLC6.
- Current PCB checker enforces Mini-B connector, discrete ESD, CP2102N/native
  USB endpoint proximity, shield/GND pad handling, and explicit USB route
  policy after placement/routing exists.
