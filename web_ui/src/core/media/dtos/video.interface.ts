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
