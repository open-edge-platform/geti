// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Label } from '../../labels/label.interface';
import { MEDIA_TYPE } from '../../media/base-media.interface';
import { MediaItem } from '../../media/media.interface';
import { Video } from '../../media/video.interface';
import { DatasetIdentifier } from '../../projects/dataset.interface';
import { AnnotationResultDTO } from '../dtos/annotation.interface';
import { LabeledVideoRange } from '../labeled-video-range.interface';
import { ShapeType } from '../shapetype.enum';
import { labelFromUser } from '../utils';
import { Annotation } from './../annotation.interface';
import { AnnotationService } from './annotation-service.interface';

export const createInMemoryAnnotationService = (): AnnotationService => {
    const getAnnotations = async (
        _datasetIdentifier: DatasetIdentifier,
        labels: Label[],
        _mediaItem: MediaItem,
        _annotationId = 'latest'
    ): Promise<Annotation[]> => {
        const annotations: Annotation[] = [
            {
                id: 'rect-1',
                labels: [labelFromUser(labels[0])],
                shape: { shapeType: ShapeType.Rect as const, x: 10, y: 10, width: 300, height: 300 },
                zIndex: 0,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
            {
                id: 'rect-2',
                labels: [labelFromUser(labels[1])],
                shape: { shapeType: ShapeType.Rect as const, x: 410, y: 410, width: 300, height: 300 },
                zIndex: 1,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
            {
                id: 'circle-1',
                labels: [labelFromUser(labels[2])],
                shape: { shapeType: ShapeType.Circle as const, x: 500, y: 100, r: 100 },
                zIndex: 2,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
            {
                id: 'polygon-1',
                labels: [labelFromUser(labels[3])],
                shape: {
                    shapeType: ShapeType.Polygon as const,
                    points: [
                        { x: 50, y: 300 },
                        { x: 150, y: 450 },
                        { x: 250, y: 340 },
                    ],
                },
                zIndex: 3,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
        ];

        return [...annotations];
    };

    const getVideoAnnotations = async (
        _datasetIdentifier: DatasetIdentifier,
        _projectLabels: Label[],
        _mediaItem: Video
    ) => {
        return {};
    };

    const saveAnnotations = async (
        _datasetIdentifier: DatasetIdentifier,
        _mediaItem: MediaItem,
        _annotations: ReadonlyArray<Annotation>
    ): Promise<AnnotationResultDTO> => {
        return {
            annotations: [],
            id: 12312321,
            kind: 'annotation',
            media_identifier: {
                image_id: '60b609fbd036ba4566726c96',
                type: MEDIA_TYPE.IMAGE,
            },
            modified: '2021-06-03T13:09:18.096000+00:00',
            labels_to_revisit_full_scene: [],
            annotation_state_per_task: [],
        };
    };

    const getLabeledVideoRanges = async (
        _datasetIdentifier: DatasetIdentifier,
        _mediaItem: Video,
        _projectLabels: Label[]
    ): Promise<LabeledVideoRange[]> => {
        return [];
    };
    const saveLabeledVideoRanges = async (
        _datasetIdentifier: DatasetIdentifier,
        _mediaItem: Video,
        _ranges: LabeledVideoRange[]
    ): Promise<void> => {
        return;
    };

    return {
        getAnnotations,
        getVideoAnnotations,
        saveAnnotations,
        getLabeledVideoRanges,
        saveLabeledVideoRanges,
    };
};
