#ifndef MICRO_CLASSIFIER_CODEC_H
#define MICRO_CLASSIFIER_CODEC_H

#include <stddef.h>
#include "micro_classifier_protocol.h"

typedef enum {
    MC_V0_DECODE_OK = 0,
    MC_V0_ERROR_ARGUMENT,
    MC_V0_ERROR_LENGTH,
    MC_V0_ERROR_CRC,
    MC_V0_ERROR_HEADER,
    MC_V0_ERROR_STATE,
    MC_V0_ERROR_DECISION
} mc_v0_result;

typedef struct {
    uint32_t sequence;
    uint32_t timestamp_us;
    uint16_t validity;
    uint16_t task_id;
    uint32_t ages_us[5];
    float velocity_m_s[3];
    float angular_velocity_rad_s[3];
    float goal_m[3];
    float battery_fraction;
    uint32_t faults;
} mc_v0_state;

typedef struct {
    uint8_t question_id;
    uint8_t answer_type;
    uint8_t selected;
    uint8_t option_count;
    float confidence;
    float probabilities[5];
} mc_v0_answer;

typedef struct {
    uint32_t sequence;
    uint32_t timestamp_us;
    uint32_t latency_us;
    uint16_t status;
    uint16_t model_version;
    uint16_t catalogue_version;
    uint16_t answer_mask;
    mc_v0_answer answers[4];
} mc_v0_decision;

typedef struct {
    uint8_t kind;
    union {
        mc_v0_state state;
        mc_v0_decision decision;
    } body;
} mc_v0_packet;

typedef struct {
    uint8_t buffer[MC_V0_MAX_FRAME_SIZE];
    size_t used;
    uint32_t rejected_frames;
} mc_v0_stream;

typedef void (*mc_v0_packet_handler)(const mc_v0_packet *packet, void *context);

uint32_t mc_v0_crc32(const uint8_t *data, size_t length);
mc_v0_result mc_v0_decode_state(const uint8_t *data, size_t length,
                               mc_v0_state *output);
mc_v0_result mc_v0_decode_decision(const uint8_t *data, size_t length,
                                  mc_v0_decision *output);
void mc_v0_stream_init(mc_v0_stream *stream);
mc_v0_result mc_v0_stream_feed(mc_v0_stream *stream, const uint8_t *data,
                              size_t length, mc_v0_packet_handler handler,
                              void *context);

#endif
