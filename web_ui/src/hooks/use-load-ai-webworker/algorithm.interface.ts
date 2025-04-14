// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum AlgorithmType {
    GRABCUT = 'GRABCUT',
    WATERSHED = 'WATERSHED',
    SSIM = 'SSIM',
    RITM = 'RITM',
    INTELLIGENT_SCISSORS = 'INTELLIGENT_SCISSORS',
    INFERENCE_IMAGE = 'INFERENCE_IMAGE',
    // For Segment Anything we use two workers so that the encoder and decoder are run on separate threads
    SEGMENT_ANYTHING_ENCODER = 'SEGMENT_ANYTHING_ENCODER',
    SEGMENT_ANYTHING_DECODER = 'SEGMENT_ANYTHING_DECODER',
}
