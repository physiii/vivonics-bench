"""Projector light control via GPIO lasers on the Vivonics Pi bench."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from laser_gpio import LaserGPIOConfig, LaserGPIOController

if TYPE_CHECKING:
    from laser_controller_client import LaserControllerClient


def _opt_int_env(name: str) -> int | None:
    raw = os.environ.get(name)
    return int(raw) if raw not in (None, "") else None


@dataclass
class ProjectorConfig:
    red_laser_gpio: int = int(os.environ.get("VIVONICS_RED_LASER_GPIO", "15"))
    green_laser_gpio: int = int(os.environ.get("VIVONICS_GREEN_LASER_GPIO", "24"))
    infrared_laser_gpio: int | None = _opt_int_env("VIVONICS_INFRARED_LASER_GPIO")
    # 405 nm reversal channel. Unset => not wired (two-laser bench, unchanged).
    blue_laser_gpio: int | None = _opt_int_env("VIVONICS_BLUE_LASER_GPIO")
    laser_active_high: bool = os.environ.get("VIVONICS_LASER_ACTIVE_HIGH", "1") == "1"
    laser_pwm_hz: int = int(os.environ.get("VIVONICS_LASER_PWM_HZ", "10000"))
    light_driver: str = os.environ.get("VIVONICS_LIGHT_DRIVER", "gpio")


class Projector:
    def __init__(
        self,
        config: ProjectorConfig | None = None,
        controller: LaserControllerClient | None = None,
    ) -> None:
        self.config = config or ProjectorConfig()
        self._controller = controller
        self._controller_open = False
        self._laser: LaserGPIOController | None = None

    def open(self) -> None:
        if self.is_open:
            return
        if self.config.light_driver.lower() == "controller":
            if self._controller is None:
                raise RuntimeError("Laser controller driver selected but no controller client is available")
            self._controller_open = True
            self.off()
            return
        laser = LaserGPIOController(
            LaserGPIOConfig(
                red_pin=self.config.red_laser_gpio,
                green_pin=self.config.green_laser_gpio,
                infrared_pin=self.config.infrared_laser_gpio,
                blue_pin=self.config.blue_laser_gpio,
                active_high=self.config.laser_active_high,
                pwm_frequency_hz=self.config.laser_pwm_hz,
            )
        )
        laser.open()
        self._laser = laser
        self.off()

    def show_color(self, r: int, g: int, b: int, *, infrared_level: int = 0, settle: bool = True) -> None:
        if self._controller_open and self._controller is not None:
            self._controller.set_levels(red=r, green=g, infrared=infrared_level, blue=b)
            return
        if self._laser is None:
            raise RuntimeError("Projector not opened — call open() first")
        self._laser.show(red_level=r, green_level=g, infrared_level=infrared_level, blue_level=b)

    def show_red(self, level: int, *, settle: bool = True) -> None:
        self.show_color(level, 0, 0, settle=settle)

    def show_green(self, level: int, *, settle: bool = True) -> None:
        self.show_color(0, level, 0, settle=settle)

    def show_blue(self, level: int, *, settle: bool = True) -> None:
        self.show_color(0, 0, level, settle=settle)

    def show_infrared(self, level: int, *, settle: bool = True) -> None:
        self.show_color(0, 0, 0, infrared_level=level, settle=settle)

    def off(self) -> None:
        self.show_color(0, 0, 0, settle=False)

    def close(self) -> None:
        if self._controller_open and self._controller is not None:
            self._controller.off()
            self._controller_open = False
        if self._laser is not None:
            self._laser.close()
            self._laser = None

    @property
    def driver_name(self) -> str:
        if self._controller_open:
            return "laser-controller"
        if self._laser is not None:
            return self._laser.driver_name
        return "none"

    @property
    def is_open(self) -> bool:
        return self._controller_open or self._laser is not None
