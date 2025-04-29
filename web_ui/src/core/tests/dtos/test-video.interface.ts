// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
