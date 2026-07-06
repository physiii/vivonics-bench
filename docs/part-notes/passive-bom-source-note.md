# Passive BOM Source Note

Source:
- Generated BOM: `circuits/laser_controller_bom_jlcpcb.csv`
- Generated netlist fields: value, footprint, `Part Number`, and `LCSC`
- Checker: `circuits/check_laser_controller_netlist.py`
- Derating checker: `circuits/check_passive_derating.py`
- First-article passive AVL lock: `docs/part-notes/passive-first-article-avl-lock.md`

Current passive families:
- 10 pF C0G 0603: `CC0603JRNPO9BN100`, LCSC `C106245`
- 100 nF 0402: `0402B104K160CT`, LCSC `C83056`
- 1 uF 0402: `HGC0402R5105K250NTEJ`, LCSC `C7472946`
- 10 uF 1206 50 V: `CL31B106KBHNNNE`, LCSC `C89632`
- 22 uF 100 V SMD electrolytic: `100CE22FS+P`, LCSC/JLCPCB `C242011`
- 10 uF 0805: `CL21A106KAYNNNG`, LCSC `C318691`
- 1 k / 10 k / 30 k / 22 ohm / 10 M 0603 resistor families as encoded in
  the generated BOM and netlist checker.
- 240 ohm 0603 monitor-PD sense resistor: `RTT032400FTP`, LCSC/JLCPCB `C103446`.
- 2.49 k 0603 monitor-bias sink resistor: `RTT032491FTP`, LCSC/JLCPCB `C103460`.
- 237 k 0603 AP63200 feedback resistor: `FRC0603F2373TS`, LCSC `C2998117`.
- 10 ohm 2512 2 W laser sense resistors: `HoCR2512-2W-10R-1%`, LCSC `C5123624`.
- Bourns 3224W SMD trimmers: `3224W-1-103E` / LCSC `C81348` for VBIAS,
  and `3224W-1-205E` / LCSC `C116323` for TIA feedback trim.

Current verification:
- The netlist checker asserts value, footprint, MPN, and LCSC for every passive
  instance.
- The passive derating checker asserts that every assembled capacitor, resistor,
  and SMD trimmer MPN has an explicit bench rating entry and stays below the
  local steady-state voltage/power policy. Current worst cases are the
  `C68` 10 uF laser-buck output capacitor at 43.1% voltage utilization,
  `R63` 10 k RJ45/input resistor at 48.4% power utilization, and `R63` at
  29.3% voltage utilization.
- The PCB checker verifies pad-net assignment, proximity, copper clearance, and
  route class membership.

Open production gap:
- Commodity passive voltage ratings and resistor steady-state power are now
  encoded for the bench design, and the first-article passive MPN/LCSC set is
  locked against the exported netlist. Production still needs quote-time
  lifecycle/stock review, approved substitute policy, pulse/surge/current derating,
  final manufacturer datasheets for every orderable passive, and
  board-temperature measurement.

First-article upload note:
- The JLCPCB upload manifest is
  `circuits/fab/laser_controller_jlcpcb_upload_manifest.md`. For the current
  five-board first-article order, `R41` (`C103460`) and `C70` (`C242011`) are the
  only passive rows with known thin quote-time stock margin. If JLCPCB flags
  either row, use a same-footprint quote-page substitute with a new checkpoint
  commit, or hand-place the affected part.
