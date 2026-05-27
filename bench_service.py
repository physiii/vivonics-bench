"""Vivonics X1 Bench Service — runs on Raspberry Pi.

Controls the projector (HDMI), captures from the camera (CSI/rpicam),
runs photocycle measurement protocols, and streams metrics via SSE.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import threading
import time
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from capture import Capture, CaptureConfig
from photocycle import (
    LinearityResult,
    PhotocycleConfig,
    PhotocycleResult,
    run_green_write_sweep,
    run_linearity_check,
)
from projector import Projector, ProjectorConfig
from sensors import SensorSuite

CAMERA_RTSP_SCRIPT = os.environ.get(
    "VIVONICS_CAMERA_RTSP_SCRIPT",
    os.path.expanduser("~/camera_test/rtsp.sh"),
)


class RunState(str, Enum):
    idle = "idle"
    running_linearity = "running_linearity"
    running_photocycle = "running_photocycle"
    running_pulse = "running_pulse"
    completed = "completed"
    failed = "failed"
    aborted = "aborted"


class LightMode(str, Enum):
    off = "off"
    red = "red"
    green = "green"
    both = "both"


CAMERA_RTSP_SERVICE = os.environ.get("VIVONICS_CAMERA_RTSP_SERVICE", "c1-camera-rtsp")
CAMERA_OVERRIDE_DIR = Path(os.environ.get(
    "VIVONICS_CAMERA_OVERRIDE_DIR",
    os.path.expanduser("~/.config/systemd/user/c1-camera-rtsp.service.d"),
))


class BenchState:
    def __init__(self) -> None:
        self.state: RunState = RunState.idle
        self.events: list[dict[str, Any]] = []
        self.linearity_result: LinearityResult | None = None
        self.photocycle_result: PhotocycleResult | None = None
        self.light_mode: LightMode = LightMode.off
        self.red_level = 0
        self.green_level = 0
        self.pulse_config: dict[str, Any] | None = None
        self.camera_mode: str = "normal"
        self._abort_flag = False
        self._lock = threading.Lock()
        self._event_queues: list[asyncio.Queue[dict[str, Any] | None]] = []

    def emit(self, event: dict[str, Any]) -> None:
        with self._lock:
            self.events.append(event)
        for q in self._event_queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def subscribe(self) -> asyncio.Queue[dict[str, Any] | None]:
        q: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue(maxsize=200)
        self._event_queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any] | None]) -> None:
        if q in self._event_queues:
            self._event_queues.remove(q)

    def request_abort(self) -> None:
        self._abort_flag = True

    def should_abort(self) -> bool:
        return self._abort_flag

    def is_running(self) -> bool:
        return self.state in {
            RunState.running_linearity,
            RunState.running_photocycle,
            RunState.running_pulse,
        }

    def set_light_levels(self, red_level: int = 0, green_level: int = 0) -> None:
        red_level = max(0, min(255, int(red_level)))
        green_level = max(0, min(255, int(green_level)))
        if red_level > 0 and green_level > 0:
            mode = LightMode.both
        elif red_level > 0:
            mode = LightMode.red
        elif green_level > 0:
            mode = LightMode.green
        else:
            mode = LightMode.off
        with self._lock:
            self.light_mode = mode
            self.red_level = red_level
            self.green_level = green_level

    def set_light(self, mode: LightMode, red_level: int = 0, green_level: int = 0) -> None:
        if mode == LightMode.off:
            self.set_light_levels(0, 0)
        elif mode == LightMode.red:
            self.set_light_levels(red_level, 0)
        elif mode == LightMode.green:
            self.set_light_levels(0, green_level)
        elif mode == LightMode.both:
            self.set_light_levels(red_level, green_level)

    def light_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "mode": self.light_mode.value,
                "red_level": self.red_level,
                "green_level": self.green_level,
            }

    def set_pulse_config(self, config: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self.pulse_config = dict(config)
            return dict(self.pulse_config)

    def pulse_config_snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            if self.pulse_config is None:
                return None
            return dict(self.pulse_config)

    def reset(self) -> None:
        self.state = RunState.idle
        self.events.clear()
        self.linearity_result = None
        self.photocycle_result = None
        self.pulse_config = None
        self._abort_flag = False


bench_state = BenchState()
capture: Capture | None = None
projector: Projector | None = None
sensors: SensorSuite | None = None
hardware_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global capture, projector, sensors
    capture = Capture(CaptureConfig())
    projector = Projector(ProjectorConfig())
    sensors = SensorSuite()
    try:
        _force_lasers_off()
    except Exception as e:
        bench_state.emit({"type": "error", "message": f"Failed to force lasers off at startup: {e}"})
    yield
    if sensors is not None:
        sensors.close()
    if projector is not None:
        projector.close()


app = FastAPI(title="Vivonics Bench Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartRequest(BaseModel):
    green_exposure_s: float = 1.0
    recovery_interval_s: float = 30.0
    settle_time_s: float = 0.5


class PulseRequest(BaseModel):
    red_duration_s: float = Field(1.0, ge=0.01, le=60.0)
    green_duration_s: float = Field(0.1, ge=0.01, le=10.0)
    green_duration_schedule_s: list[float] | None = None
    red_level: int = Field(255, ge=0, le=255)
    green_level: int = Field(255, ge=0, le=255)
    loop: bool = False
    capture_frames: bool = True
    raw_measure: bool = False


class PulseControlRequest(BaseModel):
    red_duration_s: float | None = Field(None, ge=0.01, le=60.0)
    green_duration_s: float | None = Field(None, ge=0.01, le=10.0)
    green_duration_schedule_s: list[float] | None = None
    red_level: int | None = Field(None, ge=0, le=255)
    green_level: int | None = Field(None, ge=0, le=255)


class LightRequest(BaseModel):
    mode: LightMode | None = None
    red_level: int | None = Field(None, ge=0, le=255)
    green_level: int | None = Field(None, ge=0, le=255)


class AdcPulseCaptureRequest(BaseModel):
    pre_ms: int = Field(100, ge=1, le=5000)
    write_ms: int = Field(20, ge=1, le=5000)
    read_ms: int = Field(200, ge=1, le=10000)
    settle_ms: int = Field(20, ge=0, le=5000)
    red_level: int = Field(50, ge=0, le=255)
    green_level: int = Field(50, ge=0, le=255)
    red_during_write: bool = True
    max_samples: int = Field(5000, ge=1, le=20000)


class CameraModeRequest(BaseModel):
    mode: str = Field(..., pattern=r"^(normal|experiment)$")


class CameraSettingsRequest(BaseModel):
    shutter_us: int = Field(2000, ge=100, le=200000)
    gain: float = Field(1.0, ge=1.0, le=16.0)
    awb_red: float = Field(1.0, ge=0.1, le=10.0)
    awb_blue: float = Field(1.0, ge=0.1, le=10.0)


class CalibrateRequest(BaseModel):
    lo_threshold: float = Field(10.0, ge=1.0, le=200.0)
    hi_threshold: float = Field(240.0, ge=50.0, le=254.0)
    avg_frames: int = Field(8, ge=1, le=32)


class MultiplyRequest(BaseModel):
    a: float = Field(..., ge=0.0, le=10.0)
    b: float = Field(..., ge=0.0, le=10.0)
    green_settle_s: float = Field(0.3, ge=0.05, le=5.0)
    read_settle_s: float = Field(0.5, ge=0.1, le=10.0)
    recovery_s: float = Field(10.0, ge=0.0, le=120.0)
    avg_frames: int = Field(8, ge=1, le=32)
    repetitions: int = Field(5, ge=1, le=20)


@app.get("/camera/mode")
def get_camera_mode():
    return {"mode": bench_state.camera_mode}


@app.post("/camera/mode")
def set_camera_mode(req: CameraModeRequest):
    if req.mode == bench_state.camera_mode:
        return {"status": "ok", "mode": req.mode, "changed": False}

    result = _apply_camera_mode(req.mode)
    bench_state.camera_mode = req.mode
    return result


@app.get("/camera/settings")
def get_camera_settings():
    return _read_current_camera_settings()


@app.post("/camera/settings")
def set_camera_settings(req: CameraSettingsRequest):
    override_dir = CAMERA_OVERRIDE_DIR
    override_file = override_dir / "camera-mode.conf"
    override_dir.mkdir(parents=True, exist_ok=True)
    awb = f"{req.awb_red},{req.awb_blue}"
    override_file.write_text(
        "[Service]\n"
        f"Environment=VIVONICS_CAMERA_SHUTTER_US={req.shutter_us}\n"
        f"Environment=VIVONICS_CAMERA_GAIN={req.gain}\n"
        f"Environment=VIVONICS_CAMERA_AWB_GAINS={awb}\n"
    )
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=10)
    subprocess.run(
        ["systemctl", "--user", "restart", CAMERA_RTSP_SERVICE],
        check=True,
        timeout=15,
    )
    if capture is not None:
        capture.config.shutter_us = req.shutter_us
        capture.config.gain = req.gain
        capture.config.awb_gains = awb
    time.sleep(1.5)
    return {
        "status": "ok",
        "shutter_us": req.shutter_us,
        "gain": req.gain,
        "awb_gains": awb,
    }


@app.post("/snapshot")
def take_snapshot():
    if capture is None:
        raise HTTPException(503, "Hardware not initialized")
    with hardware_lock:
        frame, path = capture.grab_frame("snapshot")
        frame_ds = capture.subtract_dark(frame)
        analysis = capture.red_analysis(frame_ds)
        analysis["frame_path"] = str(path)
        analysis["has_spot_mask"] = capture.spot_mask is not None
        if capture.spot_mask is not None:
            analysis["spot_pixels"] = capture.spot_mask.pixel_count
        return analysis


@app.post("/calibrate")
def calibrate_spot(req: CalibrateRequest | None = None):
    if capture is None or projector is None:
        raise HTTPException(503, "Hardware not initialized")
    req = req or CalibrateRequest()

    with hardware_lock:
        _enter_still_mode()
        projector.open()
        try:
            projector.off()
            time.sleep(0.5)
            capture.capture_dark_reference()

            projector.show_red(255)
            time.sleep(0.5)

            frame, path = capture.grab_averaged(req.avg_frames, "calibrate_red")
            frame_ds = capture.subtract_dark(frame)

            spot = capture.calibrate_spot_mask(
                frame_ds, lo=req.lo_threshold, hi=req.hi_threshold,
            )

            analysis = capture.red_analysis(frame_ds)
            analysis["frame_path"] = str(path)
            analysis["calibration"] = {
                "pixel_count": spot.pixel_count,
                "centroid_x": round(spot.centroid_x, 1),
                "centroid_y": round(spot.centroid_y, 1),
                "rms_radius": round(spot.rms_radius, 1),
                "lo_threshold": spot.lo_threshold,
                "hi_threshold": spot.hi_threshold,
            }

            one_pct_full = analysis["full_mean"] * 0.01
            one_pct_masked = analysis.get("masked_mean", 0.0) * 0.01
            analysis["sensitivity"] = {
                "full_roi_1pct_delta": round(one_pct_full, 4),
                "masked_1pct_delta": round(one_pct_masked, 4),
                "improvement_factor": round(
                    one_pct_masked / one_pct_full, 1
                ) if one_pct_full > 0 else 0.0,
            }

            return analysis
        finally:
            projector.off()
            projector.close()
            _exit_still_mode()


@app.post("/multiply")
def run_multiply(req: MultiplyRequest):
    """Analog multiplication via bR: green_level ∝ A, green_duration ∝ B.

    The measured red transmission change encodes A × B.
    """
    if capture is None or projector is None:
        raise HTTPException(503, "Hardware not initialized")
    if bench_state.is_running():
        raise HTTPException(409, "Experiment already running")
    if capture.spot_mask is None:
        raise HTTPException(
            400, "No spot mask — run POST /calibrate first"
        )

    # Map inputs to green dose: level ∝ A (0-255), duration ∝ B (0-2s)
    green_level = max(1, min(255, int(req.a * 25.5)))
    green_duration_s = max(0.05, req.b * 0.2)

    with hardware_lock:
        _enter_still_mode()
        projector.open()
        try:
            deltas_masked: list[float] = []
            deltas_full: list[float] = []
            baselines: list[float] = []

            for rep in range(req.repetitions):
                # Recovery: red-only hold for bR relaxation
                projector.show_red(255)
                time.sleep(req.recovery_s if rep == 0 else max(5.0, req.recovery_s / 2))

                # Baseline
                time.sleep(req.read_settle_s)
                baseline_frame, _ = capture.grab_averaged(
                    req.avg_frames, f"mul_base_r{rep}",
                )
                baseline_ds = capture.subtract_dark(baseline_frame)
                b_masked = capture.red_masked_mean(baseline_ds)
                b_full = capture.red_channel_mean(baseline_ds)

                # Green write
                projector.show_color(0, green_level, 0, settle=False)
                time.sleep(green_duration_s)

                # Red read
                projector.show_red(255)
                time.sleep(req.green_settle_s)
                post_frame, _ = capture.grab_averaged(
                    req.avg_frames, f"mul_post_r{rep}",
                )
                post_ds = capture.subtract_dark(post_frame)
                p_masked = capture.red_masked_mean(post_ds)
                p_full = capture.red_channel_mean(post_ds)

                dm = 100.0 * (p_masked - b_masked) / b_masked if b_masked > 0 else 0.0
                df = 100.0 * (p_full - b_full) / b_full if b_full > 0 else 0.0
                deltas_masked.append(dm)
                deltas_full.append(df)
                baselines.append(b_masked)

            median_masked = float(np.median(deltas_masked))
            median_full = float(np.median(deltas_full))
            std_masked = float(np.std(deltas_masked)) if len(deltas_masked) > 1 else 0.0

            return {
                "a": req.a,
                "b": req.b,
                "product": round(req.a * req.b, 4),
                "green_level": green_level,
                "green_duration_s": round(green_duration_s, 3),
                "recovery_s": req.recovery_s,
                "repetitions": req.repetitions,
                "median_delta_pct_masked": round(median_masked, 4),
                "median_delta_pct_full": round(median_full, 4),
                "std_delta_pct": round(std_masked, 4),
                "all_deltas_masked": [round(d, 4) for d in deltas_masked],
                "median_baseline": round(float(np.median(baselines)), 3),
                "measured_response": round(median_masked, 4),
                "spot_pixels": capture.spot_mask.pixel_count if capture.spot_mask else 0,
            }
        finally:
            projector.off()
            projector.close()
            _exit_still_mode()


def _read_current_camera_settings() -> dict[str, Any]:
    result: dict[str, Any] = {"mode": bench_state.camera_mode}
    override_file = CAMERA_OVERRIDE_DIR / "camera-mode.conf"
    if override_file.exists():
        for line in override_file.read_text().splitlines():
            if "VIVONICS_CAMERA_SHUTTER_US=" in line:
                result["shutter_us"] = int(line.split("=", 2)[-1])
            elif "VIVONICS_CAMERA_GAIN=" in line:
                result["gain"] = float(line.split("=", 2)[-1])
            elif "VIVONICS_CAMERA_AWB_GAINS=" in line:
                result["awb_gains"] = line.split("=", 2)[-1]
    try:
        ps = subprocess.run(
            ["pgrep", "-a", "rpicam"], capture_output=True, text=True, timeout=5,
        )
        if ps.stdout:
            result["active_cmdline"] = ps.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return result


def _enter_still_mode() -> None:
    """Stop RTSP stream so rpicam-still can access the camera directly."""
    if capture is not None:
        capture.config.use_rtsp_grab = False
    try:
        subprocess.run(
            ["systemctl", "--user", "stop", CAMERA_RTSP_SERVICE],
            check=True, timeout=10,
        )
    except subprocess.SubprocessError:
        pass
    time.sleep(0.5)


def _exit_still_mode() -> None:
    """Restart the RTSP stream after measurement."""
    if capture is not None:
        capture.config.use_rtsp_grab = True
    try:
        subprocess.run(
            ["systemctl", "--user", "start", CAMERA_RTSP_SERVICE],
            check=True, timeout=15,
        )
    except subprocess.SubprocessError:
        pass


def _light_driver_includes_gpio(value: str) -> bool:
    modes = {part.strip().lower() for part in value.replace("+", ",").split(",")}
    modes.discard("")
    return "gpio" in modes or "both" in modes


def _force_lasers_off() -> None:
    """Best-effort physical GPIO-off for abort and startup cleanup paths."""
    config = projector.config if projector is not None else ProjectorConfig()
    from laser_gpio import LaserGPIOConfig, LaserGPIOController

    controller = LaserGPIOController(
        LaserGPIOConfig(
            red_pin=config.red_laser_gpio,
            green_pin=config.green_laser_gpio,
            active_high=config.laser_active_high,
        )
    )
    try:
        controller.open()
        controller.off()
    finally:
        controller.close()


def _apply_camera_mode(mode: str) -> dict[str, Any]:
    override_dir = CAMERA_OVERRIDE_DIR
    override_file = override_dir / "camera-mode.conf"

    if mode == "normal":
        override_dir.mkdir(parents=True, exist_ok=True)
        override_file.write_text(
            "[Service]\n"
            "Environment=VIVONICS_CAMERA_SHUTTER_US=0\n"
            "Environment=VIVONICS_CAMERA_GAIN=0\n"
            "Environment=VIVONICS_CAMERA_AWB_GAINS=auto\n"
        )
    else:
        if override_file.exists():
            override_file.unlink()

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, timeout=10)
    subprocess.run(
        ["systemctl", "--user", "restart", CAMERA_RTSP_SERVICE],
        check=True,
        timeout=15,
    )

    return {"status": "ok", "mode": mode, "method": "service_restart"}


@app.get("/status")
def get_status():
    return {
        "state": bench_state.state.value,
        "event_count": len(bench_state.events),
        "linearity_passed": (
            bench_state.linearity_result.passed
            if bench_state.linearity_result
            else None
        ),
        "photocycle_passed": (
            bench_state.photocycle_result.passed
            if bench_state.photocycle_result
            else None
        ),
        "projector_driver": projector.driver_name if projector else None,
        "light_driver_config": (
            {
                "driver": projector.config.light_driver,
                "red_laser_gpio": projector.config.red_laser_gpio,
                "green_laser_gpio": projector.config.green_laser_gpio,
                "laser_active_high": projector.config.laser_active_high,
                "laser_pwm_hz": projector.config.laser_pwm_hz,
            }
            if projector
            else None
        ),
        "manual_light": bench_state.light_snapshot(),
        "pulse_config": bench_state.pulse_config_snapshot(),
        "camera_mode": bench_state.camera_mode,
        "sensors": sensors.availability() if sensors else None,
    }


@app.get("/sensors")
def read_sensors():
    if sensors is None:
        raise HTTPException(503, "Sensors not initialized")
    return sensors.read_all()


@app.post("/adc/pulse-capture")
def capture_adc_pulse(req: AdcPulseCaptureRequest):
    if sensors is None or projector is None:
        raise HTTPException(503, "Hardware not initialized")
    if bench_state.is_running():
        raise HTTPException(409, "Experiment already running")

    total_ms = req.pre_ms + req.write_ms + req.read_ms
    samples: list[dict[str, Any]] = []
    from ad7606 import to_signed_16

    def command_for(elapsed_ms: float) -> tuple[str, int, int]:
        if elapsed_ms < req.pre_ms:
            return "baseline", req.red_level, 0
        if elapsed_ms < req.pre_ms + req.write_ms:
            return "write", req.red_level if req.red_during_write else 0, req.green_level
        return "read", req.red_level, 0

    with hardware_lock:
        projector.open()
        current_command: tuple[str, int, int] | None = None
        try:
            projector.show_color(req.red_level, 0, 0, settle=False)
            bench_state.set_light_levels(req.red_level, 0)
            if req.settle_ms > 0:
                time.sleep(req.settle_ms / 1000.0)
            start = time.perf_counter()
            while len(samples) < req.max_samples:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                if elapsed_ms >= total_ms:
                    break
                command = command_for(elapsed_ms)
                if command != current_command:
                    _, red, green = command
                    projector.show_color(red, green, 0, settle=False)
                    bench_state.set_light_levels(red, green)
                    current_command = command
                values = sensors.read_ad7606_frame()
                phase, red, green = current_command
                sample: dict[str, Any] = {
                    "t_ms": elapsed_ms,
                    "phase": phase,
                    "red_level": red,
                    "green_level": green,
                }
                for index, value in enumerate(values, start=1):
                    sample[f"ch{index}"] = float(value)
                    sample[f"ch{index}_signed"] = float(to_signed_16(value))
                samples.append(sample)
        finally:
            projector.off()
            projector.close()
            bench_state.set_light_levels(0, 0)

    duration_ms = samples[-1]["t_ms"] - samples[0]["t_ms"] if len(samples) > 1 else 0.0
    sample_hz = (len(samples) - 1) * 1000.0 / duration_ms if duration_ms > 0 else 0.0
    return {
        "status": "ok",
        "sample_count": len(samples),
        "sample_hz": sample_hz,
        "duration_ms": duration_ms,
        "protocol": req.model_dump(),
        "samples": samples,
    }


@app.post("/run/linearity")
def run_linearity(req: StartRequest | None = None):
    if bench_state.is_running():
        raise HTTPException(409, "Experiment already running")
    if capture is None or projector is None:
        raise HTTPException(503, "Hardware not initialized")

    bench_state.reset()
    bench_state.state = RunState.running_pulse_linearity
    bench_state.set_light(LightMode.off)

    config = PhotocycleConfig()
    if req and req.settle_time_s != 0.5:
        projector.config.settle_time_s = req.settle_time_s

    def worker():
        try:
            with hardware_lock:
                projector.open()

                def emit(event: dict[str, Any]) -> None:
                    bench_state.emit(_with_sensor_snapshot(event))

                result = run_linearity_check(
                    capture, projector, config,
                    emit=emit,
                    abort=bench_state.should_abort,
                )
            bench_state.linearity_result = result
            bench_state.state = RunState.completed
            emit({"type": "run_complete", "phase": 1, "passed": result.passed})
        except Exception as e:
            bench_state.state = RunState.failed
            bench_state.emit({"type": "error", "message": str(e)})
        finally:
            if projector is not None:
                projector.close()
            bench_state.set_light(LightMode.off)

    threading.Thread(target=worker, daemon=True).start()
    return {"status": "started", "phase": "linearity"}


@app.post("/run/photocycle")
def run_photocycle(req: StartRequest | None = None):
    if bench_state.is_running():
        raise HTTPException(409, "Experiment already running")
    if capture is None or projector is None:
        raise HTTPException(503, "Hardware not initialized")

    bench_state.reset()
    bench_state.state = RunState.running_pulse_photocycle
    bench_state.set_light(LightMode.off)

    config = PhotocycleConfig(
        green_exposure_s=req.green_exposure_s if req else 1.0,
        recovery_interval_s=req.recovery_interval_s if req else 30.0,
    )
    if req and req.settle_time_s != 0.5:
        projector.config.settle_time_s = req.settle_time_s

    def worker():
        try:
            with hardware_lock:
                projector.open()

                def emit(event: dict[str, Any]) -> None:
                    bench_state.emit(_with_sensor_snapshot(event))

                lin_result = run_linearity_check(
                    capture, projector, config,
                    emit=emit,
                    abort=bench_state.should_abort,
                )
                bench_state.linearity_result = lin_result

                if not lin_result.passed:
                    bench_state.state = RunState.failed
                    emit({"type": "error", "message": "Linearity check failed"})
                    return

                if bench_state.should_abort():
                    bench_state.state = RunState.aborted
                    return

                read_level = lin_result.chosen_read_level
                idx = lin_result.red_codes.index(read_level)
                blank_ref = lin_result.blank_means[idx]

                pc_result = run_green_write_sweep(
                    capture, projector, config,
                    read_level=read_level,
                    blank_reference=blank_ref,
                    emit=emit,
                    abort=bench_state.should_abort,
                )
                bench_state.photocycle_result = pc_result
                bench_state.state = RunState.completed
                emit({
                    "type": "run_complete",
                    "phase": 2,
                    "passed": pc_result.passed,
                })
        except Exception as e:
            bench_state.state = RunState.failed
            bench_state.emit({"type": "error", "message": str(e)})
        finally:
            if projector is not None:
                projector.close()
            bench_state.set_light(LightMode.off)

    threading.Thread(target=worker, daemon=True).start()
    return {"status": "started", "phase": "photocycle"}


@app.post("/run/pulse")
def run_pulse(req: PulseRequest | None = None):
    if bench_state.is_running():
        raise HTTPException(409, "Experiment already running")
    if capture is None or projector is None:
        raise HTTPException(503, "Hardware not initialized")

    req = req or PulseRequest()
    pulse_config = _pulse_config_from_request(req)
    bench_state.reset()
    bench_state.state = RunState.running_pulse
    bench_state.set_light(LightMode.off)
    bench_state.set_pulse_config(pulse_config)

    def worker():
        raw_measurer = None
        try:
            with hardware_lock:
                projector.open()

                def emit(event: dict[str, Any]) -> None:
                    bench_state.emit(_with_sensor_snapshot(event))

                initial_config = bench_state.pulse_config_snapshot() or pulse_config
                use_raw = initial_config.get("raw_measure", False)

                # If raw_measure requested, start the raw 10-bit measurement path
                if use_raw:
                    try:
                        from raw_measure import RawPulseMeasurer
                        raw_measurer = RawPulseMeasurer(
                            red_pin=projector.config.red_laser_gpio,
                            green_pin=projector.config.green_laser_gpio,
                        )
                        cal = raw_measurer.start()
                        bench_state.camera_mode = "experiment"
                        emit({
                            "type": "info",
                            "message": (
                                f"Raw 10-bit measurement active: "
                                f"{cal.mask_pixels} mask px, "
                                f"{cal.fps:.1f} fps, "
                                f"baseline SNR={cal.baseline_mean / cal.baseline_std:.0f}:1"
                                if cal.baseline_std > 0
                                else f"Raw 10-bit: {cal.mask_pixels} px, {cal.fps:.1f} fps"
                            ),
                        })
                    except Exception as e:
                        emit({"type": "info", "message": f"Raw measure init failed, using 8-bit fallback: {e}"})
                        raw_measurer = None

                emit({
                    "type": "phase_start",
                    "phase": "pulse",
                    "name": "Red Hold / Green Flash",
                    "red_duration_s": initial_config["red_duration_s"],
                    "green_duration_s": initial_config["green_duration_s"],
                    "green_duration_schedule_s": initial_config["green_duration_schedule_s"],
                    "green_duration_schedule_ms": [round(d * 1000, 1) for d in initial_config["green_duration_schedule_s"]],
                    "red_level": initial_config["red_level"],
                    "green_level": initial_config["green_level"],
                    "loop": initial_config["loop"],
                    "capture_frames": initial_config["capture_frames"],
                    "raw_measure": use_raw,
                    "raw_calibration": ({
                        "mask_pixels": raw_measurer.calibration.mask_pixels,
                        "fps": round(raw_measurer.calibration.fps, 1),
                        "baseline_mean": round(raw_measurer.calibration.baseline_mean, 3),
                        "baseline_std": round(raw_measurer.calibration.baseline_std, 4),
                    } if raw_measurer and raw_measurer.calibration.ready else None),
                })

                cycle_times: list[float] = []
                iteration = 0
                while True:
                    iteration += 1
                    _cycle_start = time.time()
                    cycle_config = bench_state.pulse_config_snapshot() or pulse_config
                    green_duration_schedule = cycle_config["green_duration_schedule_s"]
                    green_duration_s = green_duration_schedule[(iteration - 1) % len(green_duration_schedule)]
                    green_duration_ms = round(green_duration_s * 1000, 1)
                    emit({
                        "type": "pulse_iteration",
                        "iteration": iteration,
                        "green_duration_s": green_duration_s,
                        "green_duration_ms": green_duration_ms,
                        "red_duration_s": cycle_config["red_duration_s"],
                        "red_level": cycle_config["red_level"],
                        "green_level": cycle_config["green_level"],
                        "green_duration_schedule_ms": [round(d * 1000, 1) for d in green_duration_schedule],
                    })

                    _show_light(LightMode.red, cycle_config["red_level"], 0)
                    emit(_light_event(
                        "red",
                        cycle_config["red_level"],
                        0,
                        "pre_green_hold",
                        iteration,
                        {"green_duration_s": green_duration_s, "green_duration_ms": green_duration_ms},
                    ))
                    _red_hold = 0.012 if (raw_measurer is not None and raw_measurer.is_started) else cycle_config["red_duration_s"]
                    _sleep_abortable(_red_hold)
                    if bench_state.should_abort():
                        bench_state.state = RunState.aborted
                        emit({"type": "aborted", "iteration": iteration})
                        return

                    pre_green_roi: dict[str, Any] | None = None
                    raw_baseline_vals: list[float] | None = None
                    if raw_measurer is not None and raw_measurer.is_started:
                        raw_baseline_vals = raw_measurer.measure_baseline(n_frames=2)
                    if cycle_config["capture_frames"] and raw_baseline_vals is None:
                        frame, path = capture.grab_frame(f"pulse_{iteration:04d}_pre_green_red")
                        pre_green_roi = _roi_intensity(frame)
                        emit({
                            "type": "roi_intensity",
                            "label": "pre_green_red",
                            "iteration": iteration,
                            "green_duration_s": green_duration_s,
                            "green_duration_ms": green_duration_ms,
                            "frame_path": str(path),
                            **pre_green_roi,
                        })

                    green_phase_config = bench_state.pulse_config_snapshot() or cycle_config
                    green_level = green_phase_config["green_level"]
                    _show_light(LightMode.green, 0, green_level)
                    emit(_light_event(
                        "green",
                        0,
                        green_level,
                        "green_flash",
                        iteration,
                        {"green_duration_s": green_duration_s, "green_duration_ms": green_duration_ms},
                    ))
                    _green_hold = 0.012 if (raw_measurer is not None and raw_measurer.is_started) else green_duration_s
                    _sleep_abortable(_green_hold)
                    if bench_state.should_abort():
                        bench_state.state = RunState.aborted
                        emit({"type": "aborted", "iteration": iteration})
                        return

                    post_read_config = bench_state.pulse_config_snapshot() or cycle_config
                    red_level = post_read_config["red_level"]
                    _show_light(LightMode.red, red_level, 0)
                    emit(_light_event(
                        "red",
                        red_level,
                        0,
                        "post_green_read",
                        iteration,
                        {"green_duration_s": green_duration_s, "green_duration_ms": green_duration_ms},
                    ))

                    _sleep_abortable(0.012)  # hold for frame flush after green->red
                    # Raw 10-bit measurement (preferred path)
                    if raw_measurer is not None and raw_measurer.is_started and raw_baseline_vals is not None:
                        raw_result = raw_measurer.measure_response(
                            n_frames=2,
                            baseline_values=raw_baseline_vals,
                        )
                        expected_product = cycle_config["red_level"] * green_level
                        emit({
                            "type": "multiply_result",
                            "iteration": iteration,
                            "red_level": cycle_config["red_level"],
                            "green_level": green_level,
                            "green_duration_ms": green_duration_ms,
                            "expected_product": expected_product,
                            "pre_red_mean": raw_result.pre_red_mean,
                            "post_red_mean": raw_result.post_red_mean,
                            "delta_red": raw_result.delta_red,
                            "delta_red_norm": raw_result.delta_red_norm,
                            "source": "raw10",
                            "raw_snr": raw_result.raw_snr,
                            "raw_bits": raw_result.raw_bits,
                            "mask_pixels": raw_measurer.calibration.mask_pixels,
                            "baseline_frames": raw_result.baseline_frames,
                            "response_frames": raw_result.response_frames,
                            "peak_delta": raw_result.peak_delta,
                        })

                    # 8-bit fallback path (capture_frames)
                    elif post_read_config["capture_frames"]:
                        frame, path = capture.grab_frame(f"pulse_{iteration:04d}_post_green_red")
                        post_green_roi = _roi_intensity(frame)
                        emit({
                            "type": "roi_intensity",
                            "label": "post_green_red",
                            "iteration": iteration,
                            "green_duration_s": green_duration_s,
                            "green_duration_ms": green_duration_ms,
                            "frame_path": str(path),
                            **post_green_roi,
                        })

                        if pre_green_roi is not None:
                            pre_red = pre_green_roi["red_mean"]
                            post_red = post_green_roi["red_mean"]
                            delta_red = post_red - pre_red
                            delta_red_norm = delta_red / pre_red if pre_red > 0 else 0.0
                            expected_product = cycle_config["red_level"] * green_level
                            emit({
                                "type": "multiply_result",
                                "iteration": iteration,
                                "red_level": cycle_config["red_level"],
                                "green_level": green_level,
                                "green_duration_ms": green_duration_ms,
                                "expected_product": expected_product,
                                "pre_red_mean": round(pre_red, 4),
                                "post_red_mean": round(post_red, 4),
                                "delta_red": round(delta_red, 4),
                                "delta_red_norm": round(delta_red_norm, 6),
                                "source": "8bit",
                            })

                    _cycle_ms = (time.time() - _cycle_start) * 1000
                    cycle_times.append(_cycle_ms)
                    _recent = cycle_times[-20:]
                    _avg_ms = sum(_recent) / len(_recent)
                    _sps = 1000.0 / _avg_ms if _avg_ms > 0 else 0
                    emit({
                        "type": "cycle_timing",
                        "iteration": iteration,
                        "cycle_ms": round(_cycle_ms, 1),
                        "avg_cycle_ms": round(_avg_ms, 1),
                        "samples_per_sec": round(_sps, 2),
                        "total_samples": iteration,
                    })
                    if not cycle_config["loop"]:
                        break

            bench_state.state = RunState.completed
            emit({"type": "run_complete", "phase": "pulse", "passed": True})
        except Exception as e:
            bench_state.state = RunState.failed
            bench_state.emit({"type": "error", "message": str(e)})
        finally:
            if raw_measurer is not None:
                try:
                    raw_measurer.stop()
                except Exception as e:
                    bench_state.emit({"type": "error", "message": f"Failed to stop raw measurer: {e}"})
                try:
                    _apply_camera_mode("normal")
                    bench_state.camera_mode = "normal"
                except Exception as e:
                    bench_state.emit({"type": "error", "message": f"Failed to restart RTSP after raw measure: {e}"})
            if projector is not None:
                try:
                    _show_light(LightMode.off)
                except Exception as e:
                    bench_state.emit({"type": "error", "message": f"Failed to turn pulse lights off: {e}"})
                    bench_state.set_light(LightMode.off)
                projector.close()

    threading.Thread(target=worker, daemon=True).start()
    return {"status": "started", "phase": "pulse"}


@app.post("/run/pulse/config")
def update_pulse_config(req: PulseControlRequest):
    if bench_state.state != RunState.running_pulse:
        raise HTTPException(409, "Pulse run is not active")

    current = bench_state.pulse_config_snapshot()
    if current is None:
        raise HTTPException(409, "Pulse run has no active config")

    updated = _updated_pulse_config(current, req)
    bench_state.set_pulse_config(updated)
    event = {
        "type": "pulse_config_updated",
        "red_duration_s": updated["red_duration_s"],
        "green_duration_s": updated["green_duration_s"],
        "green_duration_schedule_s": updated["green_duration_schedule_s"],
        "green_duration_schedule_ms": [round(d * 1000, 1) for d in updated["green_duration_schedule_s"]],
        "red_level": updated["red_level"],
        "green_level": updated["green_level"],
    }
    bench_state.emit(event)
    return {"status": "ok", "pulse_config": event}


@app.post("/light")
def set_light(req: LightRequest):
    if bench_state.is_running():
        raise HTTPException(409, "Experiment already running")
    if projector is None:
        raise HTTPException(503, "Hardware not initialized")

    with hardware_lock:
        projector.open()
        if req.mode == LightMode.off:
            _show_light_levels(0, 0)
        elif req.mode == LightMode.red:
            _show_light_levels(req.red_level if req.red_level is not None else 255, 0)
        elif req.mode == LightMode.green:
            _show_light_levels(0, req.green_level if req.green_level is not None else 255)
        elif req.mode == LightMode.both:
            _show_light_levels(
                req.red_level if req.red_level is not None else 255,
                req.green_level if req.green_level is not None else 255,
            )
        else:
            _show_light_levels(req.red_level or 0, req.green_level or 0)

    if bench_state.state in {RunState.aborted, RunState.completed, RunState.failed}:
        bench_state.state = RunState.idle

    event = {
        "type": "manual_light",
        **bench_state.light_snapshot(),
    }
    bench_state.emit(event)
    return {"status": "ok", "light": bench_state.light_snapshot()}


@app.post("/stop")
def stop_run():
    was_running = bench_state.is_running()
    bench_state.request_abort()
    errors: list[str] = []

    acquired = hardware_lock.acquire(blocking=False)
    try:
        if projector is not None and projector.is_open:
            try:
                _show_light(LightMode.off)
            except Exception as e:
                errors.append(str(e))
        elif acquired:
            try:
                _force_lasers_off()
            except Exception as e:
                errors.append(str(e))
    finally:
        if acquired:
            hardware_lock.release()

    bench_state.set_light(LightMode.off)
    bench_state.state = RunState.aborted if was_running else RunState.idle
    event = {
        "type": "manual_light",
        **bench_state.light_snapshot(),
        "phase": "stop",
    }
    if errors:
        event["errors"] = errors
    bench_state.emit(event)
    return {
        "status": "abort_requested" if was_running else "idle",
        "light": bench_state.light_snapshot(),
        "errors": errors,
    }




@app.post("/run/burst-read")
def run_burst_read(n_frames: int = 500, red_level: int = 200):
    """Read-only burst mode - no write cycle, max camera fps."""
    if bench_state.is_running():
        return {"status": "error", "message": "Another run is active"}

    bench_state.state = RunState.running_pulse
    bench_state.events.clear()

    def emit(event):
        bench_state.emit(event)

    def worker():
        measurer = None
        try:
            from raw_measure import RawPulseMeasurer
            import numpy as np
            measurer = RawPulseMeasurer()
            cal = measurer.start()
            bench_state.camera_mode = "experiment"
            emit({"type": "info", "message": f"Burst read: {cal.mask_pixels} mask px, {cal.fps:.1f} fps"})

            measurer.set_light(red_level=red_level, green_level=0)
            import time
            time.sleep(0.2)

            cycle_times = []
            readings = []
            t_start = time.monotonic()

            for i in range(n_frames):
                if bench_state.should_abort():
                    break
                t0 = time.monotonic()
                val = measurer.read_red()
                dt_ms = (time.monotonic() - t0) * 1000
                cycle_times.append(dt_ms)
                readings.append(val)

                if (i + 1) % 50 == 0 or i == n_frames - 1:
                    recent = cycle_times[-50:]
                    avg_ms = sum(recent) / len(recent)
                    fps_now = 1000 / avg_ms if avg_ms > 0 else 0
                    vals = np.array(readings[-50:])
                    elapsed = time.monotonic() - t_start
                    emit({
                        "type": "cycle_timing",
                        "iteration": i + 1,
                        "cycle_ms": round(dt_ms, 2),
                        "avg_cycle_ms": round(avg_ms, 2),
                        "samples_per_sec": round(fps_now, 1),
                        "total_samples": i + 1,
                    })
                    emit({
                        "type": "burst_read",
                        "iteration": i + 1,
                        "total": n_frames,
                        "fps": round(fps_now, 1),
                        "ms_per_frame": round(avg_ms, 2),
                        "mean": round(float(vals.mean()), 4),
                        "std": round(float(vals.std()), 4),
                        "snr": round(float(vals.mean() / vals.std()), 1) if vals.std() > 0 else 0,
                        "bits": round(float(np.log2(vals.mean() / vals.std())), 2) if vals.std() > 0 else 0,
                        "elapsed_s": round(elapsed, 2),
                        "effective_pixel_sps": round(fps_now * cal.mask_pixels, 0),
                    })

            all_vals = np.array(readings)
            elapsed = time.monotonic() - t_start
            overall_fps = len(readings) / elapsed
            emit({
                "type": "burst_complete",
                "total_frames": len(readings),
                "elapsed_s": round(elapsed, 2),
                "overall_fps": round(overall_fps, 1),
                "mean": round(float(all_vals.mean()), 4),
                "std": round(float(all_vals.std()), 4),
                "snr": round(float(all_vals.mean() / all_vals.std()), 1) if all_vals.std() > 0 else 0,
                "bits": round(float(np.log2(all_vals.mean() / all_vals.std())), 2) if all_vals.std() > 0 else 0,
                "mask_pixels": cal.mask_pixels,
                "effective_pixel_sps": round(overall_fps * cal.mask_pixels, 0),
            })
            bench_state.state = RunState.completed
            emit({"type": "run_complete", "phase": "burst_read", "passed": True})
        except Exception as e:
            bench_state.state = RunState.failed
            emit({"type": "error", "message": str(e)})
        finally:
            if measurer is not None:
                try:
                    measurer.stop()
                except Exception:
                    pass
            bench_state.camera_mode = "normal"

    threading.Thread(target=worker, daemon=True).start()
    return {"status": "started", "phase": "burst_read", "n_frames": n_frames}



@app.post("/run/turbo-cycle")
def run_turbo_cycle(
    n_cycles: int = 1000,
    red_level: int = 255,
    green_level: int = 255,
    green_flash_ms: float = 2.0,
    hold_ms: float = 9.0,
    reads_per_write: int = 1,
):
    """Turbo write-read cycling with stored baseline for max throughput."""
    if bench_state.is_running():
        return {"status": "error", "message": "Another run is active"}

    bench_state.state = RunState.running_pulse
    bench_state.events.clear()
    bench_state._abort_flag = False

    def emit(event):
        bench_state.emit(event)

    def worker():
        measurer = None
        try:
            import time
            import numpy as np
            from raw_measure import RawPulseMeasurer

            measurer = RawPulseMeasurer()
            cal = measurer.start()
            bench_state.camera_mode = "experiment"
            emit({"type": "info", "message": f"Turbo: {cal.mask_pixels} px, {cal.fps:.1f} fps, target {n_cycles} cycles"})

            measurer.set_light(red_level=red_level, green_level=0)
            time.sleep(0.1)
            baseline_readings = [measurer.read_red() for _ in range(20)]
            stored_baseline = float(np.mean(baseline_readings))
            baseline_noise = float(np.std(baseline_readings))
            emit({"type": "info", "message": f"Baseline: {stored_baseline:.2f} +/- {baseline_noise:.4f}"})

            cycle_times = []
            all_deltas = []
            all_snrs = []
            total_reads = 0
            t_start = time.monotonic()
            green_s = green_flash_ms / 1000.0
            hold_s = hold_ms / 1000.0

            for cycle in range(n_cycles):
                if bench_state.should_abort():
                    break

                t_cycle_start = time.monotonic()
                measurer.set_light(red_level=0, green_level=green_level)
                time.sleep(green_s)
                measurer.set_light(red_level=red_level, green_level=0)
                time.sleep(hold_s)

                deltas_this_cycle = []
                for read_idx in range(reads_per_write):
                    val = measurer.read_red()
                    delta = val - stored_baseline
                    deltas_this_cycle.append(delta)
                    total_reads += 1

                cycle_ms = (time.monotonic() - t_cycle_start) * 1000
                cycle_times.append(cycle_ms)
                best_delta = max(deltas_this_cycle, key=abs)
                snr = abs(best_delta) / baseline_noise if baseline_noise > 0 else 0
                bits = float(np.log2(snr)) if snr > 1 else 0
                all_deltas.append(best_delta)
                all_snrs.append(snr)

                if (cycle + 1) % 10 == 0 or cycle == 0 or cycle == n_cycles - 1:
                    recent = cycle_times[-20:]
                    avg_ms = sum(recent) / len(recent)
                    cycles_per_sec = 1000 / avg_ms if avg_ms > 0 else 0
                    reads_per_sec = cycles_per_sec * reads_per_write
                    pixel_sps = reads_per_sec * cal.mask_pixels
                    elapsed = time.monotonic() - t_start
                    good_snrs = [s for s in all_snrs if s > 3]
                    n_good = len(good_snrs)
                    median_snr = float(np.median(good_snrs)) if n_good > 0 else 0
                    avg_bits = float(np.log2(median_snr * np.sqrt(n_good))) if n_good > 0 and median_snr * np.sqrt(n_good) > 1 else 0

                    emit({
                        "type": "cycle_timing",
                        "iteration": cycle + 1,
                        "cycle_ms": round(cycle_ms, 1),
                        "avg_cycle_ms": round(avg_ms, 1),
                        "samples_per_sec": round(reads_per_sec, 1),
                        "total_samples": total_reads,
                    })
                    emit({
                        "type": "multiply_result",
                        "iteration": cycle + 1,
                        "red_level": red_level,
                        "green_level": green_level,
                        "green_duration_ms": green_flash_ms,
                        "expected_product": red_level * green_level,
                        "pre_red_mean": round(stored_baseline, 4),
                        "post_red_mean": round(val, 4),
                        "delta_red": round(best_delta, 4),
                        "delta_red_norm": round(best_delta / stored_baseline, 6) if stored_baseline > 0 else 0,
                        "source": "turbo",
                        "raw_snr": round(snr, 1),
                        "raw_bits": round(bits, 2),
                        "mask_pixels": cal.mask_pixels,
                        "baseline_frames": 0,
                        "response_frames": reads_per_write,
                        "peak_delta": round(best_delta, 4),
                    })

                    if (cycle + 1) % 50 == 0 or cycle == n_cycles - 1:
                        emit({
                            "type": "throughput_log",
                            "cycle": cycle + 1,
                            "total_cycles": n_cycles,
                            "elapsed_s": round(elapsed, 2),
                            "cycles_per_sec": round(cycles_per_sec, 1),
                            "reads_per_sec": round(reads_per_sec, 1),
                            "pixel_samples_per_sec": round(pixel_sps, 0),
                            "camera_fps_ceiling": round(cal.fps, 1),
                            "at_camera_ceiling": cycles_per_sec >= cal.fps * 0.9,
                            "median_single_shot_bits": round(float(np.log2(median_snr)) if median_snr > 1 else 0, 1),
                            "accumulated_precision_bits": round(avg_bits, 1),
                            "good_shots_pct": round(100 * n_good / (cycle + 1), 0),
                            "target_1000_sps": reads_per_sec >= 1000,
                        })

            elapsed = time.monotonic() - t_start
            overall_cps = len(cycle_times) / elapsed if elapsed > 0 else 0
            overall_rps = total_reads / elapsed if elapsed > 0 else 0
            good_snrs = [s for s in all_snrs if s > 3]
            emit({
                "type": "turbo_complete",
                "total_cycles": len(cycle_times),
                "total_reads": total_reads,
                "elapsed_s": round(elapsed, 2),
                "cycles_per_sec": round(overall_cps, 1),
                "reads_per_sec": round(overall_rps, 1),
                "pixel_samples_per_sec": round(overall_rps * cal.mask_pixels, 0),
                "median_snr": round(float(np.median(good_snrs)) if good_snrs else 0, 1),
                "good_shots_pct": round(100 * len(good_snrs) / len(all_snrs), 0) if all_snrs else 0,
            })
            bench_state.state = RunState.completed
            emit({"type": "run_complete", "phase": "turbo_cycle", "passed": True})
        except Exception as e:
            bench_state.state = RunState.failed
            emit({"type": "error", "message": str(e)})
        finally:
            if measurer is not None:
                try:
                    measurer.set_light(red_level=0, green_level=0)
                    measurer.stop()
                except Exception:
                    pass
            bench_state.camera_mode = "normal"

    threading.Thread(target=worker, daemon=True).start()
    return {"status": "started", "phase": "turbo_cycle", "n_cycles": n_cycles, "reads_per_write": reads_per_write}

@app.get("/stream")
async def stream_events():
    queue = bench_state.subscribe()

    async def event_generator():
        import json

        for past_event in bench_state.events:
            yield f"data: {json.dumps(past_event)}\n\n"

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if event is None:
                        break
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        finally:
            bench_state.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/frames/{name}")
def get_frame(name: str):
    frame_path = Path("/tmp/bench_frames") / name
    if not frame_path.exists():
        raise HTTPException(404, "Frame not found")
    return FileResponse(frame_path, media_type="image/png")


@app.get("/events")
def get_events():
    return {"events": bench_state.events}


def _with_sensor_snapshot(event: dict[str, Any]) -> dict[str, Any]:
    if sensors is None:
        return event
    if event.get("type") not in {
        "step",
        "pre_write",
        "green_write",
        "linearity_fit",
        "delta_t",
        "result",
    }:
        return event
    event = dict(event)
    event["aux_sensors"] = sensors.read_all()
    return event


def _show_light(mode: LightMode, red_level: int = 0, green_level: int = 0) -> None:
    if projector is None:
        raise RuntimeError("Projector not initialized")

    if mode == LightMode.off:
        _show_light_levels(0, 0)
    elif mode == LightMode.red:
        _show_light_levels(red_level, 0)
    elif mode == LightMode.green:
        _show_light_levels(0, green_level)
    elif mode == LightMode.both:
        _show_light_levels(red_level, green_level)


def _show_light_levels(red_level: int = 0, green_level: int = 0) -> None:
    if projector is None:
        raise RuntimeError("Projector not initialized")
    projector.show_color(red_level, green_level, 0, settle=False)
    bench_state.set_light_levels(red_level, green_level)


def _light_event(
    mode: str,
    red_level: int,
    green_level: int,
    phase: str,
    iteration: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "type": "light_state",
        "mode": mode,
        "red_level": red_level,
        "green_level": green_level,
        "phase": phase,
    }
    if iteration is not None:
        event["iteration"] = iteration
    if extra:
        event.update(extra)
    return event


def _validated_green_duration_schedule(req: PulseRequest) -> list[float]:
    return _validate_green_duration_schedule(req.green_duration_schedule_s or [req.green_duration_s])


def _pulse_config_from_request(req: PulseRequest) -> dict[str, Any]:
    return {
        "red_duration_s": float(req.red_duration_s),
        "green_duration_s": float(req.green_duration_s),
        "green_duration_schedule_s": _validated_green_duration_schedule(req),
        "red_level": int(req.red_level),
        "green_level": int(req.green_level),
        "loop": bool(req.loop),
        "capture_frames": bool(req.capture_frames),
        "raw_measure": bool(req.raw_measure),
    }


def _updated_pulse_config(current: dict[str, Any], req: PulseControlRequest) -> dict[str, Any]:
    updated = dict(current)
    fields_set = req.model_fields_set

    if "red_duration_s" in fields_set and req.red_duration_s is not None:
        updated["red_duration_s"] = float(req.red_duration_s)
    if "green_duration_s" in fields_set and req.green_duration_s is not None:
        updated["green_duration_s"] = float(req.green_duration_s)
    if "red_level" in fields_set and req.red_level is not None:
        updated["red_level"] = int(req.red_level)
    if "green_level" in fields_set and req.green_level is not None:
        updated["green_level"] = int(req.green_level)

    if "green_duration_schedule_s" in fields_set:
        durations = req.green_duration_schedule_s
        if durations:
            updated["green_duration_schedule_s"] = _validate_green_duration_schedule(durations)
        else:
            updated["green_duration_schedule_s"] = [float(updated["green_duration_s"])]
    elif "green_duration_s" in fields_set and len(updated.get("green_duration_schedule_s", [])) <= 1:
        updated["green_duration_schedule_s"] = [float(updated["green_duration_s"])]

    return updated


def _validate_green_duration_schedule(durations: list[float]) -> list[float]:
    if len(durations) > 256:
        raise HTTPException(422, "green_duration_schedule_s may contain at most 256 durations")

    normalized: list[float] = []
    for duration in durations:
        value = float(duration)
        if value < 0.01 or value > 10.0:
            raise HTTPException(422, "green durations must be between 0.01s and 10.0s")
        normalized.append(value)
    return normalized


def _sleep_abortable(seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if bench_state.should_abort():
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.01, remaining))


def _roi_intensity(frame: np.ndarray) -> dict[str, Any]:
    arr = np.asarray(frame)
    if arr.ndim == 2:
        red = green = blue = arr
    else:
        red = arr[:, :, 0]
        green = arr[:, :, 1]
        blue = arr[:, :, 2]

    pixel_count = int(arr.shape[0] * arr.shape[1])
    red_sum = int(np.sum(red, dtype=np.float64))
    green_sum = int(np.sum(green, dtype=np.float64))
    blue_sum = int(np.sum(blue, dtype=np.float64))

    return {
        "pixel_count": pixel_count,
        "red_sum": red_sum,
        "green_sum": green_sum,
        "blue_sum": blue_sum,
        "red_mean": round(red_sum / pixel_count, 2) if pixel_count else 0.0,
        "green_mean": round(green_sum / pixel_count, 2) if pixel_count else 0.0,
        "blue_mean": round(blue_sum / pixel_count, 2) if pixel_count else 0.0,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
