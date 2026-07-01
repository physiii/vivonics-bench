# AD7606BSTZ-4RL

Role: on-board 4-channel simultaneous-sampling ADC for the four SFH2201/OPA380
signal-photodiode outputs.

Source: Analog Devices AD7606/AD7606-6/AD7606-4 datasheet, RL-64 LQFP package
table; LCSC C51512 order source.

Package/pin decisions captured in the checker:

- `AD7606BSTZ-4RL` is the LQFP-64 4-channel option used as U14.
- V1/V2/V3/V4 pins 49/51/57/59 connect to `VOUT1..4`.
- CONVSTA pin 9 and CONVSTB pin 10 are tied together on `CONVST`.
- RD/SCLK pin 12 connects to ESP32 GPIO17 as `ADC_SCLK`.
- CS pin 13 connects to ESP32 GPIO18 as `ADC_CS`.
- DOUTA pin 24 connects to ESP32 GPIO21 as `ADC_MISO_A`.
- DOUTB pin 25 connects to ESP32 GPIO38 as `ADC_MISO_B`.
- BUSY pin 14 connects to ESP32 GPIO47 as `ADC_BUSY`.
- RESET pin 11 connects to ESP32 GPIO48 as `ADC_RESET`.
- AVCC pins 1, 37, 38, and 48 connect to +5 V with local 100 nF and 10 uF
  decoupling.
- VDRIVE pin 23 connects to +3V3 for ESP32 logic-level readback.
- PAR/SER/BYTE_SEL pin 6 is tied high for serial mode.
- DB15/BYTE_SEL pin 33 is tied low so the part is in serial mode, not parallel
  byte mode.
- STBY pin 7 and REF_SELECT pin 34 are tied high; the design uses the internal
  reference.
- RANGE pin 8 is tied low for the base AD7606 +/-5 V input range.
- OS0/OS1/OS2 pins 3/4/5 are tied low for no oversampling.
- REGCAP pins 36 and 39 each have a local 1 uF capacitor.
- REFIN/REFOUT pin 42 has a local 10 uF capacitor.
- REFCAPA pin 44 and REFCAPB pin 45 share a local 10 uF capacitor.
- AGND, REFGND, V1GND, V2GND, V3GND, and V4GND pins tie to board GND, including
  REFGND pins 43 and 46.
- FRSTDATA pin 15 is intentionally no-connect in the two-data-line serial
  readout.

Layout/release notes:

- Keep U14 analog input traces from `VOUT1..4` short and away from laser-current
  switching copper.
- Keep the AVCC/VDRIVE/REGCAP/reference capacitors next to U14.
- Firmware must verify CONVST timing, serial readback timing, scaling for the
  +/-5 V range strap, and whether oversampling straps should change before
  relying on bench readings.
- Firmware contract for the current bench board is encoded in
  `check_ad7606_interface_budget.py`: use two DOUT lines, read 32 SCLK edges per
  DOUT line for each 4-channel sample, keep nominal SCLK at or below 10 MHz
  until rail/timing margin is measured, default to 100 kSPS or lower, and treat
  data as 16-bit twos-complement with 152.58 uV/LSB for the +/-5 V range.
- `check_tia_readout_budget.py` asserts that the OPA380 guarded output window
  is inside the AD7606 +/-5 V range; the production limiter for the signal-PD
  path is the OPA380/TIA headroom and optical calibration, not the ADC full
  scale.
- On power-up, firmware must pulse RESET high for at least 50 ns and then wait
  at least 25 ns after RESET returns low before CONVST. CONVST low and high
  pulses must each be at least 25 ns.
- For read-after-conversion firmware, wait for BUSY to fall before asserting CS.
  For read-during-conversion firmware, do not clock data on the BUSY falling edge
  and keep the datasheet t6 guard to the next BUSY falling edge.
- `check_laser_controller_netlist.py` asserts the AD7606 package pinout, exact
  signal nets, rail membership, reference capacitors, and the intentional
  FRSTDATA no-connect.
- `check_ad7606_package_pcb.py` asserts the U14 schematic pin nets, the current
  PCB pad-net assignments, C51-C60 AVCC/VDRIVE/REGCAP/reference capacitor
  identities and pad nets, the intentional FRSTDATA unnetted PCB pad, and the
  installed KiCad `LQFP-64_10x10mm_P0.5mm` pad geometry.
- `check_ad7606_interface_budget.py` asserts the hardware straps and the default
  firmware timing/readback budget.
