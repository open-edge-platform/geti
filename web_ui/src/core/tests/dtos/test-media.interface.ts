// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { TestImageMediaItemDTO } from './test-image.interface';
import { TestVideoFrameMediaItemDTO, TestVideoMediaItemDTO } from './test-video.interface';

export type TestMediaItemDTO = TestImageMediaItemDTO | TestVideoMediaItemDTO | TestVideoFrameMediaItemDTO;

export interface TestMediaAdvancedFilterDTO {
    media: TestMediaItemDTO[];
    next_page?: string;
    total_images: number;
    total_videos: number;
    total_matched_images: number;
    total_matched_videos: number;
    total_matched_video_frames: number;
}
