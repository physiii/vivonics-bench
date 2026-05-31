# Reactor TIA circuit — 2× OPA380AID (JLCPCB build)

Front-end that lifts the ~1 % red M-state modulation above the fixed ADC/digital
floor the passive 100 kΩ load could never beat. Full design rationale + noise
budget: `../../docs/program/REACTOR_TIA_DESIGN.md` (parent repo).
Datasheets: `../docs/datasheets/opa380.pdf`, `bpw34.pdf`.

Conventions copied from the working office board
(`~/devices/access-controller/circuits/controller` on host `office`): KiCad
`(version 20230121) (generator eeschema)`; custom symbol fields named exactly
**`Part Number`** (MPN) and **`LCSC`** (C-number); JLCPCB BOM = 4 columns
`Comment,Designator,Footprint,LCSC` (quoted, like-parts grouped) — i.e. what the
**JLCPCB Fabrication Toolkit** KiCad plugin emits.

## Files

- `reactor_tia.kicad_sch` — KiCad schematic (v7 format; opens in KiCad 7 & 8).
  Validated: `kicad-cli sch export netlist` → all 9 nets match the intended netlist.
- `reactor_tia_bom_jlcpcb.csv` — JLCPCB BOM (office 4-column format).
- `gen_reactor_tia_sch.py` — generator for **both** files (always in sync). Edit
  the tables at the top and re-run `python3 gen_reactor_tia_sch.py`.

## Topology (one channel)

```
        650 nm longpass in front of D1 (blocks green-write leak)
  D1 BPW34  cathode -> SUMMING ;  anode -> GND  (zero bias)
  U1 OPA380AID TIA:  -IN=SUMMING  +IN=VBIAS  OUT=V_TIA
     R1 = 10M 1% across SUMMING<->V_TIA   (size so red pedestal -> ~3 V)
     C1 = 10pF C0G across SUMMING<->V_TIA (band-limit ~1.6 kHz)
  Bias:  R4/R5 = 100k/10k off +5V -> 0.45 V -> R6/C4 RC filter -> VBIAS
  U2 OPA380AID 2nd stage: unity-gain Sallen-Key 2-pole LP, fc ~1.57 kHz
     R2=R3=68k, C2=2.2n (fb), C3=1n (to GND) ;  OUT=V_FILT
  J1 -> AD7606:  V_TIA = CHn (pedestal+signal),  V_FILT = CHn+1 (anti-aliased)
```

**Two OPA380AID singles, not the OPA2380 dual** — the dual is **not stocked at
JLCPCB**; the single (C201677) is in stock. `V_out = VBIAS + I_pd·R_f`; size R_f
from the *measured* red photocurrent so the DC pedestal sits ~3 V (1 % M-signal
→ ~170 codes regardless of R_f). ~300–470 nA now → 10 M; µA-scale → swap R1→1 M,
C1→~100 pF.

**5 V is plenty — 12 V not needed.** At ~1.5 kHz the band-limit buries the
`e_n·C_d` term under R_f Johnson noise, so zero-bias (D1 anode→GND) is the
default. Reverse bias only helps at ~10 kHz (then a −5 V ICL7660 on the anode,
not 12 V). See `REACTOR_TIA_DESIGN.md §5b`.

## BOM / LCSC numbers

`reactor_tia_bom_jlcpcb.csv` is upload-ready. Status of each LCSC #:

| Part | Value | LCSC | Status |
|---|---|---|---|
| U1, U2 | OPA380AID (SOIC-8) | **C201677** | ✅ verified, in stock (~$3.8) |
| D1 | BPW34 (THT) | **C85128** | ✅ verified (hand-add) |
| C4 | 10 µF 0805 | **C15850** | ✅ verified (office board) |
| C5, C7 | 100 nF 0402 | **C1525** | ✅ verified (office board) |
| C6 | 1 µF 0402 | **C52923** | ✅ verified (office board) |
| R4 | 100 k 0603 | **C25803** | ✅ verified |
| R5, R6 | 10 k 0603 | **C25804** | ✅ high confidence |
| R2, R3 | 68 k 0603 | C36871 | ⚠ verify (MPN 0603WAF6802T5E) |
| R1 | 10 M 0603 | C57129 | ⚠ best-effort — **verify** (MPN 0603WAF1005T5E) |
| C1 | 10 pF C0G 0603 | C168544 | ⚠ best-effort — **verify** |
| C2 | 2.2 nF C0G 0603 | C108194 | ⚠ best-effort — **verify** |
| C3 | 1 nF C0G 0603 | C57112 | ⚠ best-effort — **verify** |

The ⚠ rows are commodity passives whose exact C-number I couldn't fully confirm;
the MPN is in each symbol's `Part Number` field, and **JLCPCB's BOM uploader
validates every LCSC# and matches by MPN** — so it flags any stale number at
upload. Ping me to finalize the ⚠ ones (quick lookup pass).

## Assembly at JLCPCB (3 files; BOM is one)

The office board uses the **JLCPCB Fabrication Toolkit** KiCad plugin, which emits
the BOM + CPL + Gerbers from the laid-out PCB. Workflow:

1. Open `reactor_tia.kicad_sch` in KiCad → footprints already assigned →
   *Tools → Update PCB from Schematic* → place & route.
2. Run the Fabrication Toolkit plugin → it writes `Manufacturer/` (Gerbers,
   `*-top-pos.csv` CPL, and a BOM identical in format to the CSV here).
3. Upload to JLCPCB. (Or upload Gerbers + this CSV + CPL manually.)

**SMT-assembled (15 parts):** U1, U2, R1–R6, C1–C7 — top side.
**Hand-add (Assembly excluded from the SMT BOM):**
- **D1 BPW34** — leaded THT, and you *want* it positionable for optical alignment
  to the reactor/fiber. Don't reflow it flat; bring it to 2 pads / a 2-pin
  connector and cable it.
- **J1, J2** — 2.54 mm THT headers; hand-solder.

## Layout notes (kills the pickup)

- Mount D1 **at** the U1 input; flying leads are the antenna that wrecked the
  passive rig. Guard ring on the SUMMING node, driven at VBIAS.
- Whole PD + TIA in a grounded Faraday can that doubles as the optical baffle.
- Star ground: keep laser-driver/GPIO switching return off the analog return.
- Enable AD7606 oversampling (OS0–2, currently tied GND) for a free sinc
  anti-alias + averaging stage.

## 2nd-stage variant: modulation-only channel

To trade the absolute pedestal for extra resolution on the M-modulation, rebuild
U2 as an AC-coupled gain stage: series cap (~1 µF) from `V_TIA` into a
non-inverting ×100 (100 k / 1 k), HPF corner ~0.3 Hz (keeps ms kinetics, strips
the DC red-through + slow drift). Feed to a separate AD7606 channel.
