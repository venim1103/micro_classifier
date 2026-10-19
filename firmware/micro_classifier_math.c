#include "micro_classifier_math.h"

#include <float.h>
#include <math.h>
#include <string.h>

#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__ > 0)
#error "Decision math requires finite-value checks; fast math is unsupported"
#endif

_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 &&
               FLT_MAX_EXP == 128 && FLT_MIN_EXP == -125,
               "Decision math requires IEEE-754 binary32 float");
_Static_assert(DBL_MANT_DIG >= 53 && DBL_MAX_EXP >= 1024,
               "Decision math requires at least binary64 precision and range");

mc_v0_result mc_v0_softmax(const float *logits, size_t option_count,
                          float *probabilities, size_t capacity) {
    if (logits == NULL || probabilities == NULL ||
        (option_count != 2 && option_count != 4 && option_count != 5)) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if (capacity < option_count) {
        return MC_V0_ERROR_LENGTH;
    }
    double maximum = logits[0];
    for (size_t index = 0; index < option_count; ++index) {
        if (!isfinite(logits[index])) {
            return MC_V0_ERROR_DECISION;
        }
        if (logits[index] > maximum) {
            maximum = logits[index];
        }
    }
    double weights[5];
    double total = 0.0;
    for (size_t index = 0; index < option_count; ++index) {
        weights[index] = exp((double)logits[index] - maximum);
        total += weights[index];
    }
    float result[5];
    for (size_t index = 0; index < option_count; ++index) {
        result[index] = (float)(weights[index] / total);
    }
    memcpy(probabilities, result, option_count * sizeof(result[0]));
    return MC_V0_MATH_OK;
}

mc_v0_result mc_v0_sigmoid(float logit, float *probabilities, size_t capacity) {
    if (probabilities == NULL) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if (capacity < 2) {
        return MC_V0_ERROR_LENGTH;
    }
    if (!isfinite(logit)) {
        return MC_V0_ERROR_DECISION;
    }
    double weight = exp(-fabs((double)logit));
    double total = 1.0 + weight;
    float result[2];
    result[0] = (float)((logit >= 0.0f ? weight : 1.0) / total);
    result[1] = (float)((logit >= 0.0f ? 1.0 : weight) / total);
    memcpy(probabilities, result, sizeof(result));
    return MC_V0_MATH_OK;
}
