# 2026-07-05 AP2112 First-Article Signoff

Scope: first-article JLCPCB bench bring-up of the existing AP2112K-3.3 `+3V3`
rail.

This signoff accepts the AP2112 only for controlled bench firmware. It does not
close production regulator decision or sustained wireless operation.

## Accepted Bench Configuration

- Use USB/UART control firmware only during first-article bring-up.
- Keep ESP32 Wi-Fi/BLE disabled on this board.
- Keep continuous +3V3 current no higher than 120 mA.
- Do not add external 3.3 V loads to J7 unless the AP2112 thermal budget is
  rerun for the new current and ambient case.
- Measure AP2112 package temperature and +3V3 rail current during first bring-up.
- Sustained Wi-Fi/BLE requires a buck regulator, a larger thermally proven
  regulator, or measured duty-cycle proof before release.

## Current Evidence

- `check_power_thermal_budget.py --policy bench-uart-usb` passes for the
  120 mA, 85 degC, no-RF bench policy.
- `check_power_thermal_budget.py --policy wifi-tx-100-duty` is an expected fail
  for sustained Wi-Fi on the current AP2112 SOT25 rail.
- `check_power_thermal_budget.py --policy ble-tx-20dbm` is an expected fail
  for sustained BLE TX on the current AP2112 SOT25 rail.
- `check_layout_review_geometry.py` passes AP2112 input/output capacitor
  proximity checks on the current PCB artifact.

## Remaining Release Risk

This signoff is enough to order and power a controlled first article with RF
disabled. It does not close production regulator decision, AP2112 package
temperature measurement, +3V3 rail current measurement, sustained Wi-Fi/BLE, or
future 3.3 V peripheral load changes.
