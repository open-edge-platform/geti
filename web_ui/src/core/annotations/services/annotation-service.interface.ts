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

import { Label } from '../../labels/label.interface';
import { MediaItem } from '../../media/media.interface';
import { Video } from '../../media/video.interface';
import { DatasetIdentifier } from '../../projects/dataset.interface';
import { Annotation } from '../annotation.interface';
import { AnnotationResultDTO } from '../dtos/annotation.interface';
import { LabeledVideoRange } from '../labeled-video-range.interface';
import { VideoPaginationOptions } from './video-pagination-options.interface';

export interface AnnotationService {
    getAnnotations(
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItem: MediaItem,
        annotationId?: 'latest' | string
    ): Promise<Annotation[]>;

    getVideoAnnotations(
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItem: Video,
        options?: VideoPaginationOptions
    ): Promise<Record<number, Annotation[]>>;

    getLabeledVideoRanges(
        datasetIdentifier: DatasetIdentifier,
        mediaItem: Video,
        projectLabels: Label[]
    ): Promise<LabeledVideoRange[]>;
    saveLabeledVideoRanges(
        datasetIdentifier: DatasetIdentifier,
        mediaItem: Video,
        ranges: LabeledVideoRange[]
    ): Promise<void>;

    saveAnnotations(
        datasetIdentifier: DatasetIdentifier,
        mediaItem: MediaItem,
        annotations: ReadonlyArray<Annotation>
    ): Promise<AnnotationResultDTO>;
}
