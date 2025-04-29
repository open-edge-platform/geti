// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
