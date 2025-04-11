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

import { Point } from '../shapes.interface';
import { AnnotationDTO, ImageIdDTO, ShapeDTO, VideoFrameIdDTO } from './annotation.interface';

export interface ExplanationDTO {
    id: string;
    url: string;
    name: string;
    label_id: string;
    binary?: string;

    roi: {
        id: string;
        shape: {
            y: number;
            x: number;
            type: string;
            height: number;
            width: number;
        };
    };
}

export interface NewPredictionLabelDTO {
    id: string;
    name: string;
    probability: number;
}

export interface NewPredictionDTO {
    labels: NewPredictionLabelDTO[];
    shape: ShapeDTO;
}

export interface NewPredictionsDTO {
    created: string;
    predictions: NewPredictionDTO[];
}

export interface NewTestPredictionsDTO extends NewPredictionsDTO {
    media_identifier: ImageIdDTO;
}

export interface NewExplanationDTO {
    label_id: string;
    label_name: string;
    data: string;
}

export interface NewExplanationsDTO {
    created: string;
    maps: NewExplanationDTO[];
}

export interface PredictionDTO {
    id: string;
    kind: 'prediction';
    maps: ExplanationDTO[];
    media_identifier: ImageIdDTO | VideoFrameIdDTO;
    modified: string;
    annotations: AnnotationDTO[];
}

interface VideoPredictionDTO {
    annotations: AnnotationDTO[];
    labels_to_revisit_full_scene: string[];
    id: string;
    kind: 'prediction';
    media_identifier: VideoFrameIdDTO;
    modified: string;
}

export interface VideoPredictionsDTO {
    video_predictions: VideoPredictionDTO[];
    video_prediction_properties: {
        end_frame: number;
        requested_end_frame: number | null;
        requested_start_frame: number;
        start_frame: number;
        total_count: number;
        total_requested_count: number;
    };
}

export interface InferenceServerStatusDTO {
    inference_server_ready: boolean;
}

export interface PipelineServerStatusDTO {
    pipeline_ready: boolean;
}

export interface KeypointPredictionDTO {
    keypoints: Point[];
    labels: string[];
    scores: number[];
}
