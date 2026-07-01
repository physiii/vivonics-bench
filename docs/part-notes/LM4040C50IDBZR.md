# LM4040C50IDBZR Part Note

Sources:
- Texas Instruments LM4040 datasheet:
  `https://www.ti.com/lit/gpn/LM4040`
- LCSC `C69316` order source for `LM4040C50IDBZR`

Package / pinout captured:
- `LM4040C50IDBZR` is the DBZ SOT-23-3 5.0 V shunt reference.
- Pin 1 = cathode, pin 2 = anode, pin 3 = `*`.
- TI permits pin 3 to float, but recommends tying pin 3 to anode in noisy
  environments; this design ties pin 3 to `MPD_BIAS` with the anode.

Bench design decision:
- U13 creates the monitor-PD bias reference for PLT5-style/common-anode laser
  cans by holding `LASER_V+ - MPD_BIAS` near `5 V`.
- U13 pin 1 cathode connects to `LASER_V+`.
- U13 pin 2 anode and pin 3 `*` connect to `MPD_BIAS`.
- R41 is the `2.49k MPD bias` sink from `MPD_BIAS` to GND.
- C36 is the `100nF MPD bias` local capacitor from `LASER_V+` to `MPD_BIAS`.

Budget captured:
- At `LASER_V+ = 10.5 V`, `MPD_BIAS` is about `5.5 V`.
- R41 sinks about `2.21 mA`; four PLT5-style channels at `150 uA` monitor
  current leave about `1.61 mA` through the LM4040.
- At the present `LASER_V+ ~= 10.72 V`, the selected-monitor typical case
  leaves about `1.80 mA` through the LM4040 after LD1/LD2/LD3 monitor currents;
  the selected high-end case still leaves about `1.25 mA`. These pass the
  shunt-current guard, so the selected-monitor failure is ADC/INA output range,
  not LM4040 bias current.
- The guardrail in `check_laser_monitor_pd_budget.py` keeps LM4040 current
  between the local `80 uA` minimum design guard and the `15 mA` maximum.
- `check_monitor_pd_package_pcb.py` asserts U13 cathode/anode/pin-3 schematic
  pin nets, current PCB pad-net assignments, R41/C36 local support nets, and
  installed KiCad `SOT-23` pad geometry.

Release / layout implication:
- Place U13, R41, C36, the 240R sense resistors, and U12 so `MPD_BIAS` is a
  quiet local bias node near the direct laser monitor inputs and INA4180 inputs.
- LM4040 stability is acceptable with capacitive loads, but this shunt reference
  is still only the bench monitor-bias front end. Production APC still needs the
  selected driver/topology matched to each laser package polarity.
