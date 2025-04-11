// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ModelFormat } from '../../../../../core/models/dtos/model-details.interface';
import { TrainedModel } from '../../../../../core/models/optimized-models.interface';
import { getMockedOptimizedModel } from '../../../../../test-utils/mocked-items-factory/mocked-model';
import { isOptimizationType, isOptimizedModel, isOptimizedModelNoReady } from './utils';

const mockedModel = getMockedOptimizedModel({
    modelName: 'ATSS OpenVINO',
    modelStatus: 'SUCCESS',
    modelFormat: ModelFormat.OpenVINO,
});

const { hasExplainableAI, optimizationType, ...model } = mockedModel;
const mockedTrainedModel: TrainedModel = {
    ...model,
    isLabelSchemaUpToDate: false,
    numberOfFrames: 1,
    numberOfImages: 1,
    numberOfSamples: 1,
    architecture: '123',
    totalDiskSize: '10 MB',
};

describe('model-variants utils', () => {
    it('isOptimizedModel', () => {
        expect(isOptimizedModel(mockedModel)).toBe(true);
        expect(isOptimizedModel(mockedTrainedModel)).toBe(false);
    });

    it('isOptimizedModelNoReady', () => {
        expect(isOptimizedModelNoReady(mockedModel)).toBe(false);
        expect(isOptimizedModelNoReady({ ...mockedModel, modelStatus: 'FAILED' })).toBe(true);
    });

    it('isOptimizationType', () => {
        expect(isOptimizationType(mockedModel, 'MO')).toBe(true);
        expect(isOptimizationType(mockedModel, 'POT')).toBe(false);
    });
});
