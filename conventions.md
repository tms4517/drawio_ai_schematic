## Abstraction Rules

1. The objective is to create a diagram that a senior RTL engineer
   would draw on a whiteboard after 10 minutes of code review.
2. Create diagrams using **Drawio**.
3. Use the primitives below.
4. Prioritize understanding over implementation accuracy.
5. The diagram must be readable and easy to understand by a junior engineer.
6. Ignore glue logic and implementation registers unless
   they are central to understanding.

## Examples

Use the examples as a guide for creating schematics.

## Paper

1. Paper size must be A4 (210mm x 297mm).
2. Orientation must be landscape.
3. Only use multiple pages if all the logic cannot be neatly represented on one
   page.

## Text

1. All text should be in Monospace in black font.
2. The font size depends on context.
3. Do not add legend, caption, or explanatory paragraph text to the diagram. The
   schematic must be self-explanatory through shapes and net/port labels alone.

## Colours

1. Background colours must be light so that all text and shapes are clearly
visible.

## Modules

1. Use rounded rectangles to represent modules boundaries.
2. The rounded rectangles should have an arc size of 5.
3. The rounded rectangle should neatly enclose the shapes and text it contains
   within maintaining a 2mm margin to the internal shapes.
4. Use a unique colour for each unique module background.
5. Module names should be on the top right written in 10px.
6. A module label is the module (type) name only — never embed the instance
   name in it (e.g. use `xlnx_sync_bit`, not `xlnx_sync_bit u_syncInitiate`).
7. If a module has been instances N times, rather than drawing the module N
   times,represent it as a deck of cards.
8. If a module has been instances N times, include N = ? next to the module
   name.

### Arrows

1. Arrows must alway be sharp (90 degrees).
2. Arrows must always be either 0 degrees flat or 90 degrees upright.
3. Arrows must have a black font.
4. If an arrow is going away from an object the connector must be an arrow at
   the end with no specific connector shape at the start.
5. Inputs are always to the left boundary of the shape; a module's input wires
   must start exactly on the module boundary.
6. Outputs are always from the right boundary of the shape; a module's output
   wires must end exactly on the module boundary.
7. If an arrow overlaps another arrow (not intended to be connected) use an arc
   line jump of 10pt.
8. If the start of an arrow originates from another arrow (they are connected
   together) the the connection shape at the start must be a circle.
9. Arrows represent nets in RTL. The net names should appear above the arrows
   in 8px. In Drawio a label sits ON the line by default; add
   `verticalAlign=bottom` to the edge style so the name floats above the wire,
   and `labelBackgroundColor=none` so there is no white box behind the label.
10. Show the net width in square brackets only for buses (more than 1 bit), eg
    readData[2]; a single-bit net shows just its name (no [1]). Draw buses with
    strokeWidth=2 (thicker line); single-bit nets use the default thickness.
11. A net name must NEVER sit on top of a shape (module, primitive, FF, gate),
    and must stay INSIDE the outer module boundary (port names included). Place
    it on an open part of its wire; if the wire is too short, lengthen the wire
    or slide the label along it. During self-review, verify every net name is
    clear of all shapes and inside the module.
12. If an arrow is going into a deck of cards (3), the net name should be a
    packed array eg - readData[N][2], where N is the number of instances of
    the module.
13. A wire must NEVER pass through a shape or through text (net names, labels,
    captions). Route it through open channels with explicit waypoints, and
    use arc jumps where unrelated wires cross. Verify during self-review.
14. A flip-flop is named by the net on its Q output; do not add a separate name
    caption that a wire could cross.
15. A wire feeding a branch/junction (circle) must have NO arrowhead — an
    arrowhead and a circle head must never be directly connected. Arrowheads
    appear only where a net terminates at a sink.
16. Branches leaving a junction must diverge AT the junction — never run two
    nets (or two branches) stacked on top of each other along the same path.
17. Connect each wire to the exact port (D, EN, Q, T, ...) aligned with the
    port label's centre — never just above or below it.
