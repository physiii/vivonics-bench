# Direct Laser Pin-Code Compatibility

Sources:
- Digikey cart text captured in the 2026-06-28 review:
  `D7805I`, `D6505I`, `PLT5 520EB_P`, and `PLT5 450GB`.
- US-Lasers `D7805I` / 780 nm 5 mW source page:
  `http://www.us-lasers.com/n780nm5m.htm`
- US-Lasers `D6505I` / 650 nm 5 mW source page:
  `http://www.us-lasers.com/d650nm5m.htm`
- ams OSRAM `PLT5 520EB_P` datasheet:
  `https://look.ams-osram.com/m/650bf4d7f1f7e736/original/PLT5-520EB_P.pdf`
- ams OSRAM `PLT5 450GB` datasheet:
  `https://look.ams-osram.com/m/29170f7edbc7cb46/original/PLT5-450GB.pdf`

Current bench topology:
- The laser driver is a low-side current sink:
  `LASER_V+ -> laser diode -> LASER_Nx -> AO3400A -> 10 ohm sense -> GND`.
- The monitor path is a high-side current-sense front end:
  `MPD_RAWx -> 750R MPD sense -> MPD_BIAS`.
- INA4180A1 gain 20 converts the 750R sense drop to `MPD_AMPx`, then
  `1k/100nF` filters feed the ESP32 ADC1 `MPDx` pins.
- `LM4040C50` holds `LASER_V+ - MPD_BIAS` near `5 V`.
- This monitor path expects the monitor photodiode cathode at the laser common
  high node and the monitor photodiode anode on `MPD_RAWx`.

Digikey cart pin-code result:
- IR `D7805I`, Digikey `38-1028-ND`: US-Lasers Style A, 5.6 mm can,
  built-in monitor diode. Pin 1 is laser cathode, pin 2 is common case, and
  pin 3 is monitor diode anode. Direct footprint `LD1` is
  `OptoDevice:LaserDiode_TO18-D5.6-3`; pin 1 -> `LASER_N1`,
  pin 2 -> `LASER_V+`, and pin 3 -> `MPD_RAW1`.
- Red `D6505I`, Digikey `38-1007-ND`: US-Lasers Style A, 5.6 mm can,
  built-in monitor diode. Pin 1 is laser cathode, pin 2 is common case, and
  pin 3 is monitor diode anode. Direct footprint `LD2` is
  `OptoDevice:LaserDiode_TO18-D5.6-3`; pin 1 -> `LASER_N2`,
  pin 2 -> `LASER_V+`, and pin 3 -> `MPD_RAW2`.
- Green `PLT5 520EB_P`, Digikey `475-PLT5520EB_P-ND`: TO56 with photo diode.
  Pin 1 = LD Cathode; pin 2 = LD Anode, PD Cathode (case); pin 3 = PD Anode.
  Direct footprint `LD3` is `OptoDevice:LaserDiode_TO56-3`; pin 1 ->
  `LASER_N3`, pin 2 -> `LASER_V+`, and pin 3 -> `MPD_RAW3`.
- Blue `PLT5 450GB`, Digikey `475-PLT5450GB-ND`: TO56 package with no monitor
  photodiode. Pin 1 = LD Anode; pin 2 = Case; pin 3 = LD Cathode. Direct
  footprint `LD4` is `OptoDevice:LaserDiode_TO56-3`; pin 1 ->
  `LASER_V+`, pin 3 -> `LASER_N4`; pin 2 case is not tied into `MPD_RAW4`.
  `MPD_RAW4` is spare/open unless a different blue source with a compatible
  monitor photodiode is selected.

Design implication:
- LD1, LD2, and LD3 use the same Style-A/PLT monitor-can model:
  `LD_K -> LASER_Nx`, common `LD_A/PD_K/case -> LASER_V+`, and `PD_A ->
  MPD_RAWx`.
- LD4 uses the laser-only diode/case model: `LD_A -> LASER_V+`, `LD_K ->
  LASER_N4`, and `CASE` is an intentional no-connect in the generated schematic.
- The board uses direct soldered TO-can footprints `LD1..LD4`; the old
  laser/MPD harness header is removed. J5 is now the center-positive 12 V
  barrel input, and U16 generates the shared bench `LASER_V+` rail on-board.

Required action before laser bring-up:
- Solder each diode directly into the matching `LDx` TO-can footprint after
  checking the exact per-MPN pin table above.
- Do not connect PLT5 450GB case pin 2 to `MPD_RAW4`; that net is an analog
  monitor input, not a case/shield node.
- Do not rely on `MPD4` optical telemetry for PLT5 450GB. Use laser current
  telemetry plus external optical calibration, or choose a blue diode with a
  compatible monitor photodiode and update the schematic.
- Run `check_laser_current_budget.py` for each actual diode forward-voltage and
  current limit, not only the green reference case.
