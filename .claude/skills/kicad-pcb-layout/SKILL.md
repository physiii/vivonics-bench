---
name: kicad-pcb-layout
description: Rules for placing footprints and routing copper on the laser_controller KiCad board (or any board using circuits/pcb_critical_routes.py + gen_pcb.py). Load before touching laser_controller.kicad_pcb, pcb_critical_routes.py, or gen_pcb.py -- placement, routing, vias, or power-plane/zone work.
---

# KiCad PCB layout rules (laser_controller board)

These rules came out of a cleanup pass that found the router silently
producing vias-on-pads as its default fanout strategy, and multiple
same-layer flood zones for different rails geographically fighting each
other. Both are easy to reintroduce by accident. Read this before editing
`circuits/pcb_critical_routes.py`, `circuits/gen_pcb.py`, or hand-patching
`circuits/laser_controller.kicad_pcb`.

## Vias must never sit on pad copper -- not even same-net

A via centered on (or overlapping) a component pad is bad practice outside
a deliberate, fab-supported via-in-pad process (which this board does not
use): it risks solder wicking into the barrel on hand-soldered parts and
reads as sloppy in review. It is easy to miss because it is not a DRC
violation in the usual sense -- same-net copper touching same-net copper
isn't a clearance error.

`pcb_critical_routes.py`'s `_via_clear_sized()` had exactly this bug: it
skipped clearance checks entirely for pads on the SAME net as the via
(`if pad_net == net_name: continue`), so a via center landing exactly on a
same-net pad was never rejected. `emit_ground_plane_fanout_segments()` also
had an explicit `via_in_pad_fallbacks` escape hatch that placed a via
directly at a pad's coordinates whenever the normal offset-via search
failed. Between the two, roughly 3 out of every 4 vias on the board ended
up centered on a pad.

**The fix already applied**: `_via_clear_sized` now checks same-net pads
too, with a smaller clearance (`SAME_NET_VIA_PAD_CLEARANCE_MM = 0.15`) than
the cross-net DRC clearance. `via_in_pad_fallbacks` was deleted -- do not
reintroduce a "just put it on the pad" escape hatch. If a fanout genuinely
can't find a clear offset position, leave the pad unfanned in that pass and
let a connectivity-closure pass (see below) find a different route, rather
than silently violating the no-via-on-pad rule.

Before landing any change to via placement logic, spot check with:

```python
# via center within any pad's inflated bbox, same-net included
for via in vias:
    for ref, pin, pad in all_pads:
        if pad_polygon_hit(via.x, via.y, via.size/2, pad):
            ...  # should be zero results
```

## Prefer 45-degree corners over hard right angles

The router (`_route_one`) is a 4-directional grid A* -- every bend it
produces is a raw 90 degrees. `_chamfer_polyline()` (called from inside
`_route_one` right before it returns, and from the forced-route-shape path
in `emit_critical_route_segments`) shaves a small 45-degree cut off each
square corner where there's room, verified clear via `_route_shape_clear`
before being accepted. If a corner has no room (tight pad-to-pad escapes),
it silently stays square -- that's correct, not a bug.

If you add a new route-emission path that builds its own point list instead
of going through `_route_one`, pass the finished polyline through
`_chamfer_polyline(points, pads, existing_segments, net_name, width,
route_layer)` before emitting segments, the same way the forced-route path
does. Don't hand-roll 45-degree cuts inline.

## Soft layer-by-direction preference, not a hard rule

Inside `_route_one`'s A* cost function, moving vertically on `F.Cu` or
horizontally on `B.Cu` carries a small `axis_bias` (0.03, versus 1.0 per
grid step and 0.05 per turn) -- enough to break ties toward "horizontal
runs on F.Cu, vertical runs on B.Cu" without ever blocking the router from
taking the only available path. This is intentionally weak: most nets in
this design have their layer picked for electrical reasons (USB must stay
on B.Cu, laser cathodes need a specific inner layer, etc.), not because the
direction was free to choose. Don't strengthen this bias to the point where
it fights those hard layer requirements.

## Power planes: one ground plane, one power layer split in two -- nothing else

