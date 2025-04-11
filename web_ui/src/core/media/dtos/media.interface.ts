// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ImageMediaDTO } from './image.interface';
import { FilterVideoFrameMediaDTO, VideoFrameMediaDTO, VideoMediaDTO } from './video.interface';

export type MediaItemDTO = ImageMediaDTO | VideoMediaDTO | VideoFrameMediaDTO;

export interface MediaAdvancedFilterDTO {
    media: MediaItemDTO[];
    next_page?: string;
    total_images: number;
    total_matched_images: number;
    total_matched_video_frames: number;
    total_matched_videos: number;
    total_videos: number;
}
export interface MediaAdvancedFramesFilterDTO {
    video_frames: FilterVideoFrameMediaDTO[];
    next_page: string | undefined;
    total_matched_video_frames: number;
}

type ActiveImageMediaDTO = ImageMediaDTO;

interface ActiveVideoMediaDTO extends VideoMediaDTO {
    active_frames: number[];
}

export type ActiveMediaItemDTO = ActiveImageMediaDTO | ActiveVideoMediaDTO;

export interface ActiveMediaDTO {
    active_set: ActiveMediaItemDTO[];
}
