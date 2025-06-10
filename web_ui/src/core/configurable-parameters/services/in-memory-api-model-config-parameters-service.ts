// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ProjectIdentifier } from '../../projects/core.interface';
import { ConfigurableParametersReconfigureDTO } from '../dtos/configurable-parameters.interface';
import { CreateApiModelConfigParametersService } from './api-model-config-parameters-service';
import { ConfigurableParametersTaskChain } from './configurable-parameters.interface';
import { mockedConfigParamData, mockedReadOnlyConfigTaskChainData } from './test-utils';

export const createInMemoryApiModelConfigParametersService = (): CreateApiModelConfigParametersService => {
    const getModelConfigParameters: CreateApiModelConfigParametersService['getModelConfigParameters'] =
        async (): Promise<ConfigurableParametersTaskChain> => {
            return Promise.resolve(mockedReadOnlyConfigTaskChainData);
        };

    const getConfigParameters: CreateApiModelConfigParametersService['getConfigParameters'] = async (
        _projectIdentifier: ProjectIdentifier
    ): Promise<ConfigurableParametersTaskChain[]> => {
        return Promise.resolve(mockedConfigParamData);
    };

    const reconfigureParameters: CreateApiModelConfigParametersService['reconfigureParameters'] = async (
        _projectIdentifier: ProjectIdentifier,
        _body: ConfigurableParametersReconfigureDTO
    ): Promise<void> => {
        return Promise.resolve();
    };

    const getProjectConfiguration: CreateApiModelConfigParametersService['getProjectConfiguration'] = async () => {
        return Promise.resolve({
            taskConfigs: [],
        });
    };

    const getTrainingConfiguration: CreateApiModelConfigParametersService['getTrainingConfiguration'] = async () => {
        return Promise.resolve({
            taskId: 'task-id',
            training: [],
            datasetPreparation: {
                augmentation: {},
                filtering: {},
                subsetSplit: [],
            },
            evaluation: [],
        });
    };

    const updateProjectConfiguration: CreateApiModelConfigParametersService['updateProjectConfiguration'] =
        async () => {
            return Promise.resolve();
        };

    const updateTrainingConfiguration: CreateApiModelConfigParametersService['updateTrainingConfiguration'] =
        async () => {
            return Promise.resolve();
        };

    return {
        getModelConfigParameters,
        getConfigParameters,
        reconfigureParameters,
        getProjectConfiguration,
        getTrainingConfiguration,
        updateProjectConfiguration,
        updateTrainingConfiguration,
    };
};
