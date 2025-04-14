// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
