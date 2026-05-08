"""Optional I2C sensor support for the Vivonics Pi bench.

The IMX477 camera is still the primary C1/X1 detector. These sensors are
auxiliary readouts for intensity drift, crude spectral checks, and eventual
photodiode cross-checks.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SensorReading:
    name: str
    ok: bool
    channels: dict[str, float] = field(default_factory=dict)
    error: str | None = None
    timestamp_s: float = field(default_factory=time.time)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "channels": self.channels,
            "error": self.error,
            "timestamp_s": self.timestamp_s,
        }


class SensorSuite:
    """Read the ordered TSL2591 and AS7341 I2C modules when present."""

    def __init__(self, enable_tsl2591: bool = True, enable_as7341: bool = True) -> None:
        self._i2c = None
        self._tsl2591 = None
        self._as7341 = None
        self._init_errors: dict[str, str] = {}

        if enable_tsl2591 or enable_as7341:
            self._i2c = self._open_i2c()

        if self._i2c is not None and enable_tsl2591:
            self._tsl2591 = self._init_tsl2591()
        if self._i2c is not None and enable_as7341:
            self._as7341 = self._init_as7341()

    def availability(self) -> dict[str, Any]:
        return {
            "tsl2591": self._tsl2591 is not None,
            "as7341": self._as7341 is not None,
            "bpw34": "external_adc_required",
            "init_errors": self._init_errors,
        }

    def read_all(self) -> dict[str, Any]:
        readings: list[dict[str, Any]] = []
        readings.append(self.read_tsl2591().as_dict())
        readings.append(self.read_as7341().as_dict())
        readings.append(
            SensorReading(
                name="bpw34",
                ok=False,
                error="Raw BPW34 has no Pi analog input; use ESP32 ADC or an external ADC/TIA.",
            ).as_dict()
        )
        return {
            "availability": self.availability(),
            "readings": readings,
            "timestamp_s": time.time(),
        }

    def read_tsl2591(self) -> SensorReading:
        if self._tsl2591 is None:
            return SensorReading(
                name="tsl2591",
                ok=False,
                error=self._init_errors.get("tsl2591", "TSL2591 not initialized"),
            )
        try:
            channels = {
                "lux": _safe_float(getattr(self._tsl2591, "lux", None)),
                "visible": _safe_float(getattr(self._tsl2591, "visible", None)),
                "infrared": _safe_float(getattr(self._tsl2591, "infrared", None)),
                "full_spectrum": _safe_float(getattr(self._tsl2591, "full_spectrum", None)),
            }
            return SensorReading("tsl2591", True, channels)
        except Exception as exc:  # pragma: no cover - hardware dependent
            return SensorReading("tsl2591", False, error=str(exc))

    def read_as7341(self) -> SensorReading:
        if self._as7341 is None:
            return SensorReading(
                name="as7341",
                ok=False,
                error=self._init_errors.get("as7341", "AS7341 not initialized"),
            )
        channels: dict[str, float] = {}
        channel_attrs = {
            "415nm": "channel_415nm",
            "445nm": "channel_445nm",
            "480nm": "channel_480nm",
            "515nm": "channel_515nm",
            "555nm": "channel_555nm",
            "590nm": "channel_590nm",
            "630nm": "channel_630nm",
            "680nm": "channel_680nm",
            "clear": "channel_clear",
            "nir": "channel_nir",
        }
        try:
            for label, attr in channel_attrs.items():
                if hasattr(self._as7341, attr):
                    channels[label] = _safe_float(getattr(self._as7341, attr))
            return SensorReading("as7341", True, channels)
        except Exception as exc:  # pragma: no cover - hardware dependent
            return SensorReading("as7341", False, error=str(exc))

    def _open_i2c(self):
        try:
            import board
            import busio

            return busio.I2C(board.SCL, board.SDA)
        except Exception as exc:  # pragma: no cover - hardware dependent
            self._init_errors["i2c"] = str(exc)
            return None

    def _init_tsl2591(self):
        try:
            import adafruit_tsl2591

            return adafruit_tsl2591.TSL2591(self._i2c)
        except Exception as exc:  # pragma: no cover - hardware dependent
            self._init_errors["tsl2591"] = str(exc)
            return None

    def _init_as7341(self):
        try:
            import adafruit_as7341

            return adafruit_as7341.AS7341(self._i2c)
        except Exception as exc:  # pragma: no cover - hardware dependent
            self._init_errors["as7341"] = str(exc)
            return None


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
