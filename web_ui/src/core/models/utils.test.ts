// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    getMockedModelsGroup,
    getMockedModelsGroupAlgorithmDetails,
    getMockedModelVersion,
} from '../../test-utils/mocked-items-factory/mocked-model';
import { PerformanceType } from '../projects/task.interface';
import { SortDirection } from '../shared/query-parameters';
import {
    hasActiveModels,
    sortModelsByCreationTime,
    sortModelsGroupsByActiveModel,
    sortModelsGroupsByComplexity,
    sortModelsGroupsByCreationTime,
    sortModelsGroupsByModelSize,
    sortModelsGroupsByScore,
} from './utils';

const mockedActiveModelsGroup = getMockedModelsGroup({});
const mockedModelsGroup = getMockedModelsGroup({ modelVersions: [getMockedModelVersion({ isActiveModel: false })] });

describe('models utils', () => {
    it('hasActiveModels', () => {
        expect(hasActiveModels(mockedModelsGroup)).toEqual(false);
        expect(hasActiveModels(mockedActiveModelsGroup)).toEqual(true);
    });
});

describe('sortModelGroupsByActiveModel', () => {
    const groupWithActiveModel = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [
            getMockedModelVersion({ isActiveModel: true, version: 2, id: '2' }),
            getMockedModelVersion({ isActiveModel: false, version: 1, id: '1' }),
        ],
    });
    const groupWithInactiveModel = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [getMockedModelVersion({ isActiveModel: false, version: 1, id: '12' })],
    });

    it('model group that contains active model should be at the top', () => {
        expect(
            sortModelsGroupsByActiveModel([groupWithInactiveModel, groupWithActiveModel], SortDirection.ASC)
        ).toEqual([groupWithActiveModel, groupWithInactiveModel]);
        expect(
            sortModelsGroupsByActiveModel([groupWithActiveModel, groupWithInactiveModel], SortDirection.ASC)
        ).toEqual([groupWithActiveModel, groupWithInactiveModel]);
    });

    it('does not change the order of model groups across different tasks', () => {
        const taskOneActiveModel = getMockedModelsGroupAlgorithmDetails({
            taskId: '1',
            modelVersions: [
                getMockedModelVersion({ isActiveModel: true, version: 2, id: '2' }),
                getMockedModelVersion({ isActiveModel: false, version: 1, id: '1' }),
            ],
        });
        const taskOneInactiveModel = getMockedModelsGroupAlgorithmDetails({
            taskId: '1',
            modelVersions: [
                getMockedModelVersion({ isActiveModel: false, version: 2, id: '12' }),
                getMockedModelVersion({ isActiveModel: false, version: 1, id: '11' }),
            ],
        });
        const taskTwoActiveModel = getMockedModelsGroupAlgorithmDetails({
            taskId: '2',
            modelVersions: [getMockedModelVersion({ isActiveModel: true, id: '111', version: 1 })],
        });

        expect(
            sortModelsGroupsByActiveModel(
                [taskOneInactiveModel, taskOneActiveModel, taskTwoActiveModel],
                SortDirection.ASC
            )
        ).toEqual([taskOneActiveModel, taskOneInactiveModel, taskTwoActiveModel]);
    });
});

describe('sortModelsByCreationTime', () => {
    const modelA = getMockedModelVersion({ creationDate: '2025-03-31' });
    const modelB = getMockedModelVersion({ creationDate: '2025-04-01' });
    const modelC = getMockedModelVersion({ creationDate: '2025-04-05' });
    const modelD = getMockedModelVersion({ creationDate: '2025-04-05' });

    it('sorts by creation date in ascending order', () => {
        expect(sortModelsByCreationTime([modelD, modelA, modelC, modelB], SortDirection.ASC)).toEqual([
            modelA,
            modelB,
            modelD,
            modelC,
        ]);
    });

    it('sorts by creation date in descending order', () => {
        expect(sortModelsByCreationTime([modelD, modelA, modelC, modelB], SortDirection.DESC)).toEqual([
            modelD,
            modelC,
            modelB,
            modelA,
        ]);
    });
});

describe('sortModelsGroupsByCreationTime', () => {
    const modelAA = getMockedModelVersion({ creationDate: '2025-03-31' });
    const modelAB = getMockedModelVersion({ creationDate: '2025-04-01' });
    const groupA = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [modelAA, modelAB],
    });

    const modelBA = getMockedModelVersion({ creationDate: '2025-06-05' });
    const modelBB = getMockedModelVersion({ creationDate: '2025-06-06' });
    const groupB = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [modelBA, modelBB],
    });

    it('sorts by creation date in ascending order', () => {
        expect(sortModelsGroupsByCreationTime([groupB, groupA], SortDirection.ASC)).toEqual([groupA, groupB]);
    });

    it('sorts by creation date in descending order', () => {
        expect(sortModelsGroupsByCreationTime([groupB, groupA], SortDirection.DESC)).toEqual([
            { ...groupB, modelVersions: [modelBB, modelBA] },
            { ...groupA, modelVersions: [modelAB, modelAA] },
        ]);
    });
});

