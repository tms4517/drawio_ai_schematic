// Generic closed-loop CDC synchronizer.

// The sending domain toggles an initiate bit and holds the associated data.
// The toggle is resynchronized into the receiving domain with sync_bit and
// an edge (pos or neg) is detected to sample the data. The receiving domain then
// toggles a complete bit which is resynchronized back to the sending domain and
// edge-detected to flag that the round trip has finished.

// Integration protocol:
// 1. Drive the payload on i_data_send and pulse i_initiateSync_send for one
//    i_clk_send cycle. The payload is latched internally on that cycle, so
//    i_data_send need not be held stable afterwards.
// 2. In the receiving domain, o_sample_rcv pulses for one i_clk_rcv cycle when
//    the transfer arrives; o_data_rcv presents the captured payload and holds
//    it until the next transfer.
// 3. o_syncComplete_send then pulses for one i_clk_send cycle to acknowledge
//    that the payload has been sampled and the round trip is complete.
// NOTE: Do not pulse i_initiateSync_send again until o_syncComplete_send has
//       pulsed: only one transfer may be in flight at a time.

`default_nettype none

module closedLoopSynchronizer
#(parameter int unsigned DATA_WIDTH  = 1
  // Number of synchronizer stages in sync_bit
, parameter int unsigned SYNC_STAGES = 2
)
( // Sending clock domain
  input  var logic                  i_clk_send
, input  var logic                  i_arstn_send
, input  var logic [DATA_WIDTH-1:0] i_data_send
, input  var logic                  i_initiateSync_send // Pulse
, output var logic                  o_syncComplete_send // Pulse
  // Receiving clock domain
, input  var logic                  i_clk_rcv
, input  var logic                  i_arstn_rcv
, output var logic [DATA_WIDTH-1:0] o_data_rcv
, output var logic                  o_sample_rcv
);

  // {{{ Sending domain: initiate toggle + data hold

  // Toggle on each sync request; the toggle edge carries the event across the CDC.
  logic toggleInitiate_q;
  always_ff @(posedge i_clk_send, negedge i_arstn_send)
    if (!i_arstn_send)
      toggleInitiate_q <= 1'b0;
    else
      toggleInitiate_q <= i_initiateSync_send ? !toggleInitiate_q : toggleInitiate_q;

  // Hold the data stable for the whole round trip so the multi-bit crossing is
  // safe (data settles while the toggle traverses the synchronizer stages).
  logic [DATA_WIDTH-1:0] dataHold_q;
  always_ff @(posedge i_clk_send, negedge i_arstn_send)
    if (!i_arstn_send)
      dataHold_q <= '0;
    else
      dataHold_q <= i_initiateSync_send ? i_data_send : dataHold_q;

  // }}} Sending domain: initiate toggle + data hold

  // {{{ Receiving domain: resync + edge detect + sample

  logic syncInitiate_rcv;
  sync_bit
    #(.LEVELS        (SYNC_STAGES)
    , .RST_REG_VALUE (0)
    , .CELL_TYPE     ("V")
    ) u_syncInitiate
    ( .clk       (i_clk_rcv)
    , .rst_n     (i_arstn_rcv)
    , .raw_input (toggleInitiate_q)
    , .sync_out  (syncInitiate_rcv)
    );

  // Additional flop delays the resynced toggle one cycle for edge detection.
  logic syncInitiate_rcv_q;
  always_ff @(posedge i_clk_rcv, negedge i_arstn_rcv)
    if (!i_arstn_rcv)
      syncInitiate_rcv_q <= 1'b0;
    else
      syncInitiate_rcv_q <= syncInitiate_rcv;

  logic syncInitiate_pe, syncInitiate_ne;

  // Detect the pos edge and neg edge of the resynchronized initiate toggle.
  always_comb
    syncInitiate_pe = syncInitiate_rcv && !syncInitiate_rcv_q;

  always_comb
    syncInitiate_ne = !syncInitiate_rcv && syncInitiate_rcv_q;

  logic sampleEvent_rcv;
  always_comb sampleEvent_rcv = syncInitiate_pe || syncInitiate_ne;

  // Register the sample pulse so it lands in the same cycle as the captured
  // data, keeping o_sample_rcv and o_data_rcv edge aligned.
  always_ff @(posedge i_clk_rcv, negedge i_arstn_rcv)
    if (!i_arstn_rcv)
      o_sample_rcv <= 1'b0;
    else
      o_sample_rcv <= sampleEvent_rcv;

  always_ff @(posedge i_clk_rcv, negedge i_arstn_rcv)
    if (!i_arstn_rcv)
      o_data_rcv <= '0;
    else
      o_data_rcv <= sampleEvent_rcv ? dataHold_q : o_data_rcv;

  // Toggle the complete bit back to the sender once the data has been sampled.
  logic toggleComplete_q;
  always_ff @(posedge i_clk_rcv, negedge i_arstn_rcv)
    if (!i_arstn_rcv)
      toggleComplete_q <= 1'b0;
    else
      toggleComplete_q <= sampleEvent_rcv ? !toggleComplete_q : toggleComplete_q;

  // }}} Receiving domain: resync + edge detect + sample

  // {{{ Sending domain: complete resync + edge detect

  logic syncComplete_send;
  sync_bit
    #(.LEVELS        (SYNC_STAGES)
    , .RST_REG_VALUE (0)
    , .CELL_TYPE     ("V")
    ) u_syncComplete
    ( .clk       (i_clk_send)
    , .rst_n     (i_arstn_send)
    , .raw_input (toggleComplete_q)
    , .sync_out  (syncComplete_send)
    );

  // Additional flop delays the resynced toggle one cycle for edge detection.
  logic syncComplete_send_q;
  always_ff @(posedge i_clk_send, negedge i_arstn_send)
    if (!i_arstn_send)
      syncComplete_send_q <= 1'b0;
    else
      syncComplete_send_q <= syncComplete_send;

  // Register the round-trip-complete pulse.
  always_ff @(posedge i_clk_send, negedge i_arstn_send)
    if (!i_arstn_send)
      o_syncComplete_send <= 1'b0;
    else
      o_syncComplete_send <= syncComplete_send ^ syncComplete_send_q;

  // }}} Sending domain: complete resync + edge detect

endmodule
`resetall
