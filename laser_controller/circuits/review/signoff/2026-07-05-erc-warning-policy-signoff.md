# ERC Warning Policy Signoff - 2026-07-05

Scope: laser controller JLCPCB fabrication package.

KiCad ERC was rerun with the project rule policy in `laser_controller.kicad_pro`.
The active ERC report now has 0 violations, 0 errors, and 0 warnings.

Resolved warning classes:

- `wire_dangling` / unconnected wire endpoint warnings were removed around the imported USB connector ground/VBUS stubs.
- `same_local_global_label` warnings were removed by making the `MPD_RAW1..4` sheet labels explicit global labels while preserving the exported net names.
- `footprint_link_issues` for `SW1..SW3` were removed with a project-local `Button_Switch_SMD:SW_SPST_PTS645` alias that preserves the existing board/BOM footprint name.
- `lib_symbol_issues` were removed by adding project-local/library-table coverage for the imported MCU sheet symbols, standard power symbols, USB interface symbol, `R_10K_0402`, and the J7 `Conn_02x04_Utility_C192300` header symbol.

Ignored-by-policy warning classes:

- `endpoint_off_grid` is ignored for this project because the MCU sheet is imported/preserved from source geometry. The generated sheets and non-imported presentation guard still enforce the 50 mil grid.
- `lib_symbol_mismatch` is ignored because the imported sheet carries embedded/rescued symbol copies; symbol mismatch is not used as fabrication evidence for this generated release.

Replacement gates for the ignored classes:

- `check_laser_controller_netlist.py` verifies pad-level connectivity and expected component metadata.
- `check_schematic_pcb_parity.py` verifies PCB pad nets match the exported schematic netlist.
- Native KiCad PCB DRC with schematic parity verifies 0 unconnected items. See
  the dated parity-field waiver below for the current metadata-only findings.
- `check_jlcpcb_order_package.py` verifies the JLC Gerber/BOM/POS package, J7 C192300 footprint/package mapping, PD/laser labels, and backside `vivonics` mark.

Current evidence:

```text
kicad-cli sch erc --severity-all:
Found 0 violations
ERC messages: 0  Errors 0  Warnings 0
```

## 2026-07-12 native parity-field waiver

The current KiCad CLI parity report contains `36`
`footprint_symbol_field_mismatch` findings, all marked `Local override; warning`:

| Field mismatch class | References | Count |
| --- | --- | ---: |
| missing footprint `Part Number` | `H1,H2` | 2 |
| footprint `Datasheet` empty while schematic field is populated | `C41–C47,D7–D14,R50–R60,SW1–SW3,U9,U10` | 31 |
| missing footprint `Website` | `J1,J2` | 2 |
| missing footprint `Manufacturer` | `J7` | 1 |

This waiver is limited to those 36 field-copy differences for the first-article
review. It does not waive any copper, clearance, unconnected-pad, footprint
orientation, BOM/CPL, source-register, or custom pad-net parity failure. The
physical DRC reports zero violations and zero unconnected pads; the custom
schematic/PCB parity check passes `181/181` footprints. The BOM, procurement
register, and source checks remain the fabrication metadata authority for this
first article.

Before the next fabrication or any production release, either synchronize these
fields into the PCB footprints or make the review wrapper parse and accept only
this exact enumerated warning set. Any new reference, field class, count, or
non-warning severity invalidates this waiver.
