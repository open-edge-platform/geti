// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
