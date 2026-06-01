# Reactor TIA circuit — 2 channels × OPA380AID TIA (JLCPCB build)

Two independent transimpedance front-ends that lift the ~1 % red M-state
modulation above the fixed ADC/digital floor the passive 100 kΩ load could never
beat. **One op-amp per channel (TIA only — no analog 2nd-stage filter);**
anti-aliasing rides on the AD7606 oversampling. Full design rationale + noise
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
  Validated: `kicad-cli sch export netlist` → all 8 nets match the intended netlist.
- `reactor_tia_bom_jlcpcb.csv` — JLCPCB BOM (office 4-column format).
- `gen_reactor_tia_sch.py` — generator for **both** files (always in sync). Edit
  the tables at the top and re-run `python3 gen_reactor_tia_sch.py`.

## Topology (per channel — two identical channels)

```
        650 nm longpass in front of each Dn (blocks green-write leak)
  Dn BPW34  cathode -> SUMMING ;  anode -> GND  (zero bias)
  Un OPA380AID TIA:  -IN=SUMMING  +IN=VBIAS  OUT=V_CHn
     Rn = 10M 1% across SUMMING<->V_CHn   (size so red pedestal -> ~3 V)
     Cn = 10pF C0G across SUMMING<->V_CHn (band-limit -> ~1.6 kHz pole)
  Shared bias:  R3/R4 = 100k/10k off +5V -> 0.45 V -> R5/C3 RC filter -> VBIAS
                (ONE divider feeds BOTH + inputs)
  J1 -> AD7606:  V_CH1 = CHn,  V_CH2 = CHn+1     (J2 = +5 V / GND power in)
```

Channel 1 = signal; **Channel 2 = a matched copy** — use it as a ratiometric
reference PD (subtract laser RIN/drift) or a second optical plane. Identical
hardware either way; only the optics in front of `D2` decide its role.

**One op-amp per channel — no Sallen-Key.** The TIA's own `C_f` already sets a
~1.6 kHz pole; out-of-band noise is kept from folding into the slow sampled band
by the AD7606's hardware oversampling (sinc anti-alias), not an analog 2nd stage.
This is the `REACTOR_TIA_DESIGN.md §10` v1 build, doubled into two channels.
`V_out = VBIAS + I_pd·R_f`; size `R_f` from the *measured* red photocurrent so the
DC pedestal sits ~3 V (1 % M-signal → ~170 codes regardless of `R_f`). ~300–470 nA
now → 10 M; µA-scale → swap `Rn`→1 M, `Cn`→~100 pF (per channel, independently).

**5 V is plenty — 12 V not needed.** At ~1.5 kHz the band-limit buries the
`e_n·C_d` term under R_f Johnson noise, so zero-bias (Dn anode→GND) is the
default. Reverse bias only helps at ~10 kHz (then a −5 V ICL7660 on the anode,
not 12 V). See `REACTOR_TIA_DESIGN.md §5b`.

## BOM / LCSC numbers

`reactor_tia_bom_jlcpcb.csv` is upload-ready. Status of each LCSC #:

| Part | Value | LCSC | Status |
|---|---|---|---|
| U1, U2 | OPA380AID (SOIC-8) | **C201677** | ✅ verified, in stock (~$3.8) |
| D1, D2 | BPW34 (THT) | **C85128** | ✅ verified (hand-add) |
| C3, C6 | 10 µF 0805 | **C15850** | ✅ verified (office board) |
| C4, C5 | 100 nF 0402 | **C1525** | ✅ verified (office board) |
| C7 | 1 µF 0402 | **C52923** | ✅ verified (office board) |
| R3 | 100 k 0603 | **C25803** | ✅ verified |
| R4, R5 | 10 k 0603 | **C25804** | ✅ high confidence |
| R1, R2 | 10 M 0603 | C57129 | ⚠ best-effort — **verify** (MPN 0603WAF1005T5E) |
| C1, C2 | 10 pF C0G 0603 | C168544 | ⚠ best-effort — **verify** |

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

**SMT-assembled (14 parts):** U1, U2, R1–R5, C1–C7 — top side.
**Hand-add (Assembly excluded from the SMT BOM):**
- **D1, D2 BPW34** — leaded THT, and you *want* them positionable for optical
  alignment to the reactor/fiber. Don't reflow them flat; bring each to 2 pads /
  a 2-pin connector and cable it.
- **J1, J2** — 2.54 mm THT headers; hand-solder.

## Layout notes (kills the pickup)

- Mount each `Dn` **at** its `Un` input; flying leads are the antenna that
  wrecked the passive rig. Guard ring on each SUMMING node, driven at VBIAS.
- Each PD + TIA in its own grounded Faraday can that doubles as the optical
  baffle. **Keep the two channels' summing nodes apart** — crosstalk between them
  would corrupt a ratiometric (CH1−CH2) read.
- Star ground: keep laser-driver/GPIO switching return off the analog return.
- Enable AD7606 oversampling (OS0–2, currently tied GND) for a free sinc
  anti-alias + averaging stage — this is what replaces the analog filter stage.

## Want a quieter / faster channel?

For a Johnson-limited floor or fast M-formation edge, a channel's TIA can be
followed by a 2-pole Sallen-Key (back to two op-amps on that channel) or
AC-coupled into a ×100 modulation-only stage — see `REACTOR_TIA_DESIGN.md §10
v2`. Both reintroduce a second op-amp; the default board keeps it to one per
channel and leans on the ADC oversampling.
