"""GPIO laser output control for the Vivonics Pi bench."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LaserGPIOConfig:
    red_pin: int = 23
    green_pin: int = 24
    active_high: bool = True
    pwm_frequency_hz: int = 1000


class LaserGPIOController:
    def __init__(self, config: LaserGPIOConfig | None = None) -> None:
        self.config = config or LaserGPIOConfig()
        self._gpio = None
        self._red_pwm = None
        self._green_pwm = None
        self._red_pwm_running = False
        self._green_pwm_running = False
        self._opened = False

    def open(self) -> None:
        try:
            import RPi.GPIO as GPIO
        except ImportError as e:
            raise RuntimeError("RPi.GPIO is required for GPIO laser control") from e

        self._gpio = GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.config.red_pin, GPIO.OUT, initial=self._inactive_level)
        GPIO.setup(self.config.green_pin, GPIO.OUT, initial=self._inactive_level)
        self._red_pwm = GPIO.PWM(self.config.red_pin, self.config.pwm_frequency_hz)
        self._green_pwm = GPIO.PWM(self.config.green_pin, self.config.pwm_frequency_hz)
        self._red_pwm_running = False
        self._green_pwm_running = False
        self._opened = True
        self.off()

    def show(self, *, red_level: int = 0, green_level: int = 0) -> None:
        if not self._opened or self._gpio is None:
            raise RuntimeError("GPIO laser controller is not open")
        self._set_red_level(red_level)
        self._set_green_level(green_level)

    def off(self) -> None:
        if self._opened:
            self.show(red_level=0, green_level=0)

    def close(self) -> None:
        if self._opened and self._gpio is not None:
            self.off()
            if self._red_pwm is not None:
                self._red_pwm.stop()
            if self._green_pwm is not None:
                self._green_pwm.stop()
            self._gpio.setup(self.config.red_pin, self._gpio.OUT, initial=self._inactive_level)
            self._gpio.setup(self.config.green_pin, self._gpio.OUT, initial=self._inactive_level)
            self._gpio.cleanup((self.config.red_pin, self.config.green_pin))
        self._opened = False
        self._gpio = None
        self._red_pwm = None
        self._green_pwm = None
        self._red_pwm_running = False
        self._green_pwm_running = False

    @property
    def driver_name(self) -> str:
        return f"gpio-bcm{self.config.red_pin}-red/bcm{self.config.green_pin}-green"

    @property
    def _active_level(self) -> int:
        return 1 if self.config.active_high else 0

    @property
    def _inactive_level(self) -> int:
        return 0 if self.config.active_high else 1

    def _duty_cycle(self, level: int) -> float:
        level = max(0, min(255, int(level)))
        duty = 100.0 * level / 255.0
        return duty if self.config.active_high else 100.0 - duty

    def _set_red_level(self, level: int) -> None:
        self._red_pwm_running = self._set_channel_level(
            self._red_pwm,
            self.config.red_pin,
            level,
            self._red_pwm_running,
        )

    def _set_green_level(self, level: int) -> None:
        self._green_pwm_running = self._set_channel_level(
            self._green_pwm,
            self.config.green_pin,
            level,
            self._green_pwm_running,
        )

    def _set_channel_level(self, pwm, pin: int, level: int, running: bool) -> bool:
        level = max(0, min(255, int(level)))
        if pwm is None or self._gpio is None:
            raise RuntimeError("GPIO laser controller is not open")

        if level <= 0:
            if running:
                pwm.stop()
            self._gpio.setup(pin, self._gpio.OUT, initial=self._inactive_level)
            self._gpio.output(pin, self._inactive_level)
            return False

        if level >= 255:
            if running:
                pwm.stop()
            self._gpio.setup(pin, self._gpio.OUT, initial=self._active_level)
            self._gpio.output(pin, self._active_level)
            return False

        duty = self._duty_cycle(level)
        if running:
            pwm.ChangeDutyCycle(duty)
        else:
            pwm.start(duty)
        return True
