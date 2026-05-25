"""GPIO laser output control for the Vivonics Pi bench.

Uses pigpio for hardware-timed PWM — same library the test scripts use,
so there are no conflicts when switching between bench_service and tests.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LaserGPIOConfig:
    red_pin: int = 23
    green_pin: int = 24
    active_high: bool = True
    pwm_frequency_hz: int = 10000


class LaserGPIOController:
    def __init__(self, config: LaserGPIOConfig | None = None) -> None:
        self.config = config or LaserGPIOConfig()
        self._pi = None
        self._opened = False

    def open(self) -> None:
        import pigpio
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Cannot connect to pigpiod")
        for pin in (self.config.red_pin, self.config.green_pin):
            self._pi.set_mode(pin, pigpio.OUTPUT)
            self._pi.set_PWM_frequency(pin, self.config.pwm_frequency_hz)
            self._pi.set_PWM_dutycycle(pin, 0)
        self._opened = True

    def show(self, *, red_level: int = 0, green_level: int = 0) -> None:
        if not self._opened or self._pi is None:
            raise RuntimeError("GPIO laser controller is not open")
        red_level = max(0, min(255, int(red_level)))
        green_level = max(0, min(255, int(green_level)))
        if not self.config.active_high:
            red_level = 255 - red_level
            green_level = 255 - green_level
        self._pi.set_PWM_dutycycle(self.config.red_pin, red_level)
        self._pi.set_PWM_dutycycle(self.config.green_pin, green_level)

    def off(self) -> None:
        if self._opened:
            self.show(red_level=0, green_level=0)

    def close(self) -> None:
        if self._opened and self._pi is not None:
            self.off()
            self._pi.stop()
        self._opened = False
        self._pi = None

    @property
    def driver_name(self) -> str:
        return f"gpio-bcm{self.config.red_pin}-red/bcm{self.config.green_pin}-green"
