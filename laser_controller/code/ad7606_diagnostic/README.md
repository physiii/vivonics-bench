# AD7606-4 isolated hardware diagnostic

This temporary first-article image distinguishes a missing AD7606-4 BUSY pulse
from an ESP32 polling miss and tests serial readback without trusting BUSY. It
does not provide a laser arm path: GPIO10, GPIO11, GPIO12, and GPIO16 are forced
low continuously.

The image performs three bounded phases with the ESP32 internal pulls floating,
up, and down on BUSY/DOUTA/DOUTB. Each phase:

- applies a 10 us active-high RESET followed by 100 us recovery;
- generates eight 10 us-low CONVST pulses;
- counts BUSY transitions using a GPIO any-edge interrupt;
- samples BUSY immediately, 1 us, and 3 us after CONVST rises;
- waits 20 us, then reads two 16-bit channels from each DOUT line using 32 slow
  bit-banged serial clocks.

It then generates a conversion every 100 ms indefinitely for scope triggering.

Build on an ESP-IDF host:

```bash
source "$HOME/esp/esp-idf/export.sh"
cd firmware/ad7606_diagnostic
idf.py set-target esp32s3
idf.py build
```

Flash on the office bench host:

```bash
export ESPTOOL_CFGFILE="$PWD/esptool.cfg"
idf.py -p /dev/ttyUSB0 flash
```

Interpretation:

- BUSY edges prove conversion signaling even if polling missed it.
- BUSY following the ESP32 pull-up indicates an undriven/open BUSY connection.
- Read data invariant across DOUT pull states indicates the ADC is driving it.
- Read data following pull state indicates DOUT is undriven, narrowing the fault
  to ADC power/configuration, CS/SCLK connectivity, package soldering, or U14.
