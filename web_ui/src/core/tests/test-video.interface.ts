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

import { MEDIA_TYPE } from '../media/base-media.interface';
import { Video, VideoFrame } from '../media/video.interface';
import { TestImageMediaResult } from './test-image.interface';

interface TestVideoMediaFilteredFrames extends TestImageMediaResult {
    frameIndex: number;
}

export interface TestVideoMediaItem {
    type: MEDIA_TYPE.VIDEO;
    media: Video;
    matchedFrames: number;
    filteredFrames: TestVideoMediaFilteredFrames[];
}

export interface TestVideoFrameMediaItem {
    type: MEDIA_TYPE.VIDEO_FRAME;
    media: VideoFrame;
    testResult: TestImageMediaResult;
}
