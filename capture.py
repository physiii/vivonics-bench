"""Camera capture via rpicam-still or ffmpeg single-frame grab.

Grabs frames from the IMX477 on the Pi, extracts center 512x512 ROI,
handles dark subtraction, frame averaging, and hot-pixel masking for
optimized bR response measurement.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment, misc]

ROI_SIZE = 512
FRAME_W = 1920
FRAME_H = 1080
ROI_Y_START = (FRAME_H - ROI_SIZE) // 2  # 284
ROI_X_START = (FRAME_W - ROI_SIZE) // 2  # 704


@dataclass
class CaptureConfig:
    output_dir: Path = field(default_factory=lambda: Path("/tmp/bench_frames"))
    roi_size: int = ROI_SIZE
    dark_frame_count: int = 8
    use_rtsp_grab: bool = True
    rtsp_url: str = "rtsp://127.0.0.1:8554/cam"
    shutter_us: int = 1000
    gain: float = 1.0
    awb_gains: str = "1.5,1.0"


@dataclass
class SpotMask:
    """Binary mask identifying the laser-illuminated pixels in the ROI."""
    mask: np.ndarray
    centroid_x: float
    centroid_y: float
    rms_radius: float
    pixel_count: int
    lo_threshold: float
    hi_threshold: float


class Capture:
    def __init__(self, config: CaptureConfig | None = None) -> None:
        self.config = config or CaptureConfig()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self._dark_ref: np.ndarray | None = None
        self._spot_mask: SpotMask | None = None

    def grab_frame(self, label: str = "") -> tuple[np.ndarray, Path]:
        ts = int(time.time() * 1000)
        fname = f"{ts}_{label}.png" if label else f"{ts}.png"
        path = self.config.output_dir / fname

        if self.config.use_rtsp_grab:
            self._grab_via_ffmpeg(path)
        else:
            self._grab_via_rpicam(path)

        frame = self._load_frame(path)
        roi = self._extract_roi(frame)
        return roi, path

    def grab_averaged(self, count: int, label: str = "") -> tuple[np.ndarray, Path]:
        frames: list[np.ndarray] = []
        last_path = Path()
        for i in range(count):
            roi, last_path = self.grab_frame(f"{label}_avg{i}")
            frames.append(roi.astype(np.float64))
            if i < count - 1:
                time.sleep(0.05)
        avg = np.mean(frames, axis=0)
        return avg, last_path

    def capture_dark_reference(self) -> np.ndarray:
        dark_frames: list[np.ndarray] = []
        for i in range(self.config.dark_frame_count):
            roi, _ = self.grab_frame(f"dark_{i}")
            dark_frames.append(roi.astype(np.float64))
            time.sleep(0.05)
        self._dark_ref = np.mean(dark_frames, axis=0)
        return self._dark_ref

    def subtract_dark(self, frame: np.ndarray) -> np.ndarray:
        if self._dark_ref is None:
            return frame.astype(np.float64)
        return np.clip(frame.astype(np.float64) - self._dark_ref, 0.0, None)

    def calibrate_spot_mask(
        self, frame: np.ndarray, lo: float = 10.0, hi: float = 240.0,
    ) -> SpotMask:
        """Build a mask from the illuminated, unsaturated pixels in the red channel."""
        red = frame[:, :, 0] if frame.ndim == 3 else frame
        red = red.astype(np.float64)
        mask = (red > lo) & (red < hi)
        count = int(mask.sum())

        if count < 10:
            cx, cy, rms = 0.0, 0.0, 0.0
        else:
            yy, xx = np.mgrid[: red.shape[0], : red.shape[1]]
            weights = np.where(mask, red, 0.0)
            total_w = weights.sum()
            cx = float((xx * weights).sum() / total_w)
            cy = float((yy * weights).sum() / total_w)
            r2 = (xx - cx) ** 2 + (yy - cy) ** 2
            rms = float(np.sqrt((r2 * weights).sum() / total_w))

        self._spot_mask = SpotMask(
            mask=mask,
            centroid_x=cx,
            centroid_y=cy,
            rms_radius=rms,
            pixel_count=count,
            lo_threshold=lo,
            hi_threshold=hi,
        )
        return self._spot_mask

    def red_channel_mean(self, frame: np.ndarray) -> float:
        if frame.ndim == 3:
            red = frame[:, :, 0]
        else:
            red = frame
        return float(np.mean(red))

    def red_masked_mean(self, frame: np.ndarray) -> float:
        """Mean of red channel using only the spot-mask pixels."""
        if self._spot_mask is None or self._spot_mask.pixel_count < 10:
            return self.red_channel_mean(frame)
        red = frame[:, :, 0] if frame.ndim == 3 else frame
        red = red.astype(np.float64)
        return float(np.mean(red[self._spot_mask.mask]))

    def red_analysis(self, frame: np.ndarray) -> dict[str, Any]:
        """Full analysis of red channel: full-ROI and masked metrics."""
        red = frame[:, :, 0] if frame.ndim == 3 else frame
        red = red.astype(np.float64)
        result: dict[str, Any] = {
            "full_mean": float(np.mean(red)),
            "full_std": float(np.std(red)),
            "full_max": float(np.max(red)),
            "full_min": float(np.min(red)),
        }
        if self._spot_mask is not None and self._spot_mask.pixel_count >= 10:
            masked = red[self._spot_mask.mask]
            result.update({
                "masked_mean": float(np.mean(masked)),
                "masked_std": float(np.std(masked)),
                "masked_max": float(np.max(masked)),
                "masked_min": float(np.min(masked)),
                "masked_pixels": self._spot_mask.pixel_count,
                "centroid_x": self._spot_mask.centroid_x,
                "centroid_y": self._spot_mask.centroid_y,
                "rms_radius": self._spot_mask.rms_radius,
            })
        return result

    @property
    def spot_mask(self) -> SpotMask | None:
        return self._spot_mask

    def _grab_via_rpicam(self, path: Path) -> None:
        cmd = [
            "rpicam-still",
            "--immediate",
            "--width", str(FRAME_W),
            "--height", str(FRAME_H),
            "--output", str(path),
            "--encoding", "png",
            "--nopreview",
            "--denoise", "off",
        ]
        if self.config.shutter_us > 0:
            cmd.extend(["--shutter", str(self.config.shutter_us)])
        if self.config.gain > 0:
            cmd.extend(["--gain", str(self.config.gain)])
        if self.config.awb_gains and self.config.awb_gains != "auto":
            cmd.extend(["--awbgains", self.config.awb_gains])
        subprocess.run(cmd, check=True, capture_output=True)

    def _grab_via_ffmpeg(self, path: Path) -> None:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-rtsp_transport", "tcp",
                "-i", self.config.rtsp_url,
                "-frames:v", "1",
                str(path),
            ],
            check=True,
            capture_output=True,
        )

    def _load_frame(self, path: Path) -> np.ndarray:
        if Image is not None:
            img = Image.open(path).convert("RGB")
            return np.array(img)
        raise ImportError("Pillow is required: pip install Pillow")

    def _extract_roi(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        cy, cx = h // 2, w // 2
        half = self.config.roi_size // 2
        return frame[cy - half : cy + half, cx - half : cx + half]
