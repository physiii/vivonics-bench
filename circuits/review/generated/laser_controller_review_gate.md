# Laser Controller Review Gate

Generated: 2026-07-04T21:24:59+00:00

This is a generated local audit artifact. It proves only the checks listed below.
Fabrication remains blocked if any row is `FAIL` or `BLOCKED`.

Overall release status: BLOCKED

| Status | Step | Return | Command |
|---|---|---:|---|
| PASS | Python compile | 0 | `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_pcb_staging.py circuits/check_laser_controller_release_gate.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_schematic_presentation.py circuits/check_power_thermal_budget.py circuits/check_ad7606_package_pcb.py circuits/check_ad7606_interface_budget.py circuits/check_tia_readout_budget.py circuits/check_ap6320x_package_pcb.py circuits/check_buck_input_power_budget.py circuits/check_vin24_input_protection.py circuits/check_usb_vbus_interface.py circuits/check_esp32_reset_boot_controls.py circuits/check_laser_driver_control_loop.py circuits/check_laser_driver_package_pcb.py circuits/check_laser_diode_footprints.py circuits/check_monitor_pd_package_pcb.py circuits/check_laser_current_budget.py circuits/check_laser_monitor_pd_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py` |
| PASS | Generate schematic/BOM | 0 | `python3 circuits/gen_laser_controller.py` |
| PASS | Export schematic netlist | 0 | `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net` |
| PASS | Netlist assertions | 0 | `python3 circuits/check_laser_controller_netlist.py /tmp/lc.net` |
| FAIL | Schematic hierarchy/label assertions | 1 | `python3 circuits/check_schematic_hierarchy_labels.py circuits/laser_controller.kicad_sch` |

## PASS: Python compile

Command: `python3 -m py_compile circuits/run_laser_controller_review.py circuits/gen_laser_controller.py circuits/adapt_mcu.py circuits/gen_pcb.py circuits/pcb_critical_routes.py circuits/check_laser_controller_netlist.py circuits/check_laser_controller_pcb.py circuits/check_pcb_staging.py circuits/check_laser_controller_release_gate.py circuits/check_laser_controller_release_readiness.py circuits/check_schematic_hierarchy_labels.py circuits/check_schematic_presentation.py circuits/check_power_thermal_budget.py circuits/check_ad7606_package_pcb.py circuits/check_ad7606_interface_budget.py circuits/check_tia_readout_budget.py circuits/check_ap6320x_package_pcb.py circuits/check_buck_input_power_budget.py circuits/check_vin24_input_protection.py circuits/check_usb_vbus_interface.py circuits/check_esp32_reset_boot_controls.py circuits/check_laser_driver_control_loop.py circuits/check_laser_driver_package_pcb.py circuits/check_laser_diode_footprints.py circuits/check_monitor_pd_package_pcb.py circuits/check_laser_current_budget.py circuits/check_laser_monitor_pd_budget.py circuits/check_passive_derating.py circuits/generate_laser_controller_audit_tables.py circuits/circuit_designators.py circuits/check_laser_controller_sources.py circuits/check_part_notes_completeness.py circuits/check_source_documents.py`

## PASS: Generate schematic/BOM

Command: `python3 circuits/gen_laser_controller.py`

```text
wrote tia_ir.kicad_sch (36315 bytes, 569 lines)
  wrote tia_red.kicad_sch (36316 bytes, 569 lines)
  wrote tia_green.kicad_sch (36330 bytes, 569 lines)
  wrote tia_blue.kicad_sch (36331 bytes, 569 lines)
  wrote laser_ir.kicad_sch (35160 bytes, 538 lines)
  wrote laser_red.kicad_sch (35161 bytes, 538 lines)
  wrote laser_green.kicad_sch (35156 bytes, 538 lines)
  wrote laser_blue.kicad_sch (34847 bytes, 536 lines)
  wrote power_io.kicad_sch (199066 bytes, 3121 lines)
  wrote laser_controller.kicad_sch (30750 bytes, 247 lines)
  wrote laser_controller_bom_jlcpcb.csv
```

## PASS: Export schematic netlist

Command: `kicad-cli sch export netlist circuits/laser_controller.kicad_sch -o /tmp/lc.net`

## PASS: Netlist assertions

Command: `python3 circuits/check_laser_controller_netlist.py /tmp/lc.net`

```text
PASS 603 netlist assertions across 156 nets
```

## FAIL: Schematic hierarchy/label assertions

Command: `python3 circuits/check_schematic_hierarchy_labels.py circuits/laser_controller.kicad_sch`

```text
FAIL 1 schematic hierarchy/label checks
  mcu.kicad_sch contains accidental global labels: ['GND', 'GND', '+3V3', '+3V3', '+5V', '+5V', 'VIN_24V', 'VIN_24V']
```
