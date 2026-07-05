# Return-Path Layout Signoff

Date: 2026-07-04 CDT

Scope: close the current-layout GND and sensitive return-path review blocker for
`laser_controller.kicad_pcb`. This signoff is for the routed PCB artifact at
the time of review. It does not close KiCad schematic ERC, KiCad schematic
parity, native KiCad DRC, board-temperature measurement, optical calibration,
or power-input transient/protection decisions.

## Evidence Commands

```bash
python3 circuits/check_layout_review_geometry.py circuits/laser_controller.kicad_pcb
python3 circuits/check_laser_controller_pcb.py circuits/laser_controller.kicad_pcb /tmp/lc_final_pkg.net
python3 circuits/check_laser_controller_release_gate.py circuits/laser_controller.kicad_pcb /tmp/lc_final_pkg.net
```

Key outputs:

```text
PASS layout geometry review: 15 high-risk layout distances within targets
PASS fabrication release gate: 110/110 multi-pad nets explicitly routed, no pending rail/zone nets, laser cathode/anode routes meet generated width targets, and laser sense returns have distinct high-current GND vias.
```

The PCB checker reports routed copper, plane-zone, return-path, and spacing
evidence for the current board:

```text
3/3 required GND/+3V3/+5V plane-zone definitions
110/110 explicitly routed multi-pad nets
0 zone/rail pending nets
111/111 connected critical local route links
sensitive-to-laser clearances [TIA_Sensitive:12219 min 5.235/2.00mm; MPD_RAW:5232 min 0.525/0.50mm; Monitor_ADC:16374 min 0.300/0.25mm]
```

## Zone / Via Evidence

Local `pcbnew` inspection of the current board reports:

```text
zones: 3
0 In1.Cu GND filled_outlines 3
1 In2.Cu +3V3 filled_outlines 1
2 In2.Cu +5V filled_outlines 1
gnd_vias 101
gnd_via_size (0.6, 0.3) 31
gnd_via_size (1.0, 0.5) 69
gnd_via_size (1.0, 0.6) 1
```

Laser sense-return pads have local high-current GND vias:

```text
R18.2 GND nearest GND via 1.439mm, 1.00/0.50mm
R23.2 GND nearest GND via 1.502mm, 1.00/0.50mm
R28.2 GND nearest GND via 1.688mm, 1.00/0.50mm
R33.2 GND nearest GND via 1.477mm, 1.00/0.50mm
```

Buck input/output return pads have local GND vias at the regulator and capacitor
cluster:

```text
U15.4 nearest GND via 1.000mm, 1.00/0.50mm
U16.4 nearest GND via 1.124mm, 1.00/0.50mm
C61.2 nearest GND via 1.076mm, 1.00/0.50mm
C62.2 nearest GND via 0.783mm, 1.00/0.50mm
C64.2 nearest GND via 1.325mm, 1.00/0.50mm
C65.2 nearest GND via 1.287mm, 1.00/0.50mm
C67.2 nearest GND via 1.538mm, 1.00/0.50mm
C68.2 nearest GND via 3.259mm, 1.00/0.50mm
```

## Verdict

The current board has a filled full-board `In1.Cu` GND reference zone, explicit
routed connectivity for all multi-pad nets, no rail/zone pending nets in the
custom checker, local high-current GND vias at the laser sense returns, local
buck return vias, and same-layer copper separation between laser-current routes
and TIA/monitor telemetry routes above the project limits.

This closes the repository's `VISUAL_RETURN_PATH_REVIEW` blocker for the
current PCB artifact. Reopen the review if placement/routing/zones change, if a
new native KiCad DRC report identifies copper/zone problems, or if bench noise,
ripple, USB ESD, laser-current, or TIA measurements show return-path coupling.
