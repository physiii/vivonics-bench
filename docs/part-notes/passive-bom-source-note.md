# Passive BOM Source Note

Source:
- Generated BOM: `circuits/laser_controller_bom_jlcpcb.csv`
- Generated netlist fields: value, footprint, `Part Number`, and `LCSC`
- Checker: `circuits/check_laser_controller_netlist.py`
- Derating checker: `circuits/check_passive_derating.py`

Current passive families:
- 10 pF C0G 0603: `CC0603JRNPO9BN100`, LCSC `C106245`
- 100 nF 0402: `0402B104K160CT`, LCSC `C83056`
- 1 uF 0402: `HGC0402R5105K250NTEJ`, LCSC `C7472946`
- 10 uF 0805: `CL21A106KAYNNNG`, LCSC `C318691`
- 1 k / 10 k / 30 k / 22 ohm / 10 M 0603 resistor families as encoded in
  the generated BOM and netlist checker.
- 750 ohm 0603 monitor-PD sense resistor: `RC0603FR-07750RL`, LCSC `C114635`.
- 2.49 k 0603 monitor-bias sink resistor: `CRCW06032K49FKEAHP`, LCSC `C2099849`.
- 10 ohm 2512 2 W laser sense resistors: `HoCR2512-2W-10R-1%`, LCSC `C5123624`.

Current verification:
- The netlist checker asserts value, footprint, MPN, and LCSC for every passive
  instance.
- The passive derating checker asserts that every assembled capacitor, resistor,
  and SMD trimmer MPN has an explicit bench rating entry and stays below the
  local steady-state voltage/power policy. Current worst cases are the
  `100nF MPD bias` capacitor at 31.6% of 16 V and the 10 ohm 2512 laser
  sense resistors at 30.6% of 2 W.
- The PCB checker verifies pad-net assignment, proximity, copper clearance, and
  route class membership.

Open production gap:
- Commodity passive voltage ratings and resistor steady-state power are now
  encoded for the bench design. Production still needs a procurement lock file
  with lifecycle/AVL status, pulse/surge/current derating, final manufacturer
  datasheets for every orderable passive, and board-temperature measurement.
