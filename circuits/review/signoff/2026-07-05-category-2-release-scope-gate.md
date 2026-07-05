# Category 2 Release-Scope Gate

Date: 2026-07-05

Scope: Separate current JLCPCB fabrication/order readiness from first-article
and production-release readiness.

## Result

The review wrapper now reports two statuses:

- JLCPCB order package status
- First-article/production release status

Rows marked `FAIL` or `BLOCKED` still block the JLCPCB fabrication/order
package. Rows marked `DEFERRED` are real blockers for bench-use or production
release, but they are not evidence that the current Gerber/BOM/POS package is
invalid.

## Current Deferred Work

The release-readiness registry still tracks these first-article/production
items:

- monitor-PD optical calibration and fail-shutoff behavior
- signal-PD/TIA range calibration and AD7606 scaling checks
- per-diode laser optical-output, temperature, and firmware clamp validation
- AP2112 +3V3 current/temperature measurement or regulator change
- VIN24 production protection and buck startup/ripple/load-step/temperature
  validation
- passive quote-time AVL, substitution, pulse/surge/current derating, and board
  temperature evidence
- AD7606 firmware timing, two-DOUT readback, channel order, scaling, and known
  input validation

These items remain mandatory before trusting the board for bench measurements,
optical safety behavior, or production/field use.

## JLCPCB Package Evidence

The package-order evidence remains owned by:

- `python3 circuits/check_jlcpcb_order_package.py`
- KiCad ERC/DRC/parity rows in `python3 circuits/run_laser_controller_review.py`
- generated Gerbers/drills, BOM, and POS in `circuits/fab/` and
  `circuits/laser_controller_jlcpcb_package.zip`
