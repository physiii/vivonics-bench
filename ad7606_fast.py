"""Fast AD7606 reader using /dev/gpiomem mmap — 10-30 kHz instead of 388 Hz.

Replaces RPi.GPIO bit-banging with direct GPIO register access via mmap.
One GPLEV0 read captures all 32 GPIO levels; bit extraction is pure Python.
Outputs use GPSET/GPCLR registers for atomic pin control.
"""

from __future__ import annotations

import mmap
import os
import struct
import time

# BCM2835/2711 GPIO register offsets (confirmed on Pi 4)
GPIO_BASE = 0x00
GPFSEL0 = 0x00   # Function select 0-9
GPFSEL1 = 0x04
GPFSEL2 = 0x08
GPSET0  = 0x1C   # Set pins 0-31
GPCLR0  = 0x28   # Clear pins 0-31
GPLEV0  = 0x34   # Level pins 0-31

# AD7606 pin mapping (BCM numbers) — must match bench/ad7606.py
DEFAULT_CV_PIN = 4
DEFAULT_RD_PIN = 20
DEFAULT_RST_PIN = 21
DEFAULT_BUSY_PIN = 26
DEFAULT_DATA_PINS = (
    17, 18, 27, 22,   # bits 0-3
    10, 9, 25, 11,    # bits 4-7
    8, 7, 5, 6,       # bits 8-11
    12, 13, 19, 16,   # bits 12-15
)

# Pre-compute bit masks for fast extraction
def _build_pin_mask(pins: tuple[int, ...]) -> list[tuple[int, int]]:
    """Return list of (gpio_bit_position, output_bit_position)."""
    return [(pin, bit_pos) for bit_pos, pin in enumerate(pins)]


class FastAD7606:
    """Ultra-fast AD7606 reader using /dev/gpiomem memory-mapped GPIO."""

    def __init__(
        self,
        cv_pin: int = DEFAULT_CV_PIN,
        rd_pin: int = DEFAULT_RD_PIN,
        rst_pin: int = DEFAULT_RST_PIN,
        busy_pin: int = DEFAULT_BUSY_PIN,
        data_pins: tuple[int, ...] = DEFAULT_DATA_PINS,
    ) -> None:
        self._cv = cv_pin
        self._rd = rd_pin
        self._rst = rst_pin
        self._busy = busy_pin
        self._data_pins = data_pins
        self._pin_map = _build_pin_mask(data_pins)

        self._fd: int | None = None
        self._map: mmap.mmap | None = None
        self._opened = False

    def open(self) -> None:
        self._fd = os.open("/dev/gpiomem", os.O_RDWR | os.O_SYNC)
        self._map = mmap.mmap(self._fd, 4096, mmap.MAP_SHARED,
                              mmap.PROT_READ | mmap.PROT_WRITE)

        # Configure pins as outputs (CV, RD, RST) or inputs (BUSY, data)
        for pin in self._data_pins + (self._busy,):
            self._set_pin_mode(pin, input_mode=True)
        for pin in (self._cv, self._rd, self._rst):
            self._set_pin_mode(pin, input_mode=False)

        # Initial state: CV=HIGH, RD=HIGH, RST=LOW
        self._set_pin(self._cv, 1)
        self._set_pin(self._rd, 1)
        self._set_pin(self._rst, 0)

        self._opened = True
        self.reset()

    def reset(self) -> None:
        self._set_pin(self._rst, 1)
        self._spin_us(1)
        self._set_pin(self._rst, 0)
        self._spin_us(1)

    def read_frame(self) -> list[int]:
        """Read all 8 ADC channels in one conversion cycle. Returns raw 16-bit values."""
        if not self._opened:
            raise RuntimeError("FastAD7606 not open")

        # CONVST pulse: HIGH → LOW → HIGH
        self._set_pin(self._cv, 0)
        self._spin_us(1)
        self._set_pin(self._cv, 1)

        # Wait for BUSY to go low
        deadline = time.monotonic() + 0.02
        while self._read_pin(self._busy):
            if time.monotonic() > deadline:
                raise TimeoutError("AD7606 conversion timed out")

        # Read 8 channels via RD pin
        values = []
        for _ in range(8):
            self._set_pin(self._rd, 0)   # RD low
            self._spin_us(0)             # minimal delay
            values.append(self._read_parallel_word())
            self._set_pin(self._rd, 1)   # RD high
            self._spin_us(0)

        return values

    def close(self) -> None:
        if self._map is not None:
            self._map.close()
            self._map = None
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        self._opened = False

    # ── internal helpers ──

    def _reg_write(self, offset: int, value: int) -> None:
        assert self._map is not None
        self._map[offset:offset + 4] = struct.pack("<I", value)

    def _reg_read(self, offset: int) -> int:
        assert self._map is not None
        return struct.unpack_from("<I", self._map, offset)[0]

    def _set_pin_mode(self, pin: int, *, input_mode: bool) -> None:
        """Set GPIO pin mode (input or output)."""
        reg = GPFSEL0 + (pin // 10) * 4
        shift = (pin % 10) * 3
        mask = 0b111 << shift
        val = self._reg_read(reg) & ~mask
        if not input_mode:
            val |= (0b001 << shift)  # output
        self._reg_write(reg, val)

    def _set_pin(self, pin: int, level: int) -> None:
        if level:
            self._reg_write(GPSET0, 1 << pin)
        else:
            self._reg_write(GPCLR0, 1 << pin)

    def _read_pin(self, pin: int) -> bool:
        return bool(self._reg_read(GPLEV0) & (1 << pin))

    def _read_parallel_word(self) -> int:
        """Read 16-bit word from data pins in one pass."""
        gpio_levels = self._reg_read(GPLEV0)
        value = 0
        for gpio_bit, out_bit in self._pin_map:
            if gpio_levels & (1 << gpio_bit):
                value |= (1 << out_bit)
        return value

    @staticmethod
    def _spin_us(us: float) -> None:
        if us <= 0:
            return
        # Busy-wait for sub-millisecond delays
        end = time.perf_counter() + us / 1_000_000
        while time.perf_counter() < end:
            pass


def to_signed_16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value
