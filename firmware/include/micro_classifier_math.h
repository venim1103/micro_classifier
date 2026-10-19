#ifndef MICRO_CLASSIFIER_MATH_H
#define MICRO_CLASSIFIER_MATH_H

#include "micro_classifier_codec.h"

mc_v0_result mc_v0_softmax(const float *logits, size_t option_count,
                          float *probabilities, size_t capacity);
mc_v0_result mc_v0_sigmoid(float logit, float *probabilities, size_t capacity);

#endif
