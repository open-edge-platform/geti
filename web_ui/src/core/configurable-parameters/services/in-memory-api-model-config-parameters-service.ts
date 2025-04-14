// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersTaskChain } from '../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { ConfigurableParametersReconfigureDTO } from '../dtos/configurable-parameters.interface';
import { CreateApiModelConfigParametersService } from './api-model-config-parameters-service';
import { mockedConfigParamData, mockedReadOnlyConfigTaskChainData } from './test-utils';

export const createInMemoryApiModelConfigParametersService = (): CreateApiModelConfigParametersService => {
    const getModelConfigParameters = async (
        _projectIdentifier: ProjectIdentifier,
        _taskId: string,
        _modelId?: string,
        _modelTemplateId?: string,
        _editable?: boolean
    ): Promise<ConfigurableParametersTaskChain> => {
        return Promise.resolve(mockedReadOnlyConfigTaskChainData);
    };

    const getConfigParameters = async (
        _projectIdentifier: ProjectIdentifier
    ): Promise<ConfigurableParametersTaskChain[]> => {
        return Promise.resolve(mockedConfigParamData);
    };

    const reconfigureParameters = async (
        _projectIdentifier: ProjectIdentifier,
        _body: ConfigurableParametersReconfigureDTO
    ): Promise<void> => {
        return Promise.resolve();
    };

    return {
        getModelConfigParameters,
        getConfigParameters,
        reconfigureParameters,
    };
};
