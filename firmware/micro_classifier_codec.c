#include "micro_classifier_codec.h"

#include <float.h>
#include <math.h>
#include <string.h>

#if defined(__FAST_MATH__) || (defined(__FINITE_MATH_ONLY__) && __FINITE_MATH_ONLY__ > 0)
#error "Wire validation requires finite-value checks; fast math is unsupported"
#endif

_Static_assert(sizeof(float) == 4 && FLT_RADIX == 2 && FLT_MANT_DIG == 24 &&
               FLT_MAX_EXP == 128 && FLT_MIN_EXP == -125,
               "Wire decoding requires IEEE-754 binary32 float");
_Static_assert(DBL_MANT_DIG >= 53, "Confidence validation requires binary64 precision");
_Static_assert(MC_V0_PROTOCOL_VERSION == 0 && MC_V0_SCHEMA_VERSION == 0 &&
               MC_V0_PROFILE_ID == 1 && MC_V0_PROFILE_VERSION == 0 &&
               MC_V0_CATALOGUE_VERSION == 0,
               "Codec supports only the provisional rover v0 contract");
_Static_assert(MC_V0_HEADER_SIZE == 20 && MC_V0_CRC_SIZE == 4 &&
               MC_V0_STATE_PAYLOAD_SIZE == 68 && MC_V0_DECISION_PREFIX_SIZE == 12 &&
               MC_V0_ANSWER_PREFIX_SIZE == 8 && MC_V0_DECISION_MAX_PAYLOAD_SIZE == 104 &&
               MC_V0_MAX_FRAME_SIZE == 128 && MC_V0_PATH_BLOCKED_OPTION_COUNT == 2 &&
               MC_V0_CLEAR_SECTOR_OPTION_COUNT == 4 && MC_V0_SPEED_TIER_OPTION_COUNT == 4 &&
               MC_V0_MODE_OPTION_COUNT == 5,
               "Wire layout changed; update the bounded codec before building");

static uint16_t read16(const uint8_t *data) {
    return (uint16_t)((uint32_t)data[0] | ((uint32_t)data[1] << 8));
}

static uint32_t read32(const uint8_t *data) {
    return (uint32_t)data[0] | ((uint32_t)data[1] << 8) |
           ((uint32_t)data[2] << 16) | ((uint32_t)data[3] << 24);
}

static float read_float(const uint8_t *data) {
    uint32_t bits = read32(data);
    float value;
    memcpy(&value, &bits, sizeof(value));
    return value;
}

uint32_t mc_v0_crc32(const uint8_t *data, size_t length) {
    uint32_t crc = MC_V0_CRC_INITIAL;
    for (size_t index = 0; index < length; ++index) {
        crc ^= data[index];
        for (unsigned bit = 0; bit < 8; ++bit) {
            crc = (crc >> 1) ^ ((crc & 1) ? MC_V0_CRC_POLYNOMIAL_REFLECTED : 0);
        }
    }
    return crc ^ MC_V0_CRC_XOR_OUT;
}

static mc_v0_result check_frame(const uint8_t *data, size_t length,
                                 uint8_t kind, size_t payload_size) {
    if (length != MC_V0_HEADER_SIZE + payload_size + MC_V0_CRC_SIZE) {
        return MC_V0_ERROR_LENGTH;
    }
    if (mc_v0_crc32(data, length - MC_V0_CRC_SIZE) !=
        read32(data + length - MC_V0_CRC_SIZE)) {
        return MC_V0_ERROR_CRC;
    }
    if (data[0] != MC_V0_MAGIC_0 || data[1] != MC_V0_MAGIC_1 ||
        data[MC_V0_HEADER_PROTOCOL_VERSION_OFFSET] != MC_V0_PROTOCOL_VERSION ||
        data[MC_V0_HEADER_KIND_OFFSET] != kind ||
        read16(data + MC_V0_HEADER_PAYLOAD_SIZE_OFFSET) != payload_size ||
        read16(data + MC_V0_HEADER_SCHEMA_VERSION_OFFSET) != MC_V0_SCHEMA_VERSION ||
        read16(data + MC_V0_HEADER_PROFILE_ID_OFFSET) != MC_V0_PROFILE_ID ||
        read16(data + MC_V0_HEADER_PROFILE_VERSION_OFFSET) != MC_V0_PROFILE_VERSION) {
        return MC_V0_ERROR_HEADER;
    }
    return MC_V0_DECODE_OK;
}

