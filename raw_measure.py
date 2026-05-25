"""Raw 10-bit Bayer measurement for pulse cycles.

Provides RawPulseMeasurer which uses Picamera2 with raw CSI2P stream
and FastRedReader to compute deltaRed from the actual red Bayer pixels
at camera rate (~122fps), bypassing the 8-bit ISP/WebRTC path entirely.

This achieves 11+ bit precision (SNR>2000:1) vs ~6-7 bits through WebRTC.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

SENSOR_W = 1332
SENSOR_H = 990


def unpack_10bit_csi2p(packed: np.ndarray) -> np.ndarray:
    """Unpack CSI-2 10-bit packed format to uint16."""
    h = packed.shape[0]
    n_groups = SENSOR_W // 4
    stride = n_groups * 5
    data = packed[:, :stride].reshape(h, n_groups, 5)
    b0 = data[:, :, 0].astype(np.uint16)
    b1 = data[:, :, 1].astype(np.uint16)
    b2 = data[:, :, 2].astype(np.uint16)
    b3 = data[:, :, 3].astype(np.uint16)
    b4 = data[:, :, 4].astype(np.uint16)
    p0 = (b0 << 2) | ((b4 >> 0) & 0x03)
    p1 = (b1 << 2) | ((b4 >> 2) & 0x03)
    p2 = (b2 << 2) | ((b4 >> 4) & 0x03)
    p3 = (b3 << 2) | ((b4 >> 6) & 0x03)
    out = np.empty((h, n_groups * 4), dtype=np.uint16)
    out[:, 0::4] = p0
    out[:, 1::4] = p1
    out[:, 2::4] = p2
    out[:, 3::4] = p3
    return out[:, :SENSOR_W]


class FastRedReader:
    """Pre-computes packed byte positions for masked red Bayer pixels.

    Reads only the ~500-1400 masked red pixels directly from the packed
    raw buffer using pre-computed byte offsets (~1-2ms per frame on Pi 4).
    """

    def __init__(self, rr: int, rc: int, mask: np.ndarray) -> None:
        sub_rows, sub_cols = np.where(mask)
        full_rows = sub_rows * 2 + rr
        full_cols = sub_cols * 2 + rc
        groups = full_cols // 4
        positions = full_cols % 4
        n_groups = SENSOR_W // 4

        self.row_idx = full_rows.astype(np.intp)
        self.hi_offset = (groups * 5 + positions).astype(np.intp)
        self.lsb_offset = (groups * 5 + 4).astype(np.intp)
        self.lsb_shift = (positions * 2).astype(np.uint16)
        self.n_pixels = len(sub_rows)

    def read(self, raw: np.ndarray) -> float:
        hi = raw[self.row_idx, self.hi_offset].astype(np.uint16)
        lsb = raw[self.row_idx, self.lsb_offset].astype(np.uint16)
        values = (hi << 2) | ((lsb >> self.lsb_shift) & 0x03)
        return float(values.mean())

    def read_from_cam(self, cam: Any) -> float:
        raw = cam.capture_array("raw")
        return self.read(raw)


def detect_bayer(cam: Any, pi: Any, red_pin: int = 23, green_pin: int = 24) -> dict[str, tuple[int, int]]:
    """Detect which Bayer sub-grid has the strongest red/green response."""
    positions = {}
    for pin, name in [(red_pin, "red"), (green_pin, "green")]:
        pi.set_PWM_dutycycle(red_pin, 0)
        pi.set_PWM_dutycycle(green_pin, 0)
        time.sleep(0.3)
        pi.set_PWM_frequency(pin, 10000)
        pi.set_PWM_dutycycle(pin, 255)
        time.sleep(0.5)
        frames = [unpack_10bit_csi2p(cam.capture_array("raw")).astype(np.float64)
                  for _ in range(10)]
        avg = np.median(frames, axis=0)
        pi.set_PWM_dutycycle(pin, 0)
        time.sleep(0.3)
        off_frames = [unpack_10bit_csi2p(cam.capture_array("raw")).astype(np.float64)
                      for _ in range(10)]
        off_avg = np.median(off_frames, axis=0)
        diff = avg - off_avg
        subs = {
            (0, 0): diff[0::2, 0::2], (0, 1): diff[0::2, 1::2],
            (1, 0): diff[1::2, 0::2], (1, 1): diff[1::2, 1::2],
        }
        best = max(subs, key=lambda k: subs[k].mean())
        positions[name] = best
    return positions


def build_red_mask(
    cam: Any, pi: Any, rr: int, rc: int,
    red_pin: int = 23, green_pin: int = 24,
    target_px: int = 500,
) -> tuple[np.ndarray, int]:
    """Build a binary mask of illuminated red Bayer pixels."""
    pi.set_PWM_dutycycle(green_pin, 0)
    pi.set_PWM_frequency(red_pin, 10000)
    pi.set_PWM_dutycycle(red_pin, 255)
    time.sleep(0.5)
    on_frames = []
    for _ in range(15):
        raw = cam.capture_array("raw")
        red = unpack_10bit_csi2p(raw)[rr::2, rc::2].astype(np.float64)
        on_frames.append(red)
    on_avg = np.median(on_frames, axis=0)
    pi.set_PWM_dutycycle(red_pin, 0)
    time.sleep(0.3)
    off_frames = []
    for _ in range(10):
        raw = cam.capture_array("raw")
        red = unpack_10bit_csi2p(raw)[rr::2, rc::2].astype(np.float64)
        off_frames.append(red)
    off_avg = np.median(off_frames, axis=0)
    diff = on_avg - off_avg
    thresh = np.percentile(diff.flatten(), 97)
    mask = diff > max(thresh, 15)
    n = int(mask.sum())
    while n > target_px * 3 and thresh < diff.max() - 10:
        thresh += 10
        mask = diff > thresh
        n = int(mask.sum())
    while n < 50 and thresh > 5:
        thresh -= 5
        mask = diff > thresh
        n = int(mask.sum())
    return mask, n


@dataclass
class RawPulseCalibration:
    """Calibration data for the raw pulse measurer."""
    bayer_red: tuple[int, int] = (0, 0)
    mask_pixels: int = 0
    baseline_mean: float = 0.0
    baseline_std: float = 0.0
    fps: float = 0.0
    ready: bool = False


@dataclass
class RawPulseMeasurement:
    """A single raw 10-bit pulse measurement result."""
    pre_red_mean: float = 0.0
    post_red_mean: float = 0.0
    delta_red: float = 0.0
    delta_red_norm: float = 0.0
    baseline_frames: int = 0
    response_frames: int = 0
    peak_frame_idx: int = 0
    peak_delta: float = 0.0
    raw_snr: float = 0.0
    raw_bits: float = 0.0
    source: str = "raw10"


class RawPulseMeasurer:
    """Manages raw 10-bit Bayer measurement during pulse experiments.

    Lifecycle:
      1. start() — stops RTSP, starts Picamera2 with raw stream, calibrates
      2. measure_baseline(n) — capture n baseline frames, return stats
      3. measure_post_read(n) — capture n post-read frames, compute delta
      4. stop() — stop camera, restart RTSP
    """

    def __init__(
        self,
        red_pin: int = 23,
        green_pin: int = 24,
        frame_dur_us: int = 6761,
    ) -> None:
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.frame_dur_us = frame_dur_us
        self._cam: Any = None
        self._reader: FastRedReader | None = None
        self._calibration = RawPulseCalibration()
        self._started = False
        self._pi: Any = None

    @property
    def calibration(self) -> RawPulseCalibration:
        return self._calibration

    @property
    def is_started(self) -> bool:
        return self._started

    def start(self, pi_instance: Any = None) -> RawPulseCalibration:
        """Start raw capture, detect Bayer pattern, build mask, calibrate.

        Args:
            pi_instance: An open pigpio.pi() instance for GPIO control.
                         If None, creates its own.

        Returns the calibration result.
        """
        if self._started:
            return self._calibration

        import pigpio
        from dual_stream import start_dual_camera

        if pi_instance is not None:
            self._pi = pi_instance
            own_pi = False
        else:
            self._pi = pigpio.pi()
            if not self._pi.connected:
                raise RuntimeError("Cannot connect to pigpiod")
            own_pi = True

        for pin in (self.red_pin, self.green_pin):
            self._pi.set_mode(pin, pigpio.OUTPUT)
            self._pi.set_PWM_frequency(pin, 10000)
            self._pi.set_PWM_dutycycle(pin, 0)

        self._cam = start_dual_camera(controls={
            "FrameDurationLimits": (self.frame_dur_us, self.frame_dur_us),
        })
        time.sleep(1.0)

        # Measure actual FPS
        t0 = time.monotonic()
        for _ in range(60):
            self._cam.capture_array("raw")
        fps = 60.0 / (time.monotonic() - t0)

        # Detect Bayer pattern
        bayer = detect_bayer(self._cam, self._pi, self.red_pin, self.green_pin)
        rr, rc = bayer["red"]

        # Build mask
        mask, mask_n = build_red_mask(
            self._cam, self._pi, rr, rc,
            self.red_pin, self.green_pin,
        )

        # Create fast reader
        self._reader = FastRedReader(rr, rc, mask)

        # Baseline stability
        self._pi.set_PWM_dutycycle(self.green_pin, 0)
        self._pi.set_PWM_frequency(self.red_pin, 10000)
        self._pi.set_PWM_dutycycle(self.red_pin, 200)
        time.sleep(0.5)
        vals = [self._reader.read_from_cam(self._cam) for _ in range(50)]
        self._pi.set_PWM_dutycycle(self.red_pin, 0)

        bl_mean = float(np.mean(vals))
        bl_std = float(np.std(vals))

        self._calibration = RawPulseCalibration(
            bayer_red=(rr, rc),
            mask_pixels=mask_n,
            baseline_mean=bl_mean,
            baseline_std=bl_std,
            fps=fps,
            ready=True,
        )
        self._started = True
        return self._calibration

    def read_red(self) -> float:
        """Read mean red value from raw 10-bit Bayer pixels (masked)."""
        if not self._started or self._reader is None or self._cam is None:
            raise RuntimeError("RawPulseMeasurer not started")
        return self._reader.read_from_cam(self._cam)

    def measure_baseline(self, n_frames: int = 5) -> list[float]:
        """Capture n baseline red readings (red laser should be ON)."""
        return [self.read_red() for _ in range(n_frames)]

    def measure_response(
        self,
        n_frames: int = 5,
        baseline_values: list[float] | None = None,
    ) -> RawPulseMeasurement:
        """Capture n post-read frames and compute delta vs baseline.

        Call this immediately after green-off + red-on.
        """
        post_vals = [self.read_red() for _ in range(n_frames)]
        pre_mean = float(np.mean(baseline_values)) if baseline_values else 0.0
        post_arr = np.array(post_vals)

        # Peak is the frame with largest delta from baseline
        deltas = post_arr - pre_mean
        peak_idx = int(np.argmax(np.abs(deltas)))
        peak_delta = float(deltas[peak_idx])

        # Use first few frames for response (before decay)
        n_early = min(3, len(post_vals))
        post_mean = float(np.mean(post_vals[:n_early]))
        delta_red = post_mean - pre_mean
        delta_red_norm = delta_red / pre_mean if pre_mean > 0 else 0.0

        # SNR from baseline std
        bl_std = self._calibration.baseline_std
        raw_snr = abs(delta_red) / bl_std if bl_std > 0 else 0.0
        raw_bits = np.log2(raw_snr) if raw_snr > 1 else 0.0

        return RawPulseMeasurement(
            pre_red_mean=round(pre_mean, 4),
            post_red_mean=round(post_mean, 4),
            delta_red=round(delta_red, 4),
            delta_red_norm=round(delta_red_norm, 6),
            baseline_frames=len(baseline_values) if baseline_values else 0,
            response_frames=n_frames,
            peak_frame_idx=peak_idx,
            peak_delta=round(peak_delta, 4),
            raw_snr=round(raw_snr, 1),
            raw_bits=round(float(raw_bits), 2),
            source="raw10",
        )

    def set_light(self, red_level: int = 0, green_level: int = 0) -> None:
        """Control laser GPIOs directly for pulse timing."""
        if self._pi is None:
            raise RuntimeError("RawPulseMeasurer not started")
        if red_level > 0:
            self._pi.set_PWM_frequency(self.red_pin, 10000)
        self._pi.set_PWM_dutycycle(self.red_pin, max(0, min(255, red_level)))
        if green_level > 0:
            self._pi.set_PWM_frequency(self.green_pin, 10000)
        self._pi.set_PWM_dutycycle(self.green_pin, max(0, min(255, green_level)))

    def stop(self) -> None:
        """Stop camera, restart RTSP service."""
        if not self._started:
            return

        if self._pi is not None:
            self._pi.set_PWM_dutycycle(self.red_pin, 0)
            self._pi.set_PWM_dutycycle(self.green_pin, 0)

        if self._cam is not None:
            from dual_stream import stop_dual_camera
            try:
                stop_dual_camera(self._cam)
            except Exception:
                try:
                    self._cam.stop()
                    self._cam.close()
                except Exception:
                    pass
            self._cam = None
            time.sleep(0.5)

        self._reader = None
        self._started = False
