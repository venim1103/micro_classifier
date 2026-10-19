#include "micro_classifier_history.h"

#include <string.h>

_Static_assert(MC_V0_STATE_HISTORY_TICKS == 8, "Reference requires eight history ticks");

void mc_v0_state_history_init(mc_v0_state_history *history) {
    if (history != NULL) {
        memset(history, 0, sizeof(*history));
    }
}

static void advance(mc_v0_state_history *history, const mc_v0_state *state) {
    uint8_t bit = (uint8_t)(UINT32_C(1) << history->next);
    if (state == NULL) {
        memset(&history->samples[history->next], 0, sizeof(history->samples[0]));
        history->valid_mask &= (uint8_t)~bit;
    } else {
        history->samples[history->next] = *state;
        history->valid_mask |= bit;
    }
    history->next = (uint8_t)((history->next + 1u) % MC_V0_STATE_HISTORY_TICKS);
}

mc_v0_result mc_v0_state_history_push(mc_v0_state_history *history,
                                     const mc_v0_state *state) {
    if (history == NULL || history->next >= MC_V0_STATE_HISTORY_TICKS) {
        return MC_V0_ERROR_ARGUMENT;
    }
    mc_v0_result result = mc_v0_validate_state(state);
    if (result != MC_V0_DECODE_OK) {
        return result;
    }
    advance(history, state);
    return MC_V0_HISTORY_OK;
}

mc_v0_result mc_v0_state_history_gap(mc_v0_state_history *history) {
    if (history == NULL || history->next >= MC_V0_STATE_HISTORY_TICKS) {
        return MC_V0_ERROR_ARGUMENT;
    }
    advance(history, NULL);
    return MC_V0_HISTORY_OK;
}

mc_v0_result mc_v0_state_history_snapshot(const mc_v0_state_history *history,
                                         mc_v0_state_window *output) {
    if (history == NULL || output == NULL || history->next >= MC_V0_STATE_HISTORY_TICKS) {
        return MC_V0_ERROR_ARGUMENT;
    }
    mc_v0_state_window window = {0};
    for (size_t index = 0; index < MC_V0_STATE_HISTORY_TICKS; ++index) {
        size_t physical = (history->next + index) % MC_V0_STATE_HISTORY_TICKS;
        if (history->valid_mask & (UINT32_C(1) << physical)) {
            window.samples[index] = history->samples[physical];
            window.valid_mask |= (uint8_t)(UINT32_C(1) << index);
        }
    }
    *output = window;
    return MC_V0_HISTORY_OK;
}
