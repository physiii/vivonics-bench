#!/usr/bin/env python3
"""Compatibility wrapper for older bench-circuit workflows.

The MCU sheet is now generated directly by gen_laser_controller.py.  This
wrapper intentionally does not copy the access-controller MCU sheet wholesale;
that old approach pulled unrelated GPIO labels, buttons, USB bridge circuitry,
and stale nets into the bench design.
"""

from gen_laser_controller import atomic_write, build_mcu


if __name__ == "__main__":
    atomic_write("mcu.kicad_sch", build_mcu())
    print("wrote mcu.kicad_sch from clean bench MCU generator")
