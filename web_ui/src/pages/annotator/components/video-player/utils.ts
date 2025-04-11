// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import isNil from 'lodash/isNil';

import { VideoPlayerErrorReason } from './streaming-video-player/streaming-video-player.interface';

export const VIDEO_FORMAT_NOT_SUPPORTED =
    'Unable to play video, please try a different browser or a different video format (mp4/webm).';

export const getMaxVideoSliderValue = (frames: number): number => {
    // Note: the first video frame is numbered as 0, so we want any video slider to
    // start from 0 to frames - 1
    return frames - 1;
};

export const getPlayTooltip = (
    isInSubTask: boolean,
    isBufferedFrame: boolean,
    isInferenceServerReady: boolean,
    error: VideoPlayerErrorReason | undefined
) => {
    if (isInSubTask) {
        return 'Playing videos inside a sub task is disabled. Please select all tasks or detection task.';
    }

    if (isNil(error) && !isInferenceServerReady) {
        return `The inference server isn't ready yet to process your request.`;
    }

    if (isNil(error) && !isBufferedFrame) {
        return 'Loading next annotations...';
    }

    if (isNil(error)) {
        return undefined;
    }

    if ([VideoPlayerErrorReason.MEDIA_ERR_ABORTED, VideoPlayerErrorReason.MEDIA_ERR_NETWORK].includes(error)) {
        return 'Cannot play video due to a network error, please refresh and try again.';
    }

    if ([VideoPlayerErrorReason.MEDIA_ERR_DECODE, VideoPlayerErrorReason.MEDIA_ERR_SRC_NOT_SUPPORTED].includes(error)) {
        return VIDEO_FORMAT_NOT_SUPPORTED;
    }
};
