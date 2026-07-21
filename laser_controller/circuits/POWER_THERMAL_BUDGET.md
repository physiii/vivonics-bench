# Bench Laser Controller Power/Thermal Budget

Generated design state: 2026-06-25.

This note covers the AP2112K-3.3 `+3V3` rail because it is the rail most likely
to be overinterpreted. The part is electrically rated for 600 mA, but in the
current SOT25/SOT-23-5 bench design the 5 V to 3.3 V heat is the limiting
constraint.

## Sources

- Diodes AP2112 product page and datasheet: SOT25 pinout, 600 mA rating,
  dropout, `Iq(max)=80 uA`, thetaJA 184 degC/W, and thermal shutdown behavior.
- Espressif ESP32-S3-WROOM-1/WROOM-1U datasheet: RF active-mode current table,
  including 355 mA Wi-Fi 802.11b TX at 100 percent duty cycle and 344 mA
  Bluetooth LE TX at 20 dBm.
- Espressif ESP32-S3 series datasheet: non-RF active-mode current table,
  including 107.9 mA typical for dual-core 240 MHz operation with peripheral
  clocks enabled.

## Calculation

For the AP2112 from a 5 V source:

```text
Pldo = (Vin - Vout) * Iout + Vin * Iq
Tj   = Tambient + Pldo * thetaJA
```

Constants used by `check_power_thermal_budget.py`:

| Parameter | Value |
|---|---:|
| `Vin` | 5.0 V |
| `Vout` | 3.3 V |
| `Iq(max)` | 80 uA |
| SOT25 thetaJA | 184 degC/W |
| Design target junction | 125 degC |

## Scenario Table

| Scenario | Load | Ambient | Calculated Tj | Result |
|---|---:|---:|---:|---|
| ESP32 dual-core typical, RF off | 108 mA | 85 degC | 119 degC | Pass, limited margin |
| Bench USB/UART policy, RF off | 120 mA | 85 degC | 123 degC | Pass, bring-up measurement required |
| Extra 3V3 load example | 200 mA | 85 degC | 148 degC | Fail |
| Wi-Fi 802.11b TX, 100 percent duty | 355 mA | 25 degC | 136 degC | Fail |
| Bluetooth LE TX, 20 dBm | 344 mA | 25 degC | 133 degC | Fail |

At 85 degC ambient and a 125 degC junction target, the calculated continuous
current ceiling is about 128 mA. That is why the bench policy is capped at
120 mA and RF disabled.

## Design Decision

Current bench board:

- Accept AP2112K-3.3 only for USB/UART-controlled bench firmware with Wi-Fi/BLE
  disabled and continuous +3V3 current kept below 120 mA.
- Measure AP2112 package temperature and +3V3 rail current during first bring-up.
- Do not add 3.3 V peripheral loads without rerunning the budget.

Production or sustained wireless design:

- Replace the SOT25 AP2112 rail with a buck regulator or a larger thermally
  proven regulator.
- Keep the internal laser monitor-PD feedback path; that decision is independent
  of the AP2112. The production APC driver/regulator selection still depends on
  each laser package polarity and required current.

## Verification

Expected pass for the current bench/no-RF policy:

```text
python3 circuits/check_power_thermal_budget.py --policy bench-uart-usb
```

Expected fail for sustained Wi-Fi on the current LDO:

```text
python3 circuits/check_power_thermal_budget.py --policy wifi-tx-100-duty
```
