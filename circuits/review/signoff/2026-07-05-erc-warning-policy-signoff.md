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
- Native KiCad PCB DRC with schematic parity verifies 0 unconnected items and 0 schematic parity issues.
- `check_jlcpcb_order_package.py` verifies the JLC Gerber/BOM/POS package, J7 C192300 footprint/package mapping, PD/laser labels, and backside `vivonics` mark.

Current evidence:

```text
kicad-cli sch erc --severity-all:
Found 0 violations
ERC messages: 0  Errors 0  Warnings 0
```
