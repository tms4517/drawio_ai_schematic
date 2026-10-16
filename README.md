# RTL Whiteboard

The aim of this repository is to generate a schematic an engineer would create
by hand to explain the functionality of a design so reviewers or other 
engineers can gain an understanding of what's implemented.

## Motivation

Understanding an unfamiliar RTL design is often harder than designing one.

Traditional EDA tools can generate schematics, but they require setup:
- File lists
- Include paths
- Defines
- Library models
- Elaboration and synthesis flows

Even after that effort, the resulting schematic is typically a faithful representation 
of the implementation rather than a useful explanation of the design.

When engineers review RTL, they rarely think in terms of gates, muxes, and intermediate nets. 
Instead, they build a mental model of the design and can sketch something that is functionally
close to the RTL but not accurate.

## Goal

End users should be able to ask questions about a design and the schematic generated should
be driven by their query.

For example:
- **Fanout Analysis**: Show the fanout of cfg_mode_rate_dl[1].
- **CDC Visualization**: Show all logic involved in the tx_clk to rx_clk crossing.
- **Datapath Exploration**: Show the datapath of rx_data.
- **Signal Understanding**: Show how packet_valid is generated.
- **Design Comprehension**: Explain how initialization completes.
