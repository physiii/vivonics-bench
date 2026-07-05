# Courtyard Overlap Triage

Generated from the native Pcbnew DRC report and current PCB F.Fab/F.CrtYd geometry.
This is not a fabrication waiver.

Native courtyard-overlap pairs: 14
F.Fab/body-box overlaps: 6
Courtyard-only overlaps: 8

## F.Fab/Body-Box Overlaps

These pairs have overlapping F.Fab bounding boxes and require layout review, package change, or reroute before fabrication.

- `U2` / `D2`: F.Fab overlap 2.155 mm x 1.575 mm, area 3.394 mm^2; courtyard overlap 2.730 mm x 3.525 mm, area 9.623 mm^2.
- `U4` / `D4`: F.Fab overlap 4.000 mm x 3.230 mm, area 12.920 mm^2; courtyard overlap 4.550 mm x 3.805 mm, area 17.313 mm^2.
- `U3` / `D3`: F.Fab overlap 3.230 mm x 1.325 mm, area 4.280 mm^2; courtyard overlap 3.805 mm x 3.275 mm, area 12.461 mm^2.
- `C61` / `L1`: F.Fab overlap 1.425 mm x 1.087 mm, area 1.549 mm^2; courtyard overlap 2.855 mm x 1.225 mm, area 3.497 mm^2.
- `C61` / `U15`: F.Fab overlap 1.700 mm x 0.137 mm, area 0.233 mm^2; courtyard overlap 4.150 mm x 0.275 mm, area 1.141 mm^2.
- `D1` / `U1`: F.Fab overlap 3.845 mm x 3.230 mm, area 12.420 mm^2; courtyard overlap 4.550 mm x 3.805 mm, area 17.313 mm^2.

## Courtyard-Only Overlaps

These pairs do not have overlapping F.Fab bounding boxes in the current footprint geometry, but still need assembly-clearance review or placement adjustment.

- `C8` / `D2`: courtyard overlap 1.068 mm x 0.057 mm, area 0.061 mm^2.
- `C62` / `U16`: courtyard overlap 0.462 mm x 4.150 mm, area 1.919 mm^2.
- `C62` / `C70`: courtyard overlap 0.225 mm x 4.155 mm, area 0.935 mm^2.
- `R11` / `D3`: courtyard overlap 1.510 mm x 0.435 mm, area 0.657 mm^2.
- `C6` / `D2`: courtyard overlap 0.970 mm x 0.080 mm, area 0.078 mm^2.
- `C7` / `D2`: courtyard overlap 0.970 mm x 0.080 mm, area 0.078 mm^2.
- `D2` / `R6`: courtyard overlap 1.510 mm x 0.081 mm, area 0.123 mm^2.
- `C12` / `D3`: courtyard overlap 2.010 mm x 0.655 mm, area 1.317 mm^2.

## Required Action

Resolve with a KiCad layout edit and reroute, or document an explicit assembly waiver after physical package review. Do not treat these native warnings as cleared JLCPCB fabrication evidence.
