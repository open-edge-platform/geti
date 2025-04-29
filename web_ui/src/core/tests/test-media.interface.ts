// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TestImageMediaItem } from './test-image.interface';
import { TestVideoFrameMediaItem, TestVideoMediaItem } from './test-video.interface';

export type TestMediaItem = TestImageMediaItem | TestVideoFrameMediaItem | TestVideoMediaItem;

export interface TestMediaAdvancedFilter {
    media: TestMediaItem[];
    nextPage?: string;
    totalImages: number;
    totalVideos: number;
    totalMatchedImages: number;
    totalMatchedVideos: number;
    totalMatchedVideoFrames: number;
}
