#ifndef MICRO_CLASSIFIER_ASSEMBLY_H
#define MICRO_CLASSIFIER_ASSEMBLY_H

#include "micro_classifier_heads.h"

#define MC_V0_ASSEMBLY_HEAD_COUNT UINT32_C(4)
#define MC_V0_ASSEMBLY_OK MC_V0_DECODE_OK

typedef struct {
    const float *features;
    size_t feature_count;
    const float *weights;
    size_t weight_count;
    const float *biases;
    size_t bias_count;
} mc_v0_head_input;

mc_v0_result mc_v0_assemble_decision(const mc_v0_decision *metadata,
                                   const mc_v0_head_input *inputs,
                                   size_t input_count, mc_v0_decision *output);

#endif