describe('sortModelsGroupsByActiveModel', () => {
    const groupA = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [
            getMockedModelVersion({ isActiveModel: true, version: 2, id: '2' }),
            getMockedModelVersion({ isActiveModel: false, version: 1, id: '1' }),
        ],
    });
    const groupB = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [getMockedModelVersion({ isActiveModel: false, version: 1, id: '12' })],
    });

    it('model group that contains active model should be at the top', () => {
        expect(sortModelsGroupsByActiveModel([groupB, groupA], SortDirection.ASC)).toEqual([groupA, groupB]);
        expect(sortModelsGroupsByActiveModel([groupB, groupA], SortDirection.DESC)).toEqual([groupB, groupA]);
    });

    it('does not change the order of model groups across different tasks', () => {
        const taskOneActiveModel = getMockedModelsGroupAlgorithmDetails({
            taskId: '1',
            modelVersions: [
                getMockedModelVersion({ isActiveModel: true, version: 2, id: '2' }),
                getMockedModelVersion({ isActiveModel: false, version: 1, id: '1' }),
            ],
        });
        const taskOneInactiveModel = getMockedModelsGroupAlgorithmDetails({
            taskId: '1',
            modelVersions: [
                getMockedModelVersion({ isActiveModel: false, version: 2, id: '12' }),
                getMockedModelVersion({ isActiveModel: false, version: 1, id: '11' }),
            ],
        });
        const taskTwoActiveModel = getMockedModelsGroupAlgorithmDetails({
            taskId: '2',
            modelVersions: [getMockedModelVersion({ isActiveModel: true, id: '111', version: 2 })],
        });
        const taskTwoInactiveModel = getMockedModelsGroupAlgorithmDetails({
            taskId: '2',
            modelVersions: [getMockedModelVersion({ isActiveModel: false, id: '112', version: 1 })],
        });

        expect(
            sortModelsGroupsByActiveModel(
                [taskOneInactiveModel, taskOneActiveModel, taskTwoInactiveModel, taskTwoActiveModel],
                SortDirection.ASC
            )
        ).toEqual([taskOneActiveModel, taskOneInactiveModel, taskTwoActiveModel, taskTwoInactiveModel]);
    });
});

describe('sortModelsGroupsByScore', () => {
    const modelAA = getMockedModelVersion({ performance: { type: PerformanceType.DEFAULT, score: 0.6 } });
    const modelAB = getMockedModelVersion({ performance: { type: PerformanceType.DEFAULT, score: 0.9 } });
    const groupA = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [modelAA, modelAB],
    });
    const modelBA = getMockedModelVersion({ performance: { type: PerformanceType.DEFAULT, score: 0.6 } });
    const modelBB = getMockedModelVersion({ performance: { type: PerformanceType.DEFAULT, score: 0.7 } });
    const modelBC = getMockedModelVersion({ performance: { type: PerformanceType.DEFAULT, score: 0.3 } });
    const groupB = getMockedModelsGroupAlgorithmDetails({ modelVersions: [modelBA, modelBB, modelBC] });

    it('sorts by score in ascending order', () => {
        expect(sortModelsGroupsByScore([groupA, groupB], SortDirection.ASC)).toEqual([
            { ...groupB, modelVersions: [modelBC, modelBA, modelBB] },
            groupA,
        ]);
    });

    it('sorts by score in descending order', () => {
        expect(sortModelsGroupsByScore([groupA, groupB], SortDirection.DESC)).toEqual([
            { ...groupA, modelVersions: [modelAB, modelAA] },
            { ...groupB, modelVersions: [modelBB, modelBA, modelBC] },
        ]);
    });
});

describe('sortModelsGroupsByComplexity', () => {
    const modelAA = getMockedModelVersion({ id: '1' });
    const modelAB = getMockedModelVersion({ id: '2' });
    const groupA = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [modelAA, modelAB],
        complexity: 100,
    });
    const modelBA = getMockedModelVersion({ id: '11' });
    const modelBB = getMockedModelVersion({ id: '12' });
    const modelBC = getMockedModelVersion({ id: '13' });
    const groupB = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [modelBA, modelBB, modelBC],
        complexity: 200,
    });

    it('sorts by complexity in ascending order', () => {
        expect(sortModelsGroupsByComplexity([groupA, groupB], SortDirection.ASC)).toEqual([groupA, groupB]);
    });

    it('sorts by complexity in descending order', () => {
        expect(sortModelsGroupsByComplexity([groupA, groupB], SortDirection.DESC)).toEqual([groupB, groupA]);
    });
});

describe('sortModelsGroupsByModelSize', () => {
    const modelAA = getMockedModelVersion({ modelSize: 100 });
    const modelAB = getMockedModelVersion({ modelSize: 200 });
    const groupA = getMockedModelsGroupAlgorithmDetails({
        modelVersions: [modelAA, modelAB],
    });
    const modelBA = getMockedModelVersion({ modelSize: 150 });
    const modelBB = getMockedModelVersion({ modelSize: 250 });
    const modelBC = getMockedModelVersion({ modelSize: 300 });
    const groupB = getMockedModelsGroupAlgorithmDetails({ modelVersions: [modelBA, modelBB, modelBC] });

    it('sorts by model size in ascending order', () => {
        expect(sortModelsGroupsByModelSize([groupA, groupB], SortDirection.ASC)).toEqual([groupA, groupB]);
    });

    it('sorts by model size in descending order', () => {
        expect(sortModelsGroupsByModelSize([groupA, groupB], SortDirection.DESC)).toEqual([
            { ...groupB, modelVersions: [modelBC, modelBB, modelBA] },
            { ...groupA, modelVersions: [modelAB, modelAA] },
        ]);
    });
});
