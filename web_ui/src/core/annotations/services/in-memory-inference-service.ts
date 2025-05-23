// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AxiosInstance } from 'axios';

import { API_URLS } from '../../../../packages/core/src/services/urls';
import { Label } from '../../labels/label.interface';
import { MediaItem } from '../../media/media.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { DatasetIdentifier } from '../../projects/dataset.interface';
import { Annotation } from '../annotation.interface';
import { ShapeType } from '../shapetype.enum';
import { labelFromModel } from '../utils';
import { ExplanationResult, InferenceResult, InferenceService } from './inference-service.interface';
import { PredictionMode } from './prediction-service.interface';
import { VideoPaginationOptions } from './video-pagination-options.interface';

interface CreateApiService<Type> {
    (arg?: { instance: AxiosInstance; router: typeof API_URLS }): Type;
}

export const createInMemoryInferenceService: CreateApiService<InferenceService> = () => {
    const getTestPredictions = async (
        _projectIdentifier: ProjectIdentifier,
        labels: Label[],
        _testId: string,
        _predictionId: string
    ) => {
        return [
            {
                id: 'rect-1',
                labels: [
                    labelFromModel(labels[1], 0.1, '123', '321'),
                    labelFromModel(labels[0], 0.4, '123', '321'),
                    labelFromModel(labels[10], 0.7, '123', '321'),
                    labelFromModel(labels[12], 0.9, '123', '321'),
                ],
                shape: { shapeType: ShapeType.Rect as const, x: 500, y: 100, width: 200, height: 200 },
                zIndex: 0,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
        ];
    };

    const getPredictions = async (
        _datasetIdentifier: DatasetIdentifier,
        labels: Label[],
        _mediaItem: MediaItem
    ): Promise<InferenceResult> => {
        return [
            {
                id: 'rect-1',
                labels: [
                    labelFromModel(labels[1], 0.1, '123', '321'),
                    labelFromModel(labels[0], 0.4, '123', '321'),
                    labelFromModel(labels[10], 0.7, '123', '321'),
                    labelFromModel(labels[12], 0.9, '123', '321'),
                ],
                shape: { shapeType: ShapeType.Rect as const, x: 500, y: 100, width: 200, height: 200 },
                zIndex: 0,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
            {
                id: 'rect-2',
                labels: [labelFromModel(labels[1], 0.3, '123', '321')],
                shape: { shapeType: ShapeType.Rect as const, x: 110, y: 310, width: 100, height: 200 },
                zIndex: 1,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
            {
                id: 'circle-1',
                labels: [labelFromModel(labels[2], 0.9, '123', '321')],
                shape: { shapeType: ShapeType.Circle as const, x: 200, y: 150, r: 100 },
                zIndex: 2,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
            {
                id: 'polygon-1',
                labels: [labelFromModel(labels[3], 0.1, '123', '321')],
                shape: {
                    shapeType: ShapeType.Polygon as const,
                    points: [
                        { x: 550, y: 300 },
                        { x: 550, y: 450 },
                        { x: 750, y: 540 },
                    ],
                },
                zIndex: 3,
                isSelected: false,
                isHidden: false,
                isLocked: false,
            },
        ];
    };

    const getVideoPredictions = async (
        _datasetIdentifier: DatasetIdentifier,
        _projectLabels: Label[],
        _mediaItemId: MediaItem,
        _mode: PredictionMode,
        _options?: VideoPaginationOptions
    ): Promise<Record<number, Annotation[]>> => {
        return [];
    };
    const getVideoPredictionsStream = async (
        _datasetIdentifier: DatasetIdentifier,
        _projectLabels: Label[],
        _mediaItemId: MediaItem,
        _mode: PredictionMode,
        _options?: VideoPaginationOptions
    ): Promise<Record<number, Annotation[]>> => {
        return [];
    };

    const getPredictionsForFile = async (
        _projectIdentifier: ProjectIdentifier,
        _projectLabels: Label[],
        _imageFile: File
    ): Promise<InferenceResult> => {
        return [];
    };
    const getExplanations = async (
        _projectIdentifier: ProjectIdentifier,
        _mediaItem: MediaItem
    ): Promise<ExplanationResult> => {
        return [];
    };
    const getExplanationsForFile = async (
        _projectIdentifier: ProjectIdentifier,
        _imageFile: File
    ): Promise<ExplanationResult> => {
        return [];
    };

    const getInferenceServerStatus = async (_projectIdentifier: ProjectIdentifier) => {
        return { isInferenceServerReady: true };
    };

    return {
        getPredictions,
        getTestPredictions,
        getVideoPredictions,
        getVideoPredictionsStream,
        getPredictionsForFile,
        getExplanations,
        getExplanationsForFile,
        getInferenceServerStatus,
    };
};
