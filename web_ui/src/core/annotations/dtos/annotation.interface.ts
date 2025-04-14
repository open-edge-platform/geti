// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AnnotationStatePerTaskDTO } from '../../media/dtos/base.interface';

export interface ImageIdDTO {
    image_id: string;
    type: 'image';
}

export interface VideoIdDTO {
    type: 'video';
    video_id: string;
}

export interface VideoFrameIdDTO {
    frame_index: number;
    type: 'video_frame';
    video_id: string;
}

export interface AnnotationLabelDTO {
    id: string;
    probability: number;
    source: {
        user_id: string | null;
        model_id: string | null;
        model_storage_id: string | null;
    };
    hotkey?: string;
}

interface Point {
    x: number;
    y: number;
}

export enum SHAPE_TYPE_DTO {
    ROTATED_RECTANGLE = 'ROTATED_RECTANGLE',
    RECTANGLE = 'RECTANGLE',
    ELLIPSE = 'ELLIPSE',
    POLYGON = 'POLYGON',
    KEYPOINT = 'KEYPOINT',
}

export interface RectDTO {
    type: SHAPE_TYPE_DTO.RECTANGLE;
    x: number;
    y: number;
    height: number;
    width: number;
}

export interface PolygonDTO {
    type: SHAPE_TYPE_DTO.POLYGON;
    points: Point[];
}

export interface KeypointDTO {
    type: SHAPE_TYPE_DTO.KEYPOINT;
    x: number;
    y: number;
    is_visible: boolean;
}

export type ShapeDTO =
    | RectDTO
    | PolygonDTO
    | KeypointDTO
    | { type: SHAPE_TYPE_DTO.ROTATED_RECTANGLE; x: number; y: number; height: number; width: number; angle: number }
    | { type: SHAPE_TYPE_DTO.ELLIPSE; x: number; y: number; height: number; width: number };

export interface AnnotationDTO {
    id: string;
    labels: AnnotationLabelDTO[];
    shape: ShapeDTO;
    labels_to_revisit: string[];
    // TODO Currently this is optional, because in memory services are not using it yet
    // moreover we don't have a use case for this property yet, so it's skipped in the services
    modified?: string;
}

export type KeypointAnnotationDTO = AnnotationDTO & { shape: KeypointDTO };

export interface AnnotationResultDTO {
    id: number;
    kind: 'annotation';
    media_identifier: ImageIdDTO | VideoFrameIdDTO;
    modified: string;
    annotations: AnnotationDTO[];
    labels_to_revisit_full_scene: string[];
    annotation_state_per_task: AnnotationStatePerTaskDTO[];
}

interface VideoAnnotationDTO {
    annotations: AnnotationDTO[];
    labels_to_revisit_full_scene: string[];
    id: string;
    kind: 'annotation';
    media_identifier: VideoFrameIdDTO;
    modified: string;
}

export interface VideoAnnotationsDTO {
    video_annotations: VideoAnnotationDTO[];
    video_annotation_properties: {
        end_frame: number;
        requested_end_frame: number | null;
        requested_start_frame: number;
        start_frame: number;
        total_count: number;
        total_requested_count: number;
    };
}

interface RangeLabelDTO {
    start_frame: number;
    end_frame: number;
    label_ids: string[];
}
export interface RangeAnnotationDTO {
    video_id: string;
    range_labels: RangeLabelDTO[];
}

export interface RangeAnnotationResponseDTO extends RangeAnnotationDTO {
    id: string;
}