static int valid_group(uint32_t age, int valid, const float *values, size_t count) {
    if ((valid && age == MC_V0_UNKNOWN_AGE_US) ||
        (!valid && age != MC_V0_UNKNOWN_AGE_US)) {
        return 0;
    }
    for (size_t index = 0; index < count; ++index) {
        if (!isfinite(values[index]) || (!valid && values[index] != 0.0f)) {
            return 0;
        }
    }
    return 1;
}

mc_v0_result mc_v0_decode_state(const uint8_t *data, size_t length,
                               mc_v0_state *output) {
    if (data == NULL || output == NULL) {
        return MC_V0_ERROR_ARGUMENT;
    }
    mc_v0_result result = check_frame(data, length, MC_V0_KIND_STATE,
                                      MC_V0_STATE_PAYLOAD_SIZE);
    if (result != MC_V0_DECODE_OK) {
        return result;
    }
    mc_v0_state decoded = {0};
    const uint8_t *payload = data + MC_V0_HEADER_SIZE;
    decoded.sequence = read32(data + MC_V0_HEADER_SEQUENCE_OFFSET);
    decoded.timestamp_us = read32(data + MC_V0_HEADER_TIMESTAMP_US_OFFSET);
    decoded.validity = read16(payload + MC_V0_STATE_VALIDITY_OFFSET);
    decoded.task_id = read16(payload + MC_V0_STATE_TASK_ID_OFFSET);
    for (size_t index = 0; index < 5; ++index) {
        decoded.ages_us[index] = read32(payload + MC_V0_STATE_AGES_US_OFFSET + 4 * index);
    }
    for (size_t index = 0; index < 3; ++index) {
        decoded.velocity_m_s[index] = read_float(payload + MC_V0_STATE_VELOCITY_M_S_OFFSET + 4 * index);
        decoded.angular_velocity_rad_s[index] = read_float(payload + MC_V0_STATE_ANGULAR_VELOCITY_RAD_S_OFFSET + 4 * index);
        decoded.goal_m[index] = read_float(payload + MC_V0_STATE_GOAL_M_OFFSET + 4 * index);
    }
    decoded.battery_fraction = read_float(payload + MC_V0_STATE_BATTERY_FRACTION_OFFSET);
    decoded.faults = read32(payload + MC_V0_STATE_FAULTS_OFFSET);
    if ((decoded.validity & ~UINT32_C(31)) != 0 ||
        decoded.task_id != MC_V0_TASK_GOAL_REACHING ||
        !valid_group(decoded.ages_us[0], decoded.validity & MC_V0_VALID_VELOCITY,
                     decoded.velocity_m_s, 3) ||
        !valid_group(decoded.ages_us[1], decoded.validity & MC_V0_VALID_ANGULAR_VELOCITY,
                     decoded.angular_velocity_rad_s, 3) ||
        !valid_group(decoded.ages_us[2], decoded.validity & MC_V0_VALID_GOAL,
                     decoded.goal_m, 3) ||
        !valid_group(decoded.ages_us[3], decoded.validity & MC_V0_VALID_BATTERY,
                     &decoded.battery_fraction, 1) ||
        ((decoded.validity & MC_V0_VALID_FAULTS) ?
            decoded.ages_us[4] == MC_V0_UNKNOWN_AGE_US :
            (decoded.ages_us[4] != MC_V0_UNKNOWN_AGE_US || decoded.faults != 0)) ||
        decoded.battery_fraction < 0.0f || decoded.battery_fraction > 1.0f) {
        return MC_V0_ERROR_STATE;
    }
    *output = decoded;
    return MC_V0_DECODE_OK;
}

