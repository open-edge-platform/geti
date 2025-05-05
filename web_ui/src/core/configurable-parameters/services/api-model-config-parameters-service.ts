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
import { ProjectConfiguration, TrainingConfiguration } from './configuration.interface';
import {
    getConfigParametersEntity,
    getModelConfigEntity,
    getProjectConfigurationEntity,
    getTrainingConfigurationEntity,
} from './utils';

export type TrainingConfigurationQueryParameters = Partial<{ taskId: string; algorithmId: string; modelId: string }>;

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

    getProjectConfiguration: (projectIdentifier: ProjectIdentifier) => Promise<ProjectConfiguration>;
    getTrainingConfiguration: (
        projectIdentifier: ProjectIdentifier,
        queryParameters?: TrainingConfigurationQueryParameters
    ) => Promise<TrainingConfiguration>;
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

    const getTrainingConfiguration: CreateApiModelConfigParametersService['getTrainingConfiguration'] = async (
        projectIdentifier,
        queryParameters
    ): Promise<TrainingConfiguration> => {
        const { data } = await instance.get(router.CONFIGURATION.TRAINING(projectIdentifier), {
            params: {
                task_id: queryParameters?.taskId,
                model_id: queryParameters?.modelId,
                algorithm_id: queryParameters?.algorithmId,
            },
        });

        return getTrainingConfigurationEntity(data);
    };

    const getProjectConfiguration: CreateApiModelConfigParametersService['getProjectConfiguration'] = async (
        projectIdentifier
    ) => {
        const { data } = await instance.get<ProjectConfigurationDTO>(router.CONFIGURATION.PROJECT(projectIdentifier));

        return getProjectConfigurationEntity(data);
    };

    return {
        getModelConfigParameters,
        getConfigParameters,
        reconfigureParameters,
        getProjectConfiguration,
        getTrainingConfiguration,
    };
};
