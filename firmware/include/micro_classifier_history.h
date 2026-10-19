#ifndef MICRO_CLASSIFIER_HISTORY_H
#define MICRO_CLASSIFIER_HISTORY_H

#include "micro_classifier_codec.h"

#define MC_V0_STATE_HISTORY_TICKS UINT32_C(8)

typedef struct {
    mc_v0_state samples[MC_V0_STATE_HISTORY_TICKS];
    uint8_t valid_mask;
    uint8_t next;
} mc_v0_state_history;

typedef struct {
    mc_v0_state samples[MC_V0_STATE_HISTORY_TICKS];
    uint8_t valid_mask;
} mc_v0_state_window;

void mc_v0_state_history_init(mc_v0_state_history *history);
mc_v0_result mc_v0_state_history_push(mc_v0_state_history *history,
                                     const mc_v0_state *state);
mc_v0_result mc_v0_state_history_gap(mc_v0_state_history *history);
mc_v0_result mc_v0_state_history_snapshot(const mc_v0_state_history *history,
                                         mc_v0_state_window *output);

#endif
