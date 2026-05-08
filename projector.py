"""Projector pattern display on Pi HDMI output via pygame.

Generates solid-color fullscreen frames for the green-write / red-read
photocycle protocol. Uses SDL2/KMS or fbcon for headless framebuffer output.
Falls back to SDL dummy driver if no display is connected.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass


@dataclass
class ProjectorConfig:
    width: int = 1920
    height: int = 1080
    settle_time_s: float = 0.5


class Projector:
    def __init__(self, config: ProjectorConfig | None = None) -> None:
        self.config = config or ProjectorConfig()
        self._screen = None
        self._pygame = None
        self._driver = "none"

    def open(self) -> None:
        import pygame

        self._pygame = pygame

        for driver in ("KMSDRM", "kms", "fbcon", "wayland", "x11", "dummy"):
            os.environ["SDL_VIDEODRIVER"] = driver
            try:
                pygame.display.quit()
                pygame.display.init()
                if pygame.display.get_init():
                    self._driver = driver
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
        self.off()

    def show_color(self, r: int, g: int, b: int) -> None:
        if self._screen is None or self._pygame is None:
            raise RuntimeError("Projector not opened — call open() first")
        self._screen.fill((r, g, b))
        self._pygame.display.flip()
        time.sleep(self.config.settle_time_s)

    def show_red(self, level: int) -> None:
        self.show_color(level, 0, 0)

    def show_green(self, level: int) -> None:
        self.show_color(0, level, 0)

    def off(self) -> None:
        self.show_color(0, 0, 0)

    def close(self) -> None:
        if self._pygame is not None:
            self._pygame.quit()
            self._screen = None
            self._pygame = None

    @property
    def driver_name(self) -> str:
        return self._driver
