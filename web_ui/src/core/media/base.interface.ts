// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MEDIA_TYPE } from './base-media.interface';

export enum MEDIA_ANNOTATION_STATUS {
    NONE = 'none',
    ANNOTATED = 'annotated',
    PARTIALLY_ANNOTATED = 'partially_annotated',
    TO_REVISIT = 'to_revisit',
}

export interface AnnotationStatePerTask {
    taskId: string;
    state: MEDIA_ANNOTATION_STATUS;
}

export interface BaseIdentifier {
    type: MEDIA_TYPE;
}

export interface BaseMetadata {
    width: number;
    height: number;
    size: number;
}

export interface BaseMediaItem {
    identifier: BaseIdentifier;
    name: string;
    src: string;
    thumbnailSrc: string;
    status?: MEDIA_ANNOTATION_STATUS;
    metadata: BaseMetadata;
    annotationStatePerTask?: AnnotationStatePerTask[];
    annotationSceneId?: string;
    uploadTime: string;
    uploaderId: string;
    lastAnnotatorId: string | null;
}
