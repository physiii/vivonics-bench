"""GPIO laser output control for the Vivonics Pi bench.

Channels: red (BCM 15) and green (BCM 24) are the active read/write lasers on
the reactor bench. Optional infrared (BCM 23) and blue (BCM 14) channels are
available for the reactor bench. Avoid the AD7606 data bus
(17,18,27,22,10,9,25,11,8,7,5,6,12,13,19,16), its control pins (4,20,21,26),
the I2C sensor pins (2,3), and the existing lasers. BCM 14/15 are UART pins, so
keep the serial console off when they are used as laser enables.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LaserGPIOConfig:
    red_pin: int = 15
    green_pin: int = 24
    infrared_pin: int | None = 23
    blue_pin: int | None = None  # 405 nm reversal channel; None = not wired
    active_high: bool = True
    pwm_frequency_hz: int = int(os.environ.get("VIVONICS_LASER_PWM_HZ", "10000"))


class LaserGPIOController:
    def __init__(self, config: LaserGPIOConfig | None = None) -> None:
        self.config = config or LaserGPIOConfig()
        self._pi = None
        self._gpio = None
        self._red_pwm = None
        self._green_pwm = None
        self._infrared_pwm = None
        self._blue_pwm = None
        self._backend = "none"
        self._opened = False

    def _pins(self) -> tuple[int, ...]:
        pins = [self.config.red_pin, self.config.green_pin]
        if self.config.infrared_pin is not None:
            pins.append(self.config.infrared_pin)
        if self.config.blue_pin is not None:
            pins.append(self.config.blue_pin)
        return tuple(pins)

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
        for pin in self._pins():
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
        for pin in self._pins():
            GPIO.setup(pin, GPIO.OUT, initial=initial)
        self._red_pwm = GPIO.PWM(self.config.red_pin, self.config.pwm_frequency_hz)
        self._green_pwm = GPIO.PWM(self.config.green_pin, self.config.pwm_frequency_hz)
        self._red_pwm.start(self._rpi_gpio_duty(0))
        self._green_pwm.start(self._rpi_gpio_duty(0))
        if self.config.infrared_pin is not None:
            self._infrared_pwm = GPIO.PWM(self.config.infrared_pin, self.config.pwm_frequency_hz)
            self._infrared_pwm.start(self._rpi_gpio_duty(0))
        if self.config.blue_pin is not None:
            self._blue_pwm = GPIO.PWM(self.config.blue_pin, self.config.pwm_frequency_hz)
            self._blue_pwm.start(self._rpi_gpio_duty(0))
        self._gpio = GPIO
        self._backend = "rpi-gpio"

    def show(
        self,
        *,
        red_level: int = 0,
        green_level: int = 0,
        infrared_level: int = 0,
        blue_level: int = 0,
    ) -> None:
        if not self._opened:
            raise RuntimeError("GPIO laser controller is not open")
        red_level = max(0, min(255, int(red_level)))
        green_level = max(0, min(255, int(green_level)))
        infrared_level = max(0, min(255, int(infrared_level)))
        blue_level = max(0, min(255, int(blue_level)))
        if self._backend == "pigpio" and self._pi is not None:
            self._pi.set_PWM_dutycycle(self.config.red_pin, self._pigpio_duty(red_level))
            self._pi.set_PWM_dutycycle(self.config.green_pin, self._pigpio_duty(green_level))
            if self.config.infrared_pin is not None:
                self._pi.set_PWM_dutycycle(self.config.infrared_pin, self._pigpio_duty(infrared_level))
            if self.config.blue_pin is not None:
                self._pi.set_PWM_dutycycle(self.config.blue_pin, self._pigpio_duty(blue_level))
            return
        if self._backend == "rpi-gpio" and self._red_pwm is not None and self._green_pwm is not None:
            self._red_pwm.ChangeDutyCycle(self._rpi_gpio_duty(red_level))
            self._green_pwm.ChangeDutyCycle(self._rpi_gpio_duty(green_level))
            if self._infrared_pwm is not None:
                self._infrared_pwm.ChangeDutyCycle(self._rpi_gpio_duty(infrared_level))
            if self._blue_pwm is not None:
                self._blue_pwm.ChangeDutyCycle(self._rpi_gpio_duty(blue_level))
            return
        raise RuntimeError("GPIO laser controller backend is not initialized")

    def off(self) -> None:
        if self._opened:
            self.show(red_level=0, green_level=0, infrared_level=0, blue_level=0)

    def close(self) -> None:
        if self._opened:
            self.off()
        if self._pi is not None:
            self._pi.stop()
        if self._red_pwm is not None:
            self._red_pwm.stop()
        if self._green_pwm is not None:
            self._green_pwm.stop()
        if self._infrared_pwm is not None:
            self._infrared_pwm.stop()
        if self._blue_pwm is not None:
            self._blue_pwm.stop()
        if self._gpio is not None:
            self._gpio.cleanup(self._pins())
        self._opened = False
        self._pi = None
        self._gpio = None
        self._red_pwm = None
        self._green_pwm = None
        self._infrared_pwm = None
        self._blue_pwm = None
        self._backend = "none"

    @property
    def driver_name(self) -> str:
        name = f"gpio-{self._backend}-bcm{self.config.red_pin}-red/bcm{self.config.green_pin}-green"
        if self.config.infrared_pin is not None:
            name += f"/bcm{self.config.infrared_pin}-infrared"
        if self.config.blue_pin is not None:
            name += f"/bcm{self.config.blue_pin}-blue405"
        return name

    def _pigpio_duty(self, level: int) -> int:
        return level if self.config.active_high else 255 - level

    def _rpi_gpio_duty(self, level: int) -> float:
        duty = 100.0 * level / 255.0
        return duty if self.config.active_high else 100.0 - duty