18. Net names sit a uniform small gap above their wire — the SAME gap for every
    label — with the text middle-aligned in its box. None lies on the wire.

## Primitives

1. Common primitives include but are not limited to AND, OR, NOT, NAND, NOR,
   XOR, XNOR, Multiplier, Adder, Subtractor, Comparators, MUX, DEMUX, FFs.
2. All primitive shapes must have a white background with black border.
3. Clone the exact primitive cell from `./primitives/<category>/<name>.drawio`
   (catalog: `./primitives/index.md`) and relabel it — do NOT hand-roll gate
   shapes or invent stencil names. `./primitives.svg` / `./primitives.drawio`
   are only the full visual catalog; you cannot copy styles out of the image.
4. The primitive shapes have been limited to 2 input 1 output. If necessary,
   stretch the shapes and maintain aspect ratio to accommodate 3 or more inputs.
5. `./primitives/ffs/` holds the FF family — `dff`, `dff_en`, `dff_arst`,
   `dff_arst_en`, `dff_srst`, `dff_srst_en`, `tff_arst`. Pick the variant that
   matches the RTL (a toggle flop -> `tff_arst`; an enabled capture ->
   a `*_en`).
6. For primitives such as FIFOs and memories represent them as rectangles with
   input and output ports labelled according to implementation.

## Combinational logic

1. Only use primitives if the combinational logic depth is 2.
2. For combinational logic with a depth > 2, represent it using a cloud. If it
   is important for the explanation then you may use prmitives for a depth > 2.

## CDC

To clearly show logic belonging to a different clock domain:

1. Use rounded rectangles.
2. The rounded rectangles should have an arc size of 5.
3. The rounded rectangles should not have a border - this is to distinguish it
   from modules.

## Drawio style reference

The self-review step renders with headless Drawio, which draws only core mxGraph
shapes and the `mxgraph.electrical` stencils. Inline `shape=stencil(...)` and
names like `...logic_gates.xor_2` do NOT render (they appear as empty boxes).
Prefer cloning cells from `primitives.drawio`; these verified styles are the
fallback (all white fill, black border):

- AND / OR / XOR:
  `shape=mxgraph.electrical.logic_gates.logic_gate;operation=and|or|xor;`
- NAND / NOR / XNOR: add `negating=1;negSize=0.15;` to the matching gate
- NOT (inverter): `shape=mxgraph.electrical.logic_gates.inverter_2;`
- Mirror a gate (output on the left): add `direction=west;`
- MUX / DEMUX (`-90` to flip):
  `shape=trapezoid;perimeter=trapezoidPerimeter;shapeInside=1;fixedSize=1;rotation=90;`
- Comb. logic cloud (depth > 2): `ellipse;shape=cloud;`
- FF: clone from `primitives.drawio` — rect +
  `triangle;shapeInside=1;direction=north` clock notch + D/Q/EN/ARST port text
- Module box: `rounded=1;arcSize=5;` + unique `fillColor` + dark `strokeColor`,
  name top-left 10px
- Clock-domain / CDC group: `rounded=1;arcSize=5;strokeColor=none;` (borderless)
- Fanout junction dot: `ellipse;fillColor=#000000;strokeColor=#000000;` ~8x8

Net (edge) styles — keep wires orthogonal with
`edgeStyle=orthogonalEdgeStyle;rounded=0;` and float the label above the wire
with these label styles:
`verticalAlign=bottom;labelBackgroundColor=none;fontFamily=monospace;fontSize=8`
Net labels must have a transparent background (`labelBackgroundColor=none`) —
never a white box behind them.

- Single-bit net: `endArrow=classic;html=1;`
- Bus `name[W]`: `endArrow=classic;html=1;strokeWidth=2;`
- Crossing (not connected): add `jumpStyle=arc;jumpSize=10;`
- Branch off another net: start from a junction dot, or add
  `startArrow=oval;startFill=1;`

