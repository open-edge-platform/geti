// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OptimizedModel, TrainedModel } from '../../../../../core/models/optimized-models.interface';

export const STARTED_OPTIMIZATION = 'Optimization job has been created.';

export enum ModelTableColumnKeys {
    MODEL_NAME = 'modelName',
    PRECISION = 'precision',
    ACCURACY = 'accuracy',
    MODEL_SIZE = 'modelSize',
    LICENSE = 'license',
    MENU = '',
}

export const isOptimizedModel = (row: OptimizedModel | TrainedModel): row is OptimizedModel =>
    'optimizationType' in row;

export const isOptimizedModelNoReady = (row: OptimizedModel | TrainedModel) =>
    isOptimizedModel(row) && row.modelStatus !== 'SUCCESS';

export const isOptimizationType = (row: OptimizedModel | TrainedModel, name: string): row is OptimizedModel =>
    isOptimizedModel(row) && row.optimizationType === name;
