# Passive First-Article AVL Lock

Scope: JLCPCB first-article bench order for `circuits/laser_controller.kicad_sch`
and `circuits/laser_controller.kicad_pcb`.

This lock freezes the passive MPN/LCSC set used by the generated JLCPCB BOM. It
does not replace JLCPCB quote-time availability/lifecycle checks, pulse/surge
derating for field use, or board-temperature measurement after assembly.

## Order Policy

- Do not substitute passive MPNs for the first article without rerunning
  `check_laser_controller_netlist.py`, `check_passive_derating.py`, and
  `check_passive_avl_lock.py`.
- Treat the generated BOM, POS, and this lock as one set; a quote-side passive
  substitution requires a new checkpoint commit.
- Quote-time lifecycle/stock check required: JLCPCB/LCSC availability, assembly
  tier, minimum order status, and substitute suggestions win over this static
  repository lock.
- Board-temperature measurement remains required before production release.
- Pulse/surge/current derating remains required before production or field use.

## Locked Capacitors

| MPN | LCSC | Count | Locked use |
|---|---:|---:|---|
| `0402B104K160CT` | `C83056` | 23 | 100 nF 0402 X7R local decoupling, bootstrap, MPD, and ADC filters |
| `0402CG101J500NT` | `C1546` | 1 | 100 pF 0402 C0G feed-forward capacitor |
| `CC0603JRNPO9BN100` | `C106245` | 8 | 10 pF 0603 C0G TIA/laser loop compensation |
| `CL21A106KAYNNNG` | `C318691` | 12 | 10 uF 0805 X5R local bulk/reference capacitors |
| `CL21A226MAQNNNE` | `C45783` | 4 | 22 uF 0805 X5R AP632 output banks |
| `CL31B106KBHNNNE` | `C89632` | 2 | 10 uF 1206 50 V VIN_24V ceramic input capacitors |
| `HGC0402R5105K250NTEJ` | `C7472946` | 14 | 1 uF 0402 X5R local decoupling and ADC REGCAP capacitors |
| `100CE22FS+P` | `C242011` | 1 | 22 uF 100 V SMD electrolytic VIN_24V bulk capacitor |

## Locked Resistors And Trimmers

| MPN | LCSC | Count | Locked use |
|---|---:|---:|---|
| `0603WAF1301T5E` | `C22767` | 1 | IR laser command limiter |
| `0603WAF3001T5E` | `C4211` | 1 | Green laser command limiter |
| `0603WAF4701T5E` | `C23162` | 1 | Blue laser command limiter |
| `0603WAF4752T5E` | `C23061` | 1 | CP2102N VBUS divider |
| `0603WAF7500T5E` | `C23241` | 1 | Red laser command limiter |
| `3224W-1-103E` | `C81348` | 4 | Bourns 10 k VBIAS SMD trimmers |
| `3224W-1-205E` | `C116323` | 4 | Bourns 2 M TIA feedback SMD trimmers |
| `CRCW060310K0FKEA` | `C844918` | 14 | 10 k 0603 bias, pull, and RJ45 LED/contact resistors |
| `RTT032491FTP` | `C103460` | 1 | 2.49 k monitor-PD bias shunt resistor |
| `ERJ2RKF1002X` | `C191123` | 8 | 10 k 0402 ESP32/CP2102 pull resistors |
| `FRC0402F2212TS` | `C2929993` | 2 | 22.1 k AP632 feedback and VBUS divider resistors |
| `FRC0603F1001TS` | `C2907002` | 16 | 1 k 0603 gate, sense, and ADC filter resistors |
| `FRC0603F2373TS` | `C2998117` | 1 | 237 k AP632 laser buck top feedback resistor |
| `HoCR2512-2W-10R-1%` | `C5123624` | 4 | 10 ohm 2512 2 W laser current sense resistors |
| `RTT032400FTP` | `C103446` | 4 | 240 ohm monitor-PD sense resistors |
| `RT0402BRD071KL` | `C852624` | 1 | 1 k precision CP2102N VBUS divider resistor |

## Remaining Production Evidence

This first-article lock is acceptable for ordering controlled bench prototypes.
Production release still needs current quote evidence for every C-code, a second
source or approved substitute plan for commodity passives, pulse/surge/current
derating for the 24 V input and laser-current paths, and board-temperature
measurement at the accepted duty cycle.
