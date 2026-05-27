"""GPIO laser output control for the Vivonics Pi bench."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LaserGPIOConfig:
    red_pin: int = 23
    green_pin: int = 24
    active_high: bool = True
    pwm_frequency_hz: int = int(os.environ.get("VIVONICS_LASER_PWM_HZ", "10000"))


class LaserGPIOController:
    def __init__(self, config: LaserGPIOConfig | None = None) -> None:
        self.config = config or LaserGPIOConfig()
        self._pi = None
        self._gpio = None
        self._red_pwm = None
        self._green_pwm = None
        self._backend = "none"
        self._opened = False

    def open(self) -> None:
        try:
            self._open_pigpio()
        except Exception:
            self._open_rpi_gpio()
        self._opened = True

    def _open_pigpio(self) -> None:
        import pigpio

        pi = pigpio.pi()
        if not pi.connected:
            pi.stop()
            raise RuntimeError("Cannot connect to pigpiod")
        for pin in (self.config.red_pin, self.config.green_pin):
            pi.set_mode(pin, pigpio.OUTPUT)
            pi.set_PWM_frequency(pin, self.config.pwm_frequency_hz)
            pi.set_PWM_dutycycle(pin, self._pigpio_duty(0))
        self._pi = pi
        self._backend = "pigpio"

    def _open_rpi_gpio(self) -> None:
        import RPi.GPIO as GPIO

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        initial = GPIO.HIGH if not self.config.active_high else GPIO.LOW
        for pin in (self.config.red_pin, self.config.green_pin):
            GPIO.setup(pin, GPIO.OUT, initial=initial)
        self._red_pwm = GPIO.PWM(self.config.red_pin, self.config.pwm_frequency_hz)
        self._green_pwm = GPIO.PWM(self.config.green_pin, self.config.pwm_frequency_hz)
        self._red_pwm.start(self._rpi_gpio_duty(0))
        self._green_pwm.start(self._rpi_gpio_duty(0))
        self._gpio = GPIO
        self._backend = "rpi-gpio"

    def show(self, *, red_level: int = 0, green_level: int = 0) -> None:
        if not self._opened:
            raise RuntimeError("GPIO laser controller is not open")
        red_level = max(0, min(255, int(red_level)))
        green_level = max(0, min(255, int(green_level)))
        if self._backend == "pigpio" and self._pi is not None:
            self._pi.set_PWM_dutycycle(self.config.red_pin, self._pigpio_duty(red_level))
            self._pi.set_PWM_dutycycle(self.config.green_pin, self._pigpio_duty(green_level))
            return
        if self._backend == "rpi-gpio" and self._red_pwm is not None and self._green_pwm is not None:
            self._red_pwm.ChangeDutyCycle(self._rpi_gpio_duty(red_level))
            self._green_pwm.ChangeDutyCycle(self._rpi_gpio_duty(green_level))
            return
        raise RuntimeError("GPIO laser controller backend is not initialized")

    def off(self) -> None:
        if self._opened:
            self.show(red_level=0, green_level=0)

    def close(self) -> None:
        if self._opened:
            self.off()
        if self._pi is not None:
            self._pi.stop()
        if self._red_pwm is not None:
            self._red_pwm.stop()
        if self._green_pwm is not None:
            self._green_pwm.stop()
        if self._gpio is not None:
            self._gpio.cleanup((self.config.red_pin, self.config.green_pin))
        self._opened = False
        self._pi = None
        self._gpio = None
        self._red_pwm = None
        self._green_pwm = None
        self._backend = "none"

    @property
    def driver_name(self) -> str:
        return f"gpio-{self._backend}-bcm{self.config.red_pin}-red/bcm{self.config.green_pin}-green"

    def _pigpio_duty(self, level: int) -> int:
        return level if self.config.active_high else 255 - level

    def _rpi_gpio_duty(self, level: int) -> float:
        duty = 100.0 * level / 255.0
        return duty if self.config.active_high else 100.0 - duty
