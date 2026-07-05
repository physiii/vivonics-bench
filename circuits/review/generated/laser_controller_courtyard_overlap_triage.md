# Courtyard Overlap Triage

Generated from the native Pcbnew DRC report and current PCB F.Fab/F.CrtYd geometry.
This is not a fabrication waiver.

Native courtyard-overlap pairs: 4
F.Fab/body-box overlaps: 0
Courtyard-only overlaps: 4
Waived courtyard-only overlaps: 4
Unwaived courtyard-only overlaps: 0

## Waived Courtyard-Only Overlaps

These pairs do not have overlapping F.Fab bounding boxes and have explicit assembly-clearance waivers.

- `C62` / `U16`: courtyard overlap 0.462 mm x 4.150 mm, area 1.919 mm^2. Waiver: Courtyard-only warning between the AP63200 laser-buck regulator and its local VIN ceramic. Current F.Fab geometry has no body-box overlap; separating the parts would degrade the regulator input-loop placement. Verification: Native DRC plus check_courtyard_overlap_triage.py must continue to report zero F.Fab/body-box overlap for this pair before fabrication release.
- `C62` / `C70`: courtyard overlap 0.225 mm x 4.155 mm, area 0.935 mm^2. Waiver: Courtyard-only warning between the laser-buck local VIN ceramic and upstream bulk capacitor. Current F.Fab geometry has no body-box overlap; both parts are intentionally clustered on VIN_24V/GND for low input-loop impedance. Verification: Native DRC plus check_courtyard_overlap_triage.py must continue to report zero F.Fab/body-box overlap for this pair before fabrication release.
- `U4` / `D4`: courtyard overlap 1.945 mm x 2.235 mm, area 4.347 mm^2. Waiver: Courtyard-only warning in the blue photodiode TIA channel. Current F.Fab geometry has no body-box overlap; attempted physical clearance required moving the feedback network into MPD/PWM/green-channel copper and introduced real DRC errors, so the tighter assembly courtyard is accepted to preserve the sensitive D4-A summing-node layout. Verification: Native DRC plus check_courtyard_overlap_triage.py must continue to report zero F.Fab/body-box overlap for this pair and check_layout_review_geometry.py must keep the D4-to-U4 sensitive-node distance within its release target.
- `C61` / `L1`: courtyard overlap 1.355 mm x 2.225 mm, area 3.015 mm^2. Waiver: Courtyard-only warning in the 5 V buck input/output cluster. Current F.Fab geometry has no body-box overlap; keeping C61 close to U15 preserves the local VIN/GND loop and moving L1 created higher-risk PWM2 clearance issues during layout review. Verification: Native DRC plus check_courtyard_overlap_triage.py must continue to report zero F.Fab/body-box overlap for this pair before fabrication release.

## Release Note

All native courtyard warnings are covered by explicit assembly-clearance waivers and still have zero F.Fab/body-box overlap. Recheck this triage after any placement, footprint, or selected assembly-part change.