The board is a 4-layer Sig/GND/PWR/Sig stack (`F.Cu` / `In1.Cu` / `In2.Cu`
/ `B.Cu`). Two earlier attempts at this both got corrected by the user:
first a 9-zone set with overlapping bounding boxes on the same layer for
different rails (KiCad resolves that by fill priority, which in practice
carves one net's pour into thin ugly slivers), then a "fixed" version with
small isolated local pours + trunk traces that the user still rejected as
overcomplicated ("you did a horrible job... we need to copy the planes we
have in access-controller"). The pattern that stuck, copied from
`~/projects/access-controller/circuits/controller/access-controller.kicad_pcb`:

- **`In1.Cu`**: the one true reference plane. Single full-board `GND`
  flood. Nothing else ever goes here.
- **`F.Cu` / `B.Cu`**: pure signal layers. **No flood zones at all** --
  access-controller's reference board has exactly one `GND` zone (`In1.Cu`
  only) and no outer-layer GND fill. Don't add one; it was tried and
  rejected.
- **`In2.Cu`**: the power layer, split into exactly two regions -- one per
  rail the user actually asked for (`+3V3`, `+5V`), each a simple,
  generously-sized rectangle covering that rail's real load cluster (not a
  tiny 3-6mm pour): `+3V3` over the `MCU_ESP32-S3` sheet's footprint
  extent, `+5V` over the combined `TIA_*`/`LASER_*` sheets' extent, with a
  visible gap between them (don't let them touch or overlap). The
  access-controller reference uses hand-fit irregular polygons that
  interlock without overlapping; simple axis-aligned rectangles with a gap
  are the "keep it simple" version of the same idea and are what the user
  actually asked for ("simple split the power plane into 5v and 3v3
  regions").

The `POWER_IO` sheet's own buck/OR-diode/ADC/monitor cluster (roughly
x=85..117 on the current board) sits in the gap between the two regions on
purpose: components there (`U11`/AP2112, `U12`/INA4180, `U14`/AD7606) have
real pins on *both* `+3V3` and `+5V` within a few mm of each other, so
neither region can honestly claim that territory -- those parts get trace
drops from whichever rail they need instead of flood coverage. Don't try
to extend either region to "reach" them; that's exactly the shape-fighting
problem this design avoids.

`check_laser_controller_pcb.py`'s `REQUIRED_PLANE_ZONES` should match
this exactly: `{"GND": {"In1.Cu"}, "+3V3": {"In2.Cu"}, "+5V": {"In2.Cu"}}`
-- no `B.Cu` entry. If you find yourself adding one back, you're
reintroducing the outer-layer flood the user rejected.

Before sizing a rail's region, check the *real* component clusters
(`gen_pcb.build_board(emit_routes=False)` for positions) rather than
copy-pasting the board's stale docs -- `PCB_LAYOUT.md`/`POWER_TREE.md`
used to describe a 90x50mm board with a different floorplan than the real,
current 173x61mm hand-placed layout (this has since been corrected in the
docs, but re-verify against the actual `Edge.Cuts` outline via
`check_laser_controller_pcb.py`'s `parse_board_outline_bounds` if it drifts
again).

### Zones need an actual fill pass, not just `(fill yes ...)`

Writing a zone's `(polygon ...)` outline with the `fill yes` flag set is
**not** the same as the zone having real copper. KiCad only writes the
computed `(filled_polygon ...)` sub-block -- the actual clearance-clipped
copper shape gerbers/renders are generated from -- when its own zone-fill
algorithm runs. A hand-written zone block with no `filled_polygon` data
renders as empty/invisible (confirmed via `kicad-cli pcb export svg`) and
`check_laser_controller_pcb.py`'s `required_plane_zone_failures` won't
catch this either, since it only checks for the `(fill yes` text flag, not
for actual `filled_polygon` presence -- a real gap in that checker.

Fill zones programmatically with the `pcbnew` Python API (present in this
environment at `/usr/lib/python3/dist-packages`, needs an explicit
`sys.path.insert` since the project's venv doesn't include system
packages):

```python
import sys
sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew
board = pcbnew.LoadBoard("laser_controller.kicad_pcb")
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard("laser_controller.kicad_pcb", board)
```

This round-trips cleanly through the project's own regex-based parsers
(verified: net table, pad nets, footprint count, zone summaries all read
back identically). Do this as the last step after any zone edit, and
re-verify with `kicad-cli pcb export svg` that the fill actually shows up
visually, not just that the checker's text-flag check passes.

## Zero component overlap: check real courtyards, not pad boxes

`check_laser_controller_pcb.py`'s `different_net_pad_overlap_failures` only
catches cross-net *pad* bbox overlaps -- it says nothing about two
footprint *bodies* physically overlapping (same-net pads overlapping,
or courtyards overlapping with no pad conflict at all). That's a real,
separate problem: this board's passive footprints are the
`*_HandSolder` variants, whose courtyards are deliberately elongated well
beyond the component's true footprint for manual-assembly clearance, so
templates that looked fine at normal pad-pitch spacing can still collide
once you check the actual courtyard polygon.

To check for real overlaps, extract each footprint's `F.CrtYd`/`B.CrtYd`
graphics (fall back to a pad-bbox union only if a footprint genuinely has
no courtyard layer), transform to board coordinates by the footprint's own
`(at x y rot)`, and test bbox intersection pairwise. **Use balanced-paren
block extraction to pull `fp_line`/`fp_poly` blocks out, not a single regex
spanning `start`..`end`..`layer`** -- `(stroke (width ..) (type ..))` nests
parens between those tokens and silently breaks a naive
`\(fp_line...\)[^)]*\(layer...\)` pattern, making every footprint fall back
to the (much less accurate) pad-bbox path without any error.

When resolving an overlap by moving a part:
- Prefer moving passives (caps, then diodes, then transistors/trim pots,
  then resistors) before ICs or connectors.
- Respect the project's own `PLACEMENT_CHECKS` pad-to-pin distance limits
  (`check_laser_controller_pcb.py`) for whatever you move -- but only as a
  "don't regress a constraint that currently passes" rule. This board
  already has 71 of 111 `PLACEMENT_CHECKS` failing pre-existing (from a
  board resize/re-placement that predates any of this work) -- don't let
  an already-broken constraint block an overlap fix, and don't try to
  silently fix it either; that's a separate, much bigger placement task.
  Always diff your new failure set against a baseline taken *before* your
  change (`git show <commit>:path` the pre-change file) so you can tell
  "pre-existing" from "I broke this."
- When a part is boxed in on every side at its native orientation, try a
  90-degree rotation flip before concluding there's no legal spot --
  rectangular (non-square) parts often only fit one way in a tight pocket.
- **When implementing an overlap-area check that sums contributions across
  multiple other footprints, sum a max, never a signed sum.** Summing
  `ox * oy` across footprints lets a genuine overlap with one part (a
  positive product) get numerically cancelled by a near-miss with a
  different part (one axis slightly negative -> negative product), so the
  total reads "clear" while a real overlap remains. This produced a
  bug where parts endlessly ping-ponged between two positions that each
  looked clear only because of this cancellation -- if a solver you write
  oscillates between the same two candidate positions, this is the first
  thing to check.

## Connectivity: a segment count existing isn't the same as "routed"

Before this pass, the board had 667 segments and 313 vias but only 10 of
111 `CRITICAL_ROUTE_LINKS` were actually verified end-to-end connected, and
34 whole nets (including a laser diode cathode-to-driver connection) were
split into disconnected islands -- most of the existing copper was GND
fanout stubs, not real signal routing. A segment/via count is not a
connectivity proof.

Use `check_laser_controller_pcb.py`'s `split_multi_pad_signal_nets` (walks
the actual segment/via/zone graph and returns connected-component groups
per net) and `count_connected_critical_route_links` to verify real
connectivity after any routing change, not just "did the emit function run
without error." A net with a shared common rail across multiple physical
footprints (e.g. `LASER_V+` across all 4 laser diode anodes) needs an
explicit trunk-trace link to *every* member, not just the first one seeded
from the source -- `POWER_ROUTE_LINKS` had only one `LASER_V+` link
(reaching `LASER_BLUE` only) before this pass; IR/RED/GREEN were stranded
until a 3-link daisy chain was added connecting all four.

