# JLCPCB Order Identity — Action Packet (W2026070704037950)

**Date:** 2026-07-14
**Status:** 🔴 OPEN HOLD — action required by an authorized JLCPCB account holder
**Owner action:** contact JLCPCB; this repo cannot resolve it without supplier evidence.

## Bottom line

The 5-board first-article order was **paid on 2026-07-06 15:04** against a package
whose OPA380 `U1–U4` and Bourns `RV5–RV8` **copper footprints were mirrored**. The
mirror was found **the next day (2026-07-07)** by the operator directly from
JLCPCB's assembly preview.

**UPDATE 2026-07-14 (from the 2026-07-07 bench Codex transcript):** the operator
**did re-upload corrected files to the JLCPCB order on 2026-07-07** — this is not
just a design fix. Evidence: (1) the operator directed rebuilding the board
files/BOM/CPL/zip specifically "to send to jlcpcb" (11:29) and again "repackage and
get ready to send to jlcpcb" (13:19); (2) a pasted view of the JLCPCB order page
shows **`laser_controller_gerbers — Automatically saved, last updated on 7 July,
13:54`**, i.e. the files *on the order itself* were updated on 07-07; (3) the
operator was still working in the JLCPCB portal at 18:55 resolving a parts
shortage. So the corrected package almost certainly reached the order.

**The one residual check:** the portal edits spanned the afternoon (13:54 save)
while the fix kept iterating — the final orientation repair committed at 16:15
(`99bc498`) and a further parts fix at 18:55. So confirm the **last** thing saved to
the order was the *final* corrected package (U1–U4 dot at lower-right, `C70` =
`C970665`), not an intermediate. This is now a *verification*, not a likely defect.
Still **do not power any returned board** before a quick physical pin-1 / pad-net
inspection — cheap insurance, not an expectation of failure.

## Timeline

| When (CDT) | Event | Commit |
| --- | --- | --- |
| 2026-07-06 14:17 | Package regenerated ("Fix J7 assembly clearance") | `52c5190` |
| 2026-07-06 15:03 | Uploaded to JLCPCB | — |
| 2026-07-06 15:04 | **Order placed and PAID** (this is the mirrored package) | `52c5190` |
| 2026-07-07 16:15 | OPA380/Bourns **mirror found + repaired**; C70 part swapped; package regenerated | `99bc498` |
| 2026-07-12 | Hold recorded in order journal | — |
| 2026-07-14 | This action packet | — |

## Two package identities (this is the crux)

**A. PAID / SUBMITTED package — commit `52c5190` — MIRRORED, do not trust**

```text
99edd53cbfd12dce3b5175e06c791c4805ac131a8c83f409c281d4962d1f306f  laser_controller_gerbers.zip
1923d2e624c5fecf20f3a804278eac854853a2d5e9b1e9ac31bfbd97530b8c29  laser_controller_jlcpcb_package.zip
0d0de72c72e62a764d51373d87a15c74c038ac83cad23bf5caaeb77b6064c286  laser_controller_bom_jlcpcb.csv
cc2a82c030d8bbb17dc394fd4fdf4b33de54d7cf10f1a0a383278b746caf655d  laser_controller_pos.csv
```

**B. CORRECTED package — commit `99bc498` — validated, NOT proven sent to JLCPCB**

```text
dabe6c81f73fca316be372faec0ddcb27c40db9f1081e2ea1d487c32bf62c71e  laser_controller_gerbers.zip
e87572074f1539b307b883424d7bf2417fc6e85eba7171bc98e36c94f0586496  laser_controller_jlcpcb_package.zip
08d2133a2d9b546849377074f3d8ed939b40db34f803909adadbe438cdd3a992  laser_controller_bom_jlcpcb.csv
268b0fae73f57049280859a070ec6d71502737950f65b45a3f0e6824f986faa4  laser_controller_pos.csv
```

Material differences between A and B:

1. **Copper mirror fix** on `F_Cu`/`B_Cu` for `U1–U4` (OPA380AID SOIC-8, the
   photodiode TIA amplifiers) and `RV5–RV8` (Bourns 3224W feedback trimmers).
