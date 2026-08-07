// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { API_BASE_URL } from '@/api';
import type { Model, ModelVariant } from '@/api/types';

const TRAINING_STATUS = {
    Failed: 'failed',
    InProgress: 'in_progress',
    Successful: 'successful',
} as const;

export const isFailedModel = (model: Pick<Model, 'training_info'>): boolean =>
    model.training_info?.status === TRAINING_STATUS.Failed;

export const isTrainingModel = (model: Pick<Model, 'training_info'>): boolean =>
    model.training_info?.status === TRAINING_STATUS.InProgress;

export const isSuccessfulModel = (model: Pick<Model, 'training_info'>): boolean =>
    model.training_info?.status === TRAINING_STATUS.Successful;

export const hasDeletedWeights = (model: Pick<Model, 'files_deleted'>): boolean => model.files_deleted;

export const getModelVariantBinaryUrl = (projectId: string, modelId: string, variantId: string): string =>
    `${API_BASE_URL}/api/projects/${projectId}/models/${modelId}/variants/${variantId}/binary`;

// Mirrors the Content-Disposition filename set by the backend for the endpoint above. The desktop app
// needs it up front to open the save dialog before the (potentially large) download starts.
export const getModelVariantBinaryFilename = (
    modelId: string,
    variant: Pick<ModelVariant, 'format' | 'precision'>
): string => `model-${modelId.split('-')[0]}-${variant.format}-${variant.precision}.zip`;
