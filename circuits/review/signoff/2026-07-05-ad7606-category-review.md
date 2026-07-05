# AD7606 Firmware And Readback Category Review - 2026-07-05

Scope: severity-ranked category 4 from
`circuits/review/signoff/2026-07-05-release-category-matrix.md`.

## Category Rank

Rank 4, high. A wrong AD7606 timing, DOUT, scaling, or channel-order assumption
can make assembled hardware appear functional while returning swapped, stale,
or incorrectly scaled measurement data.

## Current Result

The current layout/package state is acceptable for controlled first-article
ordering and firmware bring-up under the existing AD7606 boundary:

- AD7606BSTZ-4RL is strapped for serial mode with `RANGE=0` +/-5 V and
  `OS[2:0]=000` no oversampling.
- `CONVSTA` and `CONVSTB` are tied together on `CONVST`.
- Use read-after-conversion firmware until scoped otherwise.
- Keep nominal SCLK at or below 10 MHz and target sample rate at or below
  100 kSPS.
- Read both `ADC_MISO_A` and `ADC_MISO_B`, 32 SCLK edges per DOUT line.
- Verify `VOUT1..4` channel order and known-input counts before trusting bench
  ADC data.

This category is not production-closed. The repo proves the hardware contract,
package/pad-net mapping, strap state, and timing budget; it does not prove
firmware implementation, scoped RESET/CONVST/BUSY/CS/SCLK timing, live DOUT
readback, analog accuracy, channel order, or known-input data.

## Evidence Reviewed

- `python3 circuits/check_ad7606_package_pcb.py --netlist circuits/review/generated/laser_controller_kicad9.net --board circuits/laser_controller.kicad_pcb`
  passes the AD7606 package, schematic pinout, local support components, and
  current PCB pad-net mapping.
- `python3 circuits/check_ad7606_interface_budget.py circuits/review/generated/laser_controller_kicad9.net`
  passes the serial-mode strap and 10 MHz / 100 kSPS read-after-conversion
  timing budget.
- `python3 circuits/check_ad7606_first_article_signoff.py`
  passes the first-article firmware/readback signoff.
- `python3 circuits/check_firmware_validation_template.py`
  passes the timing, DOUT, scaling, channel-order, and known-input validation
  template guard.
- `python3 circuits/check_optical_calibration_template.py`
  includes the `adc_readback` rows that tie `VOUT1..4` to AD7606 known-input
  validation.

## Closure State

Do not mark any `AD7606_SYSTEM_INTERFACE` row closed in
`circuits/review/calibration/first_article_release_evidence.csv` until the
specific evidence exists:

- `digital_timing`: scoped RESET, CONVST, BUSY, CS, and SCLK timing with the
  accepted read policy.
- `dout_readback`: sample logs proving both `ADC_MISO_A` and `ADC_MISO_B` are
  read with 32 SCLK edges per DOUT line.
- `scaling_channel_order_known_input`: firmware metadata and measured data
  proving RANGE/OS scaling, `VOUT1..4` channel order, and known-input counts.

## Decision

No additional pre-order layout defect was found in this category by the current
automated gates. The remaining risk is intentional first-article/firmware
scope, not a cleared production measurement release.
