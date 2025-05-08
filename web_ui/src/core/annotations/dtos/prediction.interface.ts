// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
    predictions: (NewPredictionDTO | NewKeypointPredictionDTO)[];
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

export interface NewKeypointPredictionDTO {
    created: string;
    keypoints: KeypointPredictionDTO[];
}

export interface KeypointPredictionDTO {
    id: string;
    name: string;
    score: number;
    x: number;
    y: number;
}
