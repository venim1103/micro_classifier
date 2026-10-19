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

static const uint8_t answer_types[4] = {
    MC_V0_TYPE_NOUL, MC_V0_TYPE_CHOICE, MC_V0_TYPE_SCORE, MC_V0_TYPE_CHOICE
};
static const uint8_t answer_counts[4] = {
    MC_V0_PATH_BLOCKED_OPTION_COUNT, MC_V0_CLEAR_SECTOR_OPTION_COUNT,
    MC_V0_SPEED_TIER_OPTION_COUNT, MC_V0_MODE_OPTION_COUNT
};

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

static void write16(uint8_t *data, uint16_t value) {
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8);
}

static void write32(uint8_t *data, uint32_t value) {
    for (unsigned index = 0; index < 4; ++index) {
        data[index] = (uint8_t)(value >> (8 * index));
    }
}

static void write_float(uint8_t *data, float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    write32(data, bits);
}

static void write_header(uint8_t *data, uint8_t kind, uint16_t size,
                           uint32_t sequence, uint32_t timestamp_us) {
    data[0] = MC_V0_MAGIC_0;
    data[1] = MC_V0_MAGIC_1;
    data[MC_V0_HEADER_PROTOCOL_VERSION_OFFSET] = MC_V0_PROTOCOL_VERSION;
    data[MC_V0_HEADER_KIND_OFFSET] = kind;
    write16(data + MC_V0_HEADER_PAYLOAD_SIZE_OFFSET, size);
    write16(data + MC_V0_HEADER_SCHEMA_VERSION_OFFSET, MC_V0_SCHEMA_VERSION);
    write16(data + MC_V0_HEADER_PROFILE_ID_OFFSET, MC_V0_PROFILE_ID);
    write16(data + MC_V0_HEADER_PROFILE_VERSION_OFFSET, MC_V0_PROFILE_VERSION);
    write32(data + MC_V0_HEADER_SEQUENCE_OFFSET, sequence);
    write32(data + MC_V0_HEADER_TIMESTAMP_US_OFFSET, timestamp_us);
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

mc_v0_result mc_v0_validate_state(const mc_v0_state *state) {
    if (state == NULL) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if ((state->validity & ~UINT32_C(31)) != 0 ||
        state->task_id != MC_V0_TASK_GOAL_REACHING ||
        !valid_group(state->ages_us[0], state->validity & MC_V0_VALID_VELOCITY,
                     state->velocity_m_s, 3) ||
        !valid_group(state->ages_us[1], state->validity & MC_V0_VALID_ANGULAR_VELOCITY,
                     state->angular_velocity_rad_s, 3) ||
        !valid_group(state->ages_us[2], state->validity & MC_V0_VALID_GOAL,
                     state->goal_m, 3) ||
        !valid_group(state->ages_us[3], state->validity & MC_V0_VALID_BATTERY,
                     &state->battery_fraction, 1) ||
        ((state->validity & MC_V0_VALID_FAULTS) ?
            state->ages_us[4] == MC_V0_UNKNOWN_AGE_US :
            (state->ages_us[4] != MC_V0_UNKNOWN_AGE_US || state->faults != 0)) ||
        state->battery_fraction < 0.0f || state->battery_fraction > 1.0f) {
        return MC_V0_ERROR_STATE;
    }
    return MC_V0_DECODE_OK;
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
    if (mc_v0_validate_state(&decoded) != MC_V0_DECODE_OK) {
        return MC_V0_ERROR_STATE;
    }
    *output = decoded;
    return MC_V0_DECODE_OK;
}

mc_v0_result mc_v0_encode_state(const mc_v0_state *state, uint8_t *output,
                               size_t capacity, size_t *written) {
    if (state == NULL || output == NULL || written == NULL) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if (capacity < MC_V0_STATE_FRAME_SIZE) {
        return MC_V0_ERROR_LENGTH;
    }
    if (mc_v0_validate_state(state) != MC_V0_DECODE_OK) {
        return MC_V0_ERROR_STATE;
    }
    uint8_t frame[MC_V0_STATE_FRAME_SIZE] = {0};
    uint8_t *payload = frame + MC_V0_HEADER_SIZE;
    write_header(frame, MC_V0_KIND_STATE, MC_V0_STATE_PAYLOAD_SIZE,
                 state->sequence, state->timestamp_us);
    write16(payload + MC_V0_STATE_VALIDITY_OFFSET, state->validity);
    write16(payload + MC_V0_STATE_TASK_ID_OFFSET, state->task_id);
    for (size_t index = 0; index < 5; ++index) {
        write32(payload + MC_V0_STATE_AGES_US_OFFSET + 4 * index, state->ages_us[index]);
    }
    for (size_t index = 0; index < 3; ++index) {
        write_float(payload + MC_V0_STATE_VELOCITY_M_S_OFFSET + 4 * index,
                    state->velocity_m_s[index]);
        write_float(payload + MC_V0_STATE_ANGULAR_VELOCITY_RAD_S_OFFSET + 4 * index,
                    state->angular_velocity_rad_s[index]);
        write_float(payload + MC_V0_STATE_GOAL_M_OFFSET + 4 * index, state->goal_m[index]);
    }
    write_float(payload + MC_V0_STATE_BATTERY_FRACTION_OFFSET, state->battery_fraction);
    write32(payload + MC_V0_STATE_FAULTS_OFFSET, state->faults);
    write32(frame + sizeof(frame) - MC_V0_CRC_SIZE,
            mc_v0_crc32(frame, sizeof(frame) - MC_V0_CRC_SIZE));
    memcpy(output, frame, sizeof(frame));
    *written = sizeof(frame);
    return MC_V0_ENCODE_OK;
}

mc_v0_result mc_v0_answer_confidence(const mc_v0_answer *answer, double *confidence) {
    if (answer == NULL || confidence == NULL) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if (answer->question_id < 1 || answer->question_id > 4 ||
        answer->answer_type != answer_types[answer->question_id - 1] ||
        answer->option_count != answer_counts[answer->question_id - 1] ||
        answer->selected >= answer->option_count) {
        return MC_V0_ERROR_DECISION;
    }
    double total = 0.0;
    size_t mode = 0;
    for (size_t index = 0; index < answer->option_count; ++index) {
        float probability = answer->probabilities[index];
        if (!isfinite(probability) || probability < 0.0f || probability > 1.0f) {
            return MC_V0_ERROR_DECISION;
        }
        total += probability;
        if (probability > answer->probabilities[mode]) {
            mode = index;
        }
    }
    if (fabs(total - 1.0) > 1e-6) {
        return MC_V0_ERROR_DECISION;
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
    *confidence = expected;
    return MC_V0_MATH_OK;
}

static int valid_answer(const mc_v0_answer *answer) {
    double expected;
    return isfinite(answer->confidence) &&
           mc_v0_answer_confidence(answer, &expected) == MC_V0_MATH_OK &&
           fabs(answer->confidence - expected) <= 2e-6;
}

static int valid_decision_prefix(const mc_v0_decision *decision) {
    return decision->status <= MC_V0_STATUS_FAULT &&
           decision->catalogue_version == MC_V0_CATALOGUE_VERSION &&
           (decision->answer_mask & ~UINT32_C(15)) == 0 &&
           (decision->status != MC_V0_STATUS_OK ||
            (decision->answer_mask == 15 && decision->model_version != 0));
}

mc_v0_result mc_v0_decode_decision(const uint8_t *data, size_t length,
                                  mc_v0_decision *output) {
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
    if (!valid_decision_prefix(&decoded)) {
        return MC_V0_ERROR_DECISION;
    }
    size_t offset = MC_V0_DECISION_PREFIX_SIZE;
    for (size_t index = 0; index < 4; ++index) {
        if ((decoded.answer_mask & (UINT32_C(1) << index)) == 0) {
            continue;
        }
        size_t end = offset + MC_V0_ANSWER_PREFIX_SIZE + 4 * answer_counts[index];
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
        if (answer->question_id != index + 1 || answer->answer_type != answer_types[index] ||
            answer->option_count != answer_counts[index] || answer->selected >= answer_counts[index]) {
            return MC_V0_ERROR_DECISION;
        }
        for (size_t option = 0; option < answer_counts[index]; ++option) {
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

mc_v0_result mc_v0_encode_decision(const mc_v0_decision *decision, uint8_t *output,
                                  size_t capacity, size_t *written) {
    if (decision == NULL || output == NULL || written == NULL) {
        return MC_V0_ERROR_ARGUMENT;
    }
    if (capacity < MC_V0_HEADER_SIZE + MC_V0_DECISION_PREFIX_SIZE + MC_V0_CRC_SIZE) {
        return MC_V0_ERROR_LENGTH;
    }
    if (!valid_decision_prefix(decision)) {
        return MC_V0_ERROR_DECISION;
    }
    uint8_t frame[MC_V0_MAX_FRAME_SIZE] = {0};
    uint8_t *payload = frame + MC_V0_HEADER_SIZE;
    write32(payload + MC_V0_DECISION_LATENCY_US_OFFSET, decision->latency_us);
    write16(payload + MC_V0_DECISION_STATUS_OFFSET, decision->status);
    write16(payload + MC_V0_DECISION_MODEL_VERSION_OFFSET, decision->model_version);
    write16(payload + MC_V0_DECISION_CATALOGUE_VERSION_OFFSET, decision->catalogue_version);
    write16(payload + MC_V0_DECISION_ANSWER_MASK_OFFSET, decision->answer_mask);
    size_t offset = MC_V0_DECISION_PREFIX_SIZE;
    for (size_t index = 0; index < 4; ++index) {
        if ((decision->answer_mask & (UINT32_C(1) << index)) == 0) {
            continue;
        }
        const mc_v0_answer *answer = &decision->answers[index];
        if (answer->question_id != index + 1 || answer->answer_type != answer_types[index] ||
            answer->option_count != answer_counts[index] || answer->selected >= answer_counts[index]) {
            return MC_V0_ERROR_DECISION;
        }
        double confidence;
        if (mc_v0_answer_confidence(answer, &confidence) != MC_V0_MATH_OK) {
            return MC_V0_ERROR_DECISION;
        }
        uint8_t *target = payload + offset;
        target[MC_V0_ANSWER_QUESTION_ID_OFFSET] = answer->question_id;
        target[MC_V0_ANSWER_ANSWER_TYPE_OFFSET] = answer->answer_type;
        target[MC_V0_ANSWER_SELECTED_OFFSET] = answer->selected;
        target[MC_V0_ANSWER_OPTION_COUNT_OFFSET] = answer->option_count;
        write_float(target + MC_V0_ANSWER_CONFIDENCE_OFFSET, (float)confidence);
        for (size_t option = 0; option < answer_counts[index]; ++option) {
            write_float(target + MC_V0_ANSWER_PREFIX_SIZE + 4 * option,
                        answer->probabilities[option]);
        }
        offset += MC_V0_ANSWER_PREFIX_SIZE + 4 * answer_counts[index];
    }
    size_t length = MC_V0_HEADER_SIZE + offset + MC_V0_CRC_SIZE;
    if (capacity < length) {
        return MC_V0_ERROR_LENGTH;
    }
    write_header(frame, MC_V0_KIND_DECISION, (uint16_t)offset,
                 decision->sequence, decision->timestamp_us);
    write32(frame + length - MC_V0_CRC_SIZE, mc_v0_crc32(frame, length - MC_V0_CRC_SIZE));
    memcpy(output, frame, length);
    *written = length;
    return MC_V0_ENCODE_OK;
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
                             void *context, int discard_incomplete) {
    while (stream->used != 0) {
        if (stream->buffer[0] != MC_V0_MAGIC_0 ||
            (stream->used > 1 && stream->buffer[1] != MC_V0_MAGIC_1)) {
            discard_prefix(stream, 1);
            continue;
        }
        if (stream->used < MC_V0_HEADER_SIZE) {
            if (discard_incomplete) {
                stream->used = 0;
            }
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
            if (discard_incomplete) {
                reject_candidate(stream);
                continue;
            }
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
        process_pending(stream, handler, context, 0);
    }
    return MC_V0_DECODE_OK;
}

mc_v0_result mc_v0_stream_flush(mc_v0_stream *stream, mc_v0_packet_handler handler,
                               void *context) {
    if (stream == NULL || handler == NULL || stream->used >= MC_V0_MAX_FRAME_SIZE) {
        return MC_V0_ERROR_ARGUMENT;
    }
    process_pending(stream, handler, context, 1);
    return MC_V0_DECODE_OK;
}
