#ifndef MICRO_CLASSIFIER_HEADS_H
#define MICRO_CLASSIFIER_HEADS_H

#include "micro_classifier_codec.h"

#define MC_V0_HEAD_MAX_FEATURES UINT32_C(256)
#define MC_V0_HEAD_MAX_OUTPUTS UINT32_C(5)

mc_v0_result mc_v0_dense_head(const float *features, size_t feature_count,
                             const float *weights, size_t weight_count,
                             const float *biases, size_t bias_count,
                             size_t output_count, float *logits, size_t capacity);

#endif
