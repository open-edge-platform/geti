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
