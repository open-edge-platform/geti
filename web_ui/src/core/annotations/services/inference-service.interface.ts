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
