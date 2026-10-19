#include "micro_classifier_heads.h"

#include <float.h>
#include <math.h>
#include <string.h>

#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__ > 0)
#error "Head reference requires finite-value checks; fast math is unsupported"
#endif

_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 &&
               FLT_MAX_EXP == 128 && FLT_MIN_EXP == -125,
               "Head reference requires IEEE-754 binary32 float");
_Static_assert(DBL_MANT_DIG >= 53 && DBL_MAX_EXP >= 1024 && DBL_MIN_EXP <= -1021,
               "Head reference requires at least binary64 precision and range");

static size_t add_partial(double *partials, size_t used, double value) {
    size_t retained = 0;
    for (size_t index = 0; index < used; ++index) {
        double previous = partials[index];
        if (fabs(value) < fabs(previous)) {
            double swap = value;
            value = previous;
            previous = swap;
        }
        double high = value + previous;
        double low = previous - (high - value);
        if (low != 0.0) {
            partials[retained++] = low;
        }
        value = high;
    }
    partials[retained] = value;
    return retained + 1;
}

mc_v0_result mc_v0_dense_head(const float *features, size_t feature_count,
                             const float *weights, size_t weight_count,
                             const float *biases, size_t bias_count,
                             size_t output_count, float *logits, size_t capacity) {
    if (features == NULL || weights == NULL || biases == NULL || logits == NULL ||
        feature_count == 0 || feature_count > MC_V0_HEAD_MAX_FEATURES ||
        output_count == 0 || output_count > MC_V0_HEAD_MAX_OUTPUTS) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if (weight_count < feature_count * output_count || bias_count < output_count ||
        capacity < output_count) {
        return MC_V0_ERROR_LENGTH;
    }
    for (size_t index = 0; index < feature_count; ++index) {
        if (!isfinite(features[index])) {
            return MC_V0_ERROR_DECISION;
        }
    }
    float result[MC_V0_HEAD_MAX_OUTPUTS];
    double partials[MC_V0_HEAD_MAX_FEATURES + 1];
    for (size_t row = 0; row < output_count; ++row) {
        if (!isfinite(biases[row])) {
            return MC_V0_ERROR_DECISION;
        }
        partials[0] = biases[row];
        size_t used = 1;
        for (size_t column = 0; column < feature_count; ++column) {
            float weight = weights[row * feature_count + column];
            if (!isfinite(weight)) {
                return MC_V0_ERROR_DECISION;
            }
            double product = (double)features[column] * weight;
            used = add_partial(partials, used, product);
        }
        double value = 0.0;
        for (size_t index = 0; index < used; ++index) {
            value += partials[index];
        }
        if (!isfinite(value) || fabs(value) > FLT_MAX) {
            return MC_V0_ERROR_DECISION;
        }
        result[row] = (float)value;
    }
    memcpy(logits, result, output_count * sizeof(result[0]));
    return MC_V0_HEAD_OK;
}
