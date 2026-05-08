"""bR photocycle measurement protocol.

Phase 1: Red fixed-state linearity check
Phase 2: Green-write / red-read sweep with M-state lifetime fitting

Emits structured metric events via a callback for SSE streaming.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from scipy.optimize import curve_fit

from capture import Capture
from projector import Projector


@dataclass
class PhotocycleConfig:
    red_levels: tuple[int, ...] = (0, 32, 64, 96, 128, 160, 192)
    green_codes: tuple[int, ...] = (0, 16, 32, 64, 96, 128, 160, 192, 224, 255)
    read_delays_s: tuple[float, ...] = (0.0, 0.5, 1.0, 2.0, 5.0, 10.0)
    green_exposure_s: float = 1.0
    recovery_interval_s: float = 30.0
    frames_per_average: int = 4
    linearity_r2_threshold: float = 0.99
    min_linear_levels: int = 4
    min_delta_t_snr: float = 3.0
    monotonic_window: int = 4


@dataclass
class LinearityResult:
    red_codes: list[int] = field(default_factory=list)
    blank_means: list[float] = field(default_factory=list)
    sample_means: list[float] = field(default_factory=list)
    slope: float = 0.0
    intercept: float = 0.0
    r_squared: float = 0.0
    passed: bool = False
    chosen_read_level: int = 0


@dataclass
class PhotocycleResult:
    linearity: LinearityResult = field(default_factory=LinearityResult)
    delta_t_matrix: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    noise_floor: float = 0.0
    peak_delta_t: float = 0.0
    snr: float = 0.0
    monotonic_range: int = 0
    mstate_lifetime_ms: float = 0.0
    decay_tau_s: float = 0.0
    decay_amplitude: float = 0.0
    decay_r_squared: float = 0.0
    passed: bool = False


EventCallback = Callable[[dict[str, Any]], None]


def _noop_emit(event: dict[str, Any]) -> None:
    pass


def run_linearity_check(
    capture: Capture,
    projector: Projector,
    config: PhotocycleConfig,
    emit: EventCallback = _noop_emit,
    abort: Callable[[], bool] | None = None,
) -> LinearityResult:
    result = LinearityResult()

    emit({"type": "phase_start", "phase": 1, "name": "Red Linearity Check"})

    projector.off()
    time.sleep(0.5)
    emit({"type": "info", "message": "Capturing dark reference..."})
    capture.capture_dark_reference()
    emit({"type": "info", "message": "Dark reference captured"})

    for i, red_code in enumerate(config.red_levels):
        if abort and abort():
            emit({"type": "aborted"})
            return result

        projector.show_red(red_code)
        frame, path = capture.grab_averaged(config.frames_per_average, f"red{red_code:03d}")
        frame_ds = capture.subtract_dark(frame)
        red_mean = capture.red_channel_mean(frame_ds)

        result.red_codes.append(red_code)
        result.sample_means.append(red_mean)
        result.blank_means.append(red_mean)

        emit({
            "type": "step",
            "phase": 1,
            "step": i + 1,
            "total_steps": len(config.red_levels),
            "red_code": red_code,
            "sample_mean": round(red_mean, 2),
            "frame_path": str(path),
        })

    projector.off()

    x = np.array(result.red_codes, dtype=np.float64)
    y = np.array(result.sample_means, dtype=np.float64)

    if len(x) >= 2:
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        result.slope = float(slope)
        result.intercept = float(intercept)
        result.r_squared = r_squared
        result.passed = r_squared >= config.linearity_r2_threshold

        mid_idx = len(config.red_levels) // 2
        result.chosen_read_level = config.red_levels[mid_idx]

    emit({
        "type": "linearity_fit",
        "slope": round(result.slope, 4),
        "intercept": round(result.intercept, 4),
        "r_squared": round(result.r_squared, 6),
        "chosen_read_level": result.chosen_read_level,
        "passed": result.passed,
    })

    return result


def run_green_write_sweep(
    capture: Capture,
    projector: Projector,
    config: PhotocycleConfig,
    read_level: int,
    blank_reference: float,
    emit: EventCallback = _noop_emit,
    abort: Callable[[], bool] | None = None,
) -> PhotocycleResult:
    n_green = len(config.green_codes)
    n_delays = len(config.read_delays_s)
    transmission_matrix = np.zeros((n_green, n_delays))
    delta_t_matrix = np.zeros((n_green, n_delays))

    emit({
        "type": "phase_start",
        "phase": 2,
        "name": "Green-Write / Red-Read Sweep",
        "read_level": read_level,
        "blank_reference": round(blank_reference, 2),
    })

    for gi, green_code in enumerate(config.green_codes):
        if abort and abort():
            emit({"type": "aborted"})
            return PhotocycleResult()

        emit({
            "type": "green_code_start",
            "index": gi,
            "total": n_green,
            "green_code": green_code,
        })

        projector.show_red(read_level)
        pre_frame, _ = capture.grab_averaged(config.frames_per_average, f"g{green_code:03d}_pre")
        pre_frame_ds = capture.subtract_dark(pre_frame)
        pre_red = capture.red_channel_mean(pre_frame_ds)

        emit({
            "type": "pre_write",
            "green_code": green_code,
            "pre_red_mean": round(pre_red, 2),
        })

        if green_code > 0:
            projector.show_green(green_code)
            time.sleep(config.green_exposure_s)

        for di, delay_s in enumerate(config.read_delays_s):
            if abort and abort():
                emit({"type": "aborted"})
                return PhotocycleResult()

            if di == 0:
                projector.show_red(read_level)
            else:
                time.sleep(delay_s - (config.read_delays_s[di - 1] if di > 0 else 0))

            frame, path = capture.grab_averaged(
                config.frames_per_average, f"g{green_code:03d}_t{delay_s:.1f}s"
            )
            frame_ds = capture.subtract_dark(frame)
            i_sample = capture.red_channel_mean(frame_ds)

            T = i_sample / blank_reference if blank_reference > 0 else 0.0
            transmission_matrix[gi, di] = T

            emit({
                "type": "green_write",
                "green_code": green_code,
                "delay_s": delay_s,
                "i_sample": round(i_sample, 2),
                "transmission": round(T, 6),
                "frame_path": str(path),
            })

        if green_code > 0:
            emit({
                "type": "recovery_wait",
                "green_code": green_code,
                "seconds": config.recovery_interval_s,
            })
            time.sleep(config.recovery_interval_s)

    projector.off()

    baseline_row = transmission_matrix[0, :]
    for gi in range(n_green):
        delta_t_matrix[gi, :] = transmission_matrix[gi, :] - baseline_row

    for gi in range(n_green):
        for di in range(n_delays):
            emit({
                "type": "delta_t",
                "green_code": config.green_codes[gi],
                "delay_s": config.read_delays_s[di],
                "delta_t": round(float(delta_t_matrix[gi, di]), 6),
            })

    noise_floor = float(np.std(delta_t_matrix[0, :]))
    immediate_deltas = delta_t_matrix[:, 0]
    peak_delta_t = float(immediate_deltas[np.argmax(np.abs(immediate_deltas))])
    snr = abs(peak_delta_t) / noise_floor if noise_floor > 0 else 0.0
    monotonic_range = _longest_monotonic_run(np.abs(immediate_deltas))

    peak_gi = int(np.argmax(np.abs(immediate_deltas)))
    decay_curve = delta_t_matrix[peak_gi, :]
    delays_arr = np.array(config.read_delays_s)
    tau_s, amplitude, decay_r2 = fit_mstate_lifetime(delays_arr, decay_curve)

    result = PhotocycleResult(
        delta_t_matrix=delta_t_matrix,
        noise_floor=noise_floor,
        peak_delta_t=peak_delta_t,
        snr=snr,
        monotonic_range=monotonic_range,
        mstate_lifetime_ms=tau_s * 1000.0,
        decay_tau_s=tau_s,
        decay_amplitude=amplitude,
        decay_r_squared=decay_r2,
        passed=(snr >= config.min_delta_t_snr or monotonic_range >= config.monotonic_window),
    )

    emit({
        "type": "mstate_fit",
        "tau_ms": round(result.mstate_lifetime_ms, 1),
        "amplitude": round(amplitude, 6),
        "r_squared": round(decay_r2, 4),
        "peak_green_code": config.green_codes[peak_gi],
    })

    emit({
        "type": "result",
        "passed": result.passed,
        "snr": round(snr, 1),
        "peak_delta_t": round(peak_delta_t, 6),
        "noise_floor": round(noise_floor, 6),
        "monotonic_range": monotonic_range,
        "mstate_lifetime_ms": round(result.mstate_lifetime_ms, 1),
        "decay_r_squared": round(decay_r2, 4),
    })

    return result


def fit_mstate_lifetime(
    delays_s: np.ndarray, delta_t_curve: np.ndarray
) -> tuple[float, float, float]:
    if len(delays_s) < 3 or np.all(np.abs(delta_t_curve) < 1e-10):
        return 0.0, 0.0, 0.0

    def exp_decay(t: np.ndarray, A: float, tau: float, C: float) -> np.ndarray:
        return A * np.exp(-t / tau) + C

    A0 = float(delta_t_curve[0] - delta_t_curve[-1])
    tau0 = 2.0
    C0 = float(delta_t_curve[-1])

    try:
        popt, _ = curve_fit(
            exp_decay,
            delays_s,
            delta_t_curve,
            p0=[A0, tau0, C0],
            bounds=([-np.inf, 0.001, -np.inf], [np.inf, 60.0, np.inf]),
            maxfev=5000,
        )
        A_fit, tau_fit, C_fit = popt
        fitted = exp_decay(delays_s, *popt)
        ss_res = float(np.sum((delta_t_curve - fitted) ** 2))
        ss_tot = float(np.sum((delta_t_curve - delta_t_curve.mean()) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return float(tau_fit), float(A_fit), r_squared
    except (RuntimeError, ValueError):
        return 0.0, 0.0, 0.0


def _longest_monotonic_run(values: np.ndarray) -> int:
    if len(values) < 2:
        return len(values)
    best = 1
    current = 1
    for i in range(1, len(values)):
        if values[i] >= values[i - 1]:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best
