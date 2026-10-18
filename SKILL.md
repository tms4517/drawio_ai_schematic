---
name: rtl-whiteboard
description: Generate a hand-drawn-style schematic (as a Drawio diagram) that explains
  what an RTL design does, driven by a user's question rather than by elaboration or
  synthesis. Use when the user wants to understand, visualize, sketch, or draw an
  unfamiliar Verilog/SystemVerilog/VHDL design and asks things like "show the fanout
  of <signal>", "show the <clkA> to <clkB> CDC crossing", "show the datapath of
  <signal>", "how is <signal> generated", "explain how initialization completes", or
  otherwise asks for a block diagram / schematic / whiteboard sketch of RTL. Do NOT
  use for implementation-accurate netlists, gate-level schematics, or when the user
  wants a tool-generated (DC/Verdi/synthesis) view.
---

# RTL Whiteboard

Produce the schematic a senior RTL engineer would sketch on a whiteboard after ~10
minutes of reading unfamiliar RTL — a functional mental model, not an
implementation-accurate netlist. Output is a **Drawio** diagram.

## Core principle

Read the RTL the way a human sees it for the first time: skim the source, follow only
the signals relevant to the user's question, and ignore glue logic. **Do not** use
parsers, elaboration, synthesis, or any special tooling — approximate comprehension is
the goal, not signoff accuracy. Frame output as a comprehension aid.

## When invoked

1. Identify the query archetype from the user's question:
   - **Fanout** — where a signal drives (e.g. "fanout of `cfg_mode_rate_dl[1]`").
   - **CDC** — all logic in a clock crossing (e.g. "`tx_clk` to `rx_clk` crossing").
   - **Datapath** — the path a data signal takes (e.g. "datapath of `rx_data`").
   - **Signal generation** — how a signal is produced (e.g. "how is `packet_valid`
     generated").
   - **Comprehension** — a behavior (e.g. "how initialization completes").
2. Read only the RTL relevant to that query. Build an approximate mental model.
3. Draw the schematic following `conventions.md` exactly.

## Workflow

1. **Scope the slice.** From the query, decide which signals/modules matter. Discard
   everything else.
2. **Choose abstraction level.** Modules → rounded rectangles; combinational depth ≤ 2
   → primitives; depth > 2 → a cloud (unless detail is central to the explanation);
   repeated instances → a deck of cards with `N = ?`.
3. **Emit Drawio.** Follow every rule in `conventions.md` (paper, colours, module
   boxes, arrows/net labels with widths, primitives, combinational logic, CDC blocks).
4. **Clone primitives** from `primitives/<category>/<name>.drawio` (see
   `primitives/index.md` for the catalog). Read the file, copy its `<root>` cells,
   give them a unique id prefix, translate to position, and relabel. Never invent
   stencil names. The style table in `conventions.md` is the fallback for atomics.
5. **Self-review (REQUIRED).** Render the diagram to PNG, look at it, and iterate
   until it matches `conventions.md` (see below).

## Self-review loop (REQUIRED)

After emitting the `.drawio`, FIRST run the automated verifier, fix every reported
failure, then render a PNG and eyeball it. Do not hand the user a diagram that has
not passed the verifier AND been looked at.

Step 1 — run the convention checker (absolute paths; exit 0 = all pass):

    python3 tools/verify_diagram.py /abs/in.drawio

It prints `[PASS]/[FAIL]` for every convention check — geometry (overlaps, inside
module, not on shapes, shapes connected, I/O on boundary, no wire through
shape/text, no arrowhead on a junction, uniform label gap, orthogonal wires, no
stacked nets) AND style (all text Monospace + black, no legend, 8px nets, no `[1]`
on single-bit nets, buses drawn thick, transparent labels, white/black primitives,
rounded/borderless containers, right-aligned 10px module names, light backgrounds,
landscape page) AND congestion (a dense hotspot of shapes/labels/wires while empty
whitespace is wasted — what the PNG shows as a dark, unreadable cluster) — with the
offending coordinates. Fix each FAIL and re-run until it
prints `ALL N CHECKS PASSED`. Feed the log back in to drive the fixes.

Step 2 — render headlessly and eyeball (ALWAYS use absolute paths — the shell
wrapper can drop a leading `cd`):

    xvfb-run -a drawio -x -f png -o /abs/out.png --width 1700 /abs/in.drawio

- Drawio CLI: `drawio` on PATH (e.g. `/tool/pandora64/.package/drawio-21.6.1/bin/drawio`).
- GPU/EGL errors on stderr are harmless; the PNG is still produced.
- View the PNG and confirm: primitives drew (an empty box = wrong stencil name),
  arrows land on ports, buses are thick, colours/borders correct, fits one A4
  landscape page.
- CONGESTION: look for any dark, crammed cluster of shapes/labels/wires while other
  parts of the page sit empty. The verifier's congestion check (check 32) flags such
  hotspots by bounding box; the fix is to widen the page and SPREAD that block into
  the whitespace (give each primitive room, lengthen wires), not to shrink text.
- Edit and repeat Steps 1–2 until the verifier passes and it reads cleanly.

## Reference files

- `conventions.md` — the full drawing specification + Drawio style reference (MUST follow).
- `primitives/` — one `.drawio` per primitive, grouped (`gates/ ffs/ mux/ arith/ nets/ modules/ misc/`). **Clone these cells** — source of truth. See `primitives/index.md`.
- `rtl_whiteboard.mxlibrary` — the same primitives packaged for the Drawio GUI (drag-and-drop; for humans / distribution).
- `primitives.drawio` / `primitives.svg` — the full visual catalog / preview (not for cloning).
- `examples/` — golden reference diagrams, one per query archetype (use as style guide).
- `tools/verify_diagram.py` — the automated convention checker (run it in self-review).
- `tools/verifyDiagram.md` — the human-readable checklist the verifier automates.

## Constraints

- Prioritize understanding over implementation accuracy.
- Readable by a junior engineer.
- A module box is ONLY a real RTL module instance (named by its RTL module type).
  Never invent a box to group inline logic (`output regs`, `control logic`, ...) —
  that hides logic. Draw inline registers/muxes/combinational blocks with primitives.
- Map RTL operators to their matching primitive: a conditional/ternary
  `y <= sel ? a : b` (even `sel ? a : '0`) is a 2:1 MUX, NOT an AND-mask;
  `== < >` are comparators, `+ - *` are adder/subtractor/multiplier, a reduction
  is one wide gate. See `conventions.md` Primitives §9.
- Co-locate decode/control logic with the datapath element it drives (the mux/FF
  it selects), as self-contained per-lane blocks — never a global decode column
  feeding distant slices through long wires. See `conventions.md` Paper §5.
- Ignore glue logic and implementation registers unless central to understanding.
- A4 landscape; add pages only when one cannot hold the logic neatly.
