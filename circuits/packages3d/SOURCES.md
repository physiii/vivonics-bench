# Project-local 3D model sources

These project-local models are used by `circuits/laser_controller.kicad_pcb`
where the KiCad 7 system library did not provide a footprint-matched model.

## Imported via easyeda2kicad

- `Potentiometer_SMD.3dshapes/Potentiometer_Bourns_3224W_Vertical.step`
  - Source package: `RES-ADJ-SMD_3224W`
  - LCSC parts checked: `C81348`, `C116323`
  - PCB transform: rotate Z 180, offset Z 0.2 mm
- `OptoDevice.3dshapes/Osram_SFH2201.step`
  - Source package: `LED-SMD_L5.1-W4.0_SFH-2240`
  - LCSC part checked: `C2900216`
- `Inductor_SMD.3dshapes/L_MWSA0503S-4R7MT.step`
  - Source package: `IND-SMD_L5.4-W5.2-H3.0`
  - LCSC part checked: `C408410`
  - PCB transform keeps the existing footprint model offset: X -0.65 mm
- `Inductor_SMD.3dshapes/L_WPN4020H100MT.step`
  - Source package: `IND-SMD_L4.0-W4.0-H1.9`
  - LCSC part checked: `C98364`
- `Connector_USB.3dshapes/USB_Mini-B_920-462A2021S10101.step`
  - Source package: `MICRO-USB-SMD_920-462A2021S10101`
  - LCSC part checked: `C46391`
  - Status: active J1/J2 visual model and procurement family source. Active
    metadata is access-controller `920-462A2021S10101` / LCSC `C46391` on the
    KiCad Mini-B placement footprint.
  - PCB transform: rotate Z 270, offset Y 0.05 mm

## Generated project models

- `Connector_PinHeader.3dshapes/PinHeader_2x04_P2.54mm_SMD_Vertical_C192300.wrl`
  - Generated from the `Open_Automation:PinHeader_2x04_P2.54mm_SMD_Vertical_C192300`
    footprint geometry for KiCad 3D assembly review.
  - LCSC part checked: `C192300`
  - Manufacturer part: BOOMELE `2.54-2*4P`
  - Published package/spec basis: SMT, 2.54 mm pitch, 2 rows, 8 pins,
    vertical, 2.54 mm row spacing.
  - Footprint/model layout: eight visible SMT feet at the footprint pad centers,
    two columns by four positions, with duplicated
    `GND`, `+3V3`, `+5V`, and `VIN_24V` rails on the two sides.
- `Connector_PinHeader.3dshapes/PinHeader_2x04_P2.54mm_SMD_Vertical_C192300.step`
  - Legacy simplified solid generated from the same footprint geometry. The
    active board footprint uses the WRL above because it shows the SMT feet
    against the pads more clearly in KiCad's 3D viewer.
- `OptoDevice.3dshapes/LaserDiode_TO18-D5.6-3.step`
- `OptoDevice.3dshapes/LaserDiode_TO56-3.step`

The laser diode models were generated from the laser diode footprint geometry.
The package body is centered at the model origin; the PCB keeps
`offset (xyz 1 0 0)` so the three leads land on pad centers `(0, 0)`, `(1, 1)`,
and `(2, 0)`.
