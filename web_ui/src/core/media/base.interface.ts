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
