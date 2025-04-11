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

import { VideoFrameMediaDTO, VideoMediaDTO } from '../../media/dtos/video.interface';
import { TestImageMediaResultDTO } from './test-image.interface';

interface TestVideoMediaFilteredFramesDTO extends TestImageMediaResultDTO {
    frame_index: number;
}

export interface TestVideoMediaItemDTO extends VideoMediaDTO {
    filtered_frames: Record<number, TestVideoMediaFilteredFramesDTO>;
}

export interface TestVideoFrameMediaItemDTO extends Omit<VideoFrameMediaDTO, 'matched_frames'> {
    video_id: string;
    frame_index: number;
    test_result: TestImageMediaResultDTO;
}
