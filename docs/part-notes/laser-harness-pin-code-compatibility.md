# Direct Laser Pin-Code Compatibility

Sources:
- Digikey cart text captured in the 2026-06-28 review:
  `D7805I`, `D6505I`, `PLT5 520EB_P`, and `PLT5 450GB`.
- US-Lasers `D7805I` / 780 nm 5 mW source page:
  `http://www.us-lasers.com/n780nm5m.htm`
- US-Lasers `D6505I` / 650 nm 5 mW source page:
  `http://www.us-lasers.com/d650nm5m.htm`
- Digikey mirror for `D650-5I` / 650 nm 5 mW source page:
  `https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/912/D6505I.pdf`
- ams OSRAM `PLT5 520EB_P` datasheet:
  `https://look.ams-osram.com/m/650bf4d7f1f7e736/original/PLT5-520EB_P.pdf`
- ams OSRAM `PLT5 450GB` datasheet:
  `https://look.ams-osram.com/m/29170f7edbc7cb46/original/PLT5-450GB.pdf`

Current bench topology:
- The laser driver is a low-side current sink:
  `LASER_V+ -> laser diode -> LASER_Nx -> AO3400A -> 10 ohm sense -> GND`.
- The monitor path is a high-side current-sense front end:
  `MPD_RAWx -> 240R MPD sense -> MPD_BIAS`.
- INA4180A1 gain 20 converts the 240R sense drop to `MPD_AMPx`, then
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
  laser/MPD harness header is removed. J5 is now the center-positive 24 V
  barrel input, J6 is the 24 V RJ45 input, and U16 generates the shared bench
  `LASER_V+` rail on-board.
- `check_laser_diode_footprints.py` asserts the exported LD1-LD4 schematic
  MPN/footprint/pin nets, the current PCB pad-net assignments, the LD4 case
  no-connect, the `MPD_RAW4` spare/open decision, and the installed KiCad
  TO18/TO56 footprint pad geometry. This does not replace physical diode
  orientation inspection before soldering.

Current/voltage implication:
- `D7805I` is checked at 35 mA typ / 50 mA max and 2.1 V typ / 2.5 V max.
- `D6505I` is checked conservatively from the Digikey `D650-5I` datasheet at
  20 mA typ / 25 mA max and 2.2 V typ / 2.6 V max. The US-Lasers mirror for
  `D6505I` conflicts at 40 mA typ / 60 mA max, so exact order-source locking
  remains required.
- `PLT5 520EB_P` is checked at 65 mA typ / 78 mA max and 5.4 V typ / 6.1 V max.
- `PLT5 450GB` is checked at 87 mA typ / 120 mA max and 5.2 V typ / 6.5 V max.
- `selected-diodes-typ-10v72` preserves the old 10.72 V expected-fail comparison
  for the blue PLT5 450GB.
- `selected-diodes-max-9v3` is the current passing common-rail reference for the
  selected diode max-current cases, assuming real current limiting.
- `selected-diodes-hardware-clamp-10v72` fails because the 247.5 mA analog clamp
  exceeds every selected diode's datasheet operating-current maximum.

Monitor-current implication:
- The direct-footprint pin topology is compatible for LD1 `D7805I`, LD2
  `D6505I`, and LD3 `PLT5 520EB_P`, but the monitor front-end scale is not
  production-range compatible yet.
- `D7805I` monitor current is checked from the captured US-Lasers table at
  `100 uA` min / `200 uA` typ / `600 uA` max at `Po=5mW, Vr=5V`.
- `D6505I` monitor current is checked from the Digikey `D650-5I` table at
  `0.05 mA` min / `0.15 mA` typ / `0.3 mA` max at `Po=5mW`.
- `PLT5 520EB_P` monitor current is checked at the captured `150 uA` typ with
  `VRPD = 5 V`; `PLT5 450GB` has no monitor photodiode.
- With the present `240R` sense resistor and INA4180A1 gain 20, D7805I typ
  monitor current maps to about `0.96 V` at the ESP32 ADC.
- The high-end selected monitor-current case now fits the local production
  guard: D7805I max maps to about `2.88 V` and D6505I max maps to about
  `1.44 V`. This proves ADC headroom only; MPD still needs optical calibration
  before production APC/safety feedback.
- The `selected-monitor-typ-9v3` and `selected-monitor-worst-9v3` policies
  now pass for ADC headroom with the 240R/gain20 scale.

Direct-footprint signoff and required action before laser bring-up:
- The 2026-07-04 direct-laser MPN/footprint signoff closes the selected
  MPN-to-`LDx` pin-table and current-PCB pad-net mapping review for this board.
- Solder each diode directly into the matching `LDx` TO-can footprint only after
  physically checking the received part orientation against the exact per-MPN
  pin table above.
- Do not connect PLT5 450GB case pin 2 to `MPD_RAW4`; that net is an analog
  monitor input, not a case/shield node.
- Do not rely on `MPD4` optical telemetry for PLT5 450GB. Use laser current
  telemetry plus external optical calibration, or choose a blue diode with a
  compatible monitor photodiode and update the schematic.
- Run `check_laser_current_budget.py` for each actual diode forward-voltage and
  current limit, not only the green reference case.
- Run `check_laser_monitor_pd_budget.py --netlist /tmp/lc.net` for the selected
  monitor-current policies before treating `MPD1..4` as calibrated feedback.
- Do not allow firmware or the analog command path to reach the 247.5 mA clamp
  on any selected LD1-LD4 diode.
