## Paper

1. Paper size must be A4 (210mm x 297mm).
2. Orientation must be landscape.
3. Only use multiple pages if all the logic cannot be neatly represented on one page.

## Text

1. All text should be in Monospace in black font.
2. The font size depends on context.

## Colours

1. Background colours must be light so that all text and shapes are clearly
visible.

## Modules

1. Use rounded rectangles to represent modules boundaries.
2. The rounded rectangles should have an arc size of 5.
3. The rounded rectangle should neatly enclose the shapes and text it contains within maintaining a 2mm margin to the internal shapes.
4. Use a unique colour for each unique module background.
5. Module names should be on the top left written in 10px.

### Arrows

1. Arrows must alway be sharp (90 degrees).
2. Arrows must always be either 0 degrees flat or 90 degrees upright.
3. Arrows must have a black font.
4. If an arrow is going away from an object the connector must be an arrow at the end
   with no specific connector shape at the start.
5. Inputs are always to the left boundary of the shape.
6. Outputs are always from the right boundary of the shape.
7. If an arrow overlaps another arrow (not intended to be connected) use an arc line jump of 10pt.
8. If the start of an arrow originates from another arrow (they are connected together) the
   the connection shape at the start must be a circle.
9. Arrows represent nets in RTL. The net names should appear above the arrows in 8px.
10. The net names should include the width of the net besides the net name in square brackets. eg - readData[2]

## Primitives

1. All primitive shapes must have a white background with black border.
2. Use primitive shapes from `./primitives.svg` .

### Flip flops

1. Use flip-flops

### AND

### OR

### NOT

### XOR

### XNOR

### NAND

## CDC

To clearly show logic belonging to a different clock domain:
1. Use rounded rectangles.
2. The rounded rectangles should have an arc size of 5.
3. The rounded rectangles should not have a border - this is to distinguish it from modules.
