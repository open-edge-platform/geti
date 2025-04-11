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
