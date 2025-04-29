// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Label } from '../../labels/label.interface';
import { MediaItem } from '../../media/media.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { DatasetIdentifier } from '../../projects/dataset.interface';
import { Annotation, TaskChainInput } from '../annotation.interface';
import { Explanation } from '../prediction.interface';
import { InferenceServerStatusResult, PredictionCache, PredictionMode } from './prediction-service.interface';
import { VideoPaginationOptions } from './video-pagination-options.interface';

export type InferenceResult = ReadonlyArray<Annotation>;
export type ExplanationResult = Explanation[];

export interface InferenceService {
    getTestPredictions: (
        projectIdentifier: ProjectIdentifier,
        labels: Label[],
        testId: string,
        predictionId: string
    ) => Promise<InferenceResult>;
    getPredictions(
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItemId: MediaItem,
        predictionCache: PredictionCache,
        taskId?: string,
        selectedInput?: TaskChainInput,
        abortSignal?: AbortSignal
    ): Promise<InferenceResult>;
    getVideoPredictions(
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItemId: MediaItem,
        mode: PredictionMode,
        options?: VideoPaginationOptions,
        abortSignal?: AbortSignal
    ): Promise<Record<number, Annotation[]>>;
    getVideoPredictionsStream(
        datasetIdentifier: DatasetIdentifier,
        projectLabels: Label[],
        mediaItemId: MediaItem,
        mode: PredictionMode,
        options?: VideoPaginationOptions
    ): Promise<Record<number, Annotation[]>>;
    getPredictionsForFile(
        projectIdentifier: ProjectIdentifier,
        projectLabels: Label[],
        imageFile: File
    ): Promise<InferenceResult>;
    getExplanations(
        projectIdentifier: ProjectIdentifier,
        mediaItemId: MediaItem,
        taskId?: string,
        selectedInput?: TaskChainInput,
        abortSignal?: AbortSignal
    ): Promise<ExplanationResult>;
    getExplanationsForFile(projectIdentifier: ProjectIdentifier, imageFile: File): Promise<ExplanationResult>;
    getInferenceServerStatus: (
        projectIdentifier: ProjectIdentifier,
        taskId: string | undefined
    ) => Promise<InferenceServerStatusResult>;
}
