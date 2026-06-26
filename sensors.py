"""Optional I2C sensor support for the Vivonics Pi bench.

The IMX477 camera is still the primary C1/X1 detector. These sensors are
auxiliary readouts for intensity drift, crude spectral checks, and eventual
photodiode cross-checks.
"""
from __future__ import annotations

import time
import os
from dataclasses import dataclass, field
from math import sqrt
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

    def __init__(
        self,
        enable_tsl2591: bool = True,
        enable_as7341: bool = True,
        enable_ad7606: bool | None = None,
    ) -> None:
        self._i2c = None
        self._tsl2591 = None
        self._as7341 = None
        self._ad7606 = None
        self._ad7606_avg_samples = max(1, _env_int("VIVONICS_AD7606_AVG_SAMPLES", 1))
        self._init_errors: dict[str, str] = {}
        if enable_ad7606 is None:
            enable_ad7606 = _env_bool("VIVONICS_AD7606_ENABLE", False)

        if enable_tsl2591 or enable_as7341:
            self._i2c = self._open_i2c()

        if self._i2c is not None and enable_tsl2591:
            self._tsl2591 = self._init_tsl2591()
        if self._i2c is not None and enable_as7341:
            self._as7341 = self._init_as7341()
        if enable_ad7606:
            self._ad7606 = self._init_ad7606()

    def availability(self) -> dict[str, Any]:
        return {
            "tsl2591": self._tsl2591 is not None,
            "as7341": self._as7341 is not None,
            "ad7606": self._ad7606 is not None,
            "ad7606_avg_samples": self._ad7606_avg_samples,
            "bpw34": "ad7606_ch1" if self._ad7606 is not None else "external_adc_required",
            "init_errors": self._init_errors,
        }

    def read_all(self) -> dict[str, Any]:
        readings: list[dict[str, Any]] = []
        readings.append(self.read_tsl2591().as_dict())
        readings.append(self.read_as7341().as_dict())
        readings.append(
            SensorReading(
                name="bpw34",
                ok=self._ad7606 is not None,
                channels={"ad7606_channel": 1} if self._ad7606 is not None else {},
                error=None if self._ad7606 is not None else "Raw BPW34 has no Pi analog input; use ESP32 ADC or an external ADC/TIA.",
            ).as_dict()
        )
        readings.append(self.read_ad7606().as_dict())
        return {
            "availability": self.availability(),
            "readings": readings,
            "timestamp_s": time.time(),
        }

    def close(self) -> None:
        if self._ad7606 is not None:
            self._ad7606.close()

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

    def read_ad7606(self) -> SensorReading:
        if self._ad7606 is None:
            return SensorReading(
                name="ad7606",
                ok=False,
                error=self._init_errors.get("ad7606", "AD7606 not enabled"),
            )
        try:
            from ad7606 import to_signed_16

            started = time.perf_counter()
            frames = [self._ad7606.read_frame()]
            for _ in range(self._ad7606_avg_samples - 1):
                frames.append(self._ad7606.read_frame())
            elapsed_s = max(time.perf_counter() - started, 1e-9)
            channels: dict[str, float] = {}
            frame_count = len(frames)
            channel_count = len(frames[0])
            for index in range(channel_count):
                raw_values = [frame[index] for frame in frames]
                signed_values = [to_signed_16(value) for value in raw_values]
                mean_value = sum(raw_values) / frame_count
                signed_mean = sum(signed_values) / frame_count
                variance = (
                    sum((value - mean_value) ** 2 for value in raw_values) / frame_count
                    if frame_count > 1
                    else 0.0
                )
                ch = index + 1
                channels[f"ch{ch}"] = float(mean_value)
                channels[f"ch{ch}_signed"] = float(signed_mean)
                channels[f"ch{ch}_last"] = float(raw_values[-1])
                channels[f"ch{ch}_min"] = float(min(raw_values))
                channels[f"ch{ch}_max"] = float(max(raw_values))
                channels[f"ch{ch}_std"] = float(sqrt(variance))
            channels["samples"] = float(frame_count)
            channels["sample_hz"] = float(frame_count / elapsed_s)
            channels["window_ms"] = float(elapsed_s * 1000.0)
            return SensorReading("ad7606", True, channels)
        except Exception as exc:  # pragma: no cover - hardware dependent
            return SensorReading("ad7606", False, error=str(exc))

    def read_ad7606_frame(self) -> list[int]:
        if self._ad7606 is None:
            raise RuntimeError(self._init_errors.get("ad7606", "AD7606 not enabled"))
        return self._ad7606.read_frame()

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

    def _init_ad7606(self):
        try:
            from ad7606_fast import FastAD7606

            reader = FastAD7606()
            reader.open()
            return reader
        except Exception as exc:  # pragma: no cover - hardware dependent
            self._init_errors["ad7606"] = str(exc)
            return None


def _safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
