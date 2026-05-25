"""Projector light control via GPIO lasers on the Vivonics Pi bench.

Controls red (GPIO 23) and green (GPIO 24) laser modules through pigpio PWM.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

from laser_gpio import LaserGPIOConfig, LaserGPIOController


@dataclass
class ProjectorConfig:
    red_laser_gpio: int = int(os.environ.get("VIVONICS_RED_LASER_GPIO", "23"))
    green_laser_gpio: int = int(os.environ.get("VIVONICS_GREEN_LASER_GPIO", "24"))
    laser_active_high: bool = os.environ.get("VIVONICS_LASER_ACTIVE_HIGH", "1") == "1"
    light_driver: str = "gpio"


class Projector:
    def __init__(self, config: ProjectorConfig | None = None) -> None:
        self.config = config or ProjectorConfig()
        self._laser: LaserGPIOController | None = None

    def open(self) -> None:
        if self.is_open:
            return
        laser = LaserGPIOController(
            LaserGPIOConfig(
                red_pin=self.config.red_laser_gpio,
                green_pin=self.config.green_laser_gpio,
                active_high=self.config.laser_active_high,
            )
        )
        laser.open()
        self._laser = laser
        self.off()

    def show_color(self, r: int, g: int, b: int, *, settle: bool = True) -> None:
        if self._laser is None:
            raise RuntimeError("Projector not opened — call open() first")
        self._laser.show(red_level=r, green_level=g)

    def show_red(self, level: int, *, settle: bool = True) -> None:
        self.show_color(level, 0, 0, settle=settle)

    def show_green(self, level: int, *, settle: bool = True) -> None:
        self.show_color(0, level, 0, settle=settle)

    def off(self) -> None:
        self.show_color(0, 0, 0, settle=False)

    def close(self) -> None:
        if self._laser is not None:
            self._laser.close()
            self._laser = None

    @property
    def driver_name(self) -> str:
        if self._laser is not None:
            return self._laser.driver_name
        return "none"

    @property
    def is_open(self) -> bool:
        return self._laser is not None
