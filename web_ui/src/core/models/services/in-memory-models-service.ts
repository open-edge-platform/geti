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

import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { ProjectIdentifier } from '../../projects/core.interface';
import { WorkspaceIdentifier } from '../../workspaces/services/workspaces.interface';
import { TrainingBodyDTO } from '../dtos/train-model.interface';
import { ModelGroupIdentifier, ModelIdentifier, ModelsGroups } from '../models.interface';
import { ModelDetails } from '../optimized-models.interface';
import { ModelsService } from './models.interface';
import { mockedArchitectureModels, mockedOptimizedModels, mockedTrainedModel } from './test-utils';

export const createInMemoryModelsService = (): ModelsService => {
    const getModels = async (_workspaceIdentifier: WorkspaceIdentifier): Promise<ModelsGroups[]> =>
        Promise.resolve(mockedArchitectureModels);

    const getModel = async (_modelIdentifier: ModelIdentifier): Promise<ModelDetails> => {
        return Promise.resolve({
            trainedModel: mockedTrainedModel,
            optimizedModels: mockedOptimizedModels,
            totalDiskSize: '10MB',
            labels: [getMockedLabel({ name: 'label-1', id: 'label-1' })],
            trainingDatasetInfo: {
                revisionId: '60d31793d5f1fb7e6e3c1a50',
                storageId: '637f75740a130d746ce55483',
            },
        });
    };

    const getModelsByArchitecture = async (_modelGroupIdentifier: ModelGroupIdentifier): Promise<ModelsGroups> => {
        return Promise.resolve(mockedArchitectureModels[0]);
    };

    const trainModel = async (_projectIdentifier: ProjectIdentifier, _body: TrainingBodyDTO): Promise<void> => {
        await Promise.resolve();
    };

    const optimizeModel = async (_modelIdentifier: ModelIdentifier): Promise<void> => {
        await Promise.resolve();
    };

    const activateModel = async (_modelGroupIdentifier: ModelGroupIdentifier): Promise<void> => {
        await Promise.resolve();
    };

    const archiveModel = async (_modelIdentifier: ModelIdentifier): Promise<void> => {
        await Promise.resolve();
    };

    return { getModels, getModel, getModelsByArchitecture, trainModel, optimizeModel, activateModel, archiveModel };
};
