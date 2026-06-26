# PLT5 520B Harness Reference Note

Source:
- ams OSRAM PLT5 520B datasheet:
  `https://look.ams-osram.com/m/200c3d8553b61059/original/PLT5-520B.pdf`

Current bench assumption:
- Compatible 3-pin laser cans use one laser cathode, one common laser anode /
  monitor-PD cathode node, and one monitor-PD anode.
- J4 exposes `LASER_Nx`, `MPD_RAWx`, common `LASER_V+`, and GND.

Design implication:
- The monitor photodiode path is useful for source telemetry/APC, but it does
  not measure transmitted/sample optical signal.
- PLT5 520B monitor current is specified at `VRPD = 5 V` as a short-time power
  reference, not as an accurate absolute power measurement.
- The bench schematic now uses a high-side INA4180/LM4040 monitor front end:
  `MPD_RAWx -> 750R MPD sense -> MPD_BIAS`, with `LASER_V+ - MPD_BIAS` held
  near 5 V and INA4180A1 gain 20 feeding the ESP32 ADC path.
- At `LASER_V+ = 10.5 V`, PLT5-style `150 uA` monitor current gives about
  `2.25 V` at the ADC and about `4.89 V` monitor-PD reverse bias.
- The current-loop thermal budget uses this part only as a green reference. A
  PLT5 520B-style green diode needs a higher `LASER_V+` rail than low-forward-
  voltage red/IR diodes, so a shared `LASER_V+` rail must be checked per diode
  before any full-current run.

Release blocker:
- Every actual laser MPN must be checked against its own pin table and can/common
  polarity before building the J4 harness. Do not assume all 3-pin laser cans
  match PLT5 520B.
- The current bench `MPD_RAWx` high-side front end is polarity-compatible with
  PLT5-style/common-anode monitor polarity. It does not directly support
  Thorlabs `L785P090` C-code monitor feedback, and `L450G2` has no monitor
  photodiode.
- Direct PLT5-style MPD telemetry on this bench board is relative telemetry
  after diode-MPN approval and calibration, not a release-approved APC loop.
  A production PLT5 monitor-bias/APC circuit still needs a dedicated driver or
  APC front end matched to the laser pin code.
- For every actual laser MPN, run `check_laser_current_budget.py` with that
  diode's forward-voltage/current assumption and the intended `LASER_V+`.
