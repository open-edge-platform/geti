// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MEDIA_TYPE } from '../base-media.interface';
import { AnnotationStatePerTask } from '../base.interface';
import { BaseMediaDTO } from './base.interface';
import { ImageMediaInformationDTO } from './image.interface';

interface VideoMediaInformationDTO extends ImageMediaInformationDTO {
    duration: number;
    frame_count: number;
    frame_stride: number;
    frame_rate: number;
}

export interface VideoStatisticsDTO {
    annotated: number;
    partially_annotated: number;
    unannotated: number;
}

export interface VideoMediaDTO extends BaseMediaDTO {
    type: 'video';
    matched_frames?: number;
    media_information: VideoMediaInformationDTO;
    annotation_statistics: {
        annotated: number;
        partially_annotated: number;
        unannotated: number;
    };
}

interface VideoFrameMediaInformationDTO extends VideoMediaInformationDTO {
    video_id: string;
}

export interface VideoFrameMediaDTO extends BaseMediaDTO {
    type: 'video_frame';
    frame_index: number;
    matched_frames?: number;
    media_information: VideoFrameMediaInformationDTO;
}

export interface FilterVideoFrameMediaDTO {
    annotation_state_per_task: AnnotationStatePerTask[];
    annotation_statistics: VideoStatisticsDTO;
    frame_index: number;
    media_information: {
        display_url: string;
        height: number;
        width: number;
    };

    name: string;
    thumbnail: string;
    type: MEDIA_TYPE.VIDEO_FRAME;
    upload_time: string;
    uploader_id: string;
    video_id: string;
}
