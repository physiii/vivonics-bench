# 2026-07-05 VIN24 Bench Input Signoff

Scope: first-article JLCPCB bench bring-up of the existing `VIN_24V` topology.
This is not a production input-protection release.

## Accepted Bench Configuration

- Use J5 barrel input only for first article power.
- Use a regulated 24.0 V bench supply or adapter with current limit set no higher than 300 mA during initial bring-up.
- Keep RJ45 power injection disabled for first article bring-up. Do not feed
  24 V through J6 until the harness current limit, pinout, and shield/return
  wiring are separately verified.
- Verify center-positive barrel polarity before every power application.
- Do not hot-plug under load.
- Do not connect reverse polarity; the current board has no onboard reverse protection element.
- Keep ESP32 Wi-Fi/BLE disabled on this board until the AP2112 rail is replaced
  or bench temperature data proves the load case.

## Current Evidence

The automated gates prove the following for the bench configuration:

- `check_vin24_input_protection.py --policy bench-topology` passes.
- `check_buck_input_power_budget.py --policy bench-selected-max-9v3` passes.
- `check_buck_input_power_budget.py --policy hardware-clamp-9v3` passes using
  the per-channel analog laser limiter high-current tolerance case.
- `check_buck_input_power_budget.py --policy datasheet-recommended-components`
  passes after the AP632 output capacitor update.
- `check_ap6320x_package_pcb.py` passes for the U15/U16 schematic and current
  PCB pad nets.
- `check_layout_review_geometry.py` passes the focused buck-loop geometry
  checks.

## Remaining Release Risk

This signoff accepts the present board only for controlled bench bring-up. It
does not close production input protection. A production or field-powered board
still needs an onboard or otherwise formally specified current-limit/fuse
element, reverse-polarity strategy, transient/TVS strategy, RJ45 harness rating,
hot-plug behavior, buck ripple/transient/stability measurement, and buck
temperature measurement.
