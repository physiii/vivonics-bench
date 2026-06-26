"""Stable mmap PWM laser controller — replaces RPi.GPIO software PWM.

Uses /dev/gpiomem with busy-wait timing for rock-solid PWM at any duty cycle.
Runs PWM in a background thread so the main thread can just set levels.
"""

from __future__ import annotations

import mmap
import os
import struct
import threading
import time

_GPFSEL0 = 0x00
_GPSET0  = 0x1C
_GPCLR0  = 0x28

class MmapPWMLaser:
    """Stable laser PWM via mmap GPIO — no RPi.GPIO, no pigpiod needed."""
    
    def __init__(self, red_pin=15, green_pin=24, ir_pin=23, blue_pin=14,
                 pwm_hz=250, active_high=True):
        self._pins = {"red": red_pin, "green": green_pin, "ir": ir_pin, "blue": blue_pin}
        self._active_high = active_high
        self._pwm_hz = pwm_hz
        self._period_us = 1_000_000 / pwm_hz
        self._levels = {"red": 0, "green": 0, "ir": 0, "blue": 0}
        self._fd = None
        self._map = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
    
    def open(self):
        self._fd = os.open("/dev/gpiomem", os.O_RDWR | os.O_SYNC)
        self._map = mmap.mmap(self._fd, 4096, mmap.MAP_SHARED,
                              mmap.PROT_READ | mmap.PROT_WRITE)
        for pin in self._pins.values():
            reg = _GPFSEL0 + (pin // 10) * 4
            shift = (pin % 10) * 3
            val = struct.unpack_from('<I', self._map, reg)[0] & ~(0b111 << shift)
            val |= (0b001 << shift)
            self._map[reg:reg+4] = struct.pack('<I', val)
        self._running = True
        self._thread = threading.Thread(target=self._pwm_loop, daemon=True)
        self._thread.start()
    
    def set_levels(self, red=0, green=0, infrared=0, blue=0):
        with self._lock:
            self._levels["red"] = max(0, min(255, int(red)))
            self._levels["green"] = max(0, min(255, int(green)))
            self._levels["ir"] = max(0, min(255, int(infrared)))
            self._levels["blue"] = max(0, min(255, int(blue)))
    
    def off(self):
        self.set_levels(0, 0, 0, 0)
    
    def close(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        # All off
        for pin in self._pins.values():
            self._map[_GPCLR0:_GPCLR0+4] = struct.pack('<I', 1 << pin)
        if self._map:
            self._map.close(); self._map = None
        if self._fd:
            os.close(self._fd); self._fd = None
    
    def _pwm_loop(self):
        """Background PWM thread — runs continuously at pwm_hz."""
        while self._running:
            cycle_start = time.perf_counter()
            
            with self._lock:
                levels = dict(self._levels)
            
            # Determine ON time per channel (in microseconds)
            for name, pin in self._pins.items():
                level = levels.get(name, 0)
                on_us = (level / 255.0) * self._period_us if level > 0 else 0
                
                if on_us > 0:
                    # Turn ON
                    if self._active_high:
                        self._map[_GPSET0:_GPSET0+4] = struct.pack('<I', 1 << pin)
                    else:
                        self._map[_GPCLR0:_GPCLR0+4] = struct.pack('<I', 1 << pin)
                    
                    # Wait ON time
                    while (time.perf_counter() - cycle_start) * 1_000_000 < on_us:
                        pass
                    
                    # Turn OFF
                    if self._active_high:
                        self._map[_GPCLR0:_GPCLR0+4] = struct.pack('<I', 1 << pin)
                    else:
                        self._map[_GPSET0:_GPSET0+4] = struct.pack('<I', 1 << pin)
            
            # Wait for rest of period
            elapsed = (time.perf_counter() - cycle_start) * 1_000_000
            remaining = self._period_us - elapsed
            if remaining > 10:  # Only sleep if >10μs remaining
                time.sleep(remaining / 1_000_000)