static int valid_answer(const mc_v0_answer *answer) {
    double total = 0.0;
    size_t mode = 0;
    for (size_t index = 0; index < answer->option_count; ++index) {
        float probability = answer->probabilities[index];
        if (!isfinite(probability) || probability < 0.0f || probability > 1.0f) {
            return 0;
        }
        total += probability;
        if (probability > answer->probabilities[mode]) {
            mode = index;
        }
    }
    if (fabs(total - 1.0) > 1e-6 || !isfinite(answer->confidence)) {
        return 0;
    }
    double expected = -1.0;
    if (answer->answer_type == MC_V0_TYPE_CHOICE) {
        double uniform = 1.0 / answer->option_count;
        expected = (answer->probabilities[mode] - uniform) / (1.0 - uniform);
    } else if (answer->answer_type == MC_V0_TYPE_SCORE) {
        double deviation = 0.0;
        double uniform = 0.0;
        for (size_t index = 0; index < answer->option_count; ++index) {
            double distance = fabs((double)index - (double)mode);
            deviation += answer->probabilities[index] * distance;
            uniform += distance;
        }
        expected = 1.0 - deviation / (uniform / answer->option_count);
    }
    if (answer->answer_type != MC_V0_TYPE_NOUL && expected < 0.0) {
        expected = 0.0;
    }
    return fabs(answer->confidence - expected) <= 2e-6;
}

mc_v0_result mc_v0_decode_decision(const uint8_t *data, size_t length,
                                  mc_v0_decision *output) {
    static const uint8_t types[4] = {
        MC_V0_TYPE_NOUL, MC_V0_TYPE_CHOICE, MC_V0_TYPE_SCORE, MC_V0_TYPE_CHOICE
    };
    static const uint8_t counts[4] = {
        MC_V0_PATH_BLOCKED_OPTION_COUNT, MC_V0_CLEAR_SECTOR_OPTION_COUNT,
        MC_V0_SPEED_TIER_OPTION_COUNT, MC_V0_MODE_OPTION_COUNT
    };
    if (data == NULL || output == NULL) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if (length < MC_V0_HEADER_SIZE + MC_V0_DECISION_PREFIX_SIZE + MC_V0_CRC_SIZE ||
        length > MC_V0_MAX_FRAME_SIZE) {
        return MC_V0_ERROR_LENGTH;
    }
    size_t size = length - MC_V0_HEADER_SIZE - MC_V0_CRC_SIZE;
    mc_v0_result result = check_frame(data, length, MC_V0_KIND_DECISION, size);
    if (result != MC_V0_DECODE_OK) {
        return result;
    }
    const uint8_t *payload = data + MC_V0_HEADER_SIZE;
    mc_v0_decision decoded = {0};
    decoded.sequence = read32(data + MC_V0_HEADER_SEQUENCE_OFFSET);
    decoded.timestamp_us = read32(data + MC_V0_HEADER_TIMESTAMP_US_OFFSET);
    decoded.latency_us = read32(payload + MC_V0_DECISION_LATENCY_US_OFFSET);
    decoded.status = read16(payload + MC_V0_DECISION_STATUS_OFFSET);
    decoded.model_version = read16(payload + MC_V0_DECISION_MODEL_VERSION_OFFSET);
    decoded.catalogue_version = read16(payload + MC_V0_DECISION_CATALOGUE_VERSION_OFFSET);
    decoded.answer_mask = read16(payload + MC_V0_DECISION_ANSWER_MASK_OFFSET);
    if (decoded.status > MC_V0_STATUS_FAULT ||
        decoded.catalogue_version != MC_V0_CATALOGUE_VERSION ||
        (decoded.answer_mask & ~UINT32_C(15)) != 0 ||
        (decoded.status == MC_V0_STATUS_OK &&
         (decoded.answer_mask != 15 || decoded.model_version == 0))) {
        return MC_V0_ERROR_DECISION;
    }
    size_t offset = MC_V0_DECISION_PREFIX_SIZE;
    for (size_t index = 0; index < 4; ++index) {
        if ((decoded.answer_mask & (UINT32_C(1) << index)) == 0) {
            continue;
        }
        size_t end = offset + MC_V0_ANSWER_PREFIX_SIZE + 4 * counts[index];
        if (end > size) {
            return MC_V0_ERROR_DECISION;
        }
        const uint8_t *source = payload + offset;
        mc_v0_answer *answer = &decoded.answers[index];
        answer->question_id = source[MC_V0_ANSWER_QUESTION_ID_OFFSET];
        answer->answer_type = source[MC_V0_ANSWER_ANSWER_TYPE_OFFSET];
        answer->selected = source[MC_V0_ANSWER_SELECTED_OFFSET];
        answer->option_count = source[MC_V0_ANSWER_OPTION_COUNT_OFFSET];
        answer->confidence = read_float(source + MC_V0_ANSWER_CONFIDENCE_OFFSET);
        if (answer->question_id != index + 1 || answer->answer_type != types[index] ||
            answer->option_count != counts[index] || answer->selected >= counts[index]) {
            return MC_V0_ERROR_DECISION;
        }
        for (size_t option = 0; option < counts[index]; ++option) {
            answer->probabilities[option] = read_float(source + MC_V0_ANSWER_PREFIX_SIZE + 4 * option);
        }
        if (!valid_answer(answer)) {
            return MC_V0_ERROR_DECISION;
        }
        offset = end;
    }
    if (offset != size) {
        return MC_V0_ERROR_DECISION;
    }
    *output = decoded;
    return MC_V0_DECODE_OK;
}

