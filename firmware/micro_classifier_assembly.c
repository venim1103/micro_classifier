#include "micro_classifier_assembly.h"
#include "micro_classifier_math.h"

#include <string.h>

#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__ > 0)
#error "Decision assembly fast math is unsupported"
#endif

mc_v0_result mc_v0_assemble_decision(const mc_v0_decision *metadata,
                                   const mc_v0_head_input *inputs,
                                   size_t input_count, mc_v0_decision *output) {
    if (metadata == NULL || inputs == NULL || output == NULL ||
        input_count != MC_V0_ASSEMBLY_HEAD_COUNT) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if (metadata->answer_mask != UINT32_C(15)) {
        return MC_V0_ERROR_DECISION;
    }
    mc_v0_decision assembled = *metadata;
    for (size_t index = 0; index < MC_V0_ASSEMBLY_HEAD_COUNT; ++index) {
        memset(assembled.answers[index].probabilities, 0,
               sizeof(assembled.answers[index].probabilities));
        assembled.answers[index].probabilities[0] = 1.0f;
    }
    uint8_t frame[MC_V0_MAX_FRAME_SIZE];
    size_t written = 0;
    mc_v0_result result = mc_v0_encode_decision(&assembled, frame, sizeof(frame), &written);
    if (result != MC_V0_ENCODE_OK) {
        return result;
    }
    for (size_t index = 0; index < MC_V0_ASSEMBLY_HEAD_COUNT; ++index) {
        const mc_v0_head_input *input = &inputs[index];
        mc_v0_answer *answer = &assembled.answers[index];
        size_t rows = index == 0 ? 1 : answer->option_count;
        float logits[MC_V0_HEAD_MAX_OUTPUTS];
        result = mc_v0_dense_head(input->features, input->feature_count,
                                 input->weights, input->weight_count,
                                 input->biases, input->bias_count,
                                 rows, logits, MC_V0_HEAD_MAX_OUTPUTS);
        if (result != MC_V0_HEAD_OK) {
            return result;
        }
        result = index == 0
                     ? mc_v0_sigmoid(logits[0], answer->probabilities, answer->option_count)
                     : mc_v0_softmax(logits, rows, answer->probabilities, answer->option_count);
        if (result != MC_V0_MATH_OK) {
            return result;
        }
    }
    result = mc_v0_encode_decision(&assembled, frame, sizeof(frame), &written);
    if (result != MC_V0_ENCODE_OK) {
        return result;
    }
    return mc_v0_decode_decision(frame, written, output);
}