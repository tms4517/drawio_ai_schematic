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
4. **Clone primitives** from `primitives.drawio` (copyable Drawio source) for gates,
   muxes, FFs, etc. — never invent stencil names. Use the style reference in
   `conventions.md` as the fallback.
5. **Self-review (REQUIRED).** Render the diagram to PNG, look at it, and iterate
   until it matches `conventions.md` (see below).

## Self-review loop (REQUIRED)

After emitting the `.drawio`, export a PNG and inspect it like a reviewer; fix and
re-render until it reads cleanly. Do not hand the user a diagram you have not looked
at.

Render headlessly (ALWAYS use absolute paths — the shell wrapper can drop a leading
`cd`):

    xvfb-run -a drawio -x -f png -o /abs/out.png --width 1700 /abs/in.drawio

- Drawio CLI: `drawio` on PATH (e.g. `/tool/pandora64/.package/drawio-21.6.1/bin/drawio`).
- GPU/EGL errors on stderr are harmless; the PNG is still produced.
- Then view the PNG and check:
  - primitives actually drew (an empty box = wrong stencil name → clone from
    `primitives.drawio` / use the style reference);
  - net names sit ABOVE the wire (not on it) and don't overlap shapes
    (`verticalAlign=bottom` on edges);
  - arrows are orthogonal; no label/shape collisions;
  - module and CDC-domain colours/borders are correct;
  - it fits one A4 landscape page.
- Edit geometry/styles and re-render. Repeat until clean.

## Reference files

- `conventions.md` — the full drawing specification + Drawio style reference (MUST follow).
- `primitives.drawio` — copyable Drawio source; clone these exact cells. (`primitives.svg` is only its preview.)
- `examples/` — golden reference diagrams, one per query archetype (use as style guide).

## Constraints

- Prioritize understanding over implementation accuracy.
- Readable by a junior engineer.
- Ignore glue logic and implementation registers unless central to understanding.
- A4 landscape; add pages only when one cannot hold the logic neatly.
