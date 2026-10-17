# RTL Whiteboard primitive catalog

Each primitive is a self-contained `.drawio` normalized to the origin.
To place one: read the file, copy its `<root>` cells, give them a unique id
prefix, and translate to the target position. `rtl_whiteboard.mxlibrary` packages
the same shapes for the Drawio GUI.

| Category | Primitive | File | Description | w | h |
| --- | --- | --- | --- | --- | --- |
| arith | `add` | [arith/add.drawio](arith/add.drawio) | Adder | 60 | 40 |
| arith | `cmp_eq` | [arith/cmp_eq.drawio](arith/cmp_eq.drawio) | Comparator A == B | 60 | 40 |
| arith | `cmp_ge` | [arith/cmp_ge.drawio](arith/cmp_ge.drawio) | Comparator A >= B | 60 | 40 |
| arith | `cmp_gt` | [arith/cmp_gt.drawio](arith/cmp_gt.drawio) | Comparator A > B | 40 | 40 |
| arith | `cmp_le` | [arith/cmp_le.drawio](arith/cmp_le.drawio) | Comparator A <= B | 60 | 40 |
| arith | `cmp_lt` | [arith/cmp_lt.drawio](arith/cmp_lt.drawio) | Comparator A < B | 40 | 40 |
| arith | `mul` | [arith/mul.drawio](arith/mul.drawio) | Multiplier | 60 | 40 |
| arith | `sub` | [arith/sub.drawio](arith/sub.drawio) | Subtractor | 60 | 40 |
| ffs | `dff` | [ffs/dff.drawio](ffs/dff.drawio) | DFF, no reset, no enable | 60 | 80 |
| ffs | `dff_arst` | [ffs/dff_arst.drawio](ffs/dff_arst.drawio) | DFF, async reset, no enable | 60 | 80 |
| ffs | `dff_arst_en` | [ffs/dff_arst_en.drawio](ffs/dff_arst_en.drawio) | DFF, async reset, with enable | 60 | 80 |
| ffs | `dff_en` | [ffs/dff_en.drawio](ffs/dff_en.drawio) | DFF, no reset, with enable | 60 | 80 |
| ffs | `dff_srst` | [ffs/dff_srst.drawio](ffs/dff_srst.drawio) | DFF, sync reset, no enable | 60 | 80 |
| ffs | `dff_srst_en` | [ffs/dff_srst_en.drawio](ffs/dff_srst_en.drawio) | DFF, sync reset, with enable | 60 | 80 |
| ffs | `tff_arst` | [ffs/tff_arst.drawio](ffs/tff_arst.drawio) | TFF, async reset | 60 | 80 |
| gates | `and` | [gates/and.drawio](gates/and.drawio) | AND gate | 40 | 40 |
| gates | `nand` | [gates/nand.drawio](gates/nand.drawio) | NAND gate | 40 | 40 |
| gates | `nor` | [gates/nor.drawio](gates/nor.drawio) | NOR gate | 40 | 40 |
| gates | `not` | [gates/not.drawio](gates/not.drawio) | NOT / inverter | 40 | 40 |
| gates | `or` | [gates/or.drawio](gates/or.drawio) | OR gate | 40 | 40 |
| gates | `xnor` | [gates/xnor.drawio](gates/xnor.drawio) | XNOR gate | 40 | 40 |
| gates | `xor` | [gates/xor.drawio](gates/xor.drawio) | XOR gate | 40 | 40 |
| misc | `comb_cloud` | [misc/comb_cloud.drawio](misc/comb_cloud.drawio) | Combinational-logic cloud (depth > 2) | 120 | 80 |
| modules | `module_deck` | [modules/module_deck.drawio](modules/module_deck.drawio) | Module instanced N times (deck of cards) | 140 | 130 |
| mux | `demux1x2` | [mux/demux1x2.drawio](mux/demux1x2.drawio) | 1x2 DEMUX | 100 | 40 |
| mux | `mux2` | [mux/mux2.drawio](mux/mux2.drawio) | 2x1 MUX | 100 | 40 |
| nets | `net_bit` | [nets/net_bit.drawio](nets/net_bit.drawio) | Single-bit net | 0 | 40 |
| nets | `net_branch` | [nets/net_branch.drawio](nets/net_branch.drawio) | Net connected to another (junction) | 40 | 30 |
| nets | `net_bus` | [nets/net_bus.drawio](nets/net_bus.drawio) | Bus [W] | 0 | 40 |
| nets | `net_crossing` | [nets/net_crossing.drawio](nets/net_crossing.drawio) | Non-intersecting nets (arc jump) | 40 | 40 |
