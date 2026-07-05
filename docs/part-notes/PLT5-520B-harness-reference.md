# ams OSRAM PLT5 Direct-Footprint Reference Note

Sources:
- ams OSRAM `PLT5 520EB_P` datasheet:
  `https://look.ams-osram.com/m/650bf4d7f1f7e736/original/PLT5-520EB_P.pdf`
- ams OSRAM `PLT5 450GB` datasheet:
  `https://look.ams-osram.com/m/29170f7edbc7cb46/original/PLT5-450GB.pdf`

Current bench assumption for monitor-capable cans:
- Compatible 3-pin monitor cans use one laser cathode, one common laser anode /
  monitor-PD cathode node, and one monitor-PD anode.
- The direct `LDx` through-hole footprints expose the same `LASER_Nx`,
  `MPD_RAWx`, and common `LASER_V+` laser/monitor nodes.

PLT5 520EB_P result:
- The datasheet pin table says pin 1 = LD Cathode, pin 2 = LD Anode, PD
  Cathode (case), and pin 3 = PD Anode.
- This is compatible with the bench Style-A/PLT monitor model:
  `LD_K -> LASER_N3`, common `LD_A/PD_K/case -> LASER_V+`, and `PD_A ->
  MPD_RAW3`.
- Direct footprint `LD3` is `OptoDevice:LaserDiode_TO56-3`; pin 1 ->
  `LASER_N3`, pin 2 -> `LASER_V+`, and pin 3 -> `MPD_RAW3`.
- PLT5 520EB_P monitor current is specified at `VRPD = 5 V` as a short-time
  power reference, not as an accurate absolute power measurement.
- The bench schematic uses a high-side INA4180/LM4040 monitor front end:
  `MPD_RAWx -> 240R MPD sense -> MPD_BIAS`, with `LASER_V+ - MPD_BIAS` held
  near 5 V and INA4180A1 gain 20 feeding the ESP32 ADC path.
- At `LASER_V+ = 10.5 V`, PLT5-style `150 uA` monitor current gives about
  `0.72 V` at the ADC and about `4.96 V` monitor-PD reverse bias.
- The laser-current policy uses 65 mA typ / 78 mA max and 5.4 V typ / 6.1 V max
  for the PLT5 520EB_P operating point.

PLT5 450GB result:
- The datasheet pin table says pin 1 = LD Anode, pin 2 = Case, and pin 3 =
  LD Cathode.
- This part has no monitor photodiode. It must not be modeled as
  `LD_A/PD_K/case` plus `PD_A`.
- Direct footprint `LD4` is `OptoDevice:LaserDiode_TO56-3`. The bench mapping
  is `LD_A -> LASER_V+`, `LD_K -> LASER_N4`, and `CASE` deliberately left
  unconnected. `MPD_RAW4` remains a spare/open monitor front-end input at U12.
- The laser-current policy uses 87 mA typ / 120 mA max and 5.2 V typ / 6.5 V max
  for the PLT5 450GB operating point.
- `selected-diodes-typ-9v3` and `selected-diodes-max-9v3` are the current
  passing common-rail references for the selected diode typical-current and
  max-current cases, assuming bench thermal verification.
- `selected-diodes-hardware-clamp-9v3` now checks the per-channel analog command
  limits and passes for the current schematic.

Direct-footprint signoff and bring-up blockers:
- The 2026-07-04 direct-laser MPN/footprint signoff checked the selected
  Digikey-cart MPNs against their pin tables, the direct `LDx` footprints, and
  the current PCB pad nets.
- Still inspect each received diode's physical pin orientation and can/common
  polarity before soldering the diode into `LDx`.
- Direct `MPD_RAWx` telemetry is approved only for the three compatible
  monitor-PD parts in this Digikey set: `D7805I`, `D6505I`, and
  `PLT5 520EB_P`.
- `PLT5 450GB` has no monitor photodiode, so `MPD4` is not source optical
  telemetry for that blue channel.
- For every actual laser MPN, run `check_laser_current_budget.py` with that
  diode's forward-voltage/current assumption and the intended `LASER_V+`.
- The analog command path now uses per-channel limiters: green PLT5 520EB_P is limited to about 76.2 mA, and blue PLT5 450GB is limited to about 105.5 mA.
  Firmware limits and optical safety behavior still need bring-up validation.