2. **BOM part swap** `C70` → JLC `C970665` (22 µF/100 V electrolytic) in the
   corrected package. (The order journal's earlier `C70 → C242011` note is also
   superseded.)

The corrected package passes `run_laser_controller_review.py` (order package **READY**);
first-article/production release is separately BLOCKED on bring-up work, not on the
Gerbers.

## Step 1 — Ask JLCPCB what they actually built (ready to send)

Send from the account that placed the order, via the JLCPCB order page for
`W2026070704037950` (or support chat / order message):

> Subject: Production file confirmation — Work Order W2026070704037950 / Order Y57-2673627A
>
> Hello, for work order **W2026070704037950** (PCB order **Y57-2673627A**, PCBA
> **SMT026070663451-2673627A**, invoice **2673627A2026070704037950**), we need to
> confirm exactly which production files were used to fabricate and assemble the
> boards, because we uploaded a revised package after payment.
>
> Please provide: (1) the exact Gerber, BOM, and CPL/placement files used for
> production (or their checksums), and (2) the final assembly/placement preview
> images you generated for this order. Specifically, on the assembly preview,
> do the **U1, U2, U3, U4** (SOIC-8) package dots sit at the **lower-right board
> corner**? If the boards have shipped, please also send the production/DFM
> report. If they have not yet been fabricated or assembled, please **pause the
> order** so we can confirm or replace the files first. Thank you.

## Step 2 — Decision tree on JLCPCB's answer

- **Boards NOT yet fabricated/assembled** → upload the **corrected package B**
  (`gerbers.zip` `dabe6c81…` + `bom_jlcpcb.csv` `08d2133a…` + `pos.csv` `268b0fae…`),
  re-confirm the U1–U4 dot at the lower-right corner, and this time select
  **"Confirm production file: yes."** Archive the new preview + hashes here.
- **JLCPCB's production files hash-match corrected package B** → the swap happened;
  clear the hold, archive their confirmation, proceed to receipt inspection.
- **JLCPCB's production files hash-match paid package A (or show U1–U4 dot NOT at
  lower-right)** → boards carry the mirrored front-end. Treat U1–U4 / RV5–RV8 as
  defective: either scrap/rework those parts (mirrored dead-bug placement is
  fragile and not production-acceptable) or re-order with package B. Request rework
  credit / re-fab as the invoice terms allow.
- **JLCPCB cannot say** → assume mirrored (package A) until proven otherwise.

## Step 3 — Physical inspection on receipt (before any power)

1. Photograph both sides of all 5 boards before touching power.
2. Under magnification, verify `U1–U4` OPA380 pin-1 / package dot is at the
   **lower-right board corner** (matches corrected geometry). If the dot is at the
   upper-left, the mirrored copper shipped.
3. Verify `RV5–RV8` Bourns 3224W wiper/pad geometry against the corrected pad map
   in `../signoff/2026-07-07-opa380-bourns-orientation-repair-signoff.md`.
4. Continuity-check `PD_ANODE` summing node → OPA380 pin 2 and `VOUTx` → pin 6 on
   one board before powering any.
5. Confirm whether bottom-side `D1–D4` (SFH2201) were assembled; if not, hand-place.
6. Reconcile the outline discrepancy: order page said `173.03 × 71.12 mm`; the
   archived Edge.Cuts measures `173.025 × 61.125 mm`. Confirm the real board size.

## Cross-references

- Order record: [`journal/2026-07-06-jlcpcb-laser-controller-order.md`](2026-07-06-jlcpcb-laser-controller-order.md)
- Mirror repair: [`signoff/2026-07-07-opa380-bourns-orientation-repair-signoff.md`](../signoff/2026-07-07-opa380-bourns-orientation-repair-signoff.md)
- Superseded paid-package signoff: [`signoff/2026-07-05-final-jlcpcb-order-package-signoff.md`](../signoff/2026-07-05-final-jlcpcb-order-package-signoff.md)
