#!/usr/bin/env python3
"""Compatibility wrapper for older bench-circuit workflows.

The bench MCU sheet is now the imported access-controller page.  The main
generator intentionally preserves ``mcu.kicad_sch`` instead of rebuilding it
from the old synthetic MCU helper.
"""

from pathlib import Path


if __name__ == "__main__":
    path = Path(__file__).resolve().parent / "mcu.kicad_sch"
    if not path.exists():
        raise SystemExit(f"missing imported MCU sheet: {path}")
    print(f"kept imported MCU sheet: {path}")
