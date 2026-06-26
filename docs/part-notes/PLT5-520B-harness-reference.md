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
- The current-loop thermal budget uses this part only as a green reference. A
  PLT5 520B-style green diode needs a higher `LASER_V+` rail than low-forward-
  voltage red/IR diodes, so a shared `LASER_V+` rail must be checked per diode
  before any full-current run.

Release blocker:
- Every actual laser MPN must be checked against its own pin table and can/common
  polarity before building the J4 harness. Do not assume all 3-pin laser cans
  match PLT5 520B.
- The current bench `MPD_RAWx` burden supports PLT5-style/common-anode monitor
  polarity. It does not directly support Thorlabs `L785P090` C-code monitor
  feedback, and `L450G2` has no monitor photodiode.
- For every actual laser MPN, run `check_laser_current_budget.py` with that
  diode's forward-voltage/current assumption and the intended `LASER_V+`.
