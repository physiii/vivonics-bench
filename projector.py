"""Projector pattern display on Pi HDMI output via pygame.

Generates solid-color fullscreen frames for the green-write / red-read
photocycle protocol. Uses SDL2/KMS or fbcon for headless framebuffer output.
Falls back to SDL dummy driver if no display is connected.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

from laser_gpio import LaserGPIOConfig, LaserGPIOController


@dataclass
class ProjectorConfig:
    width: int = 1920
    height: int = 1080
    settle_time_s: float = 0.5
    light_driver: str = os.environ.get("VIVONICS_LIGHT_DRIVER", "hdmi")
    red_laser_gpio: int = int(os.environ.get("VIVONICS_RED_LASER_GPIO", "23"))
    green_laser_gpio: int = int(os.environ.get("VIVONICS_GREEN_LASER_GPIO", "24"))
    laser_active_high: bool = os.environ.get("VIVONICS_LASER_ACTIVE_HIGH", "1") == "1"


class Projector:
    def __init__(self, config: ProjectorConfig | None = None) -> None:
        self.config = config or ProjectorConfig()
        self._screen = None
        self._pygame = None
        self._driver = "none"
        self._laser: LaserGPIOController | None = None

    def open(self) -> None:
        if self.is_open:
            return

        modes = _parse_light_driver(self.config.light_driver)
        drivers: list[str] = []

        if "gpio" in modes:
            laser = LaserGPIOController(
                LaserGPIOConfig(
                    red_pin=self.config.red_laser_gpio,
                    green_pin=self.config.green_laser_gpio,
                    active_high=self.config.laser_active_high,
                )
            )
            laser.open()
            self._laser = laser
            drivers.append(self._laser.driver_name)

        if "hdmi" in modes:
            try:
                self._open_pygame_display()
                drivers.append(self._driver)
            except Exception:
                if drivers:
                    pass
                else:
                    raise

        if not drivers:
            raise RuntimeError("No light driver configured")

        self._driver = "+".join(drivers)
        self.off()

    def _open_pygame_display(self) -> None:
        import pygame

        self._pygame = pygame

        for driver in ("KMSDRM", "kms", "fbcon", "wayland", "x11", "dummy"):
            os.environ["SDL_VIDEODRIVER"] = driver
            try:
                pygame.display.quit()
                pygame.display.init()
                if pygame.display.get_init():
                    self._driver = f"hdmi-{driver}"
                    break
            except Exception:
                continue

        if not pygame.display.get_init():
            raise RuntimeError("No SDL video driver could initialize")

        pygame.init()
        self._screen = pygame.display.set_mode(
            (self.config.width, self.config.height),
            pygame.FULLSCREEN | pygame.NOFRAME,
        )

    def show_color(self, r: int, g: int, b: int, *, settle: bool = True) -> None:
        if self._screen is None and self._laser is None:
            raise RuntimeError("Projector not opened — call open() first")
        if self._laser is not None:
            self._laser.show(red_level=r, green_level=g)
        if self._screen is not None and self._pygame is not None:
            try:
                self._screen.fill((r, g, b))
                self._pygame.display.flip()
            except Exception:
                # Keep GPIO laser control alive if the Pi display stack loses
                # its EGL/KMS context.
                try:
                    self._pygame.display.quit()
                except Exception:
                    pass
                self._screen = None
                self._pygame = None
        if settle and self.config.settle_time_s > 0:
            time.sleep(self.config.settle_time_s)

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
        if self._pygame is not None:
            self._pygame.quit()
            self._screen = None
            self._pygame = None

    @property
    def driver_name(self) -> str:
        return self._driver

    @property
    def is_open(self) -> bool:
        return self._laser is not None or self._screen is not None


def _parse_light_driver(value: str) -> set[str]:
    modes = {part.strip().lower() for part in value.replace("+", ",").split(",")}
    modes.discard("")
    if "both" in modes:
        modes.remove("both")
        modes.update({"hdmi", "gpio"})
    return modes
