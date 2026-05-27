"""AD7606 parallel-bus reader for the reactor BPW34 bench."""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class AD7606Config:
    cv_pin: int = 4
    rd_pin: int = 20
    rst_pin: int = 21
    busy_pin: int = 26
    data_pins: tuple[int, ...] = (
        17, 18, 27, 22,
        10, 9, 25, 11,
        8, 7, 5, 6,
        12, 13, 19, 16,
    )
    conversion_timeout_s: float = 0.02

    @classmethod
    def from_env(cls) -> "AD7606Config":
        return cls(
            cv_pin=_env_int("VIVONICS_AD7606_CV_GPIO", 4),
            rd_pin=_env_int("VIVONICS_AD7606_RD_GPIO", 20),
            rst_pin=_env_int("VIVONICS_AD7606_RST_GPIO", 21),
            busy_pin=_env_int("VIVONICS_AD7606_BUSY_GPIO", 26),
            data_pins=_env_pin_tuple(
                "VIVONICS_AD7606_DATA_GPIOS",
                "17,18,27,22,10,9,25,11,8,7,5,6,12,13,19,16",
            ),
            conversion_timeout_s=_env_float("VIVONICS_AD7606_TIMEOUT_S", 0.02),
        )


class AD7606Reader:
    """Read eight 16-bit samples from an AD7606 module wired in parallel mode."""

    def __init__(self, config: AD7606Config | None = None) -> None:
        self.config = config or AD7606Config.from_env()
        self._gpio = None
        self._lock = threading.Lock()
        self._opened = False

    def open(self) -> None:
        if len(self.config.data_pins) != 16:
            raise RuntimeError("AD7606 requires exactly 16 data GPIOs")

        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in self.config.data_pins:
            GPIO.setup(pin, GPIO.IN)
        GPIO.setup(self.config.busy_pin, GPIO.IN)
        GPIO.setup(self.config.cv_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.config.rd_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.config.rst_pin, GPIO.OUT, initial=GPIO.LOW)

        self._gpio = GPIO
        self._opened = True
        self.reset()

    def reset(self) -> None:
        gpio = self._require_gpio()
        gpio.output(self.config.rd_pin, gpio.HIGH)
        gpio.output(self.config.cv_pin, gpio.HIGH)
        gpio.output(self.config.rst_pin, gpio.HIGH)
        time.sleep(0.00001)
        gpio.output(self.config.rst_pin, gpio.LOW)
        time.sleep(0.00001)

    def read_frame(self) -> list[int]:
        gpio = self._require_gpio()
        with self._lock:
            gpio.output(self.config.cv_pin, gpio.HIGH)
            time.sleep(0.000002)
            gpio.output(self.config.cv_pin, gpio.LOW)
            time.sleep(0.000005)
            gpio.output(self.config.cv_pin, gpio.HIGH)

            deadline = time.monotonic() + self.config.conversion_timeout_s
            while gpio.input(self.config.busy_pin):
                if time.monotonic() > deadline:
                    raise TimeoutError("AD7606 conversion timed out waiting for BUSY low")
                time.sleep(0.00001)

            values = []
            for _ in range(8):
                gpio.output(self.config.rd_pin, gpio.LOW)
                time.sleep(0.000002)
                values.append(self._read_parallel_word())
                gpio.output(self.config.rd_pin, gpio.HIGH)
                time.sleep(0.000002)
            return values

    def close(self) -> None:
        if not self._opened:
            return
        gpio = self._gpio
        if gpio is not None:
            gpio.output(self.config.rd_pin, gpio.HIGH)
            gpio.output(self.config.cv_pin, gpio.HIGH)
            gpio.cleanup((*self.config.data_pins, self.config.busy_pin, self.config.cv_pin, self.config.rd_pin, self.config.rst_pin))
        self._gpio = None
        self._opened = False

    def _read_parallel_word(self) -> int:
        gpio = self._require_gpio()
        value = 0
        for bit, pin in enumerate(self.config.data_pins):
            if gpio.input(pin):
                value |= 1 << bit
        return value

    def _require_gpio(self):
        if self._gpio is None or not self._opened:
            raise RuntimeError("AD7606 reader is not open")
        return self._gpio


def to_signed_16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_pin_tuple(name: str, default: str) -> tuple[int, ...]:
    raw = os.environ.get(name, default)
    try:
        return tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    except ValueError:
        return tuple(int(part.strip()) for part in default.split(",") if part.strip())