## Regenerating routing against hand-placed footprints

`gen_pcb.py`'s `build_board(emit_routes=True)` path is dead code guarded by
an unconditional `raise RuntimeError` -- it was disabled once the board
moved to hand/recovered placement, and its freshly-staged footprint
coordinates no longer match the real board. Don't remove that guard and
call it directly. Instead, source `board_ref_by_comp`/`pad_nets_by_ref`
from `gen_pcb.build_board(emit_routes=False)` (schematic/netlist-derived,
independent of PCB placement) but substitute `body` with the *real*
footprint blocks parsed out of the current `laser_controller.kicad_pcb`
(via `check_laser_controller_pcb.footprint_blocks`), then call the
`emit_*` functions directly in the same order as that dead code block
(power preroute -> critical preroute -> cathode -> inner preroute ->
critical main -> extra -> bottom -> inner -> power main -> GND fanout).
That dead code is a correct and complete recipe for the call order; it
does not need to be reachable to be worth reading.

`pcb_critical_routes.py` also has one stale absolute-coordinate assumption
worth knowing about: `_via_clear_sized`'s board-edge bounds check was
hardcoded to the board's *original* 90x50mm-at-origin coordinate system
(now fixed to reference `BOARD_X0_MM`/`BOARD_Y0_MM`/`BOARD_X1_MM`/
`BOARD_Y1_MM`, duplicated at the top of `pcb_critical_routes.py` to match
`gen_pcb.py`'s board outline since importing `gen_pcb` from there would be
circular). If routing against real board coordinates silently produces
zero placeable vias, check for this class of stale-literal bug first --
grep for bare numeric board-bound literals before assuming the search
logic itself is wrong. There's a similar unreachable stale-coordinate
forced-route shape for `"Laser buck output to direct LD rail"` in
`_forced_power_front_pad_to_front_pad_layer` (a `corridor_y = 18.0`
absolute Y that is nowhere near the real board's y=80..141 range) -- it's
harmless dead weight (falls through to the general search path) but don't
copy its pattern for new forced routes.
