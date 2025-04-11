// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { VideoPlayerErrorReason } from './streaming-video-player/streaming-video-player.interface';
import { getMaxVideoSliderValue, getPlayTooltip, VIDEO_FORMAT_NOT_SUPPORTED } from './utils';

it('getMaxVideoSliderValue', () => {
    expect(getMaxVideoSliderValue(10)).toBe(9);
});

describe('getPlayTooltip', () => {
    it('inference server is not ready', () => {
        expect(getPlayTooltip(false, true, false, undefined)).toBe(
            `The inference server isn't ready yet to process your request.`
        );
    });

    it('inference server is not ready with video errors', () => {
        expect(getPlayTooltip(false, false, false, VideoPlayerErrorReason.MEDIA_ERR_SRC_NOT_SUPPORTED)).toBe(
            VIDEO_FORMAT_NOT_SUPPORTED
        );
    });

    it('isBufferedFrame', () => {
        expect(getPlayTooltip(false, false, true, undefined)).toBe(`Loading next annotations...`);
    });

    it('isBufferedFrame with video errors', () => {
        expect(getPlayTooltip(false, false, true, VideoPlayerErrorReason.MEDIA_ERR_SRC_NOT_SUPPORTED)).toBe(
            VIDEO_FORMAT_NOT_SUPPORTED
        );
    });

    it('isInSubTask', () => {
        expect(getPlayTooltip(true, true, true, undefined)).toBe(
            `Playing videos inside a sub task is disabled. Please select all tasks or detection task.`
        );
    });

    it('undefined error', () => {
        expect(getPlayTooltip(false, true, true, undefined)).toBe(undefined);
    });

    it('network error', () => {
        const message = 'Cannot play video due to a network error, please refresh and try again.';
        expect(getPlayTooltip(false, true, true, VideoPlayerErrorReason.MEDIA_ERR_ABORTED)).toBe(message);
        expect(getPlayTooltip(false, true, true, VideoPlayerErrorReason.MEDIA_ERR_NETWORK)).toBe(message);
    });

    it('video is not supported', () => {
        expect(getPlayTooltip(false, true, true, VideoPlayerErrorReason.MEDIA_ERR_DECODE)).toBe(
            VIDEO_FORMAT_NOT_SUPPORTED
        );
        expect(getPlayTooltip(false, true, true, VideoPlayerErrorReason.MEDIA_ERR_SRC_NOT_SUPPORTED)).toBe(
            VIDEO_FORMAT_NOT_SUPPORTED
        );
    });

    it('invalid error reason', () => {
        expect(getPlayTooltip(false, true, true, 11 as VideoPlayerErrorReason)).toBe(undefined);
    });
});
