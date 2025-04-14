// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ModelsGroups } from '../../core/models/models.interface';
import { ModelDetails } from '../../core/models/optimized-models.interface';
import {
    AvailableOptimizationTypes,
    getAvailableOptimizationTypes,
    getMatchedMediaCounts,
    getModels,
    getOptimizationTypes,
    getTaskModels,
    getTotalMediaCounts,
    isModelDeleted,
} from './utils';

describe('project-details utils', () => {
    describe('getAvailableOptimizationTypes', () => {
        const optimizationTypes: AvailableOptimizationTypes = {
            id: 'model-id',
            modelName: 'modelName-test',
            optimizationType: 'POT',
        };

        it('no models', () => {
            expect(getAvailableOptimizationTypes(undefined)).toEqual([]);
        });

        it('optimizationTypes', () => {
            expect(getAvailableOptimizationTypes([optimizationTypes])).toEqual([
                { id: optimizationTypes.id, text: '' },
            ]);
        });

        it('optimizationTypes ONNX and PYTORCH', () => {
            expect(getAvailableOptimizationTypes([{ ...optimizationTypes, optimizationType: 'ONNX' }])).toEqual([]);
            expect(getAvailableOptimizationTypes([{ ...optimizationTypes, optimizationType: 'PYTORCH' }])).toEqual([]);
        });
    });

    describe('getOptimizationTypes', () => {
        const potModel = {
            id: 'id-test',
            modelName: 'POT-model',
            optimizationType: 'POT',
            modelStatus: 'SUCCESS',
        };

        it('empty model details', () => {
            expect(getOptimizationTypes(undefined)).toEqual([]);
        });

        it('"SUCCESS" optimized model', () => {
            const model = {
                optimizedModels: [potModel],
            } as unknown as ModelDetails;

            expect(getOptimizationTypes(model)).toEqual([
                {
                    id: potModel.id,
                    optimizationType: potModel.optimizationType,
                    modelName: potModel.modelName,
                },
            ]);
        });

        it('"NOT_READY" optimized model', () => {
            const model = {
                optimizedModels: [{ ...potModel, modelStatus: 'NOT_READY' }],
            } as unknown as ModelDetails;

            expect(getOptimizationTypes(model)).toEqual([]);
        });

        it('PYTORCH is not supported', () => {
            const model = {
                optimizedModels: [{ ...potModel, modelStatus: 'NOT_READY' }],
                trainedModel: {
                    id: 'pytorch-id',
                    architecture: 'pytorch-achitecture',
                    optimizationType: 'PYTORCH',
                    precision: ['123'],
                },
            } as unknown as ModelDetails;

            expect(getOptimizationTypes(model)).toEqual([]);
        });
    });

    describe('getModels', () => {
        const taskId = '123';
        const modelsGroups = { taskId } as ModelsGroups;
        const preselectedModel = {
            groupName: 'groupName-test',
            groupId: 'groupId-test',
            templateName: 'templateName-test',
            version: 2,
            id: 'modelId-test',
            taskId: 'taskId-test',
        };

        it('get models group', () => {
            expect(getModels(undefined, [modelsGroups], taskId)).toEqual([modelsGroups]);
        });

        it('preselected model', () => {
            expect(getModels(preselectedModel, [modelsGroups], taskId)).toEqual([
                {
                    groupId: preselectedModel.groupId,
                    groupName: preselectedModel.groupName,
                    modelTemplateName: preselectedModel.templateName,
                    modelVersions: [
                        {
                            id: preselectedModel.id,
                            version: preselectedModel.version,
                        },
                    ],
                    taskId: preselectedModel.taskId,
                },
            ]);
        });
    });

    describe('getTaskModels', () => {
        it('empty tasks models', () => {
            expect(getTaskModels([])).toEqual([]);
            expect(getTaskModels(undefined)).toEqual([]);
        });

        it('tasks models', () => {
            const taskId = '123';
            const modelsGroups = { taskId } as ModelsGroups;

            expect(getTaskModels([modelsGroups], '321')).toEqual([]);
            expect(getTaskModels([modelsGroups], taskId)).toEqual([modelsGroups]);
        });
    });

    describe('getMatchedMediaCounts', () => {
        it('image and video', () => {
            expect(getMatchedMediaCounts(1, 1, 1)).toBe('1 image, 1 frame from 1 video');
        });

        it('images and videos', () => {
            expect(getMatchedMediaCounts(2, 2, 2)).toBe('2 images, 2 frames from 2 videos');
        });
    });

    describe('getTotalMediaCounts', () => {
        it('image', () => {
            expect(getTotalMediaCounts(1, 0)).toBe('1 image');
        });

        it('images', () => {
            expect(getTotalMediaCounts(10, 0)).toBe('10 images');
        });

        it('image and video', () => {
            expect(getTotalMediaCounts(1, 1)).toBe('1 image, 1 video');
        });

        it('images and videos', () => {
            expect(getTotalMediaCounts(10, 5)).toBe('10 images, 5 videos');
        });
    });

    describe('getMediaCounts', () => {
        it('images', () => {
            expect(getMatchedMediaCounts(1, 0, 0)).toContain('image,');
            expect(getMatchedMediaCounts(0, 0, 0)).toContain('images,');
            expect(getMatchedMediaCounts(10, 0, 0)).toContain('images,');
        });

        it('frames', () => {
            expect(getMatchedMediaCounts(0, 1, 0)).toContain('frame ');
            expect(getMatchedMediaCounts(0, 0, 0)).toContain('frames ');
            expect(getMatchedMediaCounts(0, 10, 0)).toContain('frames ');
        });

        it('videos', () => {
            expect(getMatchedMediaCounts(0, 0, 1)).toContain('video');
            expect(getMatchedMediaCounts(0, 0, 0)).toContain('videos');
            expect(getMatchedMediaCounts(0, 0, 10)).toContain('videos');
        });

        it('full text', () => {
            expect(getMatchedMediaCounts(2, 2, 1)).toBe('2 images, 2 frames from 1 video');
        });
    });

    it('isModelDeleted', () => {
        expect(isModelDeleted({})).toBe(false);
        expect(isModelDeleted({ purgeInfo: { isPurged: true } })).toBe(true);
        expect(isModelDeleted({ purgeInfo: { isPurged: false } })).toBe(false);
    });
});
