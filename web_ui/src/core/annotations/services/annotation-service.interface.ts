// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