void mc_v0_stream_init(mc_v0_stream *stream) {
    if (stream != NULL) {
        memset(stream, 0, sizeof(*stream));
    }
}

static void discard_prefix(mc_v0_stream *stream, size_t count) {
    memmove(stream->buffer, stream->buffer + count, stream->used - count);
    stream->used -= count;
}

static void reject_candidate(mc_v0_stream *stream) {
    if (stream->rejected_frames != UINT32_MAX) {
        ++stream->rejected_frames;
    }
    discard_prefix(stream, 1);
}

static void process_pending(mc_v0_stream *stream, mc_v0_packet_handler handler,
                             void *context) {
    while (stream->used != 0) {
        if (stream->buffer[0] != MC_V0_MAGIC_0 ||
            (stream->used > 1 && stream->buffer[1] != MC_V0_MAGIC_1)) {
            discard_prefix(stream, 1);
            continue;
        }
        if (stream->used < MC_V0_HEADER_SIZE) {
            return;
        }
        uint8_t kind = stream->buffer[MC_V0_HEADER_KIND_OFFSET];
        size_t size = read16(stream->buffer + MC_V0_HEADER_PAYLOAD_SIZE_OFFSET);
        if (!((kind == MC_V0_KIND_STATE && size == MC_V0_STATE_PAYLOAD_SIZE) ||
              (kind == MC_V0_KIND_DECISION && size >= MC_V0_DECISION_PREFIX_SIZE &&
               size <= MC_V0_DECISION_MAX_PAYLOAD_SIZE))) {
            reject_candidate(stream);
            continue;
        }
        size_t length = MC_V0_HEADER_SIZE + size + MC_V0_CRC_SIZE;
        if (stream->used < length) {
            return;
        }
        mc_v0_packet packet = {0};
        packet.kind = kind;
        mc_v0_result result;
        if (kind == MC_V0_KIND_STATE) {
            result = mc_v0_decode_state(stream->buffer, length, &packet.body.state);
        } else {
            result = mc_v0_decode_decision(stream->buffer, length, &packet.body.decision);
        }
        if (result != MC_V0_DECODE_OK) {
            reject_candidate(stream);
            continue;
        }
        discard_prefix(stream, length);
        handler(&packet, context);
    }
}

mc_v0_result mc_v0_stream_feed(mc_v0_stream *stream, const uint8_t *data,
                              size_t length, mc_v0_packet_handler handler,
                              void *context) {
    if (stream == NULL || (data == NULL && length != 0) || handler == NULL ||
        stream->used >= MC_V0_MAX_FRAME_SIZE) {
        return MC_V0_ERROR_ARGUMENT;
    }
    for (size_t index = 0; index < length; ++index) {
        stream->buffer[stream->used++] = data[index];
        process_pending(stream, handler, context);
    }
    return MC_V0_DECODE_OK;
}
