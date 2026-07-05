# AD7606 First-Article Firmware/Readback Signoff - 2026-07-05

## Scope

This signoff accepts the current AD7606BSTZ-4RL hardware interface for
controlled first-article firmware bring-up and bench readback validation. It
does not release production measurement use until firmware timing and known
input readback are measured on the assembled board.

## Accepted First-Article Configuration

- Keep nominal SCLK at or below 10 MHz until rail/timing margin is scoped.
- Default target sample rate is 100 kSPS or lower with no oversampling.
- Use read-after-conversion firmware until scoped otherwise.
- Pulse RESET high for at least 50 ns, then wait at least 25 ns before CONVST.
- Keep CONVST low and high pulses at least 25 ns each.
- Wait for BUSY to fall before asserting CS in the initial firmware.
- Read 32 SCLK edges per DOUT line for each 4-channel sample.
- Read both ADC_MISO_A and ADC_MISO_B and verify channel ordering for VOUT1..4.
- Confirm RANGE=0 +/-5 V scaling and OS[2:0]=000 no-oversampling assumptions in
  firmware metadata.
- Interpret samples as 16-bit twos-complement with 152.59 uV/LSB for the
  +/-5 V range.
- Apply known voltages or known TIA calibration inputs to VOUT1..4 and compare
  AD7606 counts against the expected value before trusting bench data.
- Rerun `check_ad7606_interface_budget.py` before raising SCLK, raising sample
  rate, changing oversampling, changing range, or switching to read-during-BUSY
  firmware.

## Remaining Risk

This signoff is enough to order and perform controlled first-article AD7606
firmware/readback bring-up. It does not close firmware implementation, scoped
timing evidence, analog accuracy, known-input readback data, optical/TIA
calibration, or production measurement release.
