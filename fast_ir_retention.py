#!/usr/bin/env python3
"""Fast M-state decay measurement — runs DIRECTLY on the Pi (no HTTP).

Uses the AD7606 parallel-bus reader and laser GPIO controller for maximum
sample rate. Protocol:
  1. Dark baseline (N frames)
  2. Green write pulse (variable duration, typically 1-100ms)
  3. Immediate red-probe burst — read ADC as fast as possible for capture_duration
  4. Recovery

The AD7606 is read in a tight loop with per-frame timestamps for μs-scale
M-state lifetime fitting. Writes raw data as JSON for offline analysis.

Usage (on the Pi):
  sudo python3 fast_ir_retention.py br-retention-1 /tmp
  # or with custom settings:
  GREEN_WRITE_MS=10 CAPTURE_DURATION_MS=200 python3 fast_ir_retention.py br-retention-1 /tmp
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# --- AD7606 direct access (fast mmap version) ---
from ad7606_fast import FastAD7606, to_signed_16

# --- Laser GPIO via mmap (bypass RPi.GPIO PWM issues) ---
import mmap as _mmap_module
import os as _os_module
import struct as _struct_module

# GPIO register offsets (from ad7606_fast.py)
_GPIO_BASE = 0x00
_GPFSEL0 = 0x00
_GPFSEL1 = 0x04
_GPFSEL2 = 0x08
_GPSET0  = 0x1C
_GPCLR0  = 0x28

# Laser pins (BCM)
_PROBE_PIN = int(os.environ.get("FAST_IR_PROBE_PIN", "23"))  # IR laser
_GREEN_PIN = int(os.environ.get("VIVONICS_LASER_GREEN_PIN", "24"))

class LaserControl:
    """Minimal laser on/off via mmap GPIO — no PWM, just full on/off."""
    
    def __init__(self):
        self._fd = None
        self._map = None
    
    def open(self):
        self._fd = _os_module.open("/dev/gpiomem", _os_module.O_RDWR | _os_module.O_SYNC)
        self._map = _mmap_module.mmap(self._fd, 4096, _mmap_module.MAP_SHARED,
                              _mmap_module.PROT_READ | _mmap_module.PROT_WRITE)
        # Set red and green pins as outputs
        for pin in (_PROBE_PIN, _GREEN_PIN):
            reg = _GPFSEL0 + (pin // 10) * 4
            shift = (pin % 10) * 3
            mask = 0b111 << shift
            val = _struct_module.unpack_from('<I', self._map, reg)[0] & ~mask
            val |= (0b001 << shift)
            self._map[reg:reg+4] = _struct_module.pack('<I', val)
        self.off()
    
    def set(self, probe: int = 0, green: int = 0):
        if probe:
            self._map[_GPSET0:_GPSET0+4] = _struct_module.pack('<I', 1 << _PROBE_PIN)
        else:
            self._map[_GPCLR0:_GPCLR0+4] = _struct_module.pack('<I', 1 << _PROBE_PIN)
        if green:
            self._map[_GPSET0:_GPSET0+4] = _struct_module.pack('<I', 1 << _GREEN_PIN)
        else:
            self._map[_GPCLR0:_GPCLR0+4] = _struct_module.pack('<I', 1 << _GREEN_PIN)
    
    def off(self):
        self.set(0, 0)
    
    def close(self):
        self.off()
        if self._map:
            self._map.close()
            self._map = None
        if self._fd:
            _os_module.close(self._fd)
            self._fd = None


# ── configurable constants ──────────────────────────────────────────
GREEN_LEVEL = int(os.environ.get("FAST_IR_GREEN_LEVEL", "255"))
RED_LEVEL = int(os.environ.get("FAST_IR_RED_LEVEL", "255"))
GREEN_WRITE_MS = int(os.environ.get("FAST_IR_GREEN_WRITE_MS", "10"))
CAPTURE_DURATION_MS = int(os.environ.get("FAST_IR_CAPTURE_DURATION_MS", "200"))
BASELINE_FRAMES = int(os.environ.get("FAST_IR_BASELINE_FRAMES", "50"))
REPS = int(os.environ.get("FAST_IR_REPS", "20"))
RECOVER_MS = int(os.environ.get("FAST_IR_RECOVER_MS", "500"))
SAMPLE_CHANNEL_INDEX = int(os.environ.get("FAST_IR_SAMPLE_CHANNEL", "2"))  # 1-based
REF_CHANNEL_INDEX = int(os.environ.get("FAST_IR_REF_CHANNEL", "1"))        # 1-based

OUT_DIR = Path(os.environ.get("FAST_IR_OUT_DIR", "/tmp"))


def _level_from_env(name: str, default: int) -> int:
    val = int(os.environ.get(name, str(default)))
    return max(0, min(255, val))


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "retention"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    out_path = out_dir / f"fast_ir_retention_{label}_{timestamp}.json"

    green_level = _level_from_env("FAST_IR_GREEN_LEVEL", GREEN_LEVEL)
    red_level = _level_from_env("FAST_IR_RED_LEVEL", RED_LEVEL)
    green_write_ms = int(os.environ.get("FAST_IR_GREEN_WRITE_MS", str(GREEN_WRITE_MS)))
    capture_duration_ms = int(os.environ.get("FAST_IR_CAPTURE_DURATION_MS", str(CAPTURE_DURATION_MS)))
    baseline_frames = int(os.environ.get("FAST_IR_BASELINE_FRAMES", str(BASELINE_FRAMES)))
    reps = int(os.environ.get("FAST_IR_REPS", str(REPS)))
    recover_ms = int(os.environ.get("FAST_IR_RECOVER_MS", str(RECOVER_MS)))

    print("=" * 60)
    print("FAST IR PROBE DECAY MEASUREMENT")
    print(f"Green: level={green_level} write={green_write_ms}ms")
    print(f"IR:   level={red_level}")
    print(f"Capture: {capture_duration_ms}ms, reps={reps}")
    print(f"ADC: ch{REF_CHANNEL_INDEX} (ref), ch{SAMPLE_CHANNEL_INDEX} (sample)")
    print("=" * 60)

    # --- initialize hardware ---
    print("\nInitializing Fast AD7606 (mmap)...")
    adc = FastAD7606()
    adc.open()

    print("Initializing laser GPIO (mmap)...")
    laser = LaserControl()
    laser.open()
    # lasers start off from LaserControl.open() -> self.off()
    time.sleep(0.1)

    # Quick ADC warmup
    for _ in range(10):
        adc.read_frame()
    print("Hardware ready.\n")

    # --- measurement loop ---
    all_reps: list[dict[str, Any]] = []
    total_started = time.perf_counter()

    for rep in range(reps):
        rep_started = time.perf_counter()

        # ── 1. baseline (dark) ──
        laser.off()
        time.sleep(0.005)  # settle
        baseline_frames_data: list[dict[str, Any]] = []
        for _ in range(baseline_frames):
            raw = adc.read_frame()
            baseline_frames_data.append({
                "ch1": to_signed_16(raw[0]),
                "ch2": to_signed_16(raw[1]),
                "ch3": to_signed_16(raw[2]),
                "ch4": to_signed_16(raw[3]),
                "ch5": to_signed_16(raw[4]),
                "ch6": to_signed_16(raw[5]),
                "ch7": to_signed_16(raw[6]),
                "ch8": to_signed_16(raw[7]),
            })

        # ── 2. green write ──
        write_start = time.perf_counter()
        laser.set(probe=0, green=1)  # full on, no PWM
        # Busy-wait for precise write duration
        while (time.perf_counter() - write_start) * 1000 < green_write_ms:
            pass
        laser.off()

        # ── 3. red-probe capture burst ──
        capture_start = time.perf_counter()
        laser.set(probe=1, green=0)  # full on, no PWM
        capture_frames: list[dict[str, Any]] = []
        while (time.perf_counter() - capture_start) * 1000 < capture_duration_ms:
            frame_start = time.perf_counter()
            raw = adc.read_frame()
            frame_end = time.perf_counter()
            elapsed_us = (frame_start - capture_start) * 1_000_000
            capture_frames.append({
                "elapsed_us": round(elapsed_us, 1),
                "read_us": round((frame_end - frame_start) * 1_000_000, 1),
                "ch1": to_signed_16(raw[0]),
                "ch2": to_signed_16(raw[1]),
                "ch3": to_signed_16(raw[2]),
                "ch4": to_signed_16(raw[3]),
                "ch5": to_signed_16(raw[4]),
                "ch6": to_signed_16(raw[5]),
                "ch7": to_signed_16(raw[6]),
                "ch8": to_signed_16(raw[7]),
            })
        laser.off()
        capture_end = time.perf_counter()
        actual_capture_ms = (capture_end - capture_start) * 1000

        # ── 4. recovery ──
        laser.off()
        rep_ended = time.perf_counter()

        # Stats for this rep
        ch_sample_idx = SAMPLE_CHANNEL_INDEX - 1
        ch_ref_idx = REF_CHANNEL_INDEX - 1
        baseline_sample = [f[list(f.keys())[ch_sample_idx + 2]] for f in baseline_frames_data]  # +2 for elapsed_us,read_us
        capture_sample = [f[list(f.keys())[ch_sample_idx + 2]] for f in capture_frames]
        baseline_ref = [f[list(f.keys())[ch_ref_idx + 2]] for f in baseline_frames_data]
        capture_ref = [f[list(f.keys())[ch_ref_idx + 2]] for f in capture_frames]

        # Key names
        ch_keys = ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7", "ch8"]
        sample_key = ch_keys[SAMPLE_CHANNEL_INDEX - 1]
        ref_key = ch_keys[REF_CHANNEL_INDEX - 1]

        baseline_sample_vals = [f[sample_key] for f in baseline_frames_data]
        capture_sample_vals = [f[sample_key] for f in capture_frames]

        import statistics
        rep_data = {
            "rep": rep,
            "baseline_mean_sample": round(statistics.fmean(baseline_sample_vals), 3) if baseline_sample_vals else 0,
            "baseline_std_sample": round(statistics.stdev(baseline_sample_vals), 3) if len(baseline_sample_vals) > 1 else 0,
            "capture_frame_count": len(capture_frames),
            "actual_capture_ms": round(actual_capture_ms, 3),
            "capture_rate_hz": round(len(capture_frames) / (actual_capture_ms / 1000), 1) if actual_capture_ms > 0 else 0,
            "sample_channel": sample_key,
            "ref_channel": ref_key,
            "baseline_frames": baseline_frames_data,
            "capture_frames": capture_frames,
        }
        all_reps.append(rep_data)

        print(
            f"  rep {rep+1:2d}/{reps}: "
            f"{len(capture_frames)} frames in {actual_capture_ms:.1f}ms "
            f"({rep_data['capture_rate_hz']:.0f} Hz)  "
            f"baseline={rep_data['baseline_mean_sample']:.1f}±{rep_data['baseline_std_sample']:.1f}"
        )

        # Recovery between reps
        if rep < reps - 1:
            time.sleep(recover_ms / 1000.0)

    total_ended = time.perf_counter()

    # ── cleanup ──
    laser.off()
    time.sleep(0.05)
    laser.close()
    adc.close()

    # ── compute average frame rate ──
    all_rates = [r["capture_rate_hz"] for r in all_reps]
    import statistics
    avg_rate = statistics.fmean(all_rates) if all_rates else 0

    output = {
        "experiment": "fast_ir_retention",
        "timestamp": timestamp,
        "sample_label": label,
        "config": {
            "green_level": green_level,
            "red_level": red_level,
            "green_write_ms": green_write_ms,
            "capture_duration_ms": capture_duration_ms,
            "baseline_frames": baseline_frames,
            "reps": reps,
            "recover_ms": recover_ms,
            "sample_channel": SAMPLE_CHANNEL_INDEX,
            "ref_channel": REF_CHANNEL_INDEX,
        },
        "protocol": {
            "hypothesis": (
                "After a brief green write pulse, the M-state population decays "
                "exponentially. By reading the red-probe ADC channel as fast as "
                "possible after green off, we capture the decay curve with "
                "per-frame μs timestamps for lifetime fitting."
            ),
        },
        "statistics": {
            "rep_count": reps,
            "total_duration_s": round(total_ended - total_started, 3),
            "avg_capture_rate_hz": round(avg_rate, 1),
            "total_capture_frames": sum(r["capture_frame_count"] for r in all_reps),
        },
        "reps": all_reps,
    }

    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Average capture rate: {avg_rate:.0f} Hz")
    print(f"  Total frames: {output['statistics']['total_capture_frames']}")
    print(f"  Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
