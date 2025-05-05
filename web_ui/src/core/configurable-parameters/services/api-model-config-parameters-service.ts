// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersTaskChain } from '../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { ProjectIdentifier } from '../../projects/core.interface';
import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import {
    ConfigurableParametersDTO,
    ConfigurableParametersReconfigureDTO,
    ConfigurableParametersTaskChainDTO,
} from '../dtos/configurable-parameters.interface';
import { ProjectConfigurationDTO } from '../dtos/configuration.interface';
import { ProjectConfiguration } from './configuration.interface';
import { getConfigParametersEntity, getModelConfigEntity, getProjectConfigurationEntity } from './utils';

export interface CreateApiModelConfigParametersService {
    /**
     * @deprecated Please use getTrainingConfiguration instead
     */
    getModelConfigParameters: (
        projectIdentifier: ProjectIdentifier,
        taskId: string,
        modelId?: string,
        modelTemplateId?: string | null,
        editable?: boolean
    ) => Promise<ConfigurableParametersTaskChain>;

    /**
     * @deprecated Please use getTrainingConfiguration instead
     */
    getConfigParameters: (projectIdentifier: ProjectIdentifier) => Promise<ConfigurableParametersTaskChain[]>;

    reconfigureParameters: (
        projectIdentifier: ProjectIdentifier,
        body: ConfigurableParametersReconfigureDTO
    ) => Promise<void>;
}

export const createApiModelConfigParametersService: CreateApiService<CreateApiModelConfigParametersService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
) => {
    const getModelConfigParameters = async (
        projectIdentifier: ProjectIdentifier,
        taskId: string,
        modelId?: string,
        modelTemplateId?: string | null,
        editable?: boolean
    ): Promise<ConfigurableParametersTaskChain> => {
        const { data } = await instance.get<ConfigurableParametersTaskChainDTO>(
            router.MODEL_CONFIG_PARAMETERS(projectIdentifier, taskId, modelId, modelTemplateId)
        );

        return getModelConfigEntity(data, editable);
    };

    const getConfigParameters = async (
        projectIdentifier: ProjectIdentifier
    ): Promise<ConfigurableParametersTaskChain[]> => {
        const { data } = await instance.get<ConfigurableParametersDTO>(
            router.CONFIGURATION_PARAMETERS(projectIdentifier)
        );

        return getConfigParametersEntity(data);
    };

    const reconfigureParameters = async (
        projectIdentifier: ProjectIdentifier,
        body: ConfigurableParametersReconfigureDTO
    ) => {
        await instance.post(router.CONFIGURATION_PARAMETERS(projectIdentifier), body);
    };

    const getProjectConfiguration = async (projectIdentifier: ProjectIdentifier): Promise<ProjectConfiguration> => {
        const { data } = await instance.get<ProjectConfigurationDTO>(router.CONFIGURATION.PROJECT(projectIdentifier));

        return getProjectConfigurationEntity(data);
    };

    return {
        getModelConfigParameters,
        getConfigParameters,
        reconfigureParameters,
    };
};
