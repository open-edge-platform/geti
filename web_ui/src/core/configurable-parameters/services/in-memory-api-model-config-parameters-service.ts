// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersTaskChain } from '../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { ConfigurableParametersReconfigureDTO } from '../dtos/configurable-parameters.interface';
import { CreateApiModelConfigParametersService } from './api-model-config-parameters-service';
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

    return {
        getModelConfigParameters,
        getConfigParameters,
        reconfigureParameters,
    };
};
