# Direct Laser MPN / Footprint Signoff

Date: 2026-07-04 CDT

Scope: close the fabrication-time direct laser MPN pin-table and LDx footprint
mapping blocker for the currently selected Digikey-cart laser sources on the
current `laser_controller.kicad_pcb`.

This signoff does not close laser current/thermal limits, MPD optical
calibration, blue-channel monitor telemetry absence, physical diode orientation
inspection before soldering, or laser-safety bring-up controls.

## Sources Checked

- US-Lasers `D7805I` / 780 nm 5 mW source page:
  `http://www.us-lasers.com/n780nm5m.htm`
- US-Lasers `D6505I` / 650 nm 5 mW source page:
  `http://www.us-lasers.com/d650nm5m.htm`
- Digikey mirror for `D650-5I`:
  `https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/912/D6505I.pdf`
- ams OSRAM `PLT5 520EB_P` datasheet:
  `https://look.ams-osram.com/m/650bf4d7f1f7e736/original/PLT5-520EB_P.pdf`
- ams OSRAM `PLT5 450GB` datasheet:
  `https://look.ams-osram.com/m/29170f7edbc7cb46/original/PLT5-450GB.pdf`
- Local KiCad footprints:
  `OptoDevice:LaserDiode_TO18-D5.6-3` and
  `OptoDevice:LaserDiode_TO56-3`
- Local checker:
  `python3 circuits/check_laser_diode_footprints.py --netlist /tmp/lc_final_pkg.net --board circuits/laser_controller.kicad_pcb`

## Channel Mapping

| Ref | Color | MPN | Footprint | Pad 1 | Pad 2 | Pad 3 | Verdict |
|---|---|---|---|---|---|---|---|
| LD1 | INFRARED | `D7805I` | `OptoDevice:LaserDiode_TO18-D5.6-3` | LD cathode to `LASER_N1` | common case / LD anode / monitor-PD cathode to `LASER_V+` | monitor-PD anode to `MPD_RAW1` | Released for direct footprint mapping |
| LD2 | RED | `D6505I` | `OptoDevice:LaserDiode_TO18-D5.6-3` | LD cathode to `LASER_N2` | common case / LD anode / monitor-PD cathode to `LASER_V+` | monitor-PD anode to `MPD_RAW2` | Released for direct footprint mapping |
| LD3 | GREEN | `PLT5 520EB_P` | `OptoDevice:LaserDiode_TO56-3` | LD cathode to `LASER_N3` | LD anode / PD cathode / case to `LASER_V+` | PD anode to `MPD_RAW3` | Released for direct footprint mapping |
| LD4 | BLUE | `PLT5 450GB` | `OptoDevice:LaserDiode_TO56-3` | LD anode to `LASER_V+` | case no-connect | LD cathode to `LASER_N4` | Released for direct footprint mapping; no monitor PD |

## Evidence

The direct-footprint checker passes against the exported schematic netlist, the
current PCB pad nets, and the installed KiCad TO18/TO56 footprint geometry:

```text
PASS laser diode footprint pinout: LD1/LD2 Style-A TO18, LD3 PLT5 520EB_P TO56, LD4 PLT5 450GB case NC; schematic nets, current PCB pad nets, and KiCad TO18/TO56 pad geometry agree
```

The important blue-channel decision is explicit: `PLT5 450GB` has no monitor
photodiode. Its case pad stays unconnected and must not be tied to `MPD_RAW4`.
`MPD_RAW4` / `MPD4` remains a spare/open monitor-front-end input unless the blue
source is changed to a monitor-PD part and the schematic/PCB/docs are updated.

## Remaining Work Not Closed Here

- Inspect the actual received TO cans and package orientation before soldering.
- Keep firmware/current-loop limits below each diode's allowed operating current.
- Complete the per-diode laser current/thermal budget and bench temperature
  measurement.
- Calibrate `MPD1..3` against an external optical meter before using monitor
  telemetry for APC, normalization, or safety behavior.
- Do not use `MPD4` as blue optical telemetry with the selected `PLT5 450GB`.